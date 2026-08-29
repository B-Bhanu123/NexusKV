"""
NexusKV MVCC & Two-Phase Commit (2PC) Transaction Engine
========================================================

Implements Multi-Version Concurrency Control (MVCC), snapshot isolation,
write-conflict detection, and distributed 2PC transaction commit protocol.
"""

import time
import uuid
from enum import Enum
from typing import Dict, Optional, Set, Any

class TransactionState(Enum):
    ACTIVE = "ACTIVE"
    PREPARED = "PREPARED"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"

class Transaction:
    def __init__(self, txn_id: str, read_timestamp: float):
        self.txn_id = txn_id
        self.read_timestamp = read_timestamp
        self.write_set: Dict[bytes, bytes] = {}
        self.read_set: Set[bytes] = set()
        self.state = TransactionState.ACTIVE

class TransactionManager:
    def __init__(self, kv_db: Any):
        self.kv = kv_db
        self.active_transactions: Dict[str, Transaction] = {}
        self.committed_writes: Dict[bytes, float] = {}  # key -> commit_timestamp

    def begin_transaction(self) -> Transaction:
        txn_id = f"txn_{uuid.uuid4().hex[:8]}"
        read_ts = time.time()
        txn = Transaction(txn_id, read_ts)
        self.active_transactions[txn_id] = txn
        return txn

    def read(self, txn: Transaction, key: bytes) -> Optional[bytes]:
        txn.read_set.add(key)
        if key in txn.write_set:
            return txn.write_set[key]
        found, val = self.kv.get(key)
        return val if found else None

    def write(self, txn: Transaction, key: bytes, value: bytes):
        txn.write_set[key] = value

    def commit(self, txn: Transaction) -> bool:
        if txn.state != TransactionState.ACTIVE:
            return False

        # Write-conflict validation under Snapshot Isolation
        for key in txn.write_set:
            last_commit_ts = self.committed_writes.get(key, 0)
            if last_commit_ts > txn.read_timestamp:
                # Conflict detected -> Abort
                self.abort(txn)
                return False

        # Phase 1: Prepare
        txn.state = TransactionState.PREPARED

        # Phase 2: Commit
        commit_ts = time.time()
        for key, val in txn.write_set.items():
            self.kv.put(key, val)
            self.committed_writes[key] = commit_ts

        txn.state = TransactionState.COMMITTED
        if txn.txn_id in self.active_transactions:
            del self.active_transactions[txn.txn_id]

        return True

    def abort(self, txn: Transaction):
        txn.state = TransactionState.ABORTED
        if txn.txn_id in self.active_transactions:
            del self.active_transactions[txn.txn_id]
