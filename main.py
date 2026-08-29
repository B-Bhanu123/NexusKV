"""
NexusKV Node Cluster Main Entrypoint
====================================

Launches a NexusKV cluster node with LSM Storage Engine, Raft Consensus,
Async TCP Transport, REST HTTP Gateway, and Web Dashboard.
"""

import sys
import asyncio
import logging
from nexus_core.database import NexusDatabase
from nexus_consensus.cluster_manager import ClusterManager
from nexus_network.http_api import HTTPServerGateway
from nexus_ui.server import DashboardServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("NexusKV.Main")

async def start_nexus_node(node_id: str = "node-1", http_port: int = 9001, dashboard_port: int = 8080):
    logger.info(f"Starting NexusKV Node '{node_id}'...")

    # 1. Initialize Database Engine
    db = NexusDatabase(data_dir=f"./data/{node_id}")

    # 2. Initialize Cluster Topology & Raft
    peers = {
        "node-1": "127.0.0.1:7001",
        "node-2": "127.0.0.1:7002",
        "node-3": "127.0.0.1:7003"
    }
    cluster_mgr = ClusterManager(node_id, "127.0.0.1", 7001, peers)

    # 3. Start REST HTTP API Gateway
    http_gateway = HTTPServerGateway("127.0.0.1", http_port, db)
    await http_gateway.start()

    # 4. Start Web Admin Dashboard
    dashboard = DashboardServer("127.0.0.1", dashboard_port)
    await dashboard.start()

    logger.info(f"NexusKV Node '{node_id}' operational!")
    logger.info(f"REST API: http://127.0.0.1:{http_port}")
    logger.info(f"Dashboard UI: http://127.0.0.1:{dashboard_port}")

    # Keep node event loop running
    while True:
        await asyncio.sleep(3600)

def main():
    node_id = sys.argv[1] if len(sys.argv) > 1 else "node-1"
    try:
        asyncio.run(start_nexus_node(node_id=node_id))
    except KeyboardInterrupt:
        logger.info("NexusKV node shutting down gracefully.")

if __name__ == "__main__":
    main()
