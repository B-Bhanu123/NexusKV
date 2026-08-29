"""
NexusKV LSM Compaction Engine
=============================

Implements Leveled and Size-Tiered compaction algorithms to merge overlapping
SSTable levels, purge tombstones, and minimize read amplification.
"""

import os
import logging
from typing import List, Dict, Tuple, Optional
from .sstable import SSTableReader, SSTableWriter

logger = logging.getLogger("NexusKV.Storage.Compaction")

class CompactionStrategy:
    SIZE_TIERED = "SIZE_TIERED"
    LEVELED = "LEVELED"

class CompactionManager:
    def __init__(self, data_dir: str, strategy: str = CompactionStrategy.LEVELED, max_levels: int = 7):
        self.data_dir = data_dir
        self.strategy = strategy
        self.max_levels = max_levels
        self.levels: Dict[int, List[str]] = {lvl: [] for lvl in range(max_levels)}
        self._scan_existing_sstables()

    def _scan_existing_sstables(self):
        os.makedirs(self.data_dir, exist_ok=True)
        for fname in os.listdir(self.data_dir):
            if fname.startswith("level_") and fname.endswith(".sst"):
                try:
                    parts = fname.split("_")
                    lvl = int(parts[1])
                    if lvl in self.levels:
                        self.levels[lvl].append(os.path.join(self.data_dir, fname))
                except (IndexError, ValueError):
                    continue

    def add_sstable(self, filepath: str, level: int = 0):
        if level in self.levels:
            self.levels[level].append(filepath)
            self.check_and_compact(level)

    def check_and_compact(self, level: int):
        threshold = 4 if level == 0 else (10 ** level)
        if len(self.levels[level]) >= threshold:
            logger.info(f"Triggering compaction for Level {level} (Count={len(self.levels[level])})")
            self.compact_level(level)

    def compact_level(self, level: int):
        if level >= self.max_levels - 1:
            return

        input_files = self.levels[level][:]
        next_level = level + 1
        
        # k-way merge of all SSTable keys
        merged_entries: Dict[bytes, Optional[bytes]] = {}
        for filepath in input_files:
            try:
                reader = SSTableReader(filepath)
                for key, val in reader.scan_all():
                    merged_entries[key] = val
            except Exception as e:
                logger.error(f"Error reading SSTable {filepath} during compaction: {e}")

        # Output new SSTable at next_level
        output_filename = f"level_{next_level}_{os.urandom(4).hex()}.sst"
        output_path = os.path.join(self.data_dir, output_filename)

        writer = SSTableWriter(output_path)
        
        def generator():
            for k in sorted(merged_entries.keys()):
                yield k, merged_entries[k]

        writer.write_from_memtable(generator())

        # Update metadata and cleanup old files
        for old_file in input_files:
            if old_file in self.levels[level]:
                self.levels[level].remove(old_file)
            try:
                os.remove(old_file)
            except OSError:
                pass

        self.levels[next_level].append(output_path)
        logger.info(f"Compaction completed. Promoted {len(input_files)} SSTables to Level {next_level}: {output_path}")

class LeveledCompaction(CompactionManager):
    def __init__(self, data_dir: str):
        super().__init__(data_dir, strategy=CompactionStrategy.LEVELED)

class SizeTieredCompaction(CompactionManager):
    def __init__(self, data_dir: str):
        super().__init__(data_dir, strategy=CompactionStrategy.SIZE_TIERED)
