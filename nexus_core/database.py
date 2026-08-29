"""
NexusKV Main Database Engine
============================

Unified database engine bringing together Write-Ahead Logging (WAL), MemTable,
SSTables, Compaction, Block Cache, and Raft Consensus replication.
"""

import os
import threading
import logging
from typing import Tuple, Optional, Dict, Any, List, Generator
from nexus_storage.wal import WriteAheadLog, WALOpType
from nexus_storage.memtable import SkipListMemTable
from nexus_storage.sstable import SSTableWriter, SSTableReader
from nexus_storage.compaction import CompactionManager
from nexus_storage.cache import LRUCache

logger = logging.getLogger("NexusKV.Core.Database")

class NexusDatabase:
    def __init__(self, data_dir: str = "./data/node-1", memtable_max_bytes: int = 67108864):
        self.data_dir = data_dir
        self.memtable_max_bytes = memtable_max_bytes

        os.makedirs(self.data_dir, exist_ok=True)
        wal_dir = os.path.join(self.data_dir, "wal")
        sst_dir = os.path.join(self.data_dir, "sst")
        os.makedirs(sst_dir, exist_ok=True)

        self.wal = WriteAheadLog(wal_dir)
        self.memtable = SkipListMemTable(max_size_bytes=memtable_max_bytes)
        self.immutable_memtables: List[SkipListMemTable] = []
        self.compaction_mgr = CompactionManager(sst_dir)
        self.block_cache = LRUCache(capacity_bytes=134217728)  # 128MB Cache

        self.lock = threading.RLock()
        self._stats = {"gets": 0, "puts": 0, "deletes": 0, "flushes": 0}

        # Recover from existing WAL
        self._recover_from_wal()

    def _recover_from_wal(self):
        logger.info("Recovering database state from WAL...")
        count = 0
        for entry in self.wal.recover():
            count += 1
            if entry.op_type == WALOpType.PUT:
                self.memtable.put(entry.key, entry.value)
            elif entry.op_type == WALOpType.DELETE:
                self.memtable.put(entry.key, None)
        logger.info(f"WAL recovery completed. Restored {count} operations.")

    def put(self, key: bytes, value: bytes) -> bool:
        with self.lock:
            self._stats["puts"] += 1
            # 1. Write to WAL
            self.wal.append(WALOpType.PUT, key, value)

            # 2. Write to MemTable
            self.memtable.put(key, value)

            # 3. Check if MemTable requires flushing to SSTable
            if self.memtable.is_full():
                self.flush_memtable()

            return True

    def get(self, key: bytes) -> Tuple[bool, Optional[bytes]]:
        with self.lock:
            self._stats["gets"] += 1

            # 1. Check active MemTable
            found, val = self.memtable.get(key)
            if found:
                return True, val

            # 2. Check immutable MemTables
            for imm in reversed(self.immutable_memtables):
                found, val = imm.get(key)
                if found:
                    return True, val

            # 3. Check Block Cache
            cached_val = self.block_cache.get(key)
            if cached_val is not None:
                return True, cached_val

            # 4. Search SSTable levels on disk
            for lvl in range(self.compaction_mgr.max_levels):
                for sst_path in self.compaction_mgr.levels[lvl]:
                    try:
                        reader = SSTableReader(sst_path)
                        found, val = reader.get(key)
                        if found:
                            if val is not None:
                                self.block_cache.put(key, val, len(key) + len(val))
                            return True, val
                    except Exception as e:
                        logger.error(f"Error reading SSTable {sst_path}: {e}")

            return False, None

    def delete(self, key: bytes) -> bool:
        with self.lock:
            self._stats["deletes"] += 1
            self.wal.append(WALOpType.DELETE, key, b"")
            self.memtable.delete(key)
            return True

    def flush_memtable(self):
        with self.lock:
            if self.memtable.item_count == 0:
                return

            self._stats["flushes"] += 1
            logger.info("Flushing MemTable to SSTable Level 0...")

            sst_path = os.path.join(self.data_dir, "sst", f"level_0_{os.urandom(4).hex()}.sst")
            writer = SSTableWriter(sst_path)
            writer.write_from_memtable(self.memtable.scan())

            # Register with compaction manager
            self.compaction_mgr.add_sstable(sst_path, level=0)

            # Reset MemTable
            self.memtable = SkipListMemTable(max_size_bytes=self.memtable_max_bytes)

    def scan(self, start_key: Optional[bytes] = None, end_key: Optional[bytes] = None) -> Generator[Tuple[bytes, Optional[bytes]], None, None]:
        with self.lock:
            # Merged view over MemTable and Disk SSTables
            seen = set()
            for k, v in self.memtable.scan(start_key, end_key):
                seen.add(k)
                if v is not None:
                    yield k, v

            for lvl in range(self.compaction_mgr.max_levels):
                for sst_path in self.compaction_mgr.levels[lvl]:
                    try:
                        reader = SSTableReader(sst_path)
                        for k, v in reader.scan_all():
                            if k not in seen:
                                seen.add(k)
                                if (not start_key or k >= start_key) and (not end_key or k <= end_key):
                                    if v is not None:
                                        yield k, v
                    except Exception:
                        pass

    def get_cluster_status(self) -> Dict[str, Any]:
        return {
            "node_id": "node-1",
            "status": "HEALTHY",
            "active_level_0_sstables": len(self.compaction_mgr.levels[0]),
            "memtable_bytes": self.memtable.current_size_bytes,
        }

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "stats": self._stats,
            "cache_items": len(self.block_cache.cache),
            "wal_sequence": self.wal.current_sequence_number
        }

    def close(self):
        with self.lock:
            self.flush_memtable()
            self.wal.close()
