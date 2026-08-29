"""
NexusKV Consistent Hashing & Sharding Engine
============================================

Implements Virtual Node Consistent Hash Ring for partition distribution,
replication placement, and node membership rebalancing.
"""

import hashlib
import bisect
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ShardLocation:
    shard_id: int
    primary_node: str
    replica_nodes: List[str]

class ConsistentHashRing:
    def __init__(self, num_virtual_nodes: int = 256, replication_factor: int = 3):
        self.num_virtual_nodes = num_virtual_nodes
        self.replication_factor = replication_factor
        self.ring: Dict[int, str] = {}  # hash_value -> physical_node_id
        self.sorted_hashes: List[int] = []
        self.nodes: set = set()

    def _hash(self, key: str) -> int:
        md5_hex = hashlib.md5(key.encode("utf-8")).hexdigest()
        return int(md5_hex[:8], 16)

    def add_node(self, node_id: str):
        if node_id in self.nodes:
            return
        self.nodes.add(node_id)
        for i in range(self.num_virtual_nodes):
            vnode_key = f"{node_id}-vnode-{i}"
            h = self._hash(vnode_key)
            self.ring[h] = node_id
            bisect.insort(self.sorted_hashes, h)

    def remove_node(self, node_id: str):
        if node_id not in self.nodes:
            return
        self.nodes.remove(node_id)
        for i in range(self.num_virtual_nodes):
            vnode_key = f"{node_id}-vnode-{i}"
            h = self._hash(vnode_key)
            if h in self.ring:
                del self.ring[h]
                idx = bisect.bisect_left(self.sorted_hashes, h)
                if idx < len(self.sorted_hashes) and self.sorted_hashes[idx] == h:
                    self.sorted_hashes.pop(idx)

    def get_node(self, key: str) -> Optional[str]:
        if not self.ring:
            return None
        h = self._hash(key)
        idx = bisect.bisect_right(self.sorted_hashes, h)
        if idx == len(self.sorted_hashes):
            idx = 0
        return self.ring[self.sorted_hashes[idx]]

    def get_preference_list(self, key: str) -> List[str]:
        if not self.ring:
            return []
        h = self._hash(key)
        idx = bisect.bisect_right(self.sorted_hashes, h)

        preference_list = []
        seen_nodes = set()

        for i in range(len(self.sorted_hashes)):
            curr_idx = (idx + i) % len(self.sorted_hashes)
            node_id = self.ring[self.sorted_hashes[curr_idx]]
            if node_id not in seen_nodes:
                seen_nodes.add(node_id)
                preference_list.append(node_id)
                if len(preference_list) == min(self.replication_factor, len(self.nodes)):
                    break

        return preference_list
