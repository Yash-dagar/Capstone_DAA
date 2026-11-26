# Huffman Coding File Compressor - Project Report

**Course:** Design & Analysis of Algorithms
**Assignment:** Capstone Project 3 - File Compression Using Huffman Coding

---

## 1. Project Overview and Objectives

The project compresses files with Huffman coding, a lossless method. Frequent symbols get short bit codes and rare symbols get long ones, so the file needs fewer bits overall.

Objectives:

1. Calculate the frequency of every character (byte) in a file.
2. Construct the Huffman tree using a priority queue.
3. Generate a binary code for every character.
4. Encode a file and decode it back, exactly.
5. Analyse time and space complexity.
6. Compare the original and compressed file sizes.

All parts are connected through a menu-driven program (`main.py`) and a browser page (`web/index.html`).

## 2. Problem Definition

**Input:** a text or binary file (a sequence of n bytes).
**Output:** a compressed `.huf` file, and the ability to restore the original exactly.

| Sub-problem | Technique |
| --- | --- |
| How often does each byte occur? | Frequency table (hash map) |
| Which two nodes should be joined next? | Min-heap (priority queue) |
| What code does each byte get? | Tree traversal |
| How do we store the bits? | Bit packing with a header |
| Is it correct and how fast is it? | Tests and runtime measurement |

Assumptions: the unit of compression is one byte, so any file type is accepted, including UTF-8 text. Codes are decided per file (static Huffman coding).

## 3. Algorithm

### 3.1 Why a prefix code

If no code is the start of another code, a stream of bits can be decoded without separators: walk down the tree from the root, and each time a leaf is reached, output its symbol and go back to the root. Huffman's algorithm produces the prefix code with the smallest possible total length for the given frequencies.

### 3.2 Construction (greedy)

1. Make a leaf for each distinct symbol, with its frequency, and put all leaves in a min-heap.
2. While more than one node is in the heap: remove the two nodes with the smallest frequency, create a parent whose frequency is their sum, and push the parent.
3. The last node is the root. A left edge is 0 and a right edge is 1; the path to a leaf is its code.

Ties are broken by a creation counter, so the same input always gives the same tree. This is also what lets the decompressor rebuild the tree from the frequencies alone.

**Worked example** (`abracadabra`: a=5, b=2, r=2, c=1, d=1):

| Step | Merge | New node |
| --- | --- | --- |
| 1 | c(1) + d(1) | 2 |
| 2 | b(2) + r(2) | 4 |
| 3 | 2 + 4 | 6 |
| 4 | a(5) + 6 | 11 |

Codes: a = `0`, c = `100`, d = `101`, b = `110`, r = `111`. Total = 5x1 + 1x3 + 1x3 + 2x3 + 2x3 = 23 bits, compared with 88 bits at 8 bits per symbol. The total always equals the sum of the internal node weights (2 + 4 + 6 + 11 = 23), which the tests use as an independent check.

### 3.3 Why the greedy choice is correct (sketch)

Two least frequent symbols can always be made siblings at the deepest level of some optimal tree: if they were not, swapping them with the deepest leaves cannot increase the total cost. Merging them into one node then leaves a smaller problem of the same kind, so induction on k gives optimality.

### 3.4 Edge cases

| Case | Handling |
| --- | --- |
| Empty input | No tree; the file stores only the header |
| One distinct symbol | The root has a single leaf, which gets code `0` (one bit per symbol) |
| Two symbols | One bit each |
| Bad or truncated .huf file | Rejected with an error message |

## 4. Design

### 4.1 Modules

| File | Role |
| --- | --- |
| `minheap.py` | Array-based binary min-heap with push and pop |
| `huffman.py` | `Node`, frequency table, tree, codes, encode, decode, entropy, ASCII tree |
| `compressor.py` | `.huf` format, bit packing, compress and decompress |
| `main.py` | Menu application |
| `performance.py` | Runtime and compression measurements, charts |
| `tests.py` | 49 correctness checks |
| `web/index.html` | Browser version with a drawn tree and live statistics |

### 4.2 The .huf format

A 4-byte magic number, a 2-byte symbol count k, k entries of (byte, 4-byte frequency), then the packed bits. The decoder stops after sum(frequencies) symbols, so padding in the last byte is harmless.

## 5. Complexity Analysis

n = input symbols, k = distinct symbols.

| Step | Time | Space | Reason |
| --- | --- | --- | --- |
| Frequency count | O(n) | O(k) | One pass, one hash update per symbol |
| Heap build | O(k log k) | O(k) | k pushes |
| Merging | O(k log k) | O(k) | k - 1 merges, each 2 pops and 1 push at O(log k) |
| Code generation | O(k) | O(k) | The tree has 2k - 1 nodes |
| Encoding | O(n) | O(n) | One table lookup per symbol |
| Decoding | O(n) | O(n) | Each output symbol costs its code length; the total is the number of bits, at most n x tree height |
| **Compression total** | **O(n + k log k)** | **O(n + k)** | |

