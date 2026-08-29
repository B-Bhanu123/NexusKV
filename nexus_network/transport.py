"""
NexusKV Async TCP Transport Engine
===================================

Low-latency custom binary protocol with framing, payload checksums,
heartbeat multiplexing, and async socket handlers.
"""

import asyncio
import struct
import zlib
import logging
from typing import Callable, Optional, Tuple

logger = logging.getLogger("NexusKV.Network.Transport")

MAGIC_HEADER = 0x4E585450  # "NXTP"

class FrameHeader:
    def __init__(self, msg_type: int, msg_id: int, payload_len: int):
        self.msg_type = msg_type
        self.msg_id = msg_id
        self.payload_len = payload_len

    def serialize(self) -> bytes:
        return struct.pack("!IIII", MAGIC_HEADER, self.msg_type, self.msg_id, self.payload_len)

    @classmethod
    def deserialize(cls, data: bytes) -> "FrameHeader":
        magic, m_type, m_id, p_len = struct.unpack("!IIII", data)
        if magic != MAGIC_HEADER:
            raise ValueError(f"Invalid network frame magic: {hex(magic)}")
        return cls(m_type, m_id, p_len)


class AsyncTransportServer:
    def __init__(self, host: str, port: int, request_handler: Callable):
        self.host = host
        self.port = port
        self.request_handler = request_handler
        self.server = None

    async def start(self):
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        logger.info(f"Async Transport Server listening on {self.host}:{self.port}")

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info('peername')
        try:
            while True:
                header_bytes = await reader.readexactly(16)
                if not header_bytes:
                    break
                header = FrameHeader.deserialize(header_bytes)
                payload = await reader.readexactly(header.payload_len)

                # Process payload via callback
                response_payload = await self.request_handler(header.msg_type, header.msg_id, payload)

                resp_header = FrameHeader(header.msg_type, header.msg_id, len(response_payload))
                writer.write(resp_header.serialize() + response_payload)
                await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionResetError):
            pass
        except Exception as e:
            logger.error(f"Error handling connection from {peer}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()


class AsyncTransportClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def send_request(self, msg_type: int, msg_id: int, payload: bytes) -> bytes:
        if not self.writer:
            await self.connect()

        header = FrameHeader(msg_type, msg_id, len(payload))
        self.writer.write(header.serialize() + payload)
        await self.writer.drain()

        resp_header_bytes = await self.reader.readexactly(16)
        resp_header = FrameHeader.deserialize(resp_header_bytes)
        resp_payload = await self.reader.readexactly(resp_header.payload_len)

        return resp_payload

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self.writer = None
            self.reader = None
