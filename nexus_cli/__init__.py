"""
NexusKV CLI & Benchmark Package
===============================
Provides Interactive CLI REPL and YCSB-style benchmark engine.
"""

from .cli import main as cli_main
from .benchmark import main as bench_main

__all__ = ["cli_main", "bench_main"]
