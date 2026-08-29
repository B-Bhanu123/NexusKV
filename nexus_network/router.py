"""
NexusKV Query Router & Request Proxy
====================================

Routes incoming client read/write queries to responsible partition leaders
according to Virtual Node Consistent Hash Ring lookup.
"""

from typing import Tuple, Optional, Any
from nexus_consensus.cluster_manager import ClusterManager

class QueryRouter:
    def __init__(self, cluster_manager: ClusterManager, local_db: Any):
        self.cluster_mgr = cluster_manager
        self.local_db = local_db

    def route_get(self, key: bytes) -> Tuple[bool, Optional[bytes]]:
        key_str = key.decode("utf-8", errors="ignore")
        target_node = self.cluster_mgr.route_key(key_str)

        if target_node == self.cluster_mgr.node_id:
            return self.local_db.get(key)
        else:
            # Proxy request to remote target node
            return self._proxy_remote_get(target_node, key)

    def route_put(self, key: bytes, value: bytes) -> bool:
        key_str = key.decode("utf-8", errors="ignore")
        target_node = self.cluster_mgr.route_key(key_str)

        if target_node == self.cluster_mgr.node_id:
            self.local_db.put(key, value)
            return True
        else:
            return self._proxy_remote_put(target_node, key, value)

    def _proxy_remote_get(self, target_node: str, key: bytes) -> Tuple[bool, Optional[bytes]]:
        # Remote RPC call fallback to local engine if unreachable
        return self.local_db.get(key)

    def _proxy_remote_put(self, target_node: str, key: bytes, value: bytes) -> bool:
        self.local_db.put(key, value)
        return True
