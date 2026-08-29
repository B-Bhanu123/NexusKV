"""
NexusKV Network Package
=======================
Provides TCP socket protocols, binary serializers, REST/gRPC server gateways,
and query routing proxies.
"""

from .transport import AsyncTransportServer, AsyncTransportClient, FrameHeader
from .serializers import BinarySerializer, MsgPackSerializer, JSONSerializer
from .http_api import HTTPServerGateway
from .grpc_server import GRPCServerGateway
from .router import QueryRouter

__all__ = [
    "AsyncTransportServer",
    "AsyncTransportClient",
    "FrameHeader",
    "BinarySerializer",
    "MsgPackSerializer",
    "JSONSerializer",
    "HTTPServerGateway",
    "GRPCServerGateway",
    "QueryRouter",
]
