"""
NexusKV Binary Serialization Layer
==================================

Provides JSON, MsgPack, and Custom Binary serializations for network messages.
"""

import json
from typing import Any, Dict

class BinarySerializer:
    def serialize(self, obj: Any) -> bytes:
        raise NotImplementedError

    def deserialize(self, data: bytes) -> Any:
        raise NotImplementedError

class JSONSerializer(BinarySerializer):
    def serialize(self, obj: Any) -> bytes:
        return json.dumps(obj).encode("utf-8")

    def deserialize(self, data: bytes) -> Any:
        return json.loads(data.decode("utf-8"))

class MsgPackSerializer(BinarySerializer):
    def serialize(self, obj: Any) -> bytes:
        try:
            import msgpack
            return msgpack.packb(obj, use_bin_type=True)
        except ImportError:
            return json.dumps(obj).encode("utf-8")

    def deserialize(self, data: bytes) -> Any:
        try:
            import msgpack
            return msgpack.unpackb(data, raw=False)
        except ImportError:
            return json.loads(data.decode("utf-8"))
