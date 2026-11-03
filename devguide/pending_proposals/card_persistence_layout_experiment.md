---
summary: Compare shared view parts with compressed original bytes before changing persistence.
issue: uibcdf/sabueso#167
status: experimental_intermediate
opened: 2026-11-03
area: [persistence, performance, human-exploration, historical-reading]
---

# Physical storage experiment and compression baseline

This is the original experiment, not the production transport contract. The
following [file transport](exploration_file_transport.md) adds explicit compression
in development with separate runtime/installed qualification. The experiment
and its original measurements/readers remain unchanged.

## Result and scope

The experiment reconstructs every original byte of five public saved readings.
It shares exact canonical values only within the same view-part namespace:
`selection`, `state`, `native_payload` or `flags`. Every view occurrence, selected
member, origin, source path, unit, request, unknown and scientific result remains
present. Matching content shares storage only; it establishes no molecular identity.

The comparison supports investigating **optional compression of original JSON**
before introducing a reference-based public format. Gzip alone removes
93.36–96.58% of original bytes here. Sharing before gzip makes four files larger
than gzip alone; only the accumulated reading gains another 14.13%. This adopts
no production format or reader change. CPU, capture/verification cost and
whole-process memory remain separate work.

| Public reading | Original JSON bytes | Shared-part bytes | Gzip original bytes | Gzip shared bytes |
| --- | ---: | ---: | ---: | ---: |
| Protein function | 1,403,696 | 1,084,007 | 93,205 | 108,421 |
| Molecule property context | 1,483,207 | 1,039,374 | 79,822 | 98,115 |
| Disease meaning | 952,668 | 669,762 | 55,237 | 67,004 |
| Original structure context | 10,472,177 | 8,036,664 | 392,538 | 446,849 |
| Accumulated 2V5B reading | 11,009,687 | 5,857,671 | 376,867 | 323,610 |

Inputs are original public fixture readings from qualified runtime
`baac1438810eb3ef4af8a98f14116a2d0c8e547b`, SDK `0.14.0+139.gbaac143`, and
the preceding original SDK138 accumulated guide. No private pilot or new source
acquisition is involved. Input hashes remain unchanged. The earlier four-nature
preparation census observes 65–263 automatic support views created at first save,
unchanged Cards/scientific cache keys and byte-stable repeated saving. Automatic
support is not dispensable: the experiment removes no history or prepared support.

## Reproduce the engineering comparison

In an existing development checkout, run one owned resource-limited worker with
a new caller-owned output directory:

```bash
python devtools/experiment_exploration_storage.py original.json new-experiment-directory
```

The helper accepts canonical JSON with a `views` object. It emits an unsupported
shared-layout artifact, gzip packaging of original/shared bytes, and a report of
actual sizes/hashes and exact reconstructed-original hash. `read_exploration`
does not accept these experimental artifacts. The helper does not import Sabueso
or verify science; use the original reader and trusted expected digest separately.
Internal hashes establish consistency, not external source truth.

The visible default input/reconstructed-output ceiling is 67,108,864 bytes
(64 MiB). Refusal explains the limit and override: use
`--max-expanded-bytes <positive integer>` or `--max-expanded-bytes none` deliberately.
Parsing, part pools and full reconstructed JSON remain in memory; retain a process
resource supervisor. This byte ceiling does not bound all Python-object/RSS cost.
Noncanonical input is refused rather than normalized. Unknown layout members,
missing/foreign-kind references, changed parts, shadowed fields, unused parts,
false byte counts, duplicate keys and nonfinite values are refused. Reference-like
literal dictionaries remain literal. Exact expanded size is checked before full
reconstruction/encoding. Existing caller output directories are never overwritten.

Gzip uses the standard library, level 6 and `mtime=0`. Compressed bytes may differ
across Python/zlib versions; decoded original bytes remain exact. The recorded
host uses Python 3.14.7 and zlib 1.3.2.

## Receiving and qualification

Five fresh reader subprocesses outside the checkout receive each original and
reconstruction with its original expected bundle digest. Card construction,
current assembly engines/catalog helpers, network and fixture access are forbidden;
frozen original verification remains active. Native payload, text and HTML match
for all pairs under literal @1 and structure-assembly @6 verification. The helper's
nine codec/accounting function ASTs match the measured prototype; its CLI reproduces
the accumulated case's exact artifact hashes and sizes.

The selected local gate passes 38 cases across experiment and existing accounting
tests: genuine old capsule, inert receiving, typed Boolean/integer distinctions,
absent/null parts, literal reference lookalikes, tampering, pre-expansion refusal,
explicit overrides and caller-output preservation. This is not a new full-suite,
installed-package or exact-head hosted qualification.

Single observed sharing pack/unpack costs range from 0.109–1.547 s and
0.073–1.167 s. Gzip original encoding takes 0.014–0.108 s; decoding 0.002–0.023 s.
Caches/background load are uncontrolled; these establish no end-to-end speedup,
RSS reduction, scaling curve or accepted workload budget. Original verification
still runs. Workers are serial; largest sampled combined owned RSS is about
313 MiB, with zero owned swap and no resource stop. The historical 125 MB workload
is outside this bounded experiment.

## Next bounded implementation

1. Select optional transport through [the compressor comparison](card_compressor_comparison.md)
   (#178) before fixing a public codec/default. Gzip remains the measured
   compatibility baseline; Zstandard/XZ and supported-Python backend qualification
   now have their own comparison. Preserve unchanged canonical original bytes.
   Preserve default plain JSON and original @1–@6 readers. Save encoding must be
   explicit; detect checked input content rather than trusting a filename suffix.
   Preserve trusted `bundle_digest`, distinguishing compressed-file checksum and
   actual encoded/decoded sizes in receipts.
2. Implement bounded streaming decompression with visible decoded-byte refusal,
   positive/None override, strict arguments including skipped digestion, complete
   member/CRC checks and explicit trailing/member handling. Refuse partial output;
   retain atomic no-clobber/overwrite saving and owned temporary cleanup. A byte
   ceiling does not promise bounded whole-process memory.
3. Preserve current canonical producer behavior. Changing JSON encoding, support
   preparation, scientific verification, session retention or defensive public
   copies requires separate proof; compression alone authorizes none of them.
4. Qualify public protein/molecule/disease and mixed scientific/history routes,
   old files, fresh inert receiving, quantities and source closure. Measure full
   save/read/cached interaction and agree researcher budgets. Recover this
   intermediate helper's deferred CI at the final unskipped exact-SHA CI/governance
   checkpoint through gh-run-receptor before adoption or release.

Public compression is not implemented by this study. Finalize argument/receipt
details and default workload values with regression cases in that change.
Keep #167 open, then resume the approved broader structural/exploration order.
Researcher acceptance and 0.15.0 consolidation remain separate and pending.

Originals, subprocess receipts, tool/prototype hashes, comparison and resource
guards live under `recovered_work/shared_parts_experiment_167_20261103/`.
Owner #167/#148/#112; review at layout adoption or workload acceptance. Preserve
original inputs/capsules and useful proof; clean only finished owned reconstructions,
duplicate packaging and disposable process/build caches. Protect caller-requested
tool outputs. Publication/deferred-CI receipts belong to #167/#112 and
[the ledger](deferred_ci.md).
