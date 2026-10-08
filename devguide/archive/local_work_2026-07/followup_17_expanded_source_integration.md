# Seventeenth recovery follow-up: the expanded 13-resource queue

Reviewed the seven pending original candidates plus iPTMnet, Pharos/TCRD, ASD,
BRENDA, DepMap and TTD on **2026-10-07**. This follow-up recovers **two scoped
native readers**, Pharos exact-target metadata and DepMap public model context.
It does not claim their full historical capabilities are implemented.

## Results for every resource

| Resource | Result | Remaining condition or scope |
| --- | --- | --- |
| Pharos/TCRD | Recovered native exact-accession GraphQL target metadata | Name, symbol, accession, TDL and family only. Novelty, ligand counts and contributing aggregate associations require separate qualification and input-specific terms. |
| DepMap | Recovered complete public 24Q4-v1 Model.csv and exact-model context | Gene effects, dependencies, screen/condition joins and other datasets remain separate. Model metadata are not protein-target or essentiality knowledge. |
| BRENDA | Newly received public SPARQL EC-label probe without account; bounded inhibitor query fails HTTP 500 | SOAP needs an account, bulk download active licence acceptance. SPARQL kinetics, organism/protein scope, representation, units and release require qualification. An account is not a global prerequisite for every route. |
| iPTMnet | Official linked Swagger confirms the preserved substrate route; one native request still returns HTTP 503 | Need successful original proteoform-grouped table rows, exact identities, numbering, sequence/revision and terms. Prior P37840 failure stays historical; not source absence. |
| ASD | Official homepage and linked download/help views reviewed | Free scientific access description and navigation shells do not supply a native export or separate data grant. Article CC BY does not license the database. |
| TTD | Public frontend browser view supplies a loading shell | Original target/product/disease/variant data and applicable data terms remain unqualified. No native export was acquired. |
| GtoPdb | Actual download page redirects to required login | Provider-authorized registered access and native target/ligand/measurement scope. Database/content grants and commercial access conditions stay separate. |
| COSMIC | Current official registration/institutional licence conditions retained | Applicable accepted licence and authorized native module/release/assembly/transcript/sample scope. No-registration modules do not independently grant use or sharing. |
| BioCyc | Current native flat-file request requires agreement/manual processing | Applicable Open/Limited Database rights, native organism/release/frame identities and original acquisition receipt. No form or agreement submitted. |
| OMIM | Current NCBI description directs readers to OMIM.org/API | Authorized original entries/release and applicable terms. Gene/locus/phenotype/variant/narrative scopes stay separate. Restricted routes are not retried. |
| ELM | Download-page acquisition still supplies no native artifact | Native motif classes versus validated instances, source sequence/bounds/publications and applicable grant. No agreement accepted. |
| CASTp/CASTpFold | Current official tutorial and previously preserved result builders reviewed | Existing native result artifact with structure/model/assembly/sequence/parameter and SA/SE support plus applicable grant. Prior failed scientific routes are not repeated. |
| FDA Orphan | Official search instructions preserve AND filters and designation/approval date distinction | Authorized unblocked native designation export and OOPD/input terms. Product identity is separate from protein targets; no openFDA licence substitution or blocked-database retry. |

