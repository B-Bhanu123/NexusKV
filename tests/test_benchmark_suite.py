"""
Test Suite 7: Benchmark Workload Integration Tests
===================================================
Tests multi-threaded high throughput reads and writes.
"""

import os
import shutil
import pytest
from nexus_cli.benchmark import BenchmarkEngine

TEST_DIR = "./tmp_test_bench"

@pytest.fixture
def setup_teardown():
    os.makedirs(TEST_DIR, exist_ok=True)
    yield TEST_DIR
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

def test_benchmark_execution(setup_teardown):
    engine = BenchmarkEngine(num_threads=2, total_ops=100)
    engine.run_workload("Test Workload", read_ratio=0.5)
    assert len(engine.latencies) == 100
