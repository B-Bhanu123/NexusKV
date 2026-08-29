"""
NexusKV Web Dashboard Telemetry Server
======================================

Serves the Web Dashboard static assets and real-time WebSocket telemetry feed.
"""

import os
from aiohttp import web
import logging

logger = logging.getLogger("NexusKV.UI.Server")

class DashboardServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.static_dir = os.path.join(os.path.dirname(__file__), "static")
        self._setup_routes()

    def _setup_routes(self):
        self.app.router.add_get("/", self.handle_index)
        self.app.router.add_static("/static", self.static_dir)

    async def handle_index(self, request: web.Request) -> web.FileResponse:
        return web.FileResponse(os.path.join(self.static_dir, "index.html"))

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"Dashboard UI server active on http://{self.host}:{self.port}")
