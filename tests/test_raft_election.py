"""
Test Suite 2: Raft Leader Election Tests
==========================================
Tests candidate promotion, term advancement, and vote request handling.
"""

import os
import shutil
import pytest
from nexus_consensus.raft_node import RaftNode, NodeRole
from nexus_consensus.raft_rpc import RequestVoteRequest

TEST_DIR = "./tmp_test_raft_election"

@pytest.fixture
def setup_teardown():
    os.makedirs(TEST_DIR, exist_ok=True)
    yield TEST_DIR
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

def test_initial_follower_state(setup_teardown):
    log_dir = os.path.join(setup_teardown, "node1")
    node = RaftNode(node_id="node1", peers=["node2", "node3"], log_dir=log_dir)
    assert node.role == NodeRole.FOLLOWER
    assert node.current_term == 0

def test_handle_vote_request(setup_teardown):
    log_dir = os.path.join(setup_teardown, "node1")
    node = RaftNode(node_id="node1", peers=["node2", "node3"], log_dir=log_dir)

    req = RequestVoteRequest(term=1, candidate_id="node2", last_log_index=0, last_log_term=0)
    resp = node.handle_request_vote(req)

    assert resp.vote_granted is True
    assert resp.term == 1
    assert node.voted_for == "node2"

def test_reject_older_term_vote(setup_teardown):
    log_dir = os.path.join(setup_teardown, "node1")
    node = RaftNode(node_id="node1", peers=["node2", "node3"], log_dir=log_dir)
    node.current_term = 5

    req = RequestVoteRequest(term=3, candidate_id="node2", last_log_index=0, last_log_term=0)
    resp = node.handle_request_vote(req)

    assert resp.vote_granted is False
    assert resp.term == 5
