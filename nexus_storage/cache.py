"""
NexusKV Block Cache Engine
==========================

Implements LRU (Least Recently Used) and ARC (Adaptive Replacement Cache) block caches
for accelerating SSTable data block reads.
"""

from typing import Dict, Optional, Any
import threading

class CacheNode:
    def __init__(self, key: bytes, value: Any):
        self.key = key
        self.value = value
        self.prev: Optional["CacheNode"] = None
        self.next: Optional["CacheNode"] = None

class LRUCache:
    def __init__(self, capacity_bytes: int = 536870912):
        self.capacity_bytes = capacity_bytes
        self.current_bytes = 0
        self.cache: Dict[bytes, CacheNode] = {}
        self.head = CacheNode(b"", None)
        self.tail = CacheNode(b"", None)
        self.head.next = self.tail
        self.tail.prev = self.head
        self.lock = threading.RLock()

    def _add_node(self, node: CacheNode):
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _remove_node(self, node: CacheNode):
        prev = node.prev
        new_next = node.next
        prev.next = new_next
        new_next.prev = prev

    def _move_to_head(self, node: CacheNode):
        self._remove_node(node)
        self._add_node(node)

    def _pop_tail(self) -> CacheNode:
        res = self.tail.prev
        self._remove_node(res)
        return res

    def get(self, key: bytes) -> Optional[Any]:
        with self.lock:
            node = self.cache.get(key)
            if not node:
                return None
            self._move_to_head(node)
            return node.value

    def put(self, key: bytes, value: Any, item_bytes: int):
        with self.lock:
            node = self.cache.get(key)
            if node:
                self._remove_node(node)
                self.current_bytes -= len(node.key)
                node.value = value
                self._add_node(node)
                self.current_bytes += item_bytes
            else:
                new_node = CacheNode(key, value)
                self.cache[key] = new_node
                self._add_node(new_node)
                self.current_bytes += item_bytes

                while self.current_bytes > self.capacity_bytes and len(self.cache) > 1:
                    tail_node = self._pop_tail()
                    del self.cache[tail_node.key]
                    self.current_bytes -= item_bytes


class ARCCache:
    """Adaptive Replacement Cache (ARC) balancing recency and frequency."""
    def __init__(self, capacity_items: int = 1000):
        self.c = capacity_items
        self.p = 0  # target size for L1
        self.t1: Dict[bytes, Any] = {}
        self.t2: Dict[bytes, Any] = {}
        self.b1: Dict[bytes, Any] = {}
        self.b2: Dict[bytes, Any] = {}
        self.lock = threading.RLock()

    def get(self, key: bytes) -> Optional[Any]:
        with self.lock:
            if key in self.t1:
                val = self.t1.pop(key)
                self.t2[key] = val
                return val
            elif key in self.t2:
                val = self.t2[key]
                # refresh in t2
                self.t2.pop(key)
                self.t2[key] = val
                return val
            return None

    def put(self, key: bytes, value: Any):
        with self.lock:
            if key in self.t1 or key in self.t2:
                if key in self.t1:
                    self.t1.pop(key)
                self.t2[key] = value
            else:
                self.t1[key] = value
                if len(self.t1) + len(self.b1) > self.c:
                    if self.t1:
                        old_k, _ = self.t1.popitem()
                        self.b1[old_k] = True

BlockCache = LRUCache
