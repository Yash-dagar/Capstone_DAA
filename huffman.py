import math

from minheap import MinHeap


class Node:
    def __init__(self, symbol, freq, order, left=None, right=None):
        self.symbol = symbol      # None for internal nodes
        self.freq = freq
        self.order = order        # tie-breaker so the tree is always the same
        self.left = left
        self.right = right

    def key(self):
        return (self.freq, self.order)

    def is_leaf(self):
        return self.symbol is not None


def frequency_table(data):
    """Count how often each symbol occurs. O(n)."""
    freq = {}
    for symbol in data:
        freq[symbol] = freq.get(symbol, 0) + 1
    return freq


def build_tree(freq):
    """Build the Huffman tree. Returns (root, steps).

    steps lists every merge, used for display. O(k log k) for k distinct symbols.
    A single distinct symbol gets a root with one leaf so it still receives code "0".
    """
    if not freq:
        return None, []
    heap = MinHeap()
    order = 0
    for symbol in sorted(freq):
        heap.push(Node(symbol, freq[symbol], order))
        order += 1
    if len(heap) == 1:
        leaf = heap.pop()
        return Node(None, leaf.freq, order, left=leaf), []
    steps = []
    while len(heap) > 1:
        a = heap.pop()
        b = heap.pop()
        parent = Node(None, a.freq + b.freq, order, left=a, right=b)
        order += 1
        steps.append((a.freq, b.freq, parent.freq))
        heap.push(parent)
    return heap.pop(), steps


def generate_codes(root):
    """Walk the tree: left edge = 0, right edge = 1. O(k)."""
    codes = {}
    if root is None:
        return codes
    stack = [(root, "")]
    while stack:
        node, code = stack.pop()
        if node.is_leaf():
            codes[node.symbol] = code if code else "0"
            continue
        if node.right is not None:
            stack.append((node.right, code + "1"))
        if node.left is not None:
            stack.append((node.left, code + "0"))
    return codes


def encode(data, codes):
    """Replace each symbol by its code. O(n)."""
    return "".join([codes[symbol] for symbol in data])


def decode(bits, root, count=None):
    """Walk the tree bit by bit. Returns a list of symbols. O(number of bits)."""
    out = []
    if root is None:
        return out
    node = root
    for bit in bits:
        if count is not None and len(out) >= count:
            break
        node = node.left if bit == "0" else node.right
        if node is None:
            raise ValueError("bit sequence does not match this Huffman tree")
        if node.is_leaf():
            out.append(node.symbol)
            node = root
    return out


def total_bits(freq, codes):
    return sum(freq[s] * len(codes[s]) for s in freq)


def average_length(freq, codes):
    n = sum(freq.values())
    return total_bits(freq, codes) / n if n else 0.0


def entropy(freq):
    """Shannon entropy in bits per symbol: the lower limit for any prefix code."""
    n = sum(freq.values())
    return -sum((f / n) * math.log2(f / n) for f in freq.values()) if n else 0.0


def fixed_length_bits(freq):
    """Bits needed if every symbol used the same number of bits."""
    n = sum(freq.values())
    k = len(freq)
    return n * max(1, math.ceil(math.log2(k))) if k else 0


def tree_height(root):
    if root is None:
        return 0
    stack = [(root, 0)]
    best = 0
    while stack:
        node, d = stack.pop()
        best = max(best, d)
        for child in (node.left, node.right):
            if child is not None:
                stack.append((child, d + 1))
    return best


def show_symbol(symbol):
    if isinstance(symbol, int):
        if symbol == 32:
            return "space"
        if symbol == 10:
            return "\\n"
        if symbol == 13:
            return "\\r"
        if symbol == 9:
            return "\\t"
        if 33 <= symbol < 127:
            return chr(symbol)
        return "0x%02X" % symbol
    return str(symbol)


def tree_lines(node, prefix="", edge=""):
    """ASCII picture of the tree (use only for small alphabets)."""
    if node.is_leaf():
        label = "%s (%d)" % (show_symbol(node.symbol), node.freq)
    else:
        label = "* (%d)" % node.freq
    lines = [prefix + edge + label]
    pad = prefix + ("    " if edge else "")
    for child, e in ((node.left, "0--"), (node.right, "1--")):
        if child is not None:
            lines.extend(tree_lines(child, pad, e))
    return lines
