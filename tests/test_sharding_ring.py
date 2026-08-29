"""
Test Suite 4: Virtual Node Consistent Hashing Tests
===================================================
Tests key partition routing, preference list replication, and node topology changes.
"""

from nexus_consensus.sharding import ConsistentHashRing

def test_consistent_hash_ring_routing():
    ring = ConsistentHashRing(num_virtual_nodes=16, replication_factor=3)
    ring.add_node("node-1")
    ring.add_node("node-2")
    ring.add_node("node-3")

    node = ring.get_node("user_session_9901")
    assert node in ["node-1", "node-2", "node-3"]

    pref_list = ring.get_preference_list("user_session_9901")
    assert len(pref_list) == 3
    assert len(set(pref_list)) == 3  # All distinct nodes

def test_node_removal_rebalance():
    ring = ConsistentHashRing(num_virtual_nodes=16, replication_factor=2)
    ring.add_node("node-1")
    ring.add_node("node-2")

    target1 = ring.get_node("my_key")
    ring.remove_node("node-1")
    target2 = ring.get_node("my_key")

    assert target2 == "node-2"
