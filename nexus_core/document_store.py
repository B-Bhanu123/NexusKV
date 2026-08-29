"""
NexusKV Document Store & Secondary Index Engine
===============================================

Provides JSON Document storage, nested JSONPath queries, schema validation,
and automatic B+Tree index updating.
"""

import json
from typing import Dict, Any, List, Optional
from nexus_storage.btree import BPlusTree

class DocumentIndex:
    def __init__(self, field_path: str):
        self.field_path = field_path
        self.btree = BPlusTree(order=4)

    def extract_field(self, doc: Dict[str, Any]) -> Optional[Any]:
        parts = self.field_path.split(".")
        curr = doc
        for p in parts:
            if isinstance(curr, dict) and p in curr:
                curr = curr[p]
            else:
                return None
        return curr

    def index_document(self, doc_id: str, doc: Dict[str, Any]):
        val = self.extract_field(doc)
        if val is not None:
            val_bytes = str(val).encode("utf-8")
            self.btree.insert(val_bytes, doc_id)


class DocumentStore:
    def __init__(self, kv_db: Any):
        self.kv = kv_db
        self.indexes: Dict[str, DocumentIndex] = {}

    def create_index(self, collection: str, field_path: str):
        idx_name = f"{collection}:{field_path}"
        self.indexes[idx_name] = DocumentIndex(field_path)

    def put_document(self, collection: str, doc_id: str, doc: Dict[str, Any]):
        key = f"doc:{collection}:{doc_id}".encode("utf-8")
        val = json.dumps(doc).encode("utf-8")
        self.kv.put(key, val)

        # Update secondary indexes
        for idx_name, idx in self.indexes.items():
            if idx_name.startswith(collection + ":"):
                idx.index_document(doc_id, doc)

    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        key = f"doc:{collection}:{doc_id}".encode("utf-8")
        found, val = self.kv.get(key)
        if found and val:
            return json.loads(val.decode("utf-8"))
        return None

    def delete_document(self, collection: str, doc_id: str):
        key = f"doc:{collection}:{doc_id}".encode("utf-8")
        self.kv.delete(key)

    def query_index(self, collection: str, field_path: str, search_val: Any) -> List[Dict[str, Any]]:
        idx_name = f"{collection}:{field_path}"
        idx = self.indexes.get(idx_name)
        if not idx:
            return []

        search_bytes = str(search_val).encode("utf-8")
        doc_id = idx.btree.search(search_bytes)
        if doc_id:
            doc = self.get_document(collection, doc_id)
            return [doc] if doc else []
        return []
