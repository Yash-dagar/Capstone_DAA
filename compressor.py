"""Real file compression: packs the Huffman bits into bytes.

File format (.huf)
    4 bytes   magic "HUF1"
    2 bytes   k = number of distinct byte values
    k * 5     one entry per symbol: 1 byte value + 4 byte frequency
    rest      the encoded bits, packed 8 per byte, last byte zero padded

The decoder rebuilds the same tree from the frequencies (ties are broken the
same way every time) and stops after sum(frequencies) symbols, so no padding
length needs to be stored.
"""
import struct

from huffman import frequency_table, build_tree, generate_codes, encode, decode

MAGIC = b"HUF1"


def pack_bits(bits):
    if not bits:
        return b""
    pad = (-len(bits)) % 8
    value = int(bits + "0" * pad, 2)
    return value.to_bytes(len(bits) // 8 + (1 if pad else 0), "big")


def unpack_bits(payload):
    if not payload:
        return ""
    return bin(int.from_bytes(payload, "big"))[2:].zfill(len(payload) * 8)


def compress_bytes(data):
    freq = frequency_table(data)
    header = MAGIC + struct.pack(">H", len(freq))
    for symbol in sorted(freq):
        header += struct.pack(">BI", symbol, freq[symbol])
    if not freq:
        return header
    root, _ = build_tree(freq)
    return header + pack_bits(encode(data, generate_codes(root)))


def decompress_bytes(blob):
    if len(blob) < 6 or blob[:4] != MAGIC:
        raise ValueError("not a .huf file")
    (k,) = struct.unpack(">H", blob[4:6])
    pos = 6
    if len(blob) < pos + 5 * k:
        raise ValueError("file is truncated")
    freq = {}
    for _ in range(k):
        symbol, count = struct.unpack(">BI", blob[pos:pos + 5])
        freq[symbol] = count
        pos += 5
    if k == 0:
        return b""
    root, _ = build_tree(freq)
    out = decode(unpack_bits(blob[pos:]), root, count=sum(freq.values()))
    if len(out) != sum(freq.values()):
        raise ValueError("file is corrupt: not enough data")
    return bytes(out)


def compress_file(src, dst):
    with open(src, "rb") as f:
        data = f.read()
    blob = compress_bytes(data)
    with open(dst, "wb") as f:
        f.write(blob)
    return len(data), len(blob)


def decompress_file(src, dst):
    with open(src, "rb") as f:
        blob = f.read()
    data = decompress_bytes(blob)
    with open(dst, "wb") as f:
        f.write(data)
    return len(blob), len(data)
