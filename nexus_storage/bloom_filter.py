"""
NexusKV Bloom Filter Engine
===========================

Provides probabilistic data structures for ultra-fast non-membership key checks.
Includes Standard Bit-Array Bloom Filter and Counting Bloom Filter with double hashing.
"""

import math
import mmh3  # fallback murmurhash or zlib crc32 hash strategy
import zlib
import struct
from typing import List

class BloomFilter:
    def __init__(self, expected_items: int = 10000, fp_rate: float = 0.01):
        self.expected_items = expected_items
        self.fp_rate = fp_rate
        self.size_bits = self._calculate_bit_size(expected_items, fp_rate)
        self.num_hashes = self._calculate_num_hashes(self.size_bits, expected_items)
        self.bit_array = bytearray((self.size_bits + 7) // 8)

    @staticmethod
    def _calculate_bit_size(n: int, p: float) -> int:
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return max(64, int(m))

    @staticmethod
    def _calculate_num_hashes(m: int, n: int) -> int:
        k = (m / n) * math.log(2)
        return max(1, int(k))

    def _hashes(self, key: bytes) -> List[int]:
        """Kirsch-Mitzenmacher optimization for double hashing."""
        h1 = zlib.crc32(key) & 0xFFFFFFFF
        h2 = zlib.adler32(key) & 0xFFFFFFFF
        return [(h1 + i * h2) % self.size_bits for i in range(self.num_hashes)]

    def add(self, key: bytes):
        for bit_idx in self._hashes(key):
            byte_idx = bit_idx // 8
            bit_off = bit_idx % 8
            self.bit_array[byte_idx] |= (1 << bit_off)

    def contains(self, key: bytes) -> bool:
        for bit_idx in self._hashes(key):
            byte_idx = bit_idx // 8
            bit_off = bit_idx % 8
            if not (self.bit_array[byte_idx] & (1 << bit_off)):
                return False
        return True

    def serialize(self) -> bytes:
        header = struct.pack("!IIQ", self.expected_items, self.num_hashes, self.size_bits)
        return header + bytes(self.bit_array)

    @classmethod
    def deserialize(cls, data: bytes) -> "BloomFilter":
        items, num_hashes, size_bits = struct.unpack("!IIQ", data[:16])
        bf = cls(expected_items=items, fp_rate=0.01)
        bf.num_hashes = num_hashes
        bf.size_bits = size_bits
        bf.bit_array = bytearray(data[16:])
        return bf


class CountingBloomFilter:
    def __init__(self, expected_items: int = 10000, fp_rate: float = 0.01):
        self.expected_items = expected_items
        self.fp_rate = fp_rate
        self.size = BloomFilter._calculate_bit_size(expected_items, fp_rate)
        self.num_hashes = BloomFilter._calculate_num_hashes(self.size, expected_items)
        self.counters = [0] * self.size

    def _hashes(self, key: bytes) -> List[int]:
        h1 = zlib.crc32(key) & 0xFFFFFFFF
        h2 = zlib.adler32(key) & 0xFFFFFFFF
        return [(h1 + i * h2) % self.size for i in range(self.num_hashes)]

    def add(self, key: bytes):
        for idx in self._hashes(key):
            self.counters[idx] += 1

    def remove(self, key: bytes):
        for idx in self._hashes(key):
            if self.counters[idx] > 0:
                self.counters[idx] -= 1

    def contains(self, key: bytes) -> bool:
        for idx in self._hashes(key):
            if self.counters[idx] == 0:
                return False
        return True
