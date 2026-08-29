"""
NexusKV - Distributed Key-Value & Document Storage System
=========================================================

Setup configuration for packaging NexusKV distributed database.
"""

from setuptools import setup, find_packages

setup(
    name="nexus_kv",
    version="1.0.0",
    description="High-performance Distributed Key-Value and Document Storage System with Raft Consensus",
    author="B-Bhanu123",
    author_email="bhanu@nexuskv.io",
    url="https://github.com/B-Bhanu123/NexusKV",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Database :: Database Engines",
        "Topic :: System :: Distributed Computing",
    ],
    install_requires=[
        "aiohttp>=3.9.0",
        "grpcio>=1.60.0",
        "msgpack>=1.0.7",
        "pyyaml>=6.0.1",
        "click>=8.1.7",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "nexus-cli=nexus_cli.cli:main",
            "nexus-node=main:main",
            "nexus-bench=nexus_cli.benchmark:main",
        ],
    },
    python_requires=">=3.9",
)
