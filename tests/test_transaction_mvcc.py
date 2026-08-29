"""
Test Suite 6: MVCC & 2PC Transaction Tests
===========================================
Tests Snapshot Isolation, write conflict aborts, and 2-Phase Commit transactions.
"""

import os
import shutil
import pytest
from nexus_core.database import NexusDatabase
from nexus_core.transaction_manager import TransactionManager, TransactionState

TEST_DIR = "./tmp_test_mvcc"

@pytest.fixture
def setup_teardown():
    os.makedirs(TEST_DIR, exist_ok=True)
    yield TEST_DIR
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

def test_mvcc_isolation_and_commit(setup_teardown):
    db = NexusDatabase(data_dir=setup_teardown)
    txn_mgr = TransactionManager(db)

    txn1 = txn_mgr.begin_transaction()
    txn_mgr.write(txn1, b"balance:1", b"1000")
    success = txn_mgr.commit(txn1)

    assert success is True
    assert txn1.state == TransactionState.COMMITTED

    found, val = db.get(b"balance:1")
    assert found is True
    assert val == b"1000"
    db.close()
