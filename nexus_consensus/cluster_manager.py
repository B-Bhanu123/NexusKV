"""
NexusKV Cluster Manager Engine
=============================

Orchestrates Raft state machines, Gossip nodes, Consistent Hash Rings,
and cluster topology monitoring to ensure split-brain protection and HA.
"""

import logging
import threading
from typing import Dict, List, Optional
from .raft_node import RaftNode
from .gossip import GossipNode
from .sharding import ConsistentHashRing

logger = logging.getLogger("NexusKV.Consensus.ClusterManager")

class ClusterManager:
    def __init__(self, node_id: str, node_address: str, raft_port: int, initial_peers: Dict[str, str]):
        self.node_id = node_id
        self.node_address = node_address
        self.raft_port = raft_port
        self.initial_peers = initial_peers  # node_id -> "host:port"

        # Gossip & Sharding
        self.gossip = GossipNode(node_id, node_address, raft_port)
        self.hash_ring = ConsistentHashRing(num_virtual_nodes=256, replication_factor=3)
        self.hash_ring.add_node(node_id)

        # Register initial peers
        for peer_id, addr_str in initial_peers.items():
            if peer_id != node_id:
                host, port_s = addr_str.split(":")
                self.gossip.add_member(peer_id, host, int(port_s))
                self.hash_ring.add_node(peer_id)

        # Raft Node instance
        peer_ids = [p for p in initial_peers.keys() if p != node_id]
        self.raft = RaftNode(node_id=node_id, peers=peer_ids, log_dir=f"./data/{node_id}/raft")
        self.lock = threading.RLock()

    def sync_topology(self):
        with self.lock:
            active = self.gossip.get_active_members()
            for member_id in active:
                if member_id not in self.hash_ring.nodes:
                    self.hash_ring.add_node(member_id)

            for existing_node in list(self.hash_ring.nodes):
                if existing_node not in active:
                    self.hash_ring.remove_node(existing_node)

    def route_key(self, key: str) -> Optional[str]:
        return self.hash_ring.get_node(key)

    def get_replicas_for_key(self, key: str) -> List[str]:
        return self.hash_ring.get_preference_list(key)

    def is_quorum_available(self) -> bool:
        active_count = len(self.gossip.get_active_members())
        total_count = len(self.initial_peers)
        return active_count >= ((total_count // 2) + 1)
