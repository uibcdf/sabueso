---
summary: Explicit lossless exploration transport, bounded complete reading and atomic saving.
issue: uibcdf/sabueso#178
status: development
---

# Exploration file transport (#178, #167)

The measured [comparison](card_compressor_comparison.md) and
[qualified backends](zstd_backend_qualification.md) support a small first surface:
plain JSON by default, explicit gzip level 6, or Zstandard level 3 with checksum,
zero background workers and an 8 MiB encoder window. XZ stays an experimental
archival candidate; no measured interactive need justifies another production
backend/default. No automatic codec or filename-based choice is introduced.

## Public use

Both `CardView.save` and `AccessSelection.save` accept `compression="none"`,
`"gzip"` or `"zstd"`. Existing calls write plain JSON. The same requested original
canonical UTF-8 JSON bytes are encoded; no source assertion, quantity, request,
selected/hidden item, history occurrence or required support is removed. A codec
is storage transport, not a new Card schema or exploration scientific format.
Genuine @1–@6 files keep their original verifiers and trusted bundle digests.

`sabueso.read_exploration` detects ordinary gzip/Zstandard magic from file
content, otherwise reads UTF-8 JSON. Suffixes have no authority. It accepts exactly
one complete compressed member/frame, verifies codec integrity where present,
and refuses truncation, corruption, trailing bytes, concatenation (including an
empty second frame), dictionaries it cannot decode and unsupported framing.
JSON duplicate-member and all original scientific/binding checks still follow.
No source acquisition, Card reconstruction or current scientific recomputation
is added. A failed read returns no partial exploration.

Saving resolves optional support before bundle preparation or temporary creation,
then verifies the complete original bundle before encoding. It writes one temporary
sibling, flushes/fsyncs and publishes by atomic link (no clobber) or explicit
replacement. Budget, codec, filesystem or verification failures preserve an old
output; owned temporary siblings are removed. A missing requested codec is an
existing SMonitor `LibraryNotFoundError`, never substitution or biological absence.
The older-Python binding goes through DepDigest; 3.14 uses its optional native
module exclusively. Other codecs never request Zstandard. The optional distribution
metadata declares the 3.11–3.13 backport; required package dependencies stay fixed.

## Visible workload controls

Save/read expose `max_encoded_bytes` and `max_decoded_bytes`, each defaulting to
67,108,864 bytes (64 MiB). These limits also apply to plain JSON. A larger saved
reading now requires a consciously raised value or None; this is a visible
operational admission change, not silent truncation. Refusal names the argument
and its override. Strict positive integers or None remain checked with ArgDigest
skipped. Limits protect complete-file admission, not total Python-object memory:
save preparation/JSON and original scientific verification still materialize.

Read additionally exposes `max_window_bytes=8388608` for Zstandard. Use a power
of two of at least 1024 bytes within the backend range, or None for its platform
maximum. This codec window is separate from decoded bytes and total process RSS.
A failed window/codec decode explains the possible explicit window override;
raising it does not waive frame, checksum, JSON or scientific verification.

Encoded input is checked before reading from the file size and counted again as
chunks arrive. Compressed input/output calls use at most 65,536-byte chunks and
one detection byte beyond a byte ceiling. JSON bytes are released before original
scientific materialization. Successful receipts contain actual encoded/decoded
byte sizes and separate SHA-256 values under `transport`, distinct from the
scientific `bundle_digest`. `saved.validation["transport"]` reports observed read
transport/backend and effective limits; it is detached observational metadata,
not a SourceAssertion or a saved scientific claim. Encoded bit identity across
codec/library versions is not promised; original decoded bytes are exact.

## Qualification and scope

The [actual public API workload study](public_transport_workload.md) now records
five public retained readings, 45 saves and 45 fresh reads. `92af2c6` CI exposed
two historical calls above the default file ceiling; the test-only migration
asserts refusal then explicitly admits the verified original size with streamed
fixture preparation. This does not relax defaults, frozen bytes or science. The
failed source is not qualification; recover a new unskipped exact-source checkpoint.


Run the transport owning cases plus saved literal/science/sites/quaternary/assembly,
human/access/agent/navigation, argument, diagnostic, quantity and dependency gates.
Test real original quantities under a different unit policy, genuine historical
producer bytes, coherent resealing, missing codecs, strict limits/overrides,
corruption/trailing members and atomic output. Fresh outside-checkout readers
forbid current Card/science/network operations. Preserve protected original rules.

CI retains 18 jobs and thirteen pytest lanes. All twelve OS/Python routes run
`devtools/check_exploration_transport.py --installed` outside the checkout in
addition to the genuine backend probes. Older-Python binding acquisition uses
pinned public Conda backports.zstd 1.8.0, including the three macOS receiving lanes.
Those macOS lanes now install the consumer and its public runtime closure; they
are installed transport smokes, not additional full pytest lanes. Do not advertise
a new installation command before those clean public-channel checks pass.

Local integration passes 755 cases across nineteen files / 569.47 seconds,
followed by nine additional current @5/@6 human/agent transport cases / 15.33
seconds. The #179 failing two-test order is reproduced and its corrected order
plus fresh-process regression pass three cases. Peak integration owned RSS is
about 571 MiB, with zero owned swap and no guard stop. Warning-fatal Sphinx,
whole-repository Ruff, the executed new public example, Markdown/Python-3.11 syntax
and applicable fixture/schema/registry/dependency/governance checks pass. All 52
protected original verifiers/rules remain byte-identical. These are selected local
checks, not a full-local-suite or new hosted result. Exact-SDK reinstallation and
receiving gates are recorded with the actual committed source in the owning issues.

This production runtime needs a new unskipped exact-head CI/governance checkpoint
with full gh-run-receptor evidence. The earlier `1fdb771` result qualifies only the
engineering helper. Source-bound local and remote receipts belong in #178/#167/#112
and `recovered_work/card_transport_178_20261103/`. Retain original/qualification
proof with those owners, review at next transport/workload acceptance, and remove
only finished owned build/test/cache scratch. Public codec admission does not
establish faster scientific verification, accepted large workloads, completion of
#148/#173 or release readiness. 0.15.0 consolidation remains paused.