Primary references: [Pharos provider/API description](https://pmc.ncbi.nlm.nih.gov/articles/PMC9825581/),
[DepMap native public article metadata](https://api.figshare.com/v2/articles/27993248/versions/1),
[DepMap official data structure](https://depmap.org/portal/data_page/),
[BRENDA download conditions](https://brenda-enzymes.org/download.php),
[officially linked BRENDA SPARQL prototype](https://sparql.dsmz.de/brenda),
[iPTMnet official Swagger](https://research.bioinformatics.udel.edu/iptmnet/api/doc/),
[ASD](https://mdl.shsmu.edu.cn/ASD/), [TTD](https://idrblab.org/ttd/),
[GtoPdb download/login](https://www.guidetopharmacology.org/download.jsp),
[COSMIC terms](https://www.cosmickb.org/terms/),
[BioCyc native request](https://bioinformatics.ai.sri.com/ptools/licensing/all-reg.shtml),
[NCBI OMIM description](https://www.ncbi.nlm.nih.gov/omim/),
[ELM downloads](https://elm.eu.org/downloads.html),
[CASTpFold tutorial](https://cfold.bme.uic.edu/castpfold/infos/allabout/tutorial.html), and
[FDA search instructions](https://www.fda.gov/industry/designating-orphan-product-drugs-and-biological-products/instructions-searchable-designation-database).

## Native Pharos slice

The preserved term-search prototype requested ten targets and assigned a generic
inference class. Current access uses the provider-documented GraphQL endpoint's
exact `target(q: {uniprot: $accession})` operation through one GET, selecting
`name sym uniprot tdl fam`. Full raw native JSON survives. P60174 returns
Triosephosphate isomerase / TPI1 / Enzyme / Tbio; P31749 returns AKT1 / Kinase /
Tchem. P00000 returns explicit `target: null`. These are received source literals,
not rankings or inferred protein identity. Frontend documentation access errors
remain distinct from successful public API access.

`get_target`, online/fixture/bound JSON/gzip/hash/time clients and `map_target`
retain native identity, null/blank/future literals, query/response hash and original
time. GraphQL errors, mismatched accession, partial fields and unsupported
revision/cuts fail. Each standalone `annotations.target_development_context`
assertion uses `pharos:target:<native accession>` and full native response support.
Scientific/sequence/TDL-rule revisions stay unknown; no Sabueso rule, aggregate
association, novelty/ligand projection, linked acquisition or automatic card enrichment.

The provider API paper qualifies the endpoint, not a selected-output data grant.
`NOT-STATED` and unknown automated sharing preserve Pharos/TCRD attribution and
independent contributing-source rights. Original factual fixtures remain local
unreleased qualification material; software/article rights are not transferred.
Native P60174 JSON SHA-256:
`e311efdf4da4ce8897b7559b6670cdcf529fa7feb7397e94b163aa27895bb6ed`.

## Native DepMap slice

The preserved generic mapper attached synthetic dependency rows to a caller's
protein accession. That is not a native model/gene/condition contract. The current
slice independently qualifies the provider publication **DepMap 24Q4 Public**,
article **27993248 version 1**, DOI **10.25452/figshare.plus.27993248.v1**.
Its original metadata declares **CC BY 4.0** and identifies Model.csv as file
**51065297**, with MD5 **675210d17675f3517b0ce39a3c274f16**. The full received file
matches that digest: **645696 bytes**, **2105 rows**, **47 columns**, SHA-256
`b7a0c1385e6cef30132b56aff61f1261d11e3f490490b355c430d32ee0dbdcfa`.
The original metadata and 43103-byte README remain unchanged fixtures too.

The portal download catalog currently presents a human-verification page. It is
not bypassed or scraped; independent public provider publication access is separately
qualified. No account, verification submission or agreement acceptance occurs.

`get_model(identifier, release="24Q4")` validates all native CSV rows before exact
ACH ModelID selection. Online bytes are pinned to the qualified original release
SHA-256. Native blank cells, quotes/multiline fields, repeated/conflicting
occurrences and full-file/row support survive; names, RRID and catalog references
do not merge entities. ACH-000019 is the source's MCF7 model. `map_model` retains
sixteen descriptive fields on `depmap:model:<ModelID>`; unqualified age/media
quantities stay raw support, not asserted measurements. Public article version
and release scope stay separate from unstated individual model/ontology revisions.

Gene-effect matrices, dependency classifications, screen/condition mappings,
patient interpretation and protein projection require independent scientific
contracts. No gene essentiality or automatic card enrichment is claimed. CC BY
4.0 attribution names DepMap/Broad, release DOI, portal and program; this selected
article's grant is not propagated to collaborator datasets or other releases.

## BRENDA and iPTMnet acquisition facts

The official BRENDA download page links the public DSMZ SPARQL prototype UI,
which declares backend `https://sparql.dsmz.de/api/brenda` and D3O query examples.
One bounded EC 5.3.1.1 query receives 192 bytes of native SPARQL results JSON:
EC URI `https://purl.dsmz.de/brenda/ec/5.3.1.1`, label
`triose-phosphate isomerase`. An example-based inhibitor query with explicit EC
and LIMIT 20 returns HTTP 500. No successful inhibitor response, complete kinetics,
protein/organism identity, units or dataset revision is qualified; no brute-force
query variations or bulk request follows. Probes do not become scientific fixtures
or an adopted reader. SOAP-account and bulk-acceptance requirements remain scoped
rather than a false blanket account condition.

The original linked iPTMnet Swagger UI receives 3504 bytes and points to
`iptmnet_spec.json`. The original 45064-byte specification states base
`/iptmnet/api` and `/v1/{id}/substrate`, returning proteoform-grouped `form/table`
objects. One confirmed P60174 native request returns HTTP 503. Failed native
acquisition stays separate from missing substrate sites; example rows do not
establish source fidelity. The original guessed curated/inferred classes and
canonical placement are not restored.

## Qualification and inventory

Focused Pharos/DepMap/registry qualification initially passes **116 tests in
4.10 seconds** with **12 pytest-receptor workers**. Native live access outside the
checkout on **2026-10-07T21:28:57+00:00** verifies the existing editable Python
3.14.7 development environment: one GET per reader matches the original fixture,
then archive replay makes zero network attempts and keeps identical assertions,
source hashes and original times. Receipt: `/tmp/sabueso-followup17-live-receipt.json`.

The first full suite finds a fixture-notice inventory omission: the new JSON
paths were described outside the checked Contents table. The exact paths are now
in that table. The corrected source/fixture/registry gate passes **120 tests in 4.16 seconds**.
Full offline checkpoint: **5005 passed in 114.71 seconds** with 12
pytest-receptor workers; 10 expected failure/cut fixture warnings. Ruff, registry,
strict Sphinx, card shape/schema, dependency preflight and original-file integrity
gates pass.
Strict HTML output: `/tmp/sabueso-followup17-docs-build`. Final gate receipts:
`/tmp/sabueso-followup17-gates.json`; no failed gate is treated as passing.

Historical catalog counts are **61 in use, 11 evaluating, 11 deferred, 3 retired,
1 out of scope, 0 unregistered** among 87 declarations. The original 27-candidate
list remains **20 scoped readers / 7 pending / 0 unreviewed**. The expanded
13-resource queue has **2 scoped readers / 11 pending / 0 unreviewed**. Broader
capabilities of partially recovered sources are separate from these counts.

All 87 exported original file lengths/hashes, all 91 accounted paths, original
stash SHA `db04d97fef5a318c6d09f8312971558eafd9d14c`, empty Git index and frozen
published-card bytes remain intact. Integrity receipt:
`/tmp/sabueso-followup17-integrity.json`. No stash application/deletion, stage,
commit, push, environment/worktree creation, account action, protected schema/card
change or cross-component API change occurs.
