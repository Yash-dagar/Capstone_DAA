import os

from huffman import (frequency_table, build_tree, generate_codes, encode, decode, total_bits,
                     average_length, entropy, fixed_length_bits, tree_height, tree_lines, show_symbol)
from compressor import compress_bytes, decompress_bytes, compress_file, decompress_file
from performance import run_performance_analysis

BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_FOLDER, "data")
OUT_FOLDER = os.path.join(BASE_FOLDER, "results", "output")

state = {"name": None, "data": None, "freq": None, "root": None, "steps": None, "codes": None}


def set_data(name, data):
    state["name"] = name
    state["data"] = data
    state["freq"] = frequency_table(data)
    state["root"], state["steps"] = build_tree(state["freq"])
    state["codes"] = generate_codes(state["root"])
    print("Loaded '%s': %d bytes, %d distinct symbols." % (name, len(data), len(state["freq"])))


def ready():
    if state["data"] is None or not state["data"]:
        print("Load a non-empty input first (option 1).")
        return False
    return True


def choose_input():
    print()
    print("1. Sample file from data/")
    print("2. Type text")
    print("3. Path to your own file")
    choice = input("Enter 1, 2 or 3: ").strip()
    if choice == "1":
        names = sorted(os.listdir(DATA_FOLDER))
        for i, n in enumerate(names, 1):
            print("  %d. %s (%d bytes)" % (i, n, os.path.getsize(os.path.join(DATA_FOLDER, n))))
        pick = input("File number: ").strip()
        if pick.isdigit() and 1 <= int(pick) <= len(names):
            with open(os.path.join(DATA_FOLDER, names[int(pick) - 1]), "rb") as f:
                set_data(names[int(pick) - 1], f.read())
        else:
            print("Invalid number.")
    elif choice == "2":
        text = input("Text: ")
        if text:
            set_data("typed text", text.encode("utf-8"))
        else:
            print("Nothing entered.")
    elif choice == "3":
        path = input("File path: ").strip().strip('"')
        if os.path.isfile(path):
            with open(path, "rb") as f:
                set_data(os.path.basename(path), f.read())
        else:
            print("File not found.")
    else:
        print("Invalid choice.")


def show_frequencies():
    freq = state["freq"]
    n = len(state["data"])
    print()
    print("%-8s %10s %10s" % ("Symbol", "Frequency", "Percent"))
    print("-" * 30)
    for s in sorted(freq, key=lambda x: (-freq[x], x))[:40]:
        print("%-8s %10d %9.2f%%" % (show_symbol(s), freq[s], 100.0 * freq[s] / n))
    if len(freq) > 40:
        print("... and %d more symbols" % (len(freq) - 40))
    print("-" * 30)
    print("Total symbols:", n, "| Distinct symbols:", len(freq))


def show_merges_and_codes():
    print()
    steps = state["steps"]
    print("Merge steps (%d merges for %d symbols):" % (len(steps), len(state["freq"])))
    for i, (a, b, s) in enumerate(steps[:15], 1):
        print("  %2d. %d + %d -> %d" % (i, a, b, s))
    if len(steps) > 15:
        print("  ... %d more merges" % (len(steps) - 15))
    codes, freq = state["codes"], state["freq"]
    print()
    print("%-8s %10s %-24s %6s %10s" % ("Symbol", "Frequency", "Code", "Length", "Bits used"))
    print("-" * 64)
    for s in sorted(codes, key=lambda x: (len(codes[x]), x))[:40]:
        code = codes[s] if len(codes[s]) <= 22 else codes[s][:19] + "..."
        print("%-8s %10d %-24s %6d %10d" % (show_symbol(s), freq[s], code, len(codes[s]), freq[s] * len(codes[s])))
    if len(codes) > 40:
        print("... and %d more codes" % (len(codes) - 40))


def show_tree():
    if len(state["freq"]) > 20:
        print("The tree has %d leaves, which is too many to draw here. Use a smaller input or the web page." % len(state["freq"]))
        return
    print()
    print("Huffman tree (0 = left, 1 = right, * = internal node):")
    print("\n".join(tree_lines(state["root"])))
    print("Height:", tree_height(state["root"]))


