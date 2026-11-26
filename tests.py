import heapq
import math
import os
import random
import tempfile

from minheap import MinHeap
from huffman import (Node, frequency_table, build_tree, generate_codes, encode, decode,
                     total_bits, entropy, fixed_length_bits, tree_height)
from compressor import compress_bytes, decompress_bytes, compress_file, decompress_file, pack_bits, unpack_bits

BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
passed = 0
failed = 0


def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print("PASS:", name)
    else:
        failed += 1
        print("FAIL:", name)


def codes_for(data):
    freq = frequency_table(data)
    root, _ = build_tree(freq)
    return freq, root, generate_codes(root)


def is_prefix_free(codes):
    values = list(codes.values())
    for i, a in enumerate(values):
        for j, b in enumerate(values):
            if i != j and b.startswith(a):
                return False
    return True


def reference_cost(freq):
    """Independent check using Python's heapq: cost = sum of all merge weights."""
    heap = list(freq.values())
    heapq.heapify(heap)
    if len(heap) == 1:
        return heap[0]
    cost = 0
    while len(heap) > 1:
        s = heapq.heappop(heap) + heapq.heappop(heap)
        cost += s
        heapq.heappush(heap, s)
    return cost


def test_heap():
    print("\nMin-heap")
    random.seed(1)
    values = [random.randint(1, 1000) for _ in range(300)]
    h = MinHeap()
    for i, v in enumerate(values):
        h.push(Node(i, v, i))
    out = [h.pop().freq for _ in range(len(values))]
    check("heap pops in sorted order", out == sorted(values))
    check("heap is empty after popping everything", len(h) == 0)
    try:
        h.pop()
        check("pop from empty heap raises IndexError", False)
    except IndexError:
        check("pop from empty heap raises IndexError", True)


def test_frequency_and_tree():
    print("\nFrequency table and tree")
    check("frequency table counts", frequency_table("aabbbc") == {"a": 2, "b": 3, "c": 1})
    check("empty input gives empty table", frequency_table(b"") == {})
    freq, root, codes = codes_for(b"abracadabra")
    check("abracadabra costs 23 bits (known answer)", total_bits(freq, codes) == 23)
    check("root frequency equals input length", root.freq == 11)
    check("most frequent symbol has shortest code", len(codes[ord("a")]) == min(len(c) for c in codes.values()))
    check("empty input builds no tree", build_tree({}) == (None, []))
    f1, r1, c1 = codes_for(b"aaaa")
    check("single symbol gets code 0", c1 == {97: "0"})
    f2, r2, c2 = codes_for(b"abab")
    check("two symbols get one bit each", sorted(c2.values()) == ["0", "1"])
    check("number of merges is k - 1", len(build_tree(frequency_table(b"abracadabra"))[1]) == 4)
    a = generate_codes(build_tree(frequency_table(b"hello world"))[0])
    b = generate_codes(build_tree(frequency_table(b"hello world"))[0])
    check("tree is deterministic", a == b)


def test_properties():
    print("\nProperties on random inputs")
    random.seed(2)
    prefix_ok = optimal_ok = kraft_ok = bound_ok = True
    for _ in range(200):
        k = random.randint(2, 40)
        n = random.randint(k, 400)
        data = bytes(random.choices(range(k), weights=[random.randint(1, 50) for _ in range(k)], k=n))
        freq, root, codes = codes_for(data)
        if len(freq) < 2:
            continue
        prefix_ok &= is_prefix_free(codes)
        optimal_ok &= total_bits(freq, codes) == reference_cost(freq)
        kraft_ok &= abs(sum(2.0 ** -len(c) for c in codes.values()) - 1.0) < 1e-9
        h = entropy(freq) * n
        bound_ok &= h - 1e-6 <= total_bits(freq, codes) < h + n
    check("codes are prefix free (200 random inputs)", prefix_ok)
    check("cost equals independent heapq calculation (200 inputs)", optimal_ok)
    check("Kraft sum equals 1 (full binary tree)", kraft_ok)
    check("entropy <= cost < entropy + 1 bit per symbol", bound_ok)
    data = bytes(random.choices(range(16), k=1000))
    freq = frequency_table(data)
    root, _ = build_tree(freq)
    check("never worse than fixed length codes", total_bits(freq, generate_codes(root)) <= fixed_length_bits(freq))
    skew = b"a" * 1000 + b"b" * 10 + b"c" * 5 + b"d"
    freq, root, codes = codes_for(skew)
    check("skewed input gives a tall tree", tree_height(root) == 3)


def test_encode_decode():
    print("\nEncode and decode")
    for text in [b"abracadabra", b"hello world", b"a", b"ab", b"x" * 500, bytes(range(256)) * 3]:
        freq, root, codes = codes_for(text)
        bits = encode(text, codes)
        check("round trip, length %d, k = %d" % (len(text), len(freq)), bytes(decode(bits, root)) == text)
    freq, root, codes = codes_for("compression".encode())
    check("decode stops after count symbols", len(decode(encode(b"compression", codes), root, count=3)) == 3)
    try:
        decode("1", build_tree({1: 5})[0])
        check("bits that leave the tree raise ValueError", False)
    except ValueError:
        check("bits that leave the tree raise ValueError", True)
    check("string input round trip", "".join(decode(encode("banana", codes_for("banana")[2]), codes_for("banana")[1])) == "banana")


def test_file_format():
    print("\nFile compression")
    check("pack_bits / unpack_bits round trip", unpack_bits(pack_bits("1011001"))[:7] == "1011001")
    check("pack_bits pads to whole bytes", len(pack_bits("1" * 9)) == 2)
    for data in [b"", b"a", b"aaaa", b"abracadabra", bytes(range(256)), os.urandom(5000)]:
        check("compress/decompress %d bytes" % len(data), decompress_bytes(compress_bytes(data)) == data)
    for bad, name in [(b"nope", "wrong magic"), (b"HUF1\x00", "short header"), (b"HUF1\x00\x05ab", "truncated table")]:
        try:
            decompress_bytes(bad)
            check("rejects " + name, False)
        except ValueError:
            check("rejects " + name, True)
    blob = compress_bytes(b"hello hello hello, this is a longer message for the test")
    try:
        decompress_bytes(blob[:-3])
        check("detects a truncated payload", False)
    except ValueError:
        check("detects a truncated payload", True)
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(BASE_FOLDER, "data", "large.txt")
        huf = os.path.join(tmp, "large.huf")
        out = os.path.join(tmp, "large.out")
        original, packed = compress_file(src, huf)
        decompress_file(huf, out)
        check("large.txt is smaller after compression", packed < original)
        check("large.txt restored byte for byte", open(src, "rb").read() == open(out, "rb").read())


def test_sample_files():
    print("\nSample data files")
    folder = os.path.join(BASE_FOLDER, "data")
    for name in sorted(os.listdir(folder)):
        data = open(os.path.join(folder, name), "rb").read()
        check("%s round trips" % name, decompress_bytes(compress_bytes(data)) == data)
    data = open(os.path.join(folder, "random.bin"), "rb").read()
    freq = frequency_table(data)
    ratio = total_bits(freq, generate_codes(build_tree(freq)[0])) / (8 * len(data))
    check("random bytes barely compress (ratio near 1)", 0.98 < ratio <= 1.0)


if __name__ == "__main__":
    test_heap()
    test_frequency_and_tree()
    test_properties()
    test_encode_decode()
    test_file_format()
    test_sample_files()
    print()
    print("Passed:", passed, " Failed:", failed)
    raise SystemExit(1 if failed else 0)
