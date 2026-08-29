"""
NexusKV RESTful HTTP API Gateway
================================

Provides REST endpoints for key-value CRUD operations, document queries,
cluster health metrics, and node administration. Uses built-in asyncio HTTP
handlers for zero-dependency operation.
"""

import json
import asyncio
import logging
from typing import Any, Dict

logger = logging.getLogger("NexusKV.Network.HTTP")

class HTTPServerGateway:
    def __init__(self, host: str, port: int, db_engine: Any):
        self.host = host
        self.port = port
        self.db = db_engine
        self.server = None

    async def start(self):
        self.server = await asyncio.start_server(self._handle_request, self.host, self.port)
        logger.info(f"REST Gateway listening on http://{self.host}:{self.port}")

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

            # Read headers
            headers = {}
            while True:
                h_line = await reader.readline()
                if not h_line or h_line == b"\r\n" or h_line == b"\n":
                    break
                h_str = h_line.decode("utf-8").strip()
                if ":" in h_str:
                    hk, hv = h_str.split(":", 1)
                    headers[hk.strip().lower()] = hv.strip()

            content_length = int(headers.get("content-length", 0))
            body_bytes = b""
            if content_length > 0:
                body_bytes = await reader.readexactly(content_length)

            # Route requests
            if path.startswith("/api/v1/kv/"):
                key_str = path[len("/api/v1/kv/"):]
                key = key_str.encode("utf-8")

                if method == "GET":
                    found, val = self.db.get(key)
                    if not found or val is None:
                        self._send_json(writer, {"error": "Key not found"}, status=404)
                    else:
                        self._send_json(writer, {"key": key_str, "value": val.decode("utf-8")})
                elif method in ["PUT", "POST"]:
                    try:
                        data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                        val = data.get("value", "").encode("utf-8")
                        self.db.put(key, val)
                        self._send_json(writer, {"status": "success", "key": key_str})
                    except Exception as e:
                        self._send_json(writer, {"error": str(e)}, status=400)
                elif method == "DELETE":
                    self.db.delete(key)
                    self._send_json(writer, {"status": "deleted", "key": key_str})
                else:
                    self._send_json(writer, {"error": "Method not allowed"}, status=405)
            elif path == "/api/v1/cluster/status":
                self._send_json(writer, self.db.get_cluster_status())
            elif path == "/api/v1/metrics":
                self._send_json(writer, self.db.get_metrics())
            else:
                self._send_json(writer, {"error": "Endpoint not found"}, status=404)

        except Exception as e:
            logger.error(f"HTTP handler error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    def _send_json(self, writer: asyncio.StreamWriter, data: Dict[str, Any], status: int = 200):
        body = json.dumps(data).encode("utf-8")
        status_text = "OK" if status == 200 else ("Not Found" if status == 404 else "Error")
        header = (
            f"HTTP/1.1 {status} {status_text}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Access-Control-Allow-Origin: *\r\n"
            f"Connection: close\r\n\r\n"
        ).encode("utf-8")
        writer.write(header + body)
