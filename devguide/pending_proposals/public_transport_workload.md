---
summary: Actual public save/read costs over five original readings, with exact retained content and history.
issue: uibcdf/sabueso#167
status: measured
---

# Public exploration transport: measured API costs

Measured source `92af2c646c9c94686352b0ca5508009b67af46db`, editable SDK
`0.14.0+144.g92af2c6`, on Linux / Python 3.14.7. The
[public transport](exploration_file_transport.md) is implemented; its measured
source CI failed two large-fixture admission tests and is **not hosted-qualified**.
The following test-only correction preserves production defaults and all 653
tracked package files. Local measurements do not supersede remote admission.

## Actual API protocol

Five existing immutable **public saved readings** cover protein function, molecule
properties, disease meaning, structure context and accumulated structure reading.
No private pilot, new molecular query, fixture access or current scientific engine
is used during receiving. Each producer starts outside the checkout, opens the
original through `read_exploration` with its trusted bundle digest, then times the
actual `CardView.save` call. A separate fresh process times the actual public read
of that output with its returned trusted bundle digest. Imports/guard setup and
the producer's initial original read are outside the timed calls. This measures
reopening and saving retained exploration, not initial live capture/first viewing.

Three repetitions per case/codec produce **45 actual saves and 45 fresh reads**,
serially in seeded shuffled order (`167178`), with plain JSON, gzip 6 and Zstandard
3 (checksum, zero background workers, 8 MiB encoder window). OS cache and background
load are uncontrolled; these are observations, not a cold-cache or startup benchmark,
causal latency improvement, scaling curve or researcher-accepted workload budget.

Every output verifies through the original public scientific reader. All captured
Cards, input pins, retained objects and typed locations are byte-equivalent after
canonical comparison. Every history-node occurrence/edge, request, selection,
support and original presentation policy stays equal after normalizing only the
known operational `state.context.mode` transition from live to saved. Re-saving
updates producer/operational metadata, so compare the **new plain output** with
its compressed counterparts rather than pretending it is the original container.
All variants/repeats reconstruct the same complete new canonical JSON; all five
original input hashes remain unchanged. Root native payload, request, verifier,
text and HTML match between each saved source view and the independently reopened
output. Transport hashes/sizes match actual reading and the save receipt.

## Size and complete call times

Sizes are actual re-saved outputs in bytes. Timing cells below are median wall
seconds for **save / read**, including preparation, original verification and
atomic file publication where the public call performs them.

| Public reading | Plain JSON | Gzip | Zstandard |
| --- | ---: | ---: | ---: |
| Protein function | 1,403,771 | 93,779 | 61,025 |
| Molecule properties | 1,483,303 | 80,819 | 45,198 |
| Disease meaning | 952,736 | 54,969 | 32,322 |
| Structure context | 10,472,487 | 406,029 | 158,309 |
| Accumulated structural reading | 11,009,800 | 378,716 | 99,232 |

| Public reading | Plain save / read (s) | Gzip save / read (s) | Zstandard save / read (s) |
| --- | ---: | ---: | ---: |
| Protein function | 0.527 / 0.958 | 0.505 / 0.964 | 0.508 / 0.961 |
| Molecule properties | 0.613 / 1.001 | 0.635 / 1.012 | 0.603 / 1.038 |
| Disease meaning | 0.416 / 0.362 | 0.416 / 0.357 | 0.378 / 0.356 |
| Structure context | 4.509 / 3.657 | 4.466 / 3.622 | 4.416 / 3.606 |
| Accumulated structural reading | 3.629 / 3.038 | 3.545 / 2.983 | 3.450 / 3.031 |

Gzip removes **93.32–96.56%** and Zstandard **95.65–99.10%** of these new plain
outputs. The accumulated reading is 11,009,800 bytes plain, 378,716 gzip and
99,232 Zstandard. Its median reads are 3.038, 2.983 and 3.031 seconds respectively.
The small differences do not establish a causal full-read speedup. Complete
scientific verification remains active; compression primarily reduces stored bytes.
The earlier codec-only measurements use different containers/window settings and
cannot be substituted for these complete API observations.

## Memory, visible limits and the large historical test

Fresh-reader process watermarks after the public API range from about 69 to
160 MiB across these cases, with similar figures among codecs. They include
imports; producer watermarks include initial original restoration and input
accounting. Post-check
watermarks are recorded separately: identity/rendering/graph comparisons are not
silently attributed to the timed API. The supervising process tree peaks at about
315 MiB, with zero owned swap, no resource stop and unchanged original inputs.
The matrix runs under a 1 GiB sampled owned-RSS ceiling, 4 GiB available /256 MiB
genuinely free host floors, zero owned swap and 2 GiB owned scratch ceiling.

The five measured inputs are roughly 0.95–11.0 MB. A **separate** genuine historical
test file is 89,849,893 bytes and exceeds the new 64 MiB default. CI exposed two
older tests that had not opted into that larger workload. They now first require
the explicit default refusal and then pass positive encoded/decoded ceilings
equal to the verified original file size. Preparation and unchanged-file checks
stream the same frozen gzip/hash rather than retaining another large byte buffer.
The original SHA-256, scientific values and independent verifiers remain fixed.
The remaining selected transport/cell/region/dependency gate passes 203 cases;
its two explicitly deselected large cases run independently as described below.

The initial unstreamed local test attempt was stopped at the owned-RSS ceiling,
with zero owned swap; it is not a passing gate. The streamed two-test gate passes
2/2 in 48.85 seconds, with about 1,017 MiB sampled whole-test RSS and zero owned
swap. This includes pytest, fixture preparation, original scientific materialization
and test checks; it is not an isolated read-memory budget. These results reinforce
that file/window bounds do not bound total Python-object memory. No production
default was raised or silently disabled to satisfy the historical tests.

## Evidence and next scope

The [machine-readable aggregate receipt](public_transport_workload_checkpoint.json)
keeps all samples/ranges, backend settings, input hashes and resource observations.
Actual scripts, inputs manifest, per-worker stdout/stderr/results, original graph
parity and source/import proofs remain under
`recovered_work/public_transport_cost_167_20261103/`, owner #167/#178/#112; review
at workload acceptance or the next saved-transport change. Keep useful originals
and representative outputs; remove only finished owned disposable duplicates.

The corrected large-original and applicable local gates are followed by verified
unskipped CI 18/18 and governance 1/1 at `5f4ab15`, SDK145. All thirteen actual
pytest summaries, twelve backend producers and twelve installed transport routes
are reviewed through full gh-run-receptor evidence; the
[compact receipt](../evidence/transport_checkpoint_20261103.json) binds the source
and original manifests. The failed `92af2c6` run is never qualification. This
completes the bounded local API measurement, not #167's entire performance/human
acceptance obligation. Keep complete verification and retained history/support.
Resume #148/#173's structural/scientific exploration order after the transport
checkpoint; agreed large-workload budgets, broad-profile researcher acceptance
and 0.15.0 consolidation remain separate/open.
