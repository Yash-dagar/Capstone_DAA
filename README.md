# Huffman Coding File Compressor

**Capstone Assignment – Design and Analysis of Algorithms**

| | |
| --- | --- |
| Student | Yash Dagar (Roll No. 2501730474) |
| Programme | B.Tech CSE(AI/ML) 'G' |
| Faculty | Ms. Anvi Aggarwal |
| Language | Python 3.8 or newer (plus a web page in plain HTML and JavaScript) |

## About the project

Huffman Coding File Compressor shrinks files without losing any data. It counts how often each byte occurs, builds a Huffman tree so frequent bytes get short codes, and writes the result as a real `.huf` file that can be restored exactly. It has two parts:

1. **A menu-driven Python application** (`main.py`) that shows every step: frequency table, merge steps, codes, tree, encoded bits, decoding, file compression and size comparison.
2. **A web page** (`web/index.html`) that does the same in the browser, with a drawn tree. Open it by double-clicking the file. No server or install is needed.

## Algorithms used

| Step | Algorithm | File |
| --- | --- | --- |
| Count symbols | Frequency table (hash map) | `huffman.py` |
| Pick the two smallest nodes | Binary min-heap (priority queue), written by hand | `minheap.py` |
| Build the tree | Greedy Huffman construction | `huffman.py` |
| Assign codes | Tree traversal (left = 0, right = 1) | `huffman.py` |
| Encode and decode | Table lookup and tree walk | `huffman.py` |
| Save and load files | Bit packing and a small header | `compressor.py` |
| Measure | Runtime and compression tests | `performance.py` |

### Time and space complexity

n = number of symbols in the input, k = number of distinct symbols (at most 256 for bytes).

| Step | Time | Space |
| --- | --- | --- |
| Count frequencies | O(n) | O(k) |
| Build the tree (k - 1 merges, each heap step O(log k)) | O(k log k) | O(k) |
| Generate codes | O(k) | O(k) |
| Encode | O(n) | O(n) bits of output |
| Decode | O(n) | O(n) |
| **Whole compression** | **O(n + k log k)** | **O(n + k)** |

Because k is at most 256 for bytes, the tree step is tiny and the work is dominated by the O(n) passes over the data.

## Requirements

- Python 3.8 or newer
- Matplotlib (only for the performance charts)

```
pip install matplotlib
```

Everything else uses the Python standard library.

## How to run

Open a terminal inside the project folder and run:

```
python main.py
```

Use `python3 main.py` on Linux or macOS. The program starts with `data/small.txt` loaded. Menu:

```
1. Choose input (sample, typed text or your file)
2. Show frequency table
3. Build tree: merge steps and Huffman codes
4. Draw the Huffman tree
5. Encode and show the bits
6. Decode and verify
7. Compress to a .huf file
8. Decompress a .huf file
9. Compare sizes
10. Run performance analysis
11. Exit
```

Suggested demo order: 2, 3, 4, 5, 6, 9, 7, 8, then 1 to switch to `large.txt` and repeat 9, then 10.
Compressed files are written to `results/output/`.

Other commands:

```
python tests.py          # runs all 49 correctness tests
python performance.py    # runs only the performance analysis
```

To use the web page, open `web/index.html` in a browser.

## Sample results

Measured by `python performance.py` (sizes in bytes; the `.huf` size includes the code table):

| File | Original | Distinct symbols | Average code length | Entropy limit | .huf file | Saved |
| --- | --- | --- | --- | --- | --- | --- |
| large.txt (English-like text) | 158,770 | 25 | 3.705 bits | 3.674 bits | 73,657 | 53.6% |
| repetitive.txt | 8,800 | 4 | 1.773 bits | 1.650 bits | 1,976 | 77.5% |
| unicode.txt | 2,820 | 42 | 4.979 bits | 4.926 bits | 1,971 | 30.1% |
| medium.txt | 746 | 47 | 4.394 bits | 4.351 bits | 651 | 12.7% |
| random.bin (random bytes) | 20,000 | 256 | 8.000 bits | 7.992 bits | 21,286 | -6.4% |
| small.txt (39 bytes) | 39 | 13 | 3.000 bits | 2.926 bits | 86 | -120.5% |

Two results are worse than the original on purpose: random bytes have no pattern to exploit, and a 39-byte file is smaller than its own code table. They show when Huffman coding does not help.

**Testing:** `python tests.py` runs 49 checks. All pass. They include a known answer (`abracadabra` costs 23 bits), prefix-free codes, an independent cost check against Python's `heapq`, the Kraft sum, the entropy bounds, edge cases (empty input, one symbol, all 256 byte values) and file round trips.

**Performance** (average of 3 runs, fixed random seed): encoding 200,000 symbols takes about 4.4 ms and decoding about 42.7 ms. Tree building stays near 0.2 ms for k = 64 however large n grows, and grows with k (0.004 ms at k = 2 to 1.18 ms at k = 256). Absolute times depend on the computer.

## The .huf file format

```
4 bytes   magic "HUF1"
2 bytes   k, the number of distinct byte values
k x 5     one entry per symbol: 1 byte value + 4 byte frequency
rest      encoded bits packed 8 per byte, last byte zero padded
```

The decoder rebuilds the identical tree from the frequencies (ties are broken by a fixed order) and stops after the total number of symbols, so no padding length needs to be stored. The loader rejects a wrong header, a truncated table and a truncated payload.

## Folder structure

```
Huffman_Capstone/
    main.py              menu-driven application
    huffman.py           frequency table, tree, codes, encode, decode
    minheap.py           binary min-heap
    compressor.py        .huf file format, bit packing, compress and decompress
    performance.py       runtime measurement and chart generation
    tests.py             correctness tests
    data/                sample inputs (text, repetitive, unicode, random bytes)
    web/
        index.html       browser version with tree drawing
    results/
        performance_output.txt, test_results.txt, demo_output.txt
        runtime_by_n.csv, runtime_by_k.csv, compression_results.csv
        runtime_vs_n.png, build_vs_k.png, size_comparison.png
    docs/
        PROJECT_REPORT.md   project documentation
```

## Documentation

The complete write-up (problem definition, design, algorithm, complexity, testing, results and future work) is in `docs/PROJECT_REPORT.md`.

## Limitations and future work

- It uses one static code table per file. Adaptive Huffman coding would adjust as it reads.
- It codes single bytes only. Coding common pairs or words, or combining with LZ77 as DEFLATE does, would compress text further.
- The tree is rebuilt from a 5-byte-per-symbol table. A canonical Huffman header (code lengths only) would be smaller.
- The Python decoder walks the tree one bit at a time. A lookup table decoder would be faster.
- Whole files are read into memory; very large files would need chunked reading.
