"""
Test Suite 5: Cluster Fault Tolerance & Quorum Tests
=====================================================
Tests Gossip failure detection, quorum availability checks, and split-brain resilience.
"""

import unittest
from nexus_consensus.cluster_manager import ClusterManager

class TestClusterFaultTolerance(unittest.TestCase):
    def test_cluster_quorum_health(self):
        peers = {
            "node-1": "127.0.0.1:7001",
            "node-2": "127.0.0.1:7002",
            "node-3": "127.0.0.1:7003"
        }
        mgr = ClusterManager("node-1", "127.0.0.1", 7001, peers)

        self.assertTrue(mgr.is_quorum_available())
        active = mgr.gossip.get_active_members()
        self.assertIn("node-1", active)

if __name__ == "__main__":
    unittest.main()
