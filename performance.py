import csv
import os
import random
import time

from huffman import (frequency_table, build_tree, generate_codes, encode, decode,
                     total_bits, entropy, fixed_length_bits)
from compressor import compress_bytes

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
RESULTS_FOLDER = os.path.join(BASE_FOLDER, "results")
DATA_FOLDER = os.path.join(BASE_FOLDER, "data")

N_SIZES = [1000, 5000, 20000, 50000, 100000, 200000]
K_SIZES = [2, 4, 8, 16, 32, 64, 128, 256]
FIXED_N = 50000
REPEATS = 3


def make_data(n, k):
    """n symbols from k byte values with a skewed (Zipf-like) distribution."""
    weights = [1.0 / (i + 1) for i in range(k)]
    return bytes(random.choices(range(k), weights=weights, k=n))


def average_ms(fn):
    best_total = 0.0
    for _ in range(REPEATS):
        start = time.perf_counter()
        fn()
        best_total += time.perf_counter() - start
    return best_total / REPEATS * 1000


def measure(data):
    freq = frequency_table(data)
    root, _ = build_tree(freq)
    codes = generate_codes(root)
    bits = encode(data, codes)
    t_freq = average_ms(lambda: frequency_table(data))
    t_tree = average_ms(lambda: build_tree(freq))
    t_enc = average_ms(lambda: encode(data, codes))
    t_dec = average_ms(lambda: decode(bits, root))
    return t_freq, t_tree, t_enc, t_dec


def compression_table():
    rows = []
    for name in sorted(os.listdir(DATA_FOLDER)):
        with open(os.path.join(DATA_FOLDER, name), "rb") as f:
            data = f.read()
        if not data:
            continue
        freq = frequency_table(data)
        root, _ = build_tree(freq)
        codes = generate_codes(root)
        original = len(data)
        payload = (total_bits(freq, codes) + 7) // 8
        with_header = len(compress_bytes(data))
        rows.append((name, original, len(freq), round(entropy(freq), 3),
                     round(total_bits(freq, codes) / original, 3),
                     fixed_length_bits(freq) // 8 if len(freq) else 0,
                     payload, with_header,
                     round((1 - with_header / original) * 100, 1)))
    return rows


def run_performance_analysis():
    random.seed(42)
    print("Running performance analysis (each time is the average of %d runs)" % REPEATS)

    print("\nA. Growing input size (k = 64 distinct symbols), times in ms")
    print("%9s %12s %12s %12s %12s" % ("n", "count", "build tree", "encode", "decode"))
    size_rows = []
    for n in N_SIZES:
        t = measure(make_data(n, 64))
        size_rows.append((n,) + tuple(round(x, 4) for x in t))
        print("%9d %12.4f %12.4f %12.4f %12.4f" % ((n,) + t))

    print("\nB. Growing alphabet (n = %d), times in ms" % FIXED_N)
    print("%9s %12s %12s %12s %12s" % ("k", "count", "build tree", "encode", "decode"))
    alpha_rows = []
    for k in K_SIZES:
        t = measure(make_data(FIXED_N, k))
        alpha_rows.append((k,) + tuple(round(x, 4) for x in t))
        print("%9d %12.4f %12.4f %12.4f %12.4f" % ((k,) + t))

    print("\nC. Compression on the sample files (sizes in bytes)")
    comp = compression_table()
    print("%-16s %8s %3s %8s %8s %8s %8s %8s %8s" % (
        "file", "original", "k", "entropy", "avg len", "fixed", "payload", ".huf", "saved%"))
    for r in comp:
        print("%-16s %8d %3d %8.3f %8.3f %8d %8d %8d %7.1f%%" % r)

    os.makedirs(RESULTS_FOLDER, exist_ok=True)
    with open(os.path.join(RESULTS_FOLDER, "runtime_by_n.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n", "count_ms", "build_tree_ms", "encode_ms", "decode_ms"])
        w.writerows(size_rows)
    with open(os.path.join(RESULTS_FOLDER, "runtime_by_k.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["k", "count_ms", "build_tree_ms", "encode_ms", "decode_ms"])
        w.writerows(alpha_rows)
    with open(os.path.join(RESULTS_FOLDER, "compression_results.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "original_bytes", "distinct_symbols", "entropy_bits", "avg_code_length",
                    "fixed_length_bytes", "payload_bytes", "huf_file_bytes", "saved_percent"])
        w.writerows(comp)

    if plt is None:
        print("\nMatplotlib not installed: CSV files saved, charts skipped (pip install matplotlib).")
        return
    ns = [r[0] for r in size_rows]
    plt.figure(figsize=(7, 4.5))
    for i, label in ((1, "count"), (2, "build tree"), (3, "encode"), (4, "decode")):
        plt.plot(ns, [r[i] for r in size_rows], marker="o", label=label)
    plt.xlabel("input size n (symbols)"); plt.ylabel("time (ms)")
    plt.title("Runtime vs input size (k = 64)"); plt.legend(); plt.grid(alpha=.3)
    plt.tight_layout(); plt.savefig(os.path.join(RESULTS_FOLDER, "runtime_vs_n.png"), dpi=130); plt.close()

    ks = [r[0] for r in alpha_rows]
    plt.figure(figsize=(7, 4.5))
    plt.plot(ks, [r[2] for r in alpha_rows], marker="o", color="tab:red")
    plt.xlabel("distinct symbols k"); plt.ylabel("build tree time (ms)")
    plt.title("Tree construction vs alphabet size (n = %d)" % FIXED_N); plt.grid(alpha=.3)
    plt.tight_layout(); plt.savefig(os.path.join(RESULTS_FOLDER, "build_vs_k.png"), dpi=130); plt.close()

    names = [r[0] for r in comp]
    x = range(len(names))
    plt.figure(figsize=(8, 4.5))
    plt.bar([i - 0.2 for i in x], [r[1] for r in comp], 0.4, label="original")
    plt.bar([i + 0.2 for i in x], [r[7] for r in comp], 0.4, label="compressed (.huf)")
    plt.xticks(list(x), names, rotation=20); plt.yscale("log"); plt.ylabel("bytes (log scale)")
    plt.title("Original vs compressed size"); plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_FOLDER, "size_comparison.png"), dpi=130); plt.close()
    print("\nSaved CSV files and charts to", RESULTS_FOLDER)


if __name__ == "__main__":
    run_performance_analysis()
