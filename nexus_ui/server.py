"""
NexusKV Web Dashboard Telemetry Server
======================================

Serves the Web Dashboard static assets and real-time telemetry feed with
built-in asyncio HTTP file server.
"""

import os
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger("NexusKV.UI.Server")

class DashboardServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.static_dir = os.path.join(os.path.dirname(__file__), "static")
        self.server = None

    async def start(self):
        self.server = await asyncio.start_server(self._handle_request, self.host, self.port)
        logger.info(f"Dashboard UI server active on http://{self.host}:{self.port}")

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def _handle_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            line = await reader.readline()
            if not line:
                return
            request_line = line.decode("utf-8").strip()
            parts = request_line.split(" ")
            if len(parts) < 2:
                return
            method, path = parts[0], parts[1]

            # Drain headers
            while True:
                h_line = await reader.readline()
                if not h_line or h_line in [b"\r\n", b"\n"]:
                    break

            if path in ["/", "/index.html"]:
                file_path = os.path.join(self.static_dir, "index.html")
                content_type = "text/html; charset=utf-8"
            elif path.startswith("/static/"):
                rel_path = path[len("/static/"):]
                file_path = os.path.join(self.static_dir, rel_path)
                if file_path.endswith(".css"):
                    content_type = "text/css"
                elif file_path.endswith(".js"):
                    content_type = "application/javascript"
                else:
                    content_type = "text/plain"
            else:
                file_path = None

            if file_path and os.path.exists(file_path) and os.path.isfile(file_path):
                with open(file_path, "rb") as f:
                    content = f.read()
                header = (
                    f"HTTP/1.1 200 OK\r\n"
                    f"Content-Type: {content_type}\r\n"
                    f"Content-Length: {len(content)}\r\n"
                    f"Connection: close\r\n\r\n"
                ).encode("utf-8")
                writer.write(header + content)
            else:
                notFound = b"HTTP/1.1 404 Not Found\r\nContent-Length: 9\r\n\r\nNot Found"
                writer.write(notFound)

        except Exception as e:
            logger.error(f"Dashboard server error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
