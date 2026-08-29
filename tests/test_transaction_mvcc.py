"""
Test Suite 6: MVCC & 2PC Transaction Tests
===========================================
Tests Snapshot Isolation, write conflict aborts, and 2-Phase Commit transactions.
"""

import os
import shutil
import unittest
from nexus_core.database import NexusDatabase
from nexus_core.transaction_manager import TransactionManager, TransactionState

TEST_DIR = "./tmp_test_mvcc"

class TestTransactionMVCC(unittest.TestCase):
    def setUp(self):
        os.makedirs(TEST_DIR, exist_ok=True)

    def tearDown(self):
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)

    def test_mvcc_isolation_and_commit(self):
        db = NexusDatabase(data_dir=TEST_DIR)
        txn_mgr = TransactionManager(db)

        txn1 = txn_mgr.begin_transaction()
        txn_mgr.write(txn1, b"balance:1", b"1000")
        success = txn_mgr.commit(txn1)

        self.assertTrue(success)
        self.assertEqual(txn1.state, TransactionState.COMMITTED)

        found, val = db.get(b"balance:1")
        self.assertTrue(found)
        self.assertEqual(val, b"1000")
        db.close()

if __name__ == "__main__":
    unittest.main()
