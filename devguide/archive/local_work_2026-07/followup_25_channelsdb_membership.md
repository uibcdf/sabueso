# Follow-up 25: native ChannelsDB tunnel membership and channel references

Recovered on **2026-10-08** in the existing editable Python 3.14.7 environment.
This adapts the preserved ChannelsDB structural-context prototype and the original
lining-membership requirement, building on [follow-up 5](followup_05_source_integration.md).
Original stash, 87 exports, published card and empty index remain protected;
recovery stays local/uncommitted/unpushed.

## Original input and useful scope

The preserved `protein_translational_sources.py` generic ChannelsDB mapper supplied
a caller protein fallback and a fixed predicted class, while the original cavity
prototype could count loosely parsed residue lists. Their useful requirements are
native channel membership, occurrence support and explicit structure/residue scope.
Those defaults, generic row guessing and unqualified composition are not restored.

Current [provider OpenAPI](https://channelsdb2.biodata.ceitec.cz/api/openapi.json)
documents the separate read-only `/channels/pdb/{pdb_id}` GET, twelve required
category arrays and independent `Annotations`. Item schemas are opaque. API
version 1.0.0 is not a channel/input/scientific revision. The separate
[methods description](https://channelsdb2.biodata.ceitec.cz/methods.html) explains
channel lining and layers without establishing the exact numbering, chain,
model/assembly or sequence revision for this response.

One public existing-result GET for **1tqn** returned HTTP 200 at
**2026-10-08T08:55:00+00:00**, **751462 original bytes**, SHA-256
`f279ce91ee43ec6df7854923b8c46b723c31c2ebca204ae0309c3923ba5dd7f7`.
The new fixture `temp_data/channelsdb/channels__1tqn.json` is unchanged and
byte-identical to the earlier native probe `/tmp/sabueso-b5-channels-native.json`;
that older probe's exact retrieval time remains unknown. The separate OpenAPI
request has its own time/hash and is documentation, not scientific input.
The response contains **26 channel occurrences**, **910 layers** and **7 channel
comment/reference occurrences** across twelve category arrays. Membership lists
contain **1225 ResidueFlow**, **1059 HetResidues** and **3338 per-layer residue token
occurrences**; these are repeated source occurrences, not unique residues.

MOLE and CAVER native Id/Auto types differ. CAVER's field named HetResidues can
contain ordinary residue labels, and a layer's Residues/FlowIndices arrays can
have different cardinalities and labels. No homogeneous semantic interpretation,
chemical classification, index resolution or guessed set repair is justified.
Several comments repeat an Id with different references; that equality alone does
not attach them to any channel/category or merge scientific identity.

The [official documentation](https://channelsdb2.biodata.ceitec.cz/documentation.html)
and source terms remain **NOT-STATED**, with unknown sharing permission. Frontend
Apache, article CC BY and underlying input-resource rights are separate. Credit
ChannelsDB contributors, doi:10.1093/nar/gkad1012, and original reference/input
labels. The public fixture is declared in `temp_data/NOTICE.md` for local unpublished
qualification; no redistribution right or publication is claimed.

## Delivered behavior

`channelsdb.get_channels(identifier, client=None)` reads one explicitly selected
PDB context through online/fixture/source-kind-query-bound JSON/gzip clients. It
shares named transport, acquisition diagnostics and archive replay. Raw original
JSON, byte hash, original time or caller declaration and separate file read time
remain explicit. The response does not echo the PDB ID: online URL or supplied
declaration binds its context, not independent source identity proof.

`channelsdb_tunnel_membership_json@1` validates all required category arrays and
bounded membership/comment items before output. Late malformed/nonfinite items,
unknown/missing categories, unsupported revisions or cut/foreign envelopes fail.
Empty arrays differ from missing/malformed arrays or failed access, including 404.
`truncated=False` concerns the whole received DTO, not database completeness.

`map_channel_memberships` produces **26** standalone
`structure.channelsdb_tunnel_membership` SourceAssertions. Every channel's native
header, ResidueFlow, HetResidues and per-layer Residues/FlowIndices lists retain
their original order, labels and occurrences. `map_channel_annotations` separately
produces **7** `structure.channelsdb_channel_annotations` assertions preserving
original text and reference literals. Source-scoped occurrence subjects, explicit
identity basis, full-response canonical hash and file/transport byte support remain
detached from mutable input. Native comments are not joined by Id.

No token decoding, deduplication, parent/set repair, index resolution, chemical
class, experimental/MOLI Evidence class, source-ID channel/cavity merge or caller
protein assignment occurs. Profiles, geometry and physicochemical properties stay
in the full original DTO, uninterpreted and unmapped; no normalized physical quantity
is created from them. Numbering, chain/model/assembly/sequence axes and scientific
revisions remain unqualified. No current canonical location, composition, detected
cavity, structure-coordinate download, separate assembly/annotation/AlphaFill route,
analysis job, card/schema field or automatic enricher is introduced.

## Remaining useful work

Geometry/physical properties need a qualified native contract and explicit units
before normalized mapping. Structural/sequence projection and composition need
exact source-declared chain/numbering/insertion and model/assembly/sequence/revision
support. Separate assembly, entry annotations and channel comments cannot be joined
by equal labels. Native channel membership is not a newly detected structural cavity
or proof that a current protein residue belongs to one. Consumer acceptance remains
owner-reviewed work.

Expanded queue remains **6 scoped / 7 pending / 0 unreviewed**; original 27-list
**21 scoped / 6 pending / 0 unreviewed**. Pending providers: **ASD, GtoPdb, COSMIC,
ELM, BioCyc, OMIM and CASTp**. Catalog stays **65 in use / 7 evaluating / 11 deferred /
3 retired / 1 out of scope**. This is useful additional scope within an already
adopted source. No gated route, login/agreement, upload or scientific job is attempted;
the stash is retained.

## Qualification

Focused ChannelsDB native membership and existing annotation gates: **139 passed
in 3.74 seconds**, pytest-receptor with **12 workers**, including **44 new cases**.
They qualify original counts/support, literal source quirks, repeated/cross-category
IDs, differing arrays, opaque/signed/insertion/Backbone labels, empty/missing and late
malformed tables, all envelope guards, custom-client rebinding, public/skipped
digestion, JSON/gzip hash/time/terms, unavailable/duplicate-key files, one native GET
and zero-network archive replay with original support.

Full offline checkpoint: **5401 passed in 167.86 seconds**, pytest-receptor with
**12 workers**, 10 expected failed/cut enrichment-fixture warnings. Ruff lint/format
(**928 files**), registry/generated metadata, strict Sphinx HTML at
`/tmp/sabueso-followup25-docs-build`, frozen-card shape/schema and diff gates pass.

Outside-checkout verification confirms the shared editable origin and replays the
imported original response with its original timestamp, byte hash and all 33
assertions, using **zero verification network requests**. Native fixture intake
produces the same values and preserves its separate supplied-file receipt. One
scientific qualification GET was made; a separate OpenAPI GET read documentation.
Native receipt: `/tmp/sabueso-followup25-native-receipt.json`; ignored preview:
`recovered_work/current_preview/1tqn.channelsdb_membership.json`.
`/tmp/sabueso-followup25-integrity.json` verifies 87 original lengths/hashes,
91 accounted paths, stash/index/published card, prior LIGYSIS and ChannelsDB
annotation bytes, new channel DTO equality to both earlier and current originals,
and unchanged catalog counts. Acquisition receipt:
`/tmp/sabueso-followup25-acquisition.json`; original OpenAPI documentation:
`/tmp/sabueso-followup25-openapi.json`; gates:
`/tmp/sabueso-followup25-gates.json`.

The owning [issue #130](https://github.com/uibcdf/sabueso/issues/130) records this verified local slice and remaining
source/projection requirements. It stays open until the remaining acceptance needs
and a repository code checkpoint are handled. No separate environment, stage, commit, push, remote CI, release
or stash deletion occurs.
