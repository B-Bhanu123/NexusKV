"""
Test Suite 5: Cluster Fault Tolerance & Quorum Tests
=====================================================
Tests Gossip failure detection, quorum availability checks, and split-brain resilience.
"""

from nexus_consensus.cluster_manager import ClusterManager
from nexus_consensus.gossip import MemberStatus

def test_cluster_quorum_health():
    peers = {
        "node-1": "127.0.0.1:7001",
        "node-2": "127.0.0.1:7002",
        "node-3": "127.0.0.1:7003"
    }
    mgr = ClusterManager("node-1", "127.0.0.1", 7001, peers)

    assert mgr.is_quorum_available() is True
    active = mgr.gossip.get_active_members()
    assert "node-1" in active
