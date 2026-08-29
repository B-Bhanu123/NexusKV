"""
NexusKV Interactive CLI & Cluster Management Tool
=================================================

Provides interactive REPL, cluster health checks, key-value lookup,
and node administrative controls using standard library or Click/Rich when available.
"""

import sys
import argparse
from nexus_core.database import NexusDatabase

def main():
    parser = argparse.ArgumentParser(description="NexusKV Distributed Database CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Sub-command help")

    get_parser = subparsers.add_parser("get", help="Retrieve value for a key")
    get_parser.add_argument("--key", "-k", required=True, help="Key to fetch")

    put_parser = subparsers.add_parser("put", help="Insert or update a key-value pair")
    put_parser.add_argument("--key", "-k", required=True, help="Key to set")
    put_parser.add_argument("--value", "-v", required=True, help="Value to set")

    subparsers.add_parser("status", help="View cluster node topology and storage health")

    args = parser.parse_args()

    if args.command == "get":
        db = NexusDatabase()
        found, val = db.get(args.key.encode("utf-8"))
        if found and val is not None:
            print(f"[FOUND] {args.key} => {val.decode('utf-8')}")
        else:
            print(f"[NOT FOUND] Key {args.key} does not exist")
        db.close()
    elif args.command == "put":
        db = NexusDatabase()
        db.put(args.key.encode("utf-8"), args.value.encode("utf-8"))
        print(f"[SUCCESS] Set {args.key} => {args.value}")
        db.close()
    elif args.command == "status":
        db = NexusDatabase()
        info = db.get_cluster_status()
        print("=== NexusKV Node Status ===")
        for k, v in info.items():
            print(f"  {k}: {v}")
        db.close()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
