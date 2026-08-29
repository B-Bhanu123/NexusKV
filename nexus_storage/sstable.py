"""
NexusKV SSTable (Sorted String Table) Engine
============================================

Handles immutable on-disk SSTables for persistent LSM-Tree levels.
Features:
- Binary Block-based Data Section
- Sparse Index Block for binary search
- Bloom Filter integration for fast non-membership checks
- SSTable Footer with magic number, block offset, and checksum
"""

import os
import struct
import zlib
from typing import List, Tuple, Optional, Generator
from dataclasses import dataclass
from .bloom_filter import BloomFilter

SSTABLE_MAGIC_NUMBER = 0x4E45585553535354  # "NEXUSSST" in hex

@dataclass
class SSTableIndexEntry:
    key: bytes
    offset: int
    size: int

class SSTableIndexBlock:
    def __init__(self):
        self.entries: List[SSTableIndexEntry] = []

    def serialize(self) -> bytes:
        buf = bytearray()
        buf.extend(struct.pack("!I", len(self.entries)))
        for entry in self.entries:
            key_bytes = entry.key
            buf.extend(struct.pack("!I", len(key_bytes)))
            buf.extend(key_bytes)
            buf.extend(struct.pack("!QI", entry.offset, entry.size))
        return bytes(buf)

    @classmethod
    def deserialize(cls, data: bytes) -> "SSTableIndexBlock":
        idx_block = cls()
        num_entries = struct.unpack("!I", data[:4])[0]
        offset = 4
        for _ in range(num_entries):
            k_len = struct.unpack("!I", data[offset:offset+4])[0]
            offset += 4
            key = data[offset:offset+k_len]
            offset += k_len
            off, size = struct.unpack("!QI", data[offset:offset+12])
            offset += 12
            idx_block.entries.append(SSTableIndexEntry(key, off, size))
        return idx_block


class SSTableWriter:
    def __init__(self, filepath: str, block_size_bytes: int = 4096):
        self.filepath = filepath
        self.block_size_bytes = block_size_bytes
        self.bloom_filter = BloomFilter(expected_items=10000, fp_rate=0.01)
        self.index_block = SSTableIndexBlock()
        self.first_key: Optional[bytes] = None
        self.last_key: Optional[bytes] = None
        self.entry_count = 0

    def write_from_memtable(self, memtable_iter: Generator[Tuple[bytes, Optional[bytes]], None, None]):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "wb") as f:
            data_block_buf = bytearray()
            block_start_offset = 0
            first_key_in_block = None

            for key, val in memtable_iter:
                if self.first_key is None:
                    self.first_key = key
                self.last_key = key
                self.bloom_filter.add(key)
                self.entry_count += 1

                val_bytes = val if val is not None else b"__NEXUS_TOMBSTONE__"
                is_tombstone = 1 if val is None else 0
                
                entry_data = struct.pack("!IB", len(key), is_tombstone) + key + struct.pack("!I", len(val_bytes)) + val_bytes
                
                if first_key_in_block is None:
                    first_key_in_block = key
                    
                data_block_buf.extend(entry_data)

                if len(data_block_buf) >= self.block_size_bytes:
                    f.write(data_block_buf)
                    block_len = len(data_block_buf)
                    self.index_block.entries.append(SSTableIndexEntry(first_key_in_block, block_start_offset, block_len))
                    block_start_offset += block_len
                    data_block_buf = bytearray()
                    first_key_in_block = None

            if len(data_block_buf) > 0:
                f.write(data_block_buf)
                block_len = len(data_block_buf)
                self.index_block.entries.append(SSTableIndexEntry(first_key_in_block, block_start_offset, block_len))
                block_start_offset += block_len

            # 1. Write Index Block
            index_offset = f.tell()
            index_bytes = self.index_block.serialize()
            f.write(index_bytes)
            index_len = len(index_bytes)

            # 2. Write Bloom Filter Block
            bloom_offset = f.tell()
            bloom_bytes = self.bloom_filter.serialize()
            f.write(bloom_bytes)
            bloom_len = len(bloom_bytes)

            # 3. Write Footer [IndexOff (8B)][IndexLen (4B)][BloomOff (8B)][BloomLen (4B)][Magic (8B)]
            footer = struct.pack("!QIQIQ", index_offset, index_len, bloom_offset, bloom_len, SSTABLE_MAGIC_NUMBER)
            f.write(footer)


class SSTableReader:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.index_block: Optional[SSTableIndexBlock] = None
        self.bloom_filter: Optional[BloomFilter] = None
        self._load_metadata()

    def _load_metadata(self):
        file_size = os.path.getsize(self.filepath)
        if file_size < 32:
            raise ValueError(f"Invalid SSTable file size: {file_size}")

        with open(self.filepath, "rb") as f:
            f.seek(file_size - 32)
            footer_bytes = f.read(32)
            index_off, index_len, bloom_off, bloom_len, magic = struct.unpack("!QIQIQ", footer_bytes)

            if magic != SSTABLE_MAGIC_NUMBER:
                raise ValueError("Invalid SSTable magic header")

            # Read Index Block
            f.seek(index_off)
            index_data = f.read(index_len)
            self.index_block = SSTableIndexBlock.deserialize(index_data)

            # Read Bloom Filter Block
            f.seek(bloom_off)
            bloom_data = f.read(bloom_len)
            self.bloom_filter = BloomFilter.deserialize(bloom_data)

    def get(self, key: bytes) -> Tuple[bool, Optional[bytes]]:
        if self.bloom_filter and not self.bloom_filter.contains(key):
            return False, None

        # Binary search in index block
        target_entry = None
        for i, entry in enumerate(self.index_block.entries):
            if entry.key <= key:
                target_entry = entry
            else:
                break

        if not target_entry:
            return False, None

        with open(self.filepath, "rb") as f:
            f.seek(target_entry.offset)
            block_data = f.read(target_entry.size)
            offset = 0
            while offset < len(block_data):
                key_len, is_tomb = struct.unpack("!IB", block_data[offset:offset+5])
                offset += 5
                curr_key = block_data[offset:offset+key_len]
                offset += key_len
                val_len = struct.unpack("!I", block_data[offset:offset+4])[0]
                offset += 4
                curr_val = block_data[offset:offset+val_len]
                offset += val_len

                if curr_key == key:
                    if is_tomb == 1:
                        return True, None
                    return True, curr_val

        return False, None

    def scan_all(self) -> Generator[Tuple[bytes, Optional[bytes]], None, None]:
        with open(self.filepath, "rb") as f:
            for entry in self.index_block.entries:
                f.seek(entry.offset)
                block_data = f.read(entry.size)
                offset = 0
                while offset < len(block_data):
                    key_len, is_tomb = struct.unpack("!IB", block_data[offset:offset+5])
                    offset += 5
                    curr_key = block_data[offset:offset+key_len]
                    offset += key_len
                    val_len = struct.unpack("!I", block_data[offset:offset+4])[0]
                    offset += 4
                    curr_val = block_data[offset:offset+val_len]
                    offset += val_len

                    val = None if is_tomb == 1 else curr_val
                    yield curr_key, val
