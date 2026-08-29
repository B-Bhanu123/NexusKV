"""
NexusKV Raft State Machine Implementation
==========================================

Implements the full Raft Consensus Protocol state machine:
- Role transitions (Follower -> Candidate -> Leader / Follower)
- Election Timeout randomization (150ms-300ms)
- RequestVote & AppendEntries RPC processing
- Majority quorum consensus and Log Commit advancement
"""

import random
import time
import asyncio
import logging
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
from .raft_rpc import (
    RequestVoteRequest, RequestVoteResponse,
    AppendEntriesRequest, AppendEntriesResponse
)
from .raft_log import RaftLog, LogEntry

logger = logging.getLogger("NexusKV.Consensus.Raft")

class NodeRole(Enum):
    FOLLOWER = "FOLLOWER"
    CANDIDATE = "CANDIDATE"
    LEADER = "LEADER"

class RaftNode:
    def __init__(
        self,
        node_id: str,
        peers: List[str],
        log_dir: str,
        rpc_send_fn: Optional[Callable] = None,
        apply_fn: Optional[Callable] = None
    ):
        self.node_id = node_id
        self.peers = peers
        self.log_dir = log_dir
        self.rpc_send_fn = rpc_send_fn
        self.apply_fn = apply_fn

        # Persistent State
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.log = RaftLog(log_dir)

        # Volatile State
        self.role = NodeRole.FOLLOWER
        self.commit_index = 0
        self.last_applied = 0
        self.current_leader: Optional[str] = None

        # Leader Specific State
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}

        # Timers & Controls
        self.last_heartbeat_time = time.time()
        self.election_timeout = random.uniform(0.15, 0.30)
        self.is_running = False

    def reset_election_timeout(self):
        self.last_heartbeat_time = time.time()
        self.election_timeout = random.uniform(0.15, 0.30)

    def handle_request_vote(self, req: RequestVoteRequest) -> RequestVoteResponse:
        if req.term > self.current_term:
            self.current_term = req.term
            self.role = NodeRole.FOLLOWER
            self.voted_for = None

        vote_granted = False
        if req.term == self.current_term and (self.voted_for is None or self.voted_for == req.candidate_id):
            last_log_term = self.log.get_last_log_term()
            last_log_index = self.log.get_last_log_index()

            # Up-to-date log check
            if req.last_log_term > last_log_term or (
                req.last_log_term == last_log_term and req.last_log_index >= last_log_index
            ):
                vote_granted = True
                self.voted_for = req.candidate_id
                self.reset_election_timeout()

        return RequestVoteResponse(term=self.current_term, vote_granted=vote_granted)

    def handle_append_entries(self, req: AppendEntriesRequest) -> AppendEntriesResponse:
        if req.term < self.current_term:
            return AppendEntriesResponse(term=self.current_term, success=False, match_index=0)

        if req.term > self.current_term or self.role != NodeRole.FOLLOWER:
            self.current_term = req.term
            self.role = NodeRole.FOLLOWER
            self.voted_for = None

        self.current_leader = req.leader_id
        self.reset_election_timeout()

        # Log consistency check
        if req.prev_log_index > 0:
            prev_entry = self.log.get_entry(req.prev_log_index)
            if prev_entry is None or prev_entry.term != req.prev_log_term:
                return AppendEntriesResponse(term=self.current_term, success=False, match_index=self.log.get_last_log_index())

        # Process new entries
        for entry_dict in req.entries:
            entry = LogEntry(**entry_dict)
            existing = self.log.get_entry(entry.index)
            if existing and existing.term != entry.term:
                self.log.truncate_uncommitted(entry.index)
            if not self.log.get_entry(entry.index):
                self.log.append(entry.term, entry.command, entry.data)

        # Update commit index
        if req.leader_commit > self.commit_index:
            self.commit_index = min(req.leader_commit, self.log.get_last_log_index())
            self._apply_entries()

        return AppendEntriesResponse(
            term=self.current_term,
            success=True,
            match_index=self.log.get_last_log_index()
        )

    def _apply_entries(self):
        while self.commit_index > self.last_applied:
            self.last_applied += 1
            entry = self.log.get_entry(self.last_applied)
            if entry and self.apply_fn:
                try:
                    self.apply_fn(entry.command, entry.data)
                except Exception as e:
                    logger.error(f"Error applying entry {entry.index}: {e}")

    def start_election(self):
        self.role = NodeRole.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.reset_election_timeout()

        votes_received = 1
        req = RequestVoteRequest(
            term=self.current_term,
            candidate_id=self.node_id,
            last_log_index=self.log.get_last_log_index(),
            last_log_term=self.log.get_last_log_term()
        )

        for peer in self.peers:
            if self.rpc_send_fn:
                try:
                    resp = self.rpc_send_fn(peer, "RequestVote", req.to_json())
                    if resp:
                        vote_resp = RequestVoteResponse.from_json(resp)
                        if vote_resp.vote_granted:
                            votes_received += 1
                except Exception:
                    pass

        majority = (len(self.peers) + 1) // 2 + 1
        if votes_received >= majority and self.role == NodeRole.CANDIDATE:
            self.become_leader()

    def become_leader(self):
        self.role = NodeRole.LEADER
        self.current_leader = self.node_id
        last_log_idx = self.log.get_last_log_index()
        for peer in self.peers:
            self.next_index[peer] = last_log_idx + 1
            self.match_index[peer] = 0
        logger.info(f"Node {self.node_id} elected as LEADER for term {self.current_term}")
        self.send_heartbeats()

    def send_heartbeats(self):
        if self.role != NodeRole.LEADER:
            return

        for peer in self.peers:
            prev_idx = self.next_index.get(peer, 1) - 1
            prev_entry = self.log.get_entry(prev_idx)
            prev_term = prev_entry.term if prev_entry else 0

            entries_to_send = self.log.get_entries_from(prev_idx + 1)

            req = AppendEntriesRequest(
                term=self.current_term,
                leader_id=self.node_id,
                prev_log_index=prev_idx,
                prev_log_term=prev_term,
                entries=entries_to_send,
                leader_commit=self.commit_index
            )

            if self.rpc_send_fn:
                try:
                    resp = self.rpc_send_fn(peer, "AppendEntries", req.to_json())
                    if resp:
                        append_resp = AppendEntriesResponse.from_json(resp)
                        if append_resp.success:
                            self.next_index[peer] = append_resp.match_index + 1
                            self.match_index[peer] = append_resp.match_index
                            self._update_leader_commit_index()
                        else:
                            self.next_index[peer] = max(1, self.next_index.get(peer, 1) - 1)
                except Exception:
                    pass

    def _update_leader_commit_index(self):
        match_indices = sorted(list(self.match_index.values()) + [self.log.get_last_log_index()])
        median_match = match_indices[len(match_indices) // 2]
        if median_match > self.commit_index:
            entry = self.log.get_entry(median_match)
            if entry and entry.term == self.current_term:
                self.commit_index = median_match
                self._apply_entries()

    def propose_command(self, command: str, data: Dict[str, Any]) -> Tuple[bool, Optional[int]]:
        if self.role != NodeRole.LEADER:
            return False, None
        entry = self.log.append(self.current_term, command, data)
        self.send_heartbeats()
        return True, entry.index
