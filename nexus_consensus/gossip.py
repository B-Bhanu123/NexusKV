"""
NexusKV SWIM Gossip Protocol Engine
===================================

Provides decentralized node membership discovery, health heartbeats,
failure detection via indirect pinging, and suspect state transitions.
"""

import time
import random
import threading
import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("NexusKV.Consensus.Gossip")

class MemberStatus(Enum):
    ALIVE = "ALIVE"
    SUSPECT = "SUSPECT"
    DEAD = "DEAD"

class MemberInfo:
    def __init__(self, node_id: str, address: str, port: int, incarnation: int = 0):
        self.node_id = node_id
        self.address = address
        self.port = port
        self.incarnation = incarnation
        self.status = MemberStatus.ALIVE
        self.last_state_change = time.time()

class GossipNode:
    def __init__(self, node_id: str, address: str, port: int, ping_interval_sec: float = 1.0):
        self.node_id = node_id
        self.address = address
        self.port = port
        self.ping_interval_sec = ping_interval_sec
        self.members: Dict[str, MemberInfo] = {
            node_id: MemberInfo(node_id, address, port, incarnation=1)
        }
        self.lock = threading.RLock()
        self.is_running = False

    def add_member(self, node_id: str, address: str, port: int):
        with self.lock:
            if node_id not in self.members:
                self.members[node_id] = MemberInfo(node_id, address, port)
                logger.info(f"Gossip discovered member: {node_id} ({address}:{port})")

    def remove_member(self, node_id: str):
        with self.lock:
            if node_id in self.members:
                del self.members[node_id]

    def mark_suspect(self, node_id: str):
        with self.lock:
            member = self.members.get(node_id)
            if member and member.status == MemberStatus.ALIVE:
                member.status = MemberStatus.SUSPECT
                member.last_state_change = time.time()
                logger.warning(f"Member {node_id} marked as SUSPECT")

    def mark_dead(self, node_id: str):
        with self.lock:
            member = self.members.get(node_id)
            if member and member.status != MemberStatus.DEAD:
                member.status = MemberStatus.DEAD
                member.last_state_change = time.time()
                logger.error(f"Member {node_id} marked as DEAD")

    def select_random_members(self, count: int = 3, exclude: Optional[List[str]] = None) -> List[MemberInfo]:
        with self.lock:
            exclude_set = set(exclude) if exclude else set()
            exclude_set.add(self.node_id)
            candidates = [m for k, m in self.members.items() if k not in exclude_set and m.status != MemberStatus.DEAD]
            return random.sample(candidates, min(count, len(candidates)))

    def ping_member(self, target: MemberInfo) -> bool:
        """Simulates direct gossip ping."""
        if target.status == MemberStatus.DEAD:
            return False
        return True

    def run_gossip_cycle(self):
        with self.lock:
            targets = self.select_random_members(count=1)
            if not targets:
                return

            target = targets[0]
            success = self.ping_member(target)

            if not success:
                # Indirect Ping via 2 helpers
                helpers = self.select_random_members(count=2, exclude=[target.node_id])
                indirect_success = any(self.ping_member(h) for h in helpers)

                if not indirect_success:
                    self.mark_suspect(target.node_id)
            else:
                if target.status == MemberStatus.SUSPECT:
                    target.status = MemberStatus.ALIVE
                    target.incarnation += 1

            # Check suspect timeout (e.g. 5 sec -> DEAD)
            now = time.time()
            for m_id, member in list(self.members.items()):
                if member.status == MemberStatus.SUSPECT and (now - member.last_state_change) > 5.0:
                    self.mark_dead(m_id)

    def get_active_members(self) -> List[str]:
        with self.lock:
            return [m_id for m_id, m in self.members.items() if m.status == MemberStatus.ALIVE]