For bytes k <= 256, so the tree step is bounded by a constant and compression is effectively linear in n. Decoding takes more time than encoding in practice because it walks the tree bit by bit.

**Compression quality.** For a source with entropy H bits per symbol, Huffman coding gives an average length L with H <= L < H + 1. The tests check this bound on 200 random inputs.

## 6. Testing

`python tests.py` runs 49 checks (see `results/test_results.txt`). All pass.

| Area | What is checked |
| --- | --- |
| Min-heap | Pops come out sorted; empty pop raises an error |
| Tree and codes | Known answer (23 bits for `abracadabra`); one and two symbol inputs; k - 1 merges; deterministic tree |
| Properties (200 random inputs) | Prefix-free codes; cost equals an independent `heapq` calculation; Kraft sum equals 1; entropy bound; never worse than fixed-length codes |
| Encode and decode | Round trip for text, one symbol, long runs and all 256 byte values; invalid bits raise an error |
| File format | Bit packing; empty, tiny, all-byte and random inputs; wrong magic, short header, truncated table and truncated payload rejected |
| Sample files | Every file in `data/` round trips; random bytes give a ratio near 1 |

## 7. Performance Analysis

All times are the average of 3 runs with a fixed random seed (`results/performance_output.txt`). Absolute values depend on the computer; the shapes are what matter.

### 7.1 Growing input size (k = 64)

| n | Count (ms) | Build tree (ms) | Encode (ms) | Decode (ms) |
| --- | --- | --- | --- | --- |
| 1,000 | 0.034 | 0.210 | 0.022 | 0.218 |
| 20,000 | 0.897 | 0.219 | 0.426 | 4.233 |
| 100,000 | 3.993 | 0.210 | 2.279 | 21.663 |
| 200,000 | 7.732 | 0.226 | 4.369 | 42.692 |

Count, encode and decode grow in proportion to n. Tree building is flat, because it depends on k and not on n. See `results/runtime_vs_n.png`.

### 7.2 Growing alphabet (n = 50,000)

Tree building grows from 0.004 ms at k = 2 to 1.18 ms at k = 256, which is consistent with O(k log k). See `results/build_vs_k.png`.

### 7.3 Original vs compressed size

| File | Original (bytes) | .huf (bytes) | Saved |
| --- | --- | --- | --- |
| repetitive.txt | 8,800 | 1,976 | 77.5% |
| large.txt | 158,770 | 73,657 | 53.6% |
| unicode.txt | 2,820 | 1,971 | 30.1% |
| medium.txt | 746 | 651 | 12.7% |
| random.bin | 20,000 | 21,286 | -6.4% |
| small.txt | 39 | 86 | -120.5% |

Observations:

- The more skewed the frequencies, the better the result. `repetitive.txt` has 4 symbols and compresses most.
- English-like text saves a little over half. Its average code length (3.705 bits) is within 0.03 bits of the entropy limit (3.674 bits).
- Random bytes cannot be compressed: all 256 values are equally likely, so every code is about 8 bits, and the header makes the file larger.
- Very small files lose because the code table (5 bytes per symbol) is larger than the data. This is the main cost of static Huffman coding.

## 8. Sample Output

`results/demo_output.txt` holds a run of the menu on `data/small.txt` (merge steps, codes, size comparison and compression). The drawn tree for the same input:

```
* (39)
0--a (16)
1--* (23)
    0--* (8)
        0--* (4)
            0--r (2)
            1--* (2)
                0--\n (1)
                1--! (1)
        1--* (4)
            0--* (2)
                0--c (1)
                1--k (1)
            1--* (2)
                0--l (1)
                1--m (1)
    1--* (15)
        0--* (7)
            0--* (3)
                0--z (1)
                1--d (2)
            1--space (4)
        1--* (8)
            0--b (4)
            1--n (4)
```

## 9. Web Page

`web/index.html` repeats the algorithm in JavaScript. The input is typed or uploaded, and it shows size statistics, the merge steps, the tree as a diagram with coloured 0 and 1 edges, the code table, the encoded bits, a round-trip check and a decoder for pasted bits. It runs in the browser; the file is not uploaded anywhere.

## 10. Limitations and Future Work

- Static coding: the table is stored with the file. Adaptive Huffman coding avoids this.
- Single-byte symbols only. Pair, word or LZ77 pre-processing (as in DEFLATE) would give better ratios on text.
- A canonical Huffman header (only the code lengths) would shrink the table from about 5 bytes per symbol to about 1 byte.
- A table-driven decoder would be faster than a bit-by-bit tree walk.
- Files are read fully into memory; chunked processing would handle very large files.

## 11. Conclusion

The project implements Huffman coding end to end: counting, a hand-written priority queue, tree construction, code generation, encoding, decoding and a real file format. The results match the theory: near-linear running time, optimal prefix codes within one bit of entropy, large savings on skewed data, and no gain on random data or very small files.
