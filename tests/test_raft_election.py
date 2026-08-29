"""
Test Suite 2: Raft Leader Election Tests
==========================================
Tests candidate promotion, term advancement, and vote request handling.
"""

import os
import shutil
import unittest
from nexus_consensus.raft_node import RaftNode, NodeRole
from nexus_consensus.raft_rpc import RequestVoteRequest

TEST_DIR = "./tmp_test_raft_election"

class TestRaftElection(unittest.TestCase):
    def setUp(self):
        os.makedirs(TEST_DIR, exist_ok=True)

    def tearDown(self):
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)

    def test_initial_follower_state(self):
        log_dir = os.path.join(TEST_DIR, "node1")
        node = RaftNode(node_id="node1", peers=["node2", "node3"], log_dir=log_dir)
        self.assertEqual(node.role, NodeRole.FOLLOWER)
        self.assertEqual(node.current_term, 0)

    def test_handle_vote_request(self):
        log_dir = os.path.join(TEST_DIR, "node1")
        node = RaftNode(node_id="node1", peers=["node2", "node3"], log_dir=log_dir)

        req = RequestVoteRequest(term=1, candidate_id="node2", last_log_index=0, last_log_term=0)
        resp = node.handle_request_vote(req)

        self.assertTrue(resp.vote_granted)
        self.assertEqual(resp.term, 1)
        self.assertEqual(node.voted_for, "node2")

    def test_reject_older_term_vote(self):
        log_dir = os.path.join(TEST_DIR, "node1")
        node = RaftNode(node_id="node1", peers=["node2", "node3"], log_dir=log_dir)
        node.current_term = 5

        req = RequestVoteRequest(term=3, candidate_id="node2", last_log_index=0, last_log_term=0)
        resp = node.handle_request_vote(req)

        self.assertFalse(resp.vote_granted)
        self.assertEqual(resp.term, 5)

if __name__ == "__main__":
    unittest.main()
