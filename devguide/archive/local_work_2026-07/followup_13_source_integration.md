# Thirteenth five-source integration follow-up

Reviewed **PDBTM, Interactome3D, BioCyc, OMIM and FDA Orphan** on 2026-10-07
in the existing editable Python 3.14 development environment. Recover PDBTM's
native chain topology with unchanged XML/copyright support. The other four retain
concrete native-access/terms requirements. No stash application/deletion, stage,
commit, push, separate environment/worktree or frozen-schema change.

## PDBTM: unchanged original record and bounded topology scope

The public native [1c3w XML](https://pdbtm.unitmp.org/api/v1/entry/1c3w.xml)
responds **HTTP 200**, **6866 bytes**, SHA-256
`37ae24e30f12457eb91fb9198c5a7a6643e46e33efa0c039048784ff5b7ac55e`.
It matches the unchanged earlier `/tmp/sabueso-batch3-pdbtm-entry.txt` byte for
byte. No new data content or restored-access claim is needed: the improvement is
qualifying a conservative reader of the original XML, retaining conditional
terms and leaving unqualified transforms/projection out of structured knowledge.
The web reader cannot acquire the site/native XML, but verified curl and the
deployed reader receive the original public response without TLS bypass.

The current public [manual](https://pdbtm.unitmp.org/documents) is **16953 bytes**
at `/tmp/sabueso-followup13-pdbtm-documents.html`. It displays database label
`20250404` and server label `v.1.1.2`; describes TMDET plus manual validation,
rotation columns and translation in the fourth matrix column; and distinguishes
membrane normal/origin from original coordinates. Those site labels and historical
entry dates are not current individual PDB/sequence revisions. Units and axes of
all matrix/normal components remain separately unqualified. Raw scores do not
supply probabilities, function or MOLI Evidence. No coordinate or calculation
job is requested, and no transformation is performed.

### Conditional terms and document identity

The original embedded COPYRIGHT identifies PDBTM and the Institute of Enzymology,
Budapest. Nonprofit-institution use is conditional on unchanged content and
retained copyright; use by and for commercial entities needs an agreement.
The entire original XML and statement remain unchanged in the local unreleased
fixture, acquisition/archive response and every mapped chain occurrence.
This does not assign MIT to source data, classify a general noncommercial/open
grant or qualify redistribution. `PDBTM-CONDITIONAL` records the declaration with
unknown automated use verdicts, internal retention and unknown sharing. Public
derivative collections, commercial agreements and contributing-resource rights
retain independent requirements. A missing/changed copyright statement fails
explicitly rather than silently using the old terms.

XML character/attribute decoding is a reading of source declarations, distinct
from original bytes: ISO-8859-1/UTF-8 declarations reproduce native documents,
including non-ASCII characters. Parsed XML character data can resolve character
references/line endings; it is not advertised as a byte-identical extracted
substring. The complete original document/hash supports every decoded value.
DTD/entity declarations are unsupported and no external XML resource is resolved.
Tests construct synthetic format cases independently of the unchanged fixture.

## Recovered reader and scientific support

The preserved `protein_structural_context.py::map_pdbtm` accepted synthetic JSON,
attached a caller protein accession, supplied fallback IDs and assigned a universal
database-inference class. No native PDBTM fetcher was present. Its useful topology/
chain/segment requirement is recovered without restoring those projections.

`sabueso.tools.db.pdbtm.get_topology(identifier, client=None)` accepts one exact
lowercase four-character PDB value after ordinary public argument digestion.
Backend scope also applies with digestion skipped. Online access uses one existing
native XML GET through shared transport; fixture and source/kind/query-bound XML/
gzip/hash/time clients preserve original text, declared encoding and receipt.
Caller metadata remains a declaration rather than independent identity/version/
permission proof. Wrong native namespace/ID, unsupported shapes, changed copyright,
late malformed chains/regions, unsafe queries and wrong source/kind/version/cuts/
hashes fail before mapping. Empty/unavailable/failed/unsupported responses do not
become negative membrane knowledge. No source-wide coverage claim is made.

`sabueso.mappings.pdbtm.map_topology` retains **three** native chain occurrences
and **45** regions in `annotations.transmembrane_topology` on
`pdbtm:structure:1c3w`. Independent assertion IDs bind native document hash and
chain occurrence. All chains A/B/C retain their original source attributes,
XML-decoded sequence text and 15 region attribute sets, including native TMP,
type/TM-count strings and sequence/PDB endpoints. Every value links to complete
unchanged XML/copyright and query/hash/occurrence support.

The source sequence has 222 characters; region 10 declares sequence 130–152 and
PDB 134–156, while region 11 declares sequence 153–161 and PDB 162–170. The
offset changes nonuniformly. Endpoints do not establish exact per-residue
correspondence or a current protein/isoform axis. Biological matrices explicitly
generate B/C from A; identical sequences or generated labels do not merge entities.
Duplicates/conflicts, zero counts, future type codes and negative/inserted PDB
endpoint strings survive without repair or inferred orientation/function.

History, raw result scores and biological/membrane transforms remain in the
original XML; no guessed quantity nodes, translation units, topology computation
or transform execution are introduced. These assertions are standalone: no new
card enricher, frozen schema 0.3.12 field or automatic intake is claimed.

## Live receipt and validation

At **2026-10-07T20:09:18+00:00**, the deployed editable module, called outside
the checkout, receives the original 6866-byte XML in **one GET**, matches the
fixture, validates all chains/regions and maps all three occurrences. Replay
retains record/time/hash/assertions and makes **zero network attempts**.
Receipt: `/tmp/sabueso-followup13-live-receipt.json`; archive:
`/tmp/sabueso-followup13-live.sqlite`; ignored preview:
`recovered_work/current_preview/1c3w.pdbtm_topology.json`.
The fixture's first exact probe time remains `None`, independently of this live
timestamp. Editable metadata/import path identify this checkout.

Focused PDBTM/registry qualification passes **100 tests in 3.30 seconds**, including
**83** new PDBTM cases, through pytest-receptor with **12 workers**. The full
offline checkpoint passes **4751 tests in 157.62 seconds**, with ten existing
failed/cut enrichment warnings and no failed tests. Ruff lint/format (887 files),
source registry/packaged metadata, recorded card shape, schema alignment and
strict Sphinx HTML build also pass. `/tmp/sabueso-followup13-integrity.json`
verifies unchanged original exports/stash/index/frozen-card and PDBTM fixture;
`git diff --check` passes. Exact commands/receipts are in [validation.md](validation.md).

## Four resources with pending native access/terms

| Resource | Current primary review and remaining condition |
| --- | --- |
| Interactome3D | Public download/about pages remain readable and distinguish current/dated releases, metadata/coordinate files and complete/representative sets. Earlier failed native APIs/proteins.dat are not retried without a changed transport/data condition. Require original native records/export and exact data grant, independent protein/pair contracts, occurrence identity, model/template type, ranks and participant-specific bounds. No TLS bypass, coordinate acquisition, modelling or docking. |
| BioCyc | Current SRI Limited Use License and manually reviewed flat-file request page remain readable; BioCyc service/download browser checks fail without native data. Open Databases versus Limited Databases, exact organism/release, session/subscription and distribution-notification obligations remain separate. No form submission, agreement acceptance, authenticated session or provider contact. Require an authorized native artifact and its exact applicable grant before interpreting frame/gene/protein/reaction/pathway relations. |
| OMIM | Current NCBI description still identifies OMIM.org as the provider; it does not supply original entries or their data grant. Previously restricted agreement/API/export routes are not retried. Require current authorized release/terms and native gene/locus, phenotype, variant and narrative scope. OMIM pointers in HPO are neither direct OMIM records nor licences. No keys, registration or replacement-provider data. |
| FDA Orphan | Canonical FDA.gov instructions remain readable, retaining AND filter combinations and designation-date versus approval-date scopes. An initially guessed accessdata instructions path was unsupported by the browser; it provides no native artifact or filter qualification. Indexed search snippets are not raw database records. No native search/export is submitted or direct blocked data acquisition repeated. Preserve the earlier excessive-request block and require authorized unblocked native data plus exact OOPD/input terms, independently of openFDA CC0. No account, sponsor submission, bypass or provider message. |

Primary references: [Interactome3D downloads](https://interactome3d.irbbarcelona.org/download.php),
[provider](https://interactome3d.irbbarcelona.org/about.php),
[BioCyc flat-file terms/request](https://bioinformatics.ai.sri.com/ptools/licensing/all-reg.shtml),
[BioCyc services](https://biocyc.org/web-services.shtml),
[NCBI OMIM description](https://www.ncbi.nlm.nih.gov/omim/), and
[FDA canonical instructions](https://www.fda.gov/industry/designating-orphan-product-drugs-and-biological-products/instructions-searchable-designation-database).
Documentation availability does not qualify native knowledge, current data rights,
complete coverage or an experimental/clinical inference.

## Remaining material and preservation

The historical catalog now has **57 in use, 15 evaluating, 11 deferred, 3 retired,
1 out of scope and 0 not registered** among **87** original declarations, independently
of the maintained registry's total. **18/27** original reviewed candidates have
scoped readers; **9** remain pending: GtoPdb, COSMIC, ELM, BioCyc, OMIM,
Interactome3D, CASTp, ProBiS and FDA Orphan. Broader capabilities of recovered
sources retain their own scope/access/terms requirements. Original stash and all
87 exports remain unchanged; index empty and frozen card/schema intact. Further
blocked data attempts require changed conditions or a qualified supplied artifact.
