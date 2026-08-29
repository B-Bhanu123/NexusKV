"""
NexusKV MemTable Module
======================

In-memory data structures for fast write buffering and range queries.
Implements SkipListMemTable and RedBlackMemTable with size tracking
and tombstone support for deleted keys.
"""

import random
import threading
from typing import Optional, List, Tuple, Generator, Dict

class SkipNode:
    def __init__(self, key: bytes, value: Optional[bytes], level: int):
        self.key = key
        self.value = value  # None indicates tombstone (deletion)
        self.forward = [None] * (level + 1)

class SkipListMemTable:
    MAX_LEVEL = 16
    P = 0.5

    def __init__(self, max_size_bytes: int = 67108864):
        self.max_size_bytes = max_size_bytes
        self.current_size_bytes = 0
        self.level = 0
        self.head = SkipNode(b"", None, self.MAX_LEVEL)
        self.lock = threading.RLock()
        self.item_count = 0

    def _random_level(self) -> int:
        lvl = 0
        while random.random() < self.P and lvl < self.MAX_LEVEL:
            lvl += 1
        return lvl

    def put(self, key: bytes, value: Optional[bytes]):
        with self.lock:
            update = [None] * (self.MAX_LEVEL + 1)
            curr = self.head
            
            for i in range(self.level, -1, -1):
                while curr.forward[i] and curr.forward[i].key < key:
                    curr = curr.forward[i]
                update[i] = curr
                
            curr = curr.forward[0]
            
            if curr and curr.key == key:
                old_val_len = len(curr.value) if curr.value else 0
                new_val_len = len(value) if value else 0
                self.current_size_bytes += (new_val_len - old_val_len)
                curr.value = value
            else:
                new_lvl = self._random_level()
                if new_lvl > self.level:
                    for i in range(self.level + 1, new_lvl + 1):
                        update[i] = self.head
                    self.level = new_lvl
                    
                new_node = SkipNode(key, value, new_lvl)
                for i in range(new_lvl + 1):
                    new_node.forward[i] = update[i].forward[i]
                    update[i].forward[i] = new_node
                    
                val_len = len(value) if value else 0
                self.current_size_bytes += (len(key) + val_len + 64)
                self.item_count += 1

    def get(self, key: bytes) -> Tuple[bool, Optional[bytes]]:
        """Returns (found: bool, value: Optional[bytes]). Note value=None means tombstone."""
        with self.lock:
            curr = self.head
            for i in range(self.level, -1, -1):
                while curr.forward[i] and curr.forward[i].key < key:
                    curr = curr.forward[i]
            curr = curr.forward[0]
            
            if curr and curr.key == key:
                return True, curr.value
            return False, None

    def delete(self, key: bytes):
        self.put(key, None)

    def scan(self, start_key: Optional[bytes] = None, end_key: Optional[bytes] = None) -> Generator[Tuple[bytes, Optional[bytes]], None, None]:
        with self.lock:
            curr = self.head.forward[0]
            if start_key:
                curr = self.head
                for i in range(self.level, -1, -1):
                    while curr.forward[i] and curr.forward[i].key < start_key:
                        curr = curr.forward[i]
                curr = curr.forward[0]
                
            while curr:
                if end_key and curr.key > end_key:
                    break
                yield curr.key, curr.value
                curr = curr.forward[0]

    def is_full(self) -> bool:
        return self.current_size_bytes >= self.max_size_bytes


class RedBlackMemTable:
    def __init__(self, max_size_bytes: int = 67108864):
        self.data: Dict[bytes, Optional[bytes]] = {}
        self.max_size_bytes = max_size_bytes
        self.current_size_bytes = 0
        self.lock = threading.RLock()

    def put(self, key: bytes, value: Optional[bytes]):
        with self.lock:
            if key in self.data:
                old_len = len(self.data[key]) if self.data[key] is not None else 0
                new_len = len(value) if value is not None else 0
                self.current_size_bytes += (new_len - old_len)
            else:
                val_len = len(value) if value is not None else 0
                self.current_size_bytes += (len(key) + val_len + 32)
            self.data[key] = value

    def get(self, key: bytes) -> Tuple[bool, Optional[bytes]]:
        with self.lock:
            if key in self.data:
                return True, self.data[key]
            return False, None

    def delete(self, key: bytes):
        self.put(key, None)

    def scan(self, start_key: Optional[bytes] = None, end_key: Optional[bytes] = None) -> Generator[Tuple[bytes, Optional[bytes]], None, None]:
        with self.lock:
            sorted_keys = sorted(self.data.keys())
            for k in sorted_keys:
                if start_key and k < start_key:
                    continue
                if end_key and k > end_key:
                    break
                yield k, self.data[k]

    def is_full(self) -> bool:
        return self.current_size_bytes >= self.max_size_bytes

MemTable = SkipListMemTable
