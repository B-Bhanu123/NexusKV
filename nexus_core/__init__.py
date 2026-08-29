"""
NexusKV Database Core Package
=============================
Provides top-level database orchestrator, JSON Document store, MVCC transaction manager,
and query execution engine.
"""

from .database import NexusDatabase
from .document_store import DocumentStore, DocumentIndex
from .transaction_manager import TransactionManager, TransactionState, Transaction
from .query_engine import QueryEngine, QueryPlan

__all__ = [
    "NexusDatabase",
    "DocumentStore",
    "DocumentIndex",
    "TransactionManager",
    "TransactionState",
    "Transaction",
    "QueryEngine",
    "QueryPlan",
]
