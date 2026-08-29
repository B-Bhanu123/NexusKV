# NexusKV System Architecture Specification

## 1. Executive Summary
NexusKV is a distributed, horizontally scalable, strongly consistent key-value and document storage engine built for high-throughput transactional workloads and analytical queries.

## 2. Core Architectural Pillars

### 2.1 Multi-Layered Storage Engine (LSM-Tree + B+Tree)
NexusKV employs a hybrid storage strategy:
- **LSM-Tree (Log-Structured Merge-Tree)** for write-heavy key-value operations.
- **Persistent B+Tree** for secondary indexes and range query evaluation.
- **Write-Ahead Log (WAL)** to ensure durability prior to memory state mutation.
- **MemTable** backed by concurrent SkipList structures for O(log N) lookup and ordered key iteration.
- **SSTable (Sorted String Table)** with Sparse Index Block, Summary Block, and Bloom Filter for disk reads.

### 2.2 Consensus & Fault Tolerance (Raft + SWIM Gossip)
- **Raft Consensus Protocol**: Guarantees linearizable consistency across partition replicas.
- **SWIM Gossip Protocol**: Provides efficient O(1) failure detection and membership management.
- **Leader Election & Log Replication**: Dynamic election timeouts (150ms-300ms) with log matching property enforcement.

### 2.3 Consistent Hashing Sharding Ring
- **Virtual Nodes (256 per physical node)**: Uniform key distribution and hotspot mitigation.
- **Dynamic Rebalancing**: Seamless topology migration during scale-out or node failure.

### 2.4 Multi-Version Concurrency Control (MVCC) & 2PC
- Snapshot isolation support.
- Two-Phase Commit protocol for cross-shard atomic multi-key transactions.

## 3. Component Interaction Matrix

```
+------------------+     +-------------------+     +------------------+
|   Client Query   | --> | Consistent Router | --> | Shard Raft Leader|
+------------------+     +-------------------+     +------------------+
                                                            |
                                                   Writes to WAL + Memtable
                                                            |
                                                   Replicates via Raft
                                                            |
                                                   Flushes to SSTables
```
