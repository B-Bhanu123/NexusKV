"""
Test Suite 1: Storage Engine Unit & Integration Tests
======================================================
Tests WAL persistence, MemTable operations, SSTable flushing, and recovery.
"""

import os
import shutil
import pytest
from nexus_storage.wal import WriteAheadLog, WALOpType
from nexus_storage.memtable import SkipListMemTable
from nexus_storage.sstable import SSTableWriter, SSTableReader
from nexus_core.database import NexusDatabase

TEST_DIR = "./tmp_test_storage"

@pytest.fixture
def setup_teardown():
    os.makedirs(TEST_DIR, exist_ok=True)
    yield TEST_DIR
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

def test_memtable_put_get(setup_teardown):
    mem = SkipListMemTable()
    mem.put(b"key1", b"val1")
    mem.put(b"key2", b"val2")

    found, val = mem.get(b"key1")
    assert found is True
    assert val == b"val1"

    found, val = mem.get(b"nonexistent")
    assert found is False

def test_wal_append_recovery(setup_teardown):
    wal_dir = os.path.join(setup_teardown, "wal")
    wal = WriteAheadLog(wal_dir)
    wal.append(WALOpType.PUT, b"k1", b"v1")
    wal.append(WALOpType.PUT, b"k2", b"v2")
    wal.close()

    wal_rec = WriteAheadLog(wal_dir)
    entries = list(wal_rec.recover())
    assert len(entries) == 2
    assert entries[0].key == b"k1"
    assert entries[0].value == b"v1"
    assert entries[1].key == b"k2"
    wal_rec.close()

def test_sstable_write_read(setup_teardown):
    sst_path = os.path.join(setup_teardown, "test.sst")
    mem = SkipListMemTable()
    mem.put(b"alpha", b"100")
    mem.put(b"beta", b"200")

    writer = SSTableWriter(sst_path)
    writer.write_from_memtable(mem.scan())

    reader = SSTableReader(sst_path)
    found, val = reader.get(b"alpha")
    assert found is True
    assert val == b"100"

    found, val = reader.get(b"gamma")
    assert found is False

def test_nexus_database_recovery(setup_teardown):
    db_dir = os.path.join(setup_teardown, "nexus_db")
    db = NexusDatabase(data_dir=db_dir)
    db.put(b"user:100", b"Alice")
    db.put(b"user:200", b"Bob")
    db.close()

    # Reopen to test recovery
    db2 = NexusDatabase(data_dir=db_dir)
    found, val = db2.get(b"user:100")
    assert found is True
    assert val == b"Alice"
    db2.close()
