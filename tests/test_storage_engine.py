"""
Test Suite 1: Storage Engine Unit & Integration Tests
======================================================
Tests WAL persistence, MemTable operations, SSTable flushing, and recovery.
"""

import os
import shutil
import unittest
from nexus_storage.wal import WriteAheadLog, WALOpType
from nexus_storage.memtable import SkipListMemTable
from nexus_storage.sstable import SSTableWriter, SSTableReader
from nexus_core.database import NexusDatabase

TEST_DIR = "./tmp_test_storage"

class TestStorageEngine(unittest.TestCase):
    def setUp(self):
        os.makedirs(TEST_DIR, exist_ok=True)

    def tearDown(self):
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)

    def test_memtable_put_get(self):
        mem = SkipListMemTable()
        mem.put(b"key1", b"val1")
        mem.put(b"key2", b"val2")

        found, val = mem.get(b"key1")
        self.assertTrue(found)
        self.assertEqual(val, b"val1")

        found, val = mem.get(b"nonexistent")
        self.assertFalse(found)

    def test_wal_append_recovery(self):
        wal_dir = os.path.join(TEST_DIR, "wal")
        wal = WriteAheadLog(wal_dir)
        wal.append(WALOpType.PUT, b"k1", b"v1")
        wal.append(WALOpType.PUT, b"k2", b"v2")
        wal.close()

        wal_rec = WriteAheadLog(wal_dir)
        entries = list(wal_rec.recover())
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].key, b"k1")
        self.assertEqual(entries[0].value, b"v1")
        self.assertEqual(entries[1].key, b"k2")
        wal_rec.close()

    def test_sstable_write_read(self):
        sst_path = os.path.join(TEST_DIR, "test.sst")
        mem = SkipListMemTable()
        mem.put(b"alpha", b"100")
        mem.put(b"beta", b"200")

        writer = SSTableWriter(sst_path)
        writer.write_from_memtable(mem.scan())

        reader = SSTableReader(sst_path)
        found, val = reader.get(b"alpha")
        self.assertTrue(found)
        self.assertEqual(val, b"100")

        found, val = reader.get(b"gamma")
        self.assertFalse(found)

    def test_nexus_database_recovery(self):
        db_dir = os.path.join(TEST_DIR, "nexus_db")
        db = NexusDatabase(data_dir=db_dir)
        db.put(b"user:100", b"Alice")
        db.put(b"user:200", b"Bob")
        db.close()

        # Reopen to test recovery
        db2 = NexusDatabase(data_dir=db_dir)
        found, val = db2.get(b"user:100")
        self.assertTrue(found)
        self.assertEqual(val, b"Alice")
        db2.close()

if __name__ == "__main__":
    unittest.main()
