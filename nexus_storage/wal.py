"""
NexusKV Write-Ahead Log (WAL) Implementation
============================================

Provides persistent durability for all write operations before committing to MemTable.
Includes binary payload framing, CRC32 integrity verification, segment rotation,
and crash recovery.
"""

import os
import struct
import zlib
import time
import logging
from enum import IntEnum
from typing import Generator, Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger("NexusKV.Storage.WAL")

class WALOpType(IntEnum):
    PUT = 1
    DELETE = 2
    BATCH = 3
    CHECKPOINT = 4
    TXN_BEGIN = 5
    TXN_COMMIT = 6
    TXN_ABORT = 7

@dataclass
class WALEntry:
    sequence_number: int
    timestamp: float
    op_type: WALOpType
    key: bytes
    value: bytes
    transaction_id: Optional[str] = None

    def serialize(self) -> bytes:
        """
        Binary Format:
        [CRC32 (4B)][SeqNo (8B)][Timestamp (8B)][OpType (1B)][TxnLen (2B)][TxnID][KeyLen (4B)][Key][ValLen (4B)][Val]
        """
        txn_bytes = self.transaction_id.encode('utf-8') if self.transaction_id else b""
        payload = struct.pack(
            "!QdBH",
            self.sequence_number,
            self.timestamp,
            int(self.op_type),
            len(txn_bytes)
        ) + txn_bytes + struct.pack("!I", len(self.key)) + self.key + struct.pack("!I", len(self.value)) + self.value
        
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        return struct.pack("!I", crc) + payload

    @classmethod
    def deserialize(cls, raw_data: bytes) -> Tuple["WALEntry", int]:
        if len(raw_data) < 4:
            raise ValueError("Buffer too small for CRC header")
        
        stored_crc = struct.unpack("!I", raw_data[:4])[0]
        payload = raw_data[4:]
        
        calculated_crc = zlib.crc32(payload) & 0xFFFFFFFF
        if stored_crc != calculated_crc:
            raise ValueError(f"WAL Corrupted: CRC mismatch. Stored={stored_crc}, Calc={calculated_crc}")
        
        seq_num, timestamp, op_val, txn_len = struct.unpack("!QdBH", payload[:19])
        offset = 19
        
        txn_id = None
        if txn_len > 0:
            txn_id = payload[offset:offset+txn_len].decode('utf-8')
            offset += txn_len
            
        key_len = struct.unpack("!I", payload[offset:offset+4])[0]
        offset += 4
        key = payload[offset:offset+key_len]
        offset += key_len
        
        val_len = struct.unpack("!I", payload[offset:offset+4])[0]
        offset += 4
        value = payload[offset:offset+val_len]
        offset += val_len
        
        total_read = 4 + offset
        entry = cls(
            sequence_number=seq_num,
            timestamp=timestamp,
            op_type=WALOpType(op_val),
            key=key,
            value=value,
            transaction_id=txn_id
        )
        return entry, total_read


class WriteAheadLog:
    def __init__(self, wal_dir: str, max_segment_size_bytes: int = 33554432):
        self.wal_dir = wal_dir
        self.max_segment_size_bytes = max_segment_size_bytes
        self.current_segment_id = 0
        self.current_file = None
        self.current_sequence_number = 0
        
        os.makedirs(self.wal_dir, exist_ok=True)
        self._init_latest_segment()

    def _init_latest_segment(self):
        segments = self._get_sorted_segment_files()
        if segments:
            self.current_segment_id = segments[-1][0]
        else:
            self.current_segment_id = 1
        
        filepath = self._segment_path(self.current_segment_id)
        self.current_file = open(filepath, "a+b")

    def _segment_path(self, segment_id: int) -> str:
        return os.path.join(self.wal_dir, f"wal_{segment_id:08d}.log")

    def _get_sorted_segment_files(self) -> List[Tuple[int, str]]:
        files = []
        for filename in os.listdir(self.wal_dir):
            if filename.startswith("wal_") and filename.endswith(".log"):
                try:
                    seg_id = int(filename.split("_")[1].split(".")[0])
                    files.append((seg_id, os.path.join(self.wal_dir, filename)))
                except ValueError:
                    continue
        return sorted(files, key=lambda x: x[0])

    def append(self, op_type: WALOpType, key: bytes, value: bytes, transaction_id: Optional[str] = None) -> int:
        self.current_sequence_number += 1
        entry = WALEntry(
            sequence_number=self.current_sequence_number,
            timestamp=time.time(),
            op_type=op_type,
            key=key,
            value=value,
            transaction_id=transaction_id
        )
        data = entry.serialize()
        record_bytes = struct.pack("!I", len(data)) + data
        
        self.current_file.write(record_bytes)
        self.current_file.flush()
        
        if self.current_file.tell() >= self.max_segment_size_bytes:
            self.rotate()
            
        return self.current_sequence_number

    def rotate(self):
        if self.current_file:
            self.current_file.flush()
            os.fsync(self.current_file.fileno())
            self.current_file.close()
            
        self.current_segment_id += 1
        new_path = self._segment_path(self.current_segment_id)
        self.current_file = open(new_path, "a+b")
        logger.info(f"WAL rotated to segment: {self.current_segment_id}")

    def recover(self) -> Generator[WALEntry, None, None]:
        segments = self._get_sorted_segment_files()
        for seg_id, path in segments:
            if not os.path.exists(path):
                continue
            with open(path, "rb") as f:
                while True:
                    length_bytes = f.read(4)
                    if not length_bytes or len(length_bytes) < 4:
                        break
                    record_len = struct.unpack("!I", length_bytes)[0]
                    record_data = f.read(record_len)
                    if len(record_data) < record_len:
                        logger.warning(f"Truncated WAL record in segment {seg_id}")
                        break
                    try:
                        entry, _ = WALEntry.deserialize(record_data)
                        if entry.sequence_number > self.current_sequence_number:
                            self.current_sequence_number = entry.sequence_number
                        yield entry
                    except Exception as e:
                        logger.error(f"Failed deserializing WAL entry in segment {seg_id}: {e}")
                        break

    def purge_old_segments(self, min_sequence_to_keep: int):
        segments = self._get_sorted_segment_files()
        for seg_id, path in segments:
            if seg_id < self.current_segment_id:
                try:
                    os.remove(path)
                    logger.info(f"Purged obsolete WAL segment: {path}")
                except OSError as e:
                    logger.error(f"Error purging WAL segment {path}: {e}")

    def close(self):
        if self.current_file:
            self.current_file.flush()
            os.fsync(self.current_file.fileno())
            self.current_file.close()
            self.current_file = None
