"""
NexusKV Prometheus-Compatible Metrics Exporter
==============================================

Collects system metrics: Ops/sec, Latency Percentiles (p50, p99),
WAL sequence numbers, SSTable level counts, and Memory usage.
"""

import time
from typing import Dict, Any

class MetricsCollector:
    def __init__(self):
        self.start_time = time.time()
        self.ops_count = 0
        self.read_latencies = []
        self.write_latencies = []

    def record_read(self, latency_ms: float):
        self.ops_count += 1
        self.read_latencies.append(latency_ms)
        if len(self.read_latencies) > 1000:
            self.read_latencies.pop(0)

    def record_write(self, latency_ms: float):
        self.ops_count += 1
        self.write_latencies.append(latency_ms)
        if len(self.write_latencies) > 1000:
            self.write_latencies.pop(0)

    def get_summary(self) -> Dict[str, Any]:
        p99_read = sorted(self.read_latencies)[int(len(self.read_latencies) * 0.99)] if self.read_latencies else 0.0
        p99_write = sorted(self.write_latencies)[int(len(self.write_latencies) * 0.99)] if self.write_latencies else 0.0
        return {
            "uptime_sec": round(time.time() - self.start_time, 2),
            "total_ops": self.ops_count,
            "read_p99_ms": round(p99_read, 3),
            "write_p99_ms": round(p99_write, 3),
        }
