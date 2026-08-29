"""
NexusKV Raft Persistent Log Engine
===================================

Manages replicated write log entries, log matching invariants, index trimming,
and snapshotting for Raft state machine compaction.
"""

import os
import json
import threading
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class LogEntry:
    index: int
    term: int
    command: str  # e.g., "PUT:key:val" or "DELETE:key"
    data: Dict[str, Any]

class RaftLog:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        self.entries: List[LogEntry] = []
        self.commit_index = 0
        self.last_applied = 0
        self.last_included_index = 0
        self.last_included_term = 0
        self.lock = threading.RLock()
        os.makedirs(log_dir, exist_ok=True)
        self._load_log_from_disk()

    def _load_log_from_disk(self):
        log_file = os.path.join(self.log_dir, "raft_entries.jsonl")
        if not os.path.exists(log_file):
            return
        with open(log_file, "r") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    self.entries.append(LogEntry(**item))

    def _persist_all(self):
        log_file = os.path.join(self.log_dir, "raft_entries.jsonl")
        with open(log_file, "w") as f:
            for entry in self.entries:
                f.write(json.dumps(asdict(entry)) + "\n")

    def append(self, term: int, command: str, data: Dict[str, Any]) -> LogEntry:
        with self.lock:
            last_idx = self.get_last_log_index()
            new_entry = LogEntry(index=last_idx + 1, term=term, command=command, data=data)
            self.entries.append(new_entry)
            self._persist_all()
            return new_node_entry if 'new_node_entry' in locals() else new_entry

    def get_last_log_index(self) -> int:
        with self.lock:
            if self.entries:
                return self.entries[-1].index
            return self.last_included_index

    def get_last_log_term(self) -> int:
        with self.lock:
            if self.entries:
                return self.entries[-1].term
            return self.last_included_term

    def get_entry(self, index: int) -> Optional[LogEntry]:
        with self.lock:
            for entry in self.entries:
                if entry.index == index:
                    return entry
            return None

    def get_entries_from(self, start_index: int) -> List[Dict[str, Any]]:
        with self.lock:
            res = []
            for entry in self.entries:
                if entry.index >= start_index:
                    res.append(asdict(entry))
            return res

    def truncate_uncommitted(self, from_index: int):
        with self.lock:
            self.entries = [e for e in self.entries if e.index < from_index]
            self._persist_all()

    def snapshot(self, snapshot_index: int, snapshot_term: int):
        with self.lock:
            if snapshot_index <= self.last_included_index:
                return
            self.last_included_index = snapshot_index
            self.last_included_term = snapshot_term
            self.entries = [e for e in self.entries if e.index > snapshot_index]
            self._persist_all()
