# Tenth five-source integration follow-up

Reviewed **MEROPS, PDBTM, HPO, ELM and GtoPdb** on 2026-10-07 in the existing
editable Python 3.14 development environment. MEROPS now supplies native accession
classification occurrences with every original row retained and unresolved
representations explicit. Cleavage/sequence capabilities and public data
distribution remain separate qualification work. The other four retain concrete
scope/access/terms requirements. No stash application/deletion, stage, commit,
push, separate environment/worktree or frozen-schema edit.

## MEROPS: original rows, source classifications and unresolved coverage

The preserved `protein_expansion.py::map_merops` guessed cleavage rows, supplied
the caller's substrate identity, generated fallback IDs and assigned a universal
curated class. Its useful source/support requirements are recovered through the
provider's native accession export, without representing classifications as
cleavage observations or restoring unsupported substrate/physiological claims.

The unchanged [dnld_list export](https://ftp.ebi.ac.uk/pub/databases/merops/current_release/dnld_list.txt)
is **2914699 bytes**, SHA-256
`9758b658cd7d5f043311d5babf439590baf88b97623ad2a5d42e7e6827abc711`.
It retains **116744** headerless CRLF lines: **116741** three-column rows and
**three** four-column rows. Native `Trembl`, `swissprot` and `PIR` prefixes,
family/subfamily text, taxonomy strings, blank/space values and repeated/conflicting
occurrences remain source literals. The older description's exclamation-mark
format is not substituted for the actual response.

### Explicit representation qualification

Three four-column rows at lines **67322**, **67435** and **83822** retain their
complete original field arrays:

- `swissprot:` / `Q80ZF` / `P2A` / `10090`;
- `swissprot:` / `Q6UWY` / `S1A` / `9606`;
- `swissprot:` / `Q32Q9` / `S9` / `10090`.

These are unassigned representations. No joining, shifting, incomplete accession
completion, taxonomy reassignment or row omission occurs. Basic shape checks
admit the observed representations without claiming biological column meanings.

Full native validation finds a fourth issue missed by the earlier format/count
review: three-column line **108853** has accession literal **`swissprot:"Q96CC`**,
family **`S54`** and taxonomy **`9606`**. The leading quote is retained; the value
is not repaired into another accession or recognized as a current UniProt protein.
An exact query for that entire literal can retain its original three-column
classification. A query for `swissprot:Q96CC` does not match it.

`merops_accession_rows@1` reports these four representation issues in the envelope,
acquisition summary and assertion support. The rule qualifies representation;
it does not create biological SourceAssertions. `selection_complete=False`
prevents unresolved interpretation from passing as complete selection, including
when there is no literal match. Such an export remains a received acquisition,
not a complete not-found result. A separately qualified clean table can report
not-listed while retaining the distinction from biological absence/access failure.
`truncated=False` concerns retained received lines, without a native total or
current-database completeness guarantee.

### Reader, mapping and scientific boundary

`sabueso.tools.db.merops.get_assignments(identifier, client=None)` performs one
full native export GET. Online, fixture and exact source/kind/query/export-bound
TSV/gzip clients retain original bytes/text, raw/decoded hash, original time and
archive observation. Metadata requires source MEROPS, kind accession_assignments,
the exact case-sensitive source-prefixed literal and unknown revision. Unsafe
queries, malformed late rows, unavailable files, error bodies, unsupported revisions
and changed scope fail before selected assertions are returned. All rows are
checked before selection; generic TSV header inference is not used.

`sabueso.mappings.merops.map_assignments` emits every selected three-column
occurrence independently in `annotations.peptidase_inhibitor_classifications` on
`merops:accession:<literal>`. Values contain only native accession/family/taxonomy
literals. Original row/line, full-export hash, all four issues, selection coverage
and query scope stay in metadata; duplicates/conflicts keep independent IDs.
The eight blank taxonomy strings and 147 leading-space strings are not normalized.
Original prefixes/quoted/versioned strings do not establish modern namespace
equivalence, organism identity or protein/isoform identity.

For `swissprot:P29466`, native line **9307** supplies **C14A / 9606** as one
classification occurrence. It does not assert enzyme activity, inhibitor role,
substrate, mechanism, physiological relevance, a cleavage coordinate, sequence,
experimental method or MOLI Evidence. No protein transfer, linked family/sequence/
publication request, search/BLAST, SQL import, computation or automatic card intake.
This standalone field is outside published card schema 0.3.12. Native export,
classification, sequence and taxonomy revisions remain unknown; `current_release`,
file listings and website/download-list versions are not substituted.

## MEROPS licence qualification for local work

The [database-specific provider statement](https://www.ebi.ac.uk/merops/about/availability.shtml)
declares the complete database content the Library under GNU Library GPL, without
a precise version. The public FTP index has no separate licence attachment.
Its generic GNU link currently resolves to LGPL 3, which incorporates GPL 3;
that is not a provider-selected database version or a licence for arbitrary inputs.

The actual [historical Library GPL](https://www.gnu.org/licenses/old-licenses/lgpl-2.0.txt)
section 0 distinguishes running a tool from copying/distributing/modifying library
content; section 13 addresses unspecified versions. The linked
[GNU LGPL 3](https://www.gnu.org/licenses/lgpl-3.0.txt) and incorporated
[GNU GPL 3](https://www.gnu.org/licenses/gpl-3.0.txt), section 2, distinguish
unshared work from conveying it. These qualify this local unshared reading and
unchanged-data qualification. Public fixture/derived-dataset/package distribution
obligations remain separately unqualified; no licence version is selected on
behalf of MEROPS or contributing providers.

The normalized declaration **GNU-LIBRARY-GPL-UNVERSIONED** preserves the licence
that is stated, without mislabelling it MIT, CC0, no terms or per-record depositor
terms. Its classification is explicitly unknown: all automated use verdicts remain
**unknown / licence_not_classified**; archive retention is **internal** and sharing
**unknown**. Existing licence verdicts/rule semantics are unchanged; the new source
declaration is classified conservatively. Source and input/publication/software
rights remain separate. Credit MEROPS and EMBL-EBI, preserving full native support.
Resource bibliography is the official dataset URL, separate from row support.

The original export, provider statement and unchanged GNU support documents remain
local unreleased qualification artifacts, declared with source/date/hash in
`temp_data/NOTICE.md`. Their verbatim-document-copy permissions do not establish
blanket MEROPS redistribution permission. No data or derived collection is published.

## Live receipt

A live call from `/tmp` using this checkout's verified editable Python at
**2026-10-07T09:45:04+00:00** receives all **116744** rows in **one GET** and
matches every original fixture byte. The full native export identity remains
`sha256:9758b658cd7d5f043311d5babf439590baf88b97623ad2a5d42e7e6827abc711`.
All four representation issues and the `P29466` classification survive. Replay
preserves original record/time/hash/assertions with **zero network attempts**.
Receipt: `/tmp/sabueso-followup10-live-receipt.json`; ignored preview:
`recovered_work/current_preview/P29466.merops_assignments.json`.
The original 2026-10-06 probe's exact time remains unknown (`None`).

## Other four resources

| Candidate | Reviewed material and remaining condition |
| --- | --- |
| PDBTM | Original 1c3w XML and provider documents remain available as historical native support. Nonprofit/unchanged-content/copyright and commercial-agreement conditions require exact use/representation qualification. Membrane/assembly transforms and their physical units remain separate. Native sequence versus PDB bounds are not a constant offset: early region endpoints include seq 1/PDB 5, while a later region begins seq 153/PDB 162. Generated chains, matrices and native topology stay independent; no transform execution, coordinate acquisition, prediction or canonical projection. |
| HPO | Current repository LICENSE still consists of a link to the JAX licence route previously returning 404. Current format documentation distinguishes gene/disease/contributor scope, fractions, frequency terms and missing values. Primary QC documentation points to an annotation-data repository that returns 404 in this browser check; no licensed native release is received. Software MIT, older HPO attribution/version terms and ontology-wide licences do not establish current annotation/input rights. No ancestor expansion, gene penetrance, clinical interpretation or protein transfer. |
| ELM | The exact linked public academic agreement and download page still fail browser acquisition with timeout. No agreement bytes, acceptance or native export is obtained. Qualify the applicable original class/instance artifact, investigated sequence/revision, status/bounds/publication support and data terms. Class regexes, described instances and pattern-match predictions remain distinct. No motif search or canonical coordinate assignment. |
| GtoPdb | Current official about page explicitly requires registration for website use; previous key/download-account requirements remain. No authenticated data, credentials or account action. Qualify authorized native records and exact target/subunit/ligand identity and activity/affinity units. Database ODbL and content CC BY-SA terms remain separate, without restoring historical first-target selection or suppressing per-endpoint failures. |

Primary references: [PDBTM native 1c3w](https://pdbtm.unitmp.org/api/v1/entry/1c3w.xml),
[PDBTM documents](https://pdbtm.unitmp.org/documents),
[current HPO LICENSE](https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/LICENSE.md),
[HPO annotation format](https://obophenotype.github.io/human-phenotype-ontology/annotations/genes_to_phenotype/),
[HPO QC source documentation](https://github.com/monarch-initiative/hpoannotqc),
[ELM downloads](https://elm.eu.org/downloads.html),
[ELM agreement](https://elm.eu.org/media/Elm_academic_license.pdf), and
[GtoPdb about](https://www.guidetopharmacology.org/about.jsp).
No restricted-data retry/bypass, account, provider contact or analysis job occurs.
These access failures do not establish biological absence or resource retirement.

## Qualification and remaining material

Focused MEROPS/terms/registry selectors pass **111 tests in 6.21 seconds**, through
pytest-receptor with **12 workers**, including **74** MEROPS cases. Initial native
validation caught the quoted accession; it is now retained with explicit support.
Initial custom-client trace expectations and resource bibliography wiring were
corrected before the passing source checkpoint. The full offline checkpoint passes
**4519 tests in 165.72 seconds**, with 12 workers and ten existing exercised
failure/cut warnings. Ruff check/format (875 files), registry/generated metadata,
frozen shape/schema, strict Sphinx and final diff/integrity checks pass. Full-suite
and final selected gate receipts are recorded in [validation.md](validation.md).

Historical catalog now has **54 in use, 18 evaluating, 11 deferred, 3 retired,
1 out of scope, 0 not registered**. Fifteen of the original 27 reviewed candidates
have scoped native readers; **12** await integration: GtoPdb, COSMIC, HPO, ELM,
BioCyc, OMIM, Interactome3D, PDBTM, 3did, CASTp, ProBiS and FDA Orphan.
Scoped readers do not imply full original capabilities, automatic card enrichment
or public data distribution qualification. The original stash and all 87 exported
original files remain intact.
