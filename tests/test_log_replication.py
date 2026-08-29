"""
Test Suite 3: Raft Log Replication Tests
=========================================
Tests AppendEntries RPC, state machine commit advancement, and log matching.
"""

import os
import shutil
import pytest
from nexus_consensus.raft_node import RaftNode, NodeRole
from nexus_consensus.raft_rpc import AppendEntriesRequest

TEST_DIR = "./tmp_test_raft_log"

@pytest.fixture
def setup_teardown():
    os.makedirs(TEST_DIR, exist_ok=True)
    yield TEST_DIR
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

def test_append_entries_success(setup_teardown):
    log_dir = os.path.join(setup_teardown, "node1")
    node = RaftNode(node_id="node1", peers=["node2", "node3"], log_dir=log_dir)

    entries = [{"index": 1, "term": 1, "command": "PUT:k1:v1", "data": {}}]
    req = AppendEntriesRequest(term=1, leader_id="node2", prev_log_index=0, prev_log_term=0, entries=entries, leader_commit=1)

    resp = node.handle_append_entries(req)
    assert resp.success is True
    assert resp.match_index == 1
    assert node.commit_index == 1
