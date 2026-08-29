"""
NexusKV Raft RPC Message Definitions
===================================

Defines message structures and serialization for Raft Consensus RPCs:
RequestVote, AppendEntries, and InstallSnapshot.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class RequestVoteRequest:
    term: int
    candidate_id: str
    last_log_index: int
    last_log_term: int

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str) -> "RequestVoteRequest":
        return cls(**json.loads(raw))

@dataclass
class RequestVoteResponse:
    term: int
    vote_granted: bool

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str) -> "RequestVoteResponse":
        return cls(**json.loads(raw))

@dataclass
class AppendEntriesRequest:
    term: int
    leader_id: str
    prev_log_index: int
    prev_log_term: int
    entries: List[Dict[str, Any]]
    leader_commit: int

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str) -> "AppendEntriesRequest":
        return cls(**json.loads(raw))

@dataclass
class AppendEntriesResponse:
    term: int
    success: bool
    match_index: int

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str) -> "AppendEntriesResponse":
        return cls(**json.loads(raw))

@dataclass
class InstallSnapshotRequest:
    term: int
    leader_id: str
    last_included_index: int
    last_included_term: int
    offset: int
    data: str  # Base64 encoded snapshot data
    done: bool

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str) -> "InstallSnapshotRequest":
        return cls(**json.loads(raw))

@dataclass
class InstallSnapshotResponse:
    term: int

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str) -> "InstallSnapshotResponse":
        return cls(**json.loads(raw))