def show_encoding():
    bits = encode(state["data"], state["codes"])
    print()
    print("Encoded length:", len(bits), "bits (", (len(bits) + 7) // 8, "bytes )")
    print("First 200 bits:", bits[:200] + ("..." if len(bits) > 200 else ""))


def decode_and_verify():
    bits = encode(state["data"], state["codes"])
    back = bytes(decode(bits, state["root"]))
    print()
    print("Decoded", len(back), "bytes.")
    print("Preview:", back[:80].decode("utf-8", errors="replace").replace("\n", " "))
    print("Matches the original:", "YES" if back == state["data"] else "NO")


def do_compress():
    os.makedirs(OUT_FOLDER, exist_ok=True)
    src = os.path.join(OUT_FOLDER, "input_copy.bin")
    with open(src, "wb") as f:
        f.write(state["data"])
    dst = os.path.join(OUT_FOLDER, os.path.splitext(state["name"])[0].replace(" ", "_") + ".huf")
    original, packed = compress_file(src, dst)
    os.remove(src)
    print("Saved", dst)
    print("Original: %d bytes | Compressed file: %d bytes | Saved: %.1f%%" % (original, packed, 100.0 * (1 - packed / original)))


def do_decompress():
    path = input("Path to .huf file: ").strip().strip('"')
    if not os.path.isfile(path):
        print("File not found.")
        return
    os.makedirs(OUT_FOLDER, exist_ok=True)
    dst = os.path.join(OUT_FOLDER, os.path.splitext(os.path.basename(path))[0] + "_restored.bin")
    try:
        packed, original = decompress_file(path, dst)
    except ValueError as e:
        print("Could not decompress:", e)
        return
    print("Saved", dst, "(%d bytes restored from %d)" % (original, packed))


def show_size_comparison():
    freq, codes, data = state["freq"], state["codes"], state["data"]
    n = len(data)
    huff = total_bits(freq, codes)
    fixed = fixed_length_bits(freq)
    packed = len(compress_bytes(data))
    print()
    print("%-34s %12s %10s" % ("Method", "Size (bytes)", "vs 8-bit"))
    print("-" * 58)
    rows = [("Original (8 bits per symbol)", n),
            ("Fixed length (%d bits per symbol)" % max(1, (len(freq) - 1).bit_length()), (fixed + 7) // 8),
            ("Huffman payload only", (huff + 7) // 8),
            ("Huffman .huf file (with table)", packed)]
    for name, size in rows:
        print("%-34s %12d %9.1f%%" % (name, size, 100.0 * size / n))
    print("-" * 58)
    print("Average code length: %.3f bits | Entropy limit: %.3f bits" % (average_length(freq, codes), entropy(freq)))
    if packed >= n:
        print("Note: the code table makes the .huf file larger than the input. Huffman needs enough data to pay for its header.")


def menu():
    print("=" * 50)
    print(" Huffman Coding File Compressor")
    print("=" * 50)
    set_data("small.txt", open(os.path.join(DATA_FOLDER, "small.txt"), "rb").read())
    actions = {
        "1": choose_input,
        "2": lambda: ready() and show_frequencies(),
        "3": lambda: ready() and show_merges_and_codes(),
        "4": lambda: ready() and show_tree(),
        "5": lambda: ready() and show_encoding(),
        "6": lambda: ready() and decode_and_verify(),
        "7": lambda: ready() and do_compress(),
        "8": do_decompress,
        "9": lambda: ready() and show_size_comparison(),
        "10": run_performance_analysis,
    }
    while True:
        print()
        print("Current input:", state["name"])
        print("1. Choose input (sample, typed text or your file)")
        print("2. Show frequency table")
        print("3. Build tree: merge steps and Huffman codes")
        print("4. Draw the Huffman tree")
        print("5. Encode and show the bits")
        print("6. Decode and verify")
        print("7. Compress to a .huf file")
        print("8. Decompress a .huf file")
        print("9. Compare sizes")
        print("10. Run performance analysis")
        print("11. Exit")
        choice = input("Enter your choice: ").strip()
        if choice == "11":
            print("Goodbye.")
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    menu()
