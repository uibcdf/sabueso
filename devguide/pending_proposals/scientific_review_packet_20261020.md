---
summary: Prepare a bounded scientist review of the public dossier and first primary assay protocol.
issue: uibcdf/sabueso#132
status: active
opened: 2026-10-20
verification: local_runtime_tested
area: [scientific-inspection, literature, delivery]
related: [uibcdf/sabueso#92, uibcdf/sabueso#108, uibcdf/sabueso#112]
---

# Public scientific review packet, 2026-10-20

Prepared by Codex (agent) from unchanged public fixtures and existing SDK examples.
Scientist review is **pending**. This packet prepares decisions; it accepts no
curation, experimental comparability, project model selection or Evidence.
The [preparation receipt](scientific_review_preparation_20261020.json) identifies
the exact source, editable providers, original bundle files and local checks.
Earlier source/release receipts remain unchanged. This local run does not qualify
a staged artifact, hosted matrix, current provider health or private consumer use.

## Reproduce and inspect

Use the editable Python 3.14 environment specified in [TESTS](../TESTS.md).
Choose fresh output directories; the examples refuse overwriting original stages.
Run these commands separately from the repository root:

```bash
python examples/user_journeys/scientific_dossier.py produce --output /tmp/sabueso-review-dossier --fixtures temp_data
python examples/user_journeys/scientific_dossier.py read --output /tmp/sabueso-review-dossier --fixtures /tmp/no-review-fixtures
python examples/user_journeys/scientific_dossier.py reacquire --output /tmp/sabueso-review-dossier --fixtures temp_data
python examples/user_journeys/scientific_dossier.py read --output /tmp/sabueso-review-dossier --fixtures /tmp/no-review-fixtures
python examples/user_journeys/literature_source_review.py produce --output /tmp/sabueso-review-located --fixtures temp_data
python examples/user_journeys/literature_source_review.py read --output /tmp/sabueso-review-located --fixtures /tmp/no-review-fixtures
```

Open `original.dossier.md`, its original JSON and the located bundle's `review.md`
and `proposals.json`. Keep the stores, manifests and original runtime sidecars
beside them. Independent readers verify the original support; fixture reacquisition
is a later read of frozen answers, not a current public download. Regeneration
creates new execution identities; hashes in the receipt identify this run only.

The producer source is `391ba08fb8b3dacfbc85743505536397e2da9a11`.
Runtime/distribution metadata and outside-checkout editable imports were checked
for all seven participating runtime/test components. The providers have advanced
since the 2026-10-14 checkpoint; this is new bounded receiving evidence, not reuse
of that environment's earlier qualification.

## Original saved scope

| Role | Structure rows: meets / does not meet / insufficient | Assay rows: meets / does not meet | Received assay records |
| --- | --- | --- | --- |
| TcTIM, P52270 | 2 / 2 / 3, total 7 | 20 / 22, total 42 | 25 ChEMBL, 17 BindingDB |
| HsTIM, P60174 | 1 / 7 / 21, total 29 | 14 / 34, total 48 | 25 ChEMBL, 23 BindingDB |

These are report rows under illustrative criteria, not independent experiments,
recommended models or a complete potency survey. ChEMBL is capped at 25 of 493
and 25 of 36 fixture records respectively. UniProt-only structure references are
included in the inventory; their missing RCSB detail is not an adverse finding.
Original pins are:

- TcTIM: `sabueso:protein:uniprot:P52270@sha256:bf528e61e315816c773ff18602b9b87c54e062d50e1dbf8c039732aac95ab77b`.
- HsTIM: `sabueso:protein:uniprot:P60174@sha256:20292b614cac0a09aa14ffa633686b96e05f8b55dd873dd46f1a1e1488485677`.

## Scientist worksheet

For each row record reviewer, date, intended use, outcome, source location or
pinned support, and any required correction. Outcomes may be supported,
conflicting, unknown, unavailable or not queried; usefulness is a separate human
decision. An unresolved source-access gap is an acceptable recorded outcome.

| Review item | Inspectable preparation | Human decision still needed |
| --- | --- | --- |
| Entity applicability | Original P52270/P60174 identity, organism and alternatives | Do the stated entries/taxa answer the intended question? Record construct/strain scope separately. |
| Positive structure examples | TcTIM 1SUX and HsTIM 1HTI meet the recorded criteria | Are those illustrative resolution, coverage, assembly and active-site criteria suitable for the intended use? |
| Assembly disagreement | TcTIM 2V5B has author monomer and an explicit assembly disagreement | Interpret the separate source assembly statements; the inventory does not select a project model. |
| Mutant and fragment | HsTIM 2VOM is a recorded mutant; 1KLG has coverage 0.06 and complex context | Check construct relevance and numbering. Equal residue positions across proteins are not a correspondence. |
| Eligible assay rows | Direct-target IC50 equality and normalized concentration are recorded | Inspect actual protocols before judging comparability. Eligibility alone does not establish it. |
| Missing assay context | Original saved qualifiers and their named missing fields remain available | Decide which missing construct, variant, conditions or controls prevent interpretation. Missing variant annotation is not wild type. |
| Located occurrence | HsTIM P60174 occurs in the requested Europe PMC figure annotation | Accept only an accession mention from this record; no mechanistic finding follows. No subject match in its requested response is not article-wide absence. |
| Two structural readings | The located example retains source XML, locators, exact identity basis and drafts outside the baseline card | Review each proposed reading and its organism/subject scope. Agent preparation does not establish human curation. |
| Original reuse | Both readers pass without a fixture directory; original dossier support survives fixture reacquisition | Decide whether the saved presentation is useful and sufficiently inspectable. Original execution credit remains separate from scientific support. |

Suggested first decisions are entity applicability, the positive/negative structure
examples, and the nine activity records below. Record actual reviewer responses
separately; a blank worksheet is never a scientist-acceptance receipt.

## First primary-protocol case

Start with `CHEMBL1156043`, PMID 19733070, DOI
`10.1016/j.bmcl.2009.08.055`. All nine rows for this document are present in the
capped dossier: five TcTIM records and four HsTIM records, across three source
assays. This is a bounded source-selection reason, not proof of protocol equality
or priority of the compounds. The complete three-document fixture inventory
remains separate: 497 records and twelve assays in the
[original access review](primary_assay_methods_review.md).

| Role / assay | Native activity IDs | Original recorded measurement | Review significance |
| --- | --- | --- | --- |
| TcTIM / CHEMBL1049665 | 3011871, 3011872, 3011873 | IC50 = 6500, 8000, 14000 nM, respectively | Eligible under the illustrative rule; actual conditions remain unknown. |
| TcTIM / CHEMBL1049665 | 3011874 | IC50 > 1000000 nM | A bound, not an exact value; excluded by the equality criterion. |
| TcTIM / CHEMBL1049667 | 3011879 | Kd = 10400 nM | Separate measurement type. Whether experimentally measured, fitted or computed needs the actual method. |
| HsTIM / CHEMBL1049666 | 3011875, 3011876, 3011877, 3011878 | Each IC50 > 1000000 nM | Censored source records; no selectivity ratio is accepted. |

The JSON receipt retains each relationship and supporting SourceAssertion pin.
Native ChEMBL records are the basis of this table, not an acquired primary text.
No protocol is inferred from an assay description, the binding category or the
structural article's methods.

The bounded public search on 2026-10-20 supplied no verified authorized primary
body for the three articles. The author-institution route returned a browser
cache-miss failure, the publisher preview returned HTTP 403, and the
[RIQUIM record](https://riquim.fq.edu.uy/items/show/2008) supplies metadata and a
file link whose earlier inspected delivery was a library notice. No new PDF was
downloaded or qualified here. Indexed third-party text is not admitted as the
missing original. These browser outcomes are not SDK acquisition observations.
An authorized local original or institutional route has been requested from the
maintainer; actual Methods inspection remains pending.

For the first delivered original, record the following before accepting a protocol:

| Field | Current state | Required source binding |
| --- | --- | --- |
| Article body and supplement | Not obtained | Verify title/DOI/body, original bytes/hash, access origin and article-specific rights. |
| Enzyme/construct/organism | Not verified from primary method | Locate preparation, mutations/tags and source assay association. |
| Inactivation versus activity readout | Not verified | Separate preincubation and measurement stages, times and temperatures. |
| Buffer/substrates/concentrations | Not verified | Record original quantities and conditions at a precise source location. |
| Readout and controls | Not verified | Identify coupling enzymes, interference/solvent controls and their stated scope. |
| Compound/table/assay correspondence | Not verified | Preserve explicit source labels and supporting links; do not join by similar names. |
| Kd basis and censored values | Not verified | Distinguish measured, fitted or computed values and preserve inequality qualifiers. |
| Review and intake | Pending | Human curation identifies its reviewer; an executed extraction records its tool/version. Agent drafts remain separate. |

## Bounded completion and following work

The preparation closes reproducible reviewer material and first-case selection.
Human decisions, primary protocols and experimental comparability remain open
under #132/#92. No new SDK surface, source, schema or scientific assertion is
introduced. The subsequent [clinical/reference journey](clinical_reference_journey.md)
now has separate bounded technical acceptance. Continue workload measures through
their own scope. Release preparation proceeds
with explicit limits in the [0.15.0 scope](release_consolidation_0150.md); it does
not wait for every research/access question to close.
