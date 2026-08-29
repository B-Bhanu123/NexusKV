"""
NexusKV Consensus & Clustering Package
======================================
Provides Raft consensus engine, persistent log management, SWIM gossip membership,
and consistent hash sharding.
"""

from .raft_rpc import RequestVoteRequest, RequestVoteResponse, AppendEntriesRequest, AppendEntriesResponse, InstallSnapshotRequest, InstallSnapshotResponse
from .raft_log import RaftLog, LogEntry
from .raft_node import RaftNode, NodeRole
from .gossip import GossipNode, MemberStatus
from .sharding import ConsistentHashRing, ShardLocation
from .cluster_manager import ClusterManager

__all__ = [
    "RequestVoteRequest",
    "RequestVoteResponse",
    "AppendEntriesRequest",
    "AppendEntriesResponse",
    "InstallSnapshotRequest",
    "InstallSnapshotResponse",
    "RaftLog",
    "LogEntry",
    "RaftNode",
    "NodeRole",
    "GossipNode",
    "MemberStatus",
    "ConsistentHashRing",
    "ShardLocation",
    "ClusterManager",
]
