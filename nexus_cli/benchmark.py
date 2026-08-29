"""
NexusKV YCSB Distributed Benchmark Engine
==========================================

Executes multi-threaded workload scenarios (Workload A: 50/50 Read/Write,
Workload B: 95/5 Read Heavy, Workload C: Read Only) to measure throughput and latency percentiles.
"""

import time
import random
import threading
from nexus_core.database import NexusDatabase

class BenchmarkEngine:
    def __init__(self, num_threads: int = 4, total_ops: int = 1000):
        self.num_threads = num_threads
        self.total_ops = total_ops
        self.db = NexusDatabase()
        self.latencies = []
        self.lock = threading.Lock()

    def _worker_task(self, ops_per_thread: int, read_ratio: float):
        for i in range(ops_per_thread):
            key = f"bench_key_{random.randint(1, 100000)}".encode("utf-8")
            start = time.time()

            if random.random() < read_ratio:
                self.db.get(key)
            else:
                val = f"bench_val_{random.randint(1, 100000)}".encode("utf-8")
                self.db.put(key, val)

            elapsed_ms = (time.time() - start) * 1000.0
            with self.lock:
                self.latencies.append(elapsed_ms)

    def run_workload(self, workload_name: str, read_ratio: float):
        print(f"Running Benchmark {workload_name} ({self.total_ops} ops, {self.num_threads} threads)...")
        ops_per_thread = self.total_ops // self.num_threads
        threads = []

        start_time = time.time()

        for t in range(self.num_threads):
            th = threading.Thread(target=self._worker_task, args=(ops_per_thread, read_ratio))
            threads.append(th)
            th.start()

        for th in threads:
            th.join()

        total_time_sec = time.time() - start_time
        throughput_ops = self.total_ops / total_time_sec if total_time_sec > 0 else 0

        sorted_lat = sorted(self.latencies)
        p50 = sorted_lat[int(len(sorted_lat) * 0.50)] if sorted_lat else 0
        p99 = sorted_lat[int(len(sorted_lat) * 0.99)] if sorted_lat else 0

        print(f"=== Benchmark Results: {workload_name} ===")
        print(f"  Total Operations:     {self.total_ops}")
        print(f"  Execution Time (sec): {total_time_sec:.3f}")
        print(f"  Throughput (ops/sec): {throughput_ops:.2f}")
        print(f"  Latency p50 (ms):     {p50:.3f}")
        print(f"  Latency p99 (ms):     {p99:.3f}")
        self.db.close()

def main():
    bench = BenchmarkEngine(num_threads=4, total_ops=1000)
    bench.run_workload("Workload A (50/50 R/W)", read_ratio=0.5)

if __name__ == "__main__":
    main()
