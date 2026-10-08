# Follow-up 19: native TTD target listings and iPTMnet substrate reports

Recovered 2026-10-07 on the current development contracts. This supersedes
follow-up 18's current TTD/iPTMnet integration status; its original native receipts
and access-failure history remain unchanged. Two of ten pending resources gain
scoped readers. Eight need new authorized access or original scientific artifacts.
The original stash, 87 exported originals and published card stay intact.

## TTD native key and release qualification

The original public export acquired through the provider's explicit redirect and
[download component](https://ttd.idrblab.cn/full-data-download) is unchanged:
525950 bytes, 4298 four-field blocks, 613 NOUNIPROTAC values, SHA-256
`74b2dbb4c03e14b01d02b54bdce45507da0da1e457859e1669cdf76b39feb22e`.
Native header version **10.1.01 (2024.01.10)** is independent of the site's
2026 resource citation and unknown individual target/UniProt revisions.

`get_target_listing`, online/fixture/bound native text/gzip/hash/time clients and
`map_target_listing` validate the original title/date/header and every block
before exact `T` plus five-digit selection. Independent standalone
`annotations.therapeutic_target_listing` assertions use `ttd:target:<native ID>`,
raw block/line/header/release/query/full-export hash support. UNIPROID includes
entry names and NOUNIPROTAC, not uniformly accession IDs. Native source type,
blank values, repeated/conflicting occurrences and the T59130 bacterial-name/
TPIS_PLAFA inconsistency survive. No accession inference, protein/gene/complex
merge, clinical conclusion, derived druggability or automatic card intake.
Drug/disease/activity/variant joins remain separate unqueried scientific contracts.

Follow-up 18 had not yet admitted a reader while reuse rights remained unstated.
This slice now qualifies exact native-key parsing and the public original route
under the repository's existing Pharos/ProBiS local qualification practice:
**NOT-STATED**, automated use/sharing unknown, archive retention internal. No
new data grant, article/software substitution, publication or redistribution is
inferred. The original factual fixture is local unreleased qualification material.
Attribution retains TTD, IDRB/Zhejiang University, BIDD/NUS and native header/URL.
This scientific/implementation qualification does not clear sharing permissions.

## iPTMnet native HTML representation

The [provider homepage](https://research.bioinformatics.udel.edu/iptmnet/)
explicitly links its Q15796 sample report. This public representation supplies
native substrate tables independently of the earlier failed REST service. Original
[P60174](https://research.bioinformatics.udel.edu/iptmnet/entry/P60174/) and
[Q15796](https://research.bioinformatics.udel.edu/iptmnet/entry/Q15796/) HTML pages
are preserved unchanged in NOTICE's Contents table:

- P60174: **95748 bytes**, SHA-256
  `13c3f90770bff2cbc34463508d453758fe518ebf9069491d229a7a623d6a9f90`;
  **72 rows** across native P60174 / P60174-1 / P60174-3 groups (**62 / 7 / 3**).
- Q15796: **166093 bytes**, SHA-256
  `82833fa0fa7a1a6da2a9a7821c79eb8592211b7b86056cc53ad5584f1c681300`;
  **60 rows** across Q15796 / Q15796-1 / Q15796-2 (**42 / 15 / 3**).

`get_substrate_report`, online/fixture/bound HTML/gzip/hash/time clients and
`map_substrate_report` check native accession/link identity, matching tabs/tables,
headers and every selected-section row before producing standalone
`annotations.ptm_report_rows` on `iptmnet:report_group:<native tab>` subjects.
Raw identity/row HTML, all original cell text/link attributes, query and full
response hash support each occurrence. Hidden publication links are included;
Q15796 S2 acetylation retains all four original PMIDs, including its hidden fourth.
Native blank sites, score0, source score labels/stars, future labels and repeated/
conflicting rows survive. No independent enzyme/source/PMID pairing is invented.

A source group tab does not establish canonical or isoform sequence equivalence.
Native site strings are retained without residue projection or reconstruction.
Dataset/record/sequence/scoring-rule revisions remain unknown. Provider confidence
is not recomputed or assigned as a Sabueso versioned finding, and no curated/inferred
or experimental confirmation class is invented. Other report sections/expanded
view remain unmapped/unqueried. No script execution, linked source/publication
acquisition or automatic card enrichment. REST HTTP 503 stays a historical failed
acquisition, not recovered REST access or absent modifications.

The [official data licence](https://research.bioinformatics.udel.edu/iptmnet/license)
independently states **CC BY-NC-SA 4.0** for the database, separate from software/
article rights. Attribution, noncommercial, share-alike and original contributing
source/publication context remain in terms and archive retention. Commercial-product
verdict is restricted; independent input rights remain separate.

The native report contains a per-request form nonce outside mapped scientific
panels. A real new page has a different full-response hash while all native
identity/substrate rows match. Every original remains unchanged; no nonce removal,
static-byte replacement or scientific revision is inferred. Replay keeps the exact
original response hash/time and assertions from its particular acquisition.

## Eight remaining conditions

| Resource | Requirement before a native reader can be admitted |
| --- | --- |
| ASD | Authorized original input after its licence application/login gate and permitted research-only/no-third-party-distribution scope. Recorded sites versus predicted potential sites, native structure/residue support and mixed artifact releases stay separate. No application or gated archive acquisition. |
| GtoPdb | Registered/licensed native target/ligand/interaction input, native release and assay/quantity scope. Public frontend login requirement is not bypassed. |
| COSMIC | Authorized source variant/sample/cohort data and applicable licence, assembly/protein bounds and coverage. No protected acquisition or unqualified redistribution. |
| ELM | Successful original class/validated-instance export plus source sequence/bounds/publications and applicable grant. Public browser homepage still times out; no API guess or motif-to-site inference. |
| BioCyc | Original organism/release/frame files under applicable Open/Limited Database conditions; flat files need agreement/manual processing. Current source states API use signifies assent too, so it is not used as an agreement bypass. No form or agreement submitted. |
| OMIM | Authorized original entries/API scope and applicable terms, with separate locus/gene/phenotype/variant/narrative support. Current NCBI page refers to provider data; no rights substitution or restricted-route retry. |
| CASTp/CASTpFold | Existing original result with native structure/model/assembly/sequence/parameters, SA/SE area-volume scope and terms. Current tutorial does not supply a scientific result; no upload/job or repeated failed route. |
| FDA Orphan | Authorized unblocked native designation/export and OOPD/input terms; exact filters/status/date scope with product identity separate from protein targets. Current official instructions do not themselves provide data. No blocked-database retry or openFDA grant substitution. |

Primary current references: [BioCyc native request/conditions](https://bioinformatics.ai.sri.com/ptools/licensing/all-reg.shtml),
[NCBI OMIM provider description](https://www.ncbi.nlm.nih.gov/omim/),
[CASTpFold tutorial](https://cfold.bme.uic.edu/castpfold/infos/allabout/tutorial.html),
and [FDA search scope](https://www.fda.gov/industry/designating-orphan-product-drugs-and-biological-products/instructions-searchable-designation-database).
ASD/GtoPdb/COSMIC conditions retain follow-up 18's original receipts; this is not a
claim of new native acquisition from them. Await an actual changed access/data
condition or a qualified authorized supplied artifact; synthetic adapters are not
counted as source recovery.

## Qualification and preservation

Focused source/registry/fixture gates: **110 passed in 5.02 seconds** using
pytest-receptor with **12 workers** in the existing editable Python 3.14.7 environment.
Two initial tests used an uninstrumented custom client to request acquisition
records and the wrong commercial-use selector; corrected before qualification.

Full offline checkpoint: **5159 passed in 151.38 seconds**, pytest-receptor,
**12 workers**, 10 expected failure/cut fixture warnings.

Real qualification outside the checkout at **2026-10-07T22:20:40+00:00** verifies
editable metadata/import origin. Each source makes one observed network attempt
in that successful qualification; archive replay makes zero and keeps exact
original hashes/times/assertions. TTD yields one T59130 listing; iPTMnet yields
72 P60174 rows. Receipt `/tmp/sabueso-followup19-live-receipt.json`.
Earlier qualification-script assertions incorrectly assumed static HTML bytes and
exactly one attempt despite transport retry behavior; their failed runs are not
passing evidence. Source acquisitions retained there remain original receipts.

Final local gates pass: Ruff lint/format (914 files already formatted), source
registry, strict Sphinx, card shape/schema, dependency preflight and Git diff.
Final metadata/reader checks: **63 passed in 3.26 seconds**, pytest-receptor with
12 workers. The iPTMnet caveat is quoted as one YAML flow-list string so commas
cannot split its scientific limits or lose their negation. The live receipt's
retention section is refreshed from that final metadata without another request.
Gate receipt: `/tmp/sabueso-followup19-gates.json`.
Integrity receipt `/tmp/sabueso-followup19-integrity.json` verifies 87 original
hashes/lengths, 91-path accounting, unchanged stash and published card, empty index.
Historical counts: **64 in use / 8 evaluating / 11 deferred / 3 retired /
1 out of scope**. Expanded queue: **5 scoped resources / 8 pending / 0 unreviewed**;
original 27-list remains **20 scoped readers / 7 pending / 0 unreviewed**.
These are scoped capabilities, not full recovery of every old source promise.
No new environment, staging, commit, push, CI request, release or stash deletion.
GH Run Receptor is reserved for actual Actions evidence; no remote checkpoint.
