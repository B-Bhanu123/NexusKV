"""
NexusKV Query Execution Engine
==============================

Parses, plans, and executes key-value lookups, range scans, and document queries.
"""

from typing import Dict, Any, List, Optional

class QueryPlan:
    def __init__(self, op_type: str, collection: str, key: Optional[bytes] = None, filter_criteria: Optional[Dict[str, Any]] = None):
        self.op_type = op_type
        self.collection = collection
        self.key = key
        self.filter_criteria = filter_criteria

class QueryEngine:
    def __init__(self, doc_store: Any, kv_db: Any):
        self.doc_store = doc_store
        self.kv = kv_db

    def execute_plan(self, plan: QueryPlan) -> Any:
        if plan.op_type == "GET_BY_KEY":
            return self.kv.get(plan.key)
        elif plan.op_type == "DOC_LOOKUP":
            doc_id = plan.key.decode("utf-8") if plan.key else ""
            return self.doc_store.get_document(plan.collection, doc_id)
        elif plan.op_type == "INDEX_SCAN":
            field_path = plan.filter_criteria.get("field")
            search_val = plan.filter_criteria.get("val")
            return self.doc_store.query_index(plan.collection, field_path, search_val)
        else:
            raise ValueError(f"Unknown query plan op: {plan.op_type}")
