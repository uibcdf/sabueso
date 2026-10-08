# Follow-up 24: native LIGYSIS structure mapping and declared chain identities

Recovered on **2026-10-08** in the existing editable Python 3.14.7 environment.
This continues the preserved binding-residue/structural-context requirements and
[follow-up 23](followup_23_ligysis_correspondences.md). Recovery remains local;
the original stash, 87 exports, empty index and published card are protected.

## Original input and useful scope

The [provider implementation](https://github.com/bartongroup/LIGYSIS-web/blob/master/app.py)
documents a read-only `/get-uniprot-mapping` POST with `pdbId`, `proteinId` and
`segmentId`. Its file blob `7c30cc0906bc64720ff165e80c49f0dffefd1ed0` was read as
documentation, without executing provider code or loading pickle files. This is
not the mapping's software/data revision. The route reads existing mapping tables;
it does not submit an analysis or upload coordinates.

One public query (`7t0q`, `P60174`, segment `1`) received HTTP 200 at
**2026-10-08T07:06:36+00:00**. The unchanged original response is
`temp_data/ligysis/mapping__P60174__1__7t0q.json`, **9185 bytes**, SHA-256
`31cecd5b839f7c513fb2d330dfa618abc86b99d1756a8ab0ee37580e961be836`.
Native `pdb2up`/`up2pdb` each name 7t0q and contain two chains, **245 A + 246 B =
491 entries per direction**. `chain2acc` explicitly declares A and B as P60174;
`chains` supplies eight remappings (A–H). Those tables share one source response,
not independent scientific confirmation. Their parent sets are different and
must not be completed by guessing missing declarations.

The current code describes `chains` as new author asym IDs to original label asym
IDs. That documentation does not version the response or independently declare
the chain2acc/residue namespaces. Protein/segment request context is not echoed;
only the directed structure parents confirm the requested PDB ID. This newly
received mapping is kept separate from the older unversioned segment HTML.

The [official access page](https://www.compbio.dundee.ac.uk/ligysis/about) was
reviewed again: website access is public, including commercial users, without
login. Separate data redistribution rights remain **NOT-STATED**, with unknown
sharing permission. MIT code and article rights are not assigned to the response.
The public fixture is declared in `temp_data/NOTICE.md` for local unpublished
qualification; no source licence or publication policy is widened.

## Delivered behavior

`ligysis.get_structure_mapping(identifier, segment, pdb_id, client=None)` uses
online/fixture clients. The public PDB argument has its own ArgDigest digester;
semantic checks still run with digestion skipped. Online reading shares the
named transport, JSON validation, acquisition diagnostics and retrieval archive.
Fixture reading uses the shared supplied-snapshot loader, original file SHA-256
and separate local read time. Missing/malformed files and HTTP 404 are failures,
never biological absence. Unsupported revisions and incomplete envelopes fail.

`map_structure_mapping(envelope)` validates all four tables before output under
`ligysis_structure_mapping_json@1`. It produces **14** standalone
`annotations.ligysis_structure_mapping` SourceAssertions: four full directed
chain dictionaries, two explicit accession declarations and eight remappings.
Native labels, order, complete directed pairs and detached original support stay
separate. The canonical decoded-JSON hash is explicitly distinguished from the
original file/transport byte hash. Source-scoped subjects carry query context;
the queried protein is never assigned to a chain without its native declaration.

Heteromer/isoform declarations, chain case, signed/zero/leading-zero residue keys,
missing opposite parents and non-bijective/conflicting declarations retain their
literal form. Empty received tables differ from missing tables. No inversion,
repair, chain merge, cross-table inference or join to the old HTML occurs. Chain2acc
namespace, structure residue numbering/insertion codes and scientific revisions
stay explicit unknowns. No current canonical residue location, coordinate access,
ligand record, scientific calculation/job, card field/schema or enricher is added.

## Remaining useful work

Qualified projection still needs explicit numbering/insertion and chain namespaces,
compatible structure/sequence/mapping revisions and original scientific input.
Other structure/segment/ligand and site-table scopes remain unqueried. Consumer
projection requirements remain owner-reviewed work; this source reading does not
establish receiving-component acceptance.

Expanded queue stays **6 scoped / 7 pending / 0 unreviewed**; original 27-list stays
**21 scoped / 6 pending / 0 unreviewed**. The seven are **ASD, GtoPdb, COSMIC, ELM,
BioCyc, OMIM and CASTp**. Catalog stays **65 in use / 7 evaluating / 11 deferred /
3 retired / 1 out of scope**. This qualifies more useful scope in an already
adopted source and does not reduce that provider queue. No gated route/account,
agreement, upload or scientific job is attempted. The stash is retained.

## Qualification

Focused new/previous LIGYSIS and AlphaFill checks: **211 passed in 4.07 seconds**,
pytest-receptor with **12 workers**, including **43 new cases**. They guard native
support/identity, independent table parents, heteromers/isoforms, signed labels,
empty/missing/malformed/duplicate-key/foreign/cut/revision cases, public digestion
before access, one read-only POST and zero-network archive replay with original time.

Full offline checkpoint: **5357 passed in 160.30 seconds**, pytest-receptor with
**12 workers**, 10 expected failed/cut enrichment-fixture warnings. Ruff lint and
format (**926 files**), registry/generated metadata, strict Sphinx HTML at
`/tmp/sabueso-followup24-docs-build`, frozen-card shape/schema and diff gates pass.
An invalid `card_shape.py --check` invocation and a nonexistent `check_schema.py`
path were corrected to the maintained gate commands; neither is passing evidence.
The misleading card-shape tool docstring now states its actual no-flag check command.
The final registry wording and documentation are checked again after correction.

Outside-checkout qualification verifies the editable origin and replays the imported
original response with its original time/hash and **zero verification network
requests**. It also qualifies the native fixture intake and all 14 assertions.
One scientific request was made for initial source qualification. No old-page join
or canonical location is generated. Native receipt:
`/tmp/sabueso-followup24-native-receipt.json`; ignored local preview:
`recovered_work/current_preview/P60174.ligysis_structure_mapping.json`.
`/tmp/sabueso-followup24-integrity.json` verifies 87 original lengths/hashes,
91 accounted paths, stash, empty index, frozen-card equality to HEAD, old native
LIGYSIS HTML bytes, new JSON byte equality to the original and unchanged counts.
Acquisition receipt: `/tmp/sabueso-followup24-acquisition.json`; provider-code
reference: `/tmp/sabueso-followup24-provider-reference.json`; gate receipt:
`/tmp/sabueso-followup24-gates.json`.

The owning [issue #129 follow-up](https://github.com/uibcdf/sabueso/issues/129#issuecomment-6054707206) tracks this local
implementation and remaining projection needs. It remains open until a repository
code checkpoint. No separate environment, stage, commit, push, remote CI, release
or stash deletion occurs.
