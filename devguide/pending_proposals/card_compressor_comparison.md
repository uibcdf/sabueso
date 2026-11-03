---
summary: Compare gzip, Zstandard and XZ on identical original public readings before choosing transport.
issue: uibcdf/sabueso#178
status: measured_intermediate
opened: 2026-11-03
area: [persistence, performance, historical-reading]
---

# Compressor selection: first measured comparison

The maintainer requested a dedicated compressor discussion and experiment in
[#178](https://github.com/uibcdf/sabueso/issues/178), under persistence #167 and
coordination #112. Gzip remains the portable measured baseline, rather than a
preselected production answer. The [earlier layout study](card_persistence_layout_experiment.md)
preserves its original observations; this comparison broadens that study.

## Method and reproducibility

`devtools/compare_exploration_compressors.py` compares opaque original bytes,
without importing Sabueso or changing a public saved format:

```bash
python devtools/compare_exploration_compressors.py compare original.json --output new-comparison-directory --repeats 3
```

The default matrix contains plain bytes, gzip levels 1/6/9, Zstandard 1/3/6 and
XZ presets 0/3/6. Five retained public readings, three repeats per setting,
give **150 fresh subprocess samples in 50 groups**. Workers run serially in
seeded shuffled order (seed 178). No warmups or OS-cache clearing are performed;
background load/cache state remain uncontrolled. Timings are medians for in-memory
encode/decode calls, excluding startup, file input, JSON parsing and scientific
verification. Every decoded byte and original input hash is checked; encoded
hashes also remain stable within each three-sample group on this environment.

The visible default input/output-workload ceiling is 64 MiB. Override deliberately
with `--max-expanded-bytes <positive bytes>` or `--max-expanded-bytes none`.
It does not bound total process memory. Decoders receive only their own freshly
encoded data here; this is not an untrusted compressed-file reader. Existing
caller output directories are preserved. Missing optional backends remain
explicitly unavailable, without substitute codecs, invented zeros or mixed groups.

Measured environment: Python 3.14.7, zlib runtime 1.3.2 and native Zstandard 1.5.7.
The local Conda manifest lists liblzma 5.8.3; its loaded runtime version is not
exposed by the stdlib API. Zstandard uses zero background workers and an enabled
frame checksum; gzip uses `mtime=0`; XZ uses CRC64. All are lossless experiments.
The original five reading inputs and schemas remain unchanged, with no network
requests, new molecular acquisition or private pilot material.

## Stored size

| Public reading | Original bytes | Gzip 6 | Zstd 3 | Zstd 6 | XZ 6 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Protein function | 1,403,696 | 93,205 | 60,865 | 55,921 | 50,032 |
| Molecule properties | 1,483,207 | 79,822 | 44,889 | 42,018 | 37,416 |
| Disease meaning | 952,668 | 55,237 | 32,006 | 29,818 | 26,984 |
| Structure context | 10,472,177 | 392,538 | 169,063 | 150,033 | 124,640 |
| Accumulated 2V5B | 11,009,687 | 376,867 | 120,513 | 99,728 | 71,108 |

For the accumulated 2V5B input, median codec times and maximum whole-worker
high-water RSS across three samples are:

| Setting | Encode ms | Decode ms | Worker peak MiB |
| --- | ---: | ---: | ---: |
| Gzip 6 | 108.71 | 25.71 | 57.00 |
| Zstd 3 | 9.46 | 20.40 | 67.86 |
| Zstd 6 | 19.09 | 16.65 | 68.06 |
| XZ 3 | 178.73 | 21.11 | 69.57 |
| XZ 6 | 840.28 | 23.35 | 124.89 |

These observations favor Zstandard as a **candidate for balanced interactive
storage**, with gzip as a compatibility baseline. XZ 6 produces the smallest
files here, at greater write time and worker memory. They do not establish a
universal winner, a public default, cross-platform performance or accepted budgets.

## RSS method correction

A local Linux diagnostic observes a fresh child's `ru_maxrss` at 164,913,152 bytes
while its `/proc/self/status` VmHWM is 13,131,776 bytes after a parent allocation.
Inherited pre-exec high-water state can therefore contaminate a supposed isolated
worker measurement. Linux reports now use worker VmHWM since exec. Regression
cases preserve unknown measurements when unavailable and reject mixed RSS bases.
Other platforms report the explicit normalized resource basis or no measurement.
RSS includes worker setup, input/output buffers and hash checks, not isolated
codec allocations. This is a benchmark-method correction, not a CPython defect.
Earlier matrices are retained as superseded RSS diagnostics; the table above
comes from the final source's complete rerun.

## Original receiving remains the main read cost

A separate experiment uses the original accumulated format @6 input, with three
fresh external workers for each of plain/gzip6/zstd3/zstd6/xz3/xz6, plus one public
`read_exploration` control: **19 receiving workers**. The experimental bridge
includes file input, decode, raw hash check, UTF-8/JSON parsing and unchanged
original `_restore` verification. Startup and final display rendering are excluded
from receive timing. It is not a delivered public compressed-file API.

| Experimental bridge | Median receive seconds | Median original verification seconds |
| --- | ---: | ---: |
| Plain | 3.3232 | 3.0547 |
| Gzip 6 | 3.1651 | 2.8929 |
| Zstd 3 | 3.2547 | 2.9868 |
| Zstd 6 | 3.3250 | 3.0443 |
| XZ 3 | 3.1671 | 2.8949 |
| XZ 6 | 3.2903 | 3.0083 |

Original root/verifier and text/HTML hashes match across all workers and the public
reader control. Current Card construction, assembly engines/catalog helpers,
network and fixture access are forbidden; original frozen predicates remain active.
Cache/load/order effects are uncontrolled. **No causal receive-latency improvement
is demonstrated**; original verification dominates these timings. Process memory
is also similar across these bridges, about 154–155 MiB worker peak. The final
codec/RSS function ASTs match those used for receiving despite later comparison
argument-guard changes. The 125 MB historical case is not included.

## Qualification and next bounded work

The [backend continuation](zstd_backend_qualification.md) now qualifies native
and older-Python routes with genuine frames and an unskipped recovery checkpoint.
The following counts describe the preceding comparison checkpoint.

The owning local gate passes 65 cases across comparison, shared-layout and storage
accounting tests: exact native round trips, unavailable backends, explicit limits,
input/worker binding, seeded complete repeats, duplicate-setting refusal, mixed
hash/backend/RSS refusal, genuine original receiving and caller-output preservation.
All 648 tracked package files and 52 protected original rules remain unchanged.
This engineering helper/test continuation uses the authorized intermediate CI
batching route; it is not an exact-head hosted-qualified code checkpoint. Recover
the accumulated #167/#178 helper scope before adoption/release or final block
completion as [the ledger](deferred_ci.md) requires.

Before choosing production support/defaults, qualify Python 3.11–3.13 optional
Zstandard bindings and all supported platform routes. Native `compression.zstd`
was added in 3.14 and is itself optional; unavailable native measurements on other
versions do not establish public backend support. Any production optional backend
must follow DepDigest. Keep public plain-JSON behavior and original @1–@6 bytes,
trusted bundle digests, complete history/support and frozen readers. Finalize a
small explicit codec surface, bounded complete-frame decoding with deliberate
overrides, atomic saving and receiver/quantity/source regression gates. Public
compression remains unimplemented, #178/#167 stay open, and 0.15.0 consolidation
remains paused. Continue broader exploration after this bounded persistence block.

Primary API references: [Python gzip](https://docs.python.org/3.14/library/gzip.html),
[Python Zstandard](https://docs.python.org/3.14/library/compression.zstd.html),
[Python LZMA](https://docs.python.org/3.14/library/lzma.html).
Local immutable inputs, final/superseded matrices, native-library metadata,
worker output, receiving/source equivalence and resource proofs remain under
`recovered_work/compressor_comparison_178_20261103/`, owned by #178/#167/#112.
Review at codec adoption or workload acceptance; clean only completed owned
scratch and duplicate experiment payloads, preserving useful proof/caller outputs.
