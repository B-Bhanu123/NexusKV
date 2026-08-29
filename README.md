# NexusKV - Enterprise Distributed Key-Value & Document Storage System

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/B-Bhanu123/NexusKV)
[![LOC](https://img.shields.io/badge/LOC-69k%2B-blue.svg)](https://github.com/B-Bhanu123/NexusKV)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](https://github.com/B-Bhanu123/NexusKV)

NexusKV is a high-performance, fault-tolerant, horizontally scalable distributed key-value and document database system built for enterprise transactional workloads and analytical queries.

---

## Key Architectural Features

- **Multi-Tiered LSM-Tree Storage Engine**: Write-Ahead Logging (WAL) with CRC32 integrity verification, SkipList & Red-Black MemTables, SSTable levels, Leveled Compaction, and Bloom Filters.
- **Raft Consensus & SWIM Gossip**: Distributed state machine replication, leader election, log matching, and SWIM protocol failure detection.
- **Virtual Node Consistent Hashing**: 256 Virtual Nodes per physical node for uniform key distribution and dynamic rebalancing.
- **MVCC & 2-Phase Commit (2PC)**: Snapshot isolation and multi-key atomic transactions.
- **Web Admin Control Center**: Glassmorphic dashboard with live telemetry polling and interactive KV explorer (`http://localhost:8080`).
- **Zero External Dependency Mode**: Native Python standard library fallbacks for out-of-the-box operation.

---

## Dependencies & Prerequisites

- **Python Version**: `Python 3.9+` (Recommended `Python 3.10` or `3.11`)
- **Manifest**: [`requirements.txt`](file:///c:/Users/91807/OneDrive/Desktop/task8/requirements.txt)
- **Lockfile**: [`requirements.lock`](file:///c:/Users/91807/OneDrive/Desktop/task8/requirements.lock)

---

## Installation & Setup

### 1. Clone Repository & Setup Virtual Environment

```bash
# Clone repository
git clone https://github.com/B-Bhanu123/NexusKV.git
cd NexusKV

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install from requirements lockfile
pip install -r requirements.lock
```

---

## Build & Run Instructions

### Launch Cluster Node Server

```bash
# Launch Primary Node (Node 1)
python main.py node-1

# Launch Secondary Cluster Nodes in separate terminals
python main.py node-2
python main.py node-3
```

- **Web Admin Dashboard**: Open [http://localhost:8080](http://localhost:8080) in your web browser.
- **REST API Gateway**: Active on [http://localhost:9001](http://localhost:9001).

---

## Testing & Benchmarking

### 1. Run Automated Test Suite

```bash
# Execute unit and integration tests using python unittest discovery
python -m unittest discover -s tests

# Or run with pytest (if installed)
pytest -v tests/
```

### 2. Run YCSB Distributed Benchmark Engine

```bash
# Execute YCSB Benchmark Workload A (50/50 R/W)
python -m nexus_cli.benchmark
```

---

## API Usage Reference

### REST HTTP Endpoints

- **PUT Key**: `PUT /api/v1/kv/{key}` with body `{"value": "your-value"}`
- **GET Key**: `GET /api/v1/kv/{key}`
- **DELETE Key**: `DELETE /api/v1/kv/{key}`
- **Cluster Status**: `GET /api/v1/cluster/status`
- **Metrics Telemetry**: `GET /api/v1/metrics`
