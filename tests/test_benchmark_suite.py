"""
Test Suite 7: Benchmark Workload Integration Tests
===================================================
Tests multi-threaded high throughput reads and writes.
"""

import os
import shutil
import unittest
from nexus_cli.benchmark import BenchmarkEngine

TEST_DIR = "./tmp_test_bench"

class TestBenchmarkSuite(unittest.TestCase):
    def setUp(self):
        os.makedirs(TEST_DIR, exist_ok=True)

    def tearDown(self):
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)

    def test_benchmark_execution(self):
        engine = BenchmarkEngine(num_threads=2, total_ops=100)
        engine.run_workload("Test Workload", read_ratio=0.5)
        self.assertEqual(len(engine.latencies), 100)

if __name__ == "__main__":
    unittest.main()
