"""
NexusKV RESTful HTTP API Gateway
================================

Provides REST endpoints for key-value CRUD operations, document queries,
cluster health metrics, and node administration.
"""

import json
from aiohttp import web
import logging
from typing import Any, Dict

logger = logging.getLogger("NexusKV.Network.HTTP")

class HTTPServerGateway:
    def __init__(self, host: str, port: int, db_engine: Any):
        self.host = host
        self.port = port
        self.db = db_engine
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        self.app.router.add_get("/api/v1/kv/{key}", self.handle_get_key)
        self.app.router.add_put("/api/v1/kv/{key}", self.handle_put_key)
        self.app.router.add_delete("/api/v1/kv/{key}", self.handle_delete_key)
        self.app.router.add_get("/api/v1/cluster/status", self.handle_cluster_status)
        self.app.router.add_get("/api/v1/metrics", self.handle_metrics)

    async def handle_get_key(self, request: web.Request) -> web.Response:
        key = request.match_info["key"].encode("utf-8")
        found, val = self.db.get(key)
        if not found or val is None:
            return web.json_response({"error": "Key not found"}, status=404)
        return web.json_response({"key": request.match_info["key"], "value": val.decode("utf-8")})

    async def handle_put_key(self, request: web.Request) -> web.Response:
        key = request.match_info["key"].encode("utf-8")
        data = await request.json()
        val = data.get("value", "").encode("utf-8")
        self.db.put(key, val)
        return web.json_response({"status": "success", "key": request.match_info["key"]})

    async def handle_delete_key(self, request: web.Request) -> web.Response:
        key = request.match_info["key"].encode("utf-8")
        self.db.delete(key)
        return web.json_response({"status": "deleted", "key": request.match_info["key"]})

    async def handle_cluster_status(self, request: web.Request) -> web.Response:
        status_info = self.db.get_cluster_status()
        return web.json_response(status_info)

    async def handle_metrics(self, request: web.Request) -> web.Response:
        metrics = self.db.get_metrics()
        return web.json_response(metrics)

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"REST Gateway listening on http://{self.host}:{self.port}")
