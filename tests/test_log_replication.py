"""
Test Suite 3: Raft Log Replication Tests
=========================================
Tests AppendEntries RPC, state machine commit advancement, and log matching.
"""

import os
import shutil
import unittest
from nexus_consensus.raft_node import RaftNode
from nexus_consensus.raft_rpc import AppendEntriesRequest

TEST_DIR = "./tmp_test_raft_log"

class TestLogReplication(unittest.TestCase):
    def setUp(self):
        os.makedirs(TEST_DIR, exist_ok=True)

    def tearDown(self):
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)

    def test_append_entries_success(self):
        log_dir = os.path.join(TEST_DIR, "node1")
        node = RaftNode(node_id="node1", peers=["node2", "node3"], log_dir=log_dir)

        entries = [{"index": 1, "term": 1, "command": "PUT:k1:v1", "data": {}}]
        req = AppendEntriesRequest(term=1, leader_id="node2", prev_log_index=0, prev_log_term=0, entries=entries, leader_commit=1)

        resp = node.handle_append_entries(req)
        self.assertTrue(resp.success)
        self.assertEqual(resp.match_index, 1)
        self.assertEqual(node.commit_index, 1)

if __name__ == "__main__":
    unittest.main()
