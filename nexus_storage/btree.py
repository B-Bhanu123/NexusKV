"""
NexusKV Persistent B+Tree Implementation
=======================================

Provides secondary indexing, multi-column search, and range query processing
with node splitting, balancing, and leaf pointer linking.
"""

from typing import List, Tuple, Optional, Any, Union

class BPlusNode:
    def __init__(self, is_leaf: bool = False):
        self.is_leaf = is_leaf
        self.keys: List[bytes] = []
        self.children: List[Union["BPlusNode", Any]] = []  # Internal nodes point to BPlusNode, Leaf nodes point to data values
        self.next: Optional["BPlusNode"] = None  # Pointer to next leaf node for fast range scan
        self.prev: Optional["BPlusNode"] = None

class BPlusTree:
    def __init__(self, order: int = 4):
        if order < 3:
            raise ValueError("B+Tree order must be at least 3")
        self.order = order
        self.root = BPlusNode(is_leaf=True)

    def insert(self, key: bytes, value: Any):
        root = self.root
        if len(root.keys) == (self.order - 1):
            new_root = BPlusNode(is_leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0, self.root)
            self.root = new_root
            self._insert_non_full(self.root, key, value)
        else:
            self._insert_non_full(root, key, value)

    def _insert_non_full(self, node: BPlusNode, key: bytes, value: Any):
        if node.is_leaf:
            i = 0
            while i < len(node.keys) and node.keys[i] < key:
                i += 1
            if i < len(node.keys) and node.keys[i] == key:
                node.children[i] = value
            else:
                node.keys.insert(i, key)
                node.children.insert(i, value)
        else:
            i = len(node.keys) - 1
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            child = node.children[i]
            if len(child.keys) == (self.order - 1):
                self._split_child(node, i, child)
                if key > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key, value)

    def _split_child(self, parent: BPlusNode, index: int, child: BPlusNode):
        mid = (self.order - 1) // 2
        new_node = BPlusNode(is_leaf=child.is_leaf)

        if child.is_leaf:
            new_node.keys = child.keys[mid:]
            new_node.children = child.children[mid:]
            child.keys = child.keys[:mid]
            child.children = child.children[:mid]

            new_node.next = child.next
            if new_node.next:
                new_node.next.prev = new_node
            child.next = new_node
            new_node.prev = child

            parent.keys.insert(index, new_node.keys[0])
            parent.children.insert(index + 1, new_node)
        else:
            parent.keys.insert(index, child.keys[mid])
            new_node.keys = child.keys[mid+1:]
            new_node.children = child.children[mid+1:]
            child.keys = child.keys[:mid]
            child.children = child.children[:mid+1]
            parent.children.insert(index + 1, new_node)

    def search(self, key: bytes) -> Optional[Any]:
        curr = self.root
        while not curr.is_leaf:
            i = 0
            while i < len(curr.keys) and key >= curr.keys[i]:
                i += 1
            curr = curr.children[i]

        for i, k in enumerate(curr.keys):
            if k == key:
                return curr.children[i]
        return None

    def range_search(self, start_key: bytes, end_key: bytes) -> List[Tuple[bytes, Any]]:
        results = []
        curr = self.root
        while not curr.is_leaf:
            i = 0
            while i < len(curr.keys) and start_key >= curr.keys[i]:
                i += 1
            curr = curr.children[i]

        while curr:
            for i, k in enumerate(curr.keys):
                if k >= start_key and k <= end_key:
                    results.append((k, curr.children[i]))
                elif k > end_key:
                    return results
            curr = curr.next
        return results
