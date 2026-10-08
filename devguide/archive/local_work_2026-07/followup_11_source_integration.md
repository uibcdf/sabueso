# Eleventh five-source integration follow-up

Reviewed **HPO, COSMIC, BioCyc, OMIM and PDBTM** on 2026-10-07 in the existing
editable Python 3.14 development environment. HPO now supplies independent native
gene/disease phenotype occurrences from an unchanged dated public export. The
other four retain specific native/access/use requirements. No stash application,
stage, commit, push, separate environment/worktree or frozen-schema edit.

## HPO: official data terms located and public artifact qualified

The old JAX licence route and private annotation source repository were unhelpful
access paths; neither established an absence of data terms. The current public
[JAX website source](https://github.com/TheJacksonLaboratory/hpo-web/blob/a85f0fa92835a9f6a37881b89b6260ca3b9f4960/src/app/static/resources/license/license.component.html)
contains the actual data-licence component. The deployed website declares a static
module whose licence wording agrees with it. This is an independently checked
provider data statement, separate from web/QC software licensing.
The deployed module is 44480 bytes, SHA-256
`c2b3f2ad16f5940085242583b32e9bf90aef5b0682b54875405b1e14da738e21`,
retained outside fixtures at `/tmp/sabueso-followup11-hpo-static-routes.js`.
The public tree is complete and pinned to commit
`a85f0fa92835a9f6a37881b89b6260ca3b9f4960`; its licence component is 1764 bytes,
SHA-256 `cdd288c39f224b07642e59c1b4cd3f81d9f4210cbd4dbf18428dd2749be6c8cd`.

The Consortium permits downloading/using its files with acknowledgment/citation,
public version/date display and unchanged content/logical relationships. It
requests online credit/logo. The reader retains the entire original file and reads
original rows without modifying its content or introducing ontology relations.
OMIM/Orphanet input rights stay separate; summary disease namespaces do not identify
per-occurrence contributors or publications. Local unreleased qualification does
not establish blanket commercial, derivative-collection or redistribution rights.
Normalized `HPO-CONSORTIUM` preserves the custom declaration with unknown automatic
use verdicts and internal retention/unknown sharing. Existing licence behavior
and rule semantics are unchanged. Original artifact and licence support are
explicitly declared in `temp_data/NOTICE.md`.

The official website's public annotation-download component links the OBO PURL;
its documented redirects identify the exact
[`v2026-09-01` asset](https://github.com/obophenotype/human-phenotype-ontology/releases/download/v2026-09-01/genes_to_phenotype.txt).
The public released asset is accessible even though annotation editing sources
are private. No private repository, key or authenticated request is used.
Its complete unchanged body is **20821704 bytes**, SHA-256
`507a17bff9c49e6329fbd88b1f91734fa7e9fdea5c06304044c0892eb6ab248c`,
with **333983** six-column rows after the native header. Native columns are
`ncbi_gene_id`, `gene_symbol`, `hpo_id`, `hpo_name`, `frequency`, `disease_id`.
The artifact route states the release; original rows do not state individual gene,
ontology, annotation or contributor revision. HTTP dates are not substituted for
those revisions or for the unknown exact first probe time.

## Recovered behavior and scientific scope

The original `tools/protein_sources.py::fetch_hpo` used the mutable latest route,
filtered a generic DictReader by stringified ID and discarded the complete export.
`mappings/protein_specialist.py::map_hpo` used caller gene identity and a universal
curated/evidence class. Their useful phenotype/disease/frequency requirements are
recovered on current source contracts, without restoring that class or importing
historical biological projections.

`sabueso.tools.db.hpo.get_gene_annotations(identifier, release="v2026-09-01",
client=None)` accepts one positive literal NCBI Gene ID and an exact dated
`vYYYY-MM-DD` release. It performs one public release-asset GET through shared
transport. Backend validation rejects padding, symbol/prefix queries, malformed
dates, URL syntax, wrong source/kind/query/release and cuts, even when digestion is
skipped. Every received row validates before selection; a malformed unrelated late
row cannot disappear behind an earlier match. Online, fixture and source/kind/
query/release-bound TSV/gzip/hash/time snapshots preserve full original text and
acquisition support. Caller metadata remains a declaration rather than independent
identity or licence proof. Not-listed differs from failed/unavailable/malformed
access; it does not establish biological absence or current-database completeness.

`sabueso.mappings.hpo.map_gene_annotations` keeps each exact native Gene occurrence
in `annotations.gene_phenotype_associations` on `ncbigene:<native ID>`, with all
six unchanged column values. Each has independent release/export-hash/line identity
and full original-row/query/coverage support. Repeated/conflicting rows survive;
symbols and names do not select or merge identity. The unchanged raw record and
standalone assertions remain outside frozen card schema 0.3.12, without automatic
enrichment or changes to ontology relationships.

For **7167 / TPI1**, the native file supplies **44** occurrences. Hypotonia
`HP:0001252` has `1/2` with `OMIM:615512`, independently of `HP:0040281` with
`ORPHA:868`. These are disease-annotation frequency representations, not estimates
of gene penetrance or individual patient outcomes. The entire file retains **175077**
HP-term frequencies, **101995** fractions, **56761** missing `-` strings and **150**
percentage strings, including decimal percentages. They stay opaque and unchanged;
no normalization, conversion to a probability, denominator reconstruction or
strongest-support choice occurs. Future nonempty frequency text stays literal.
No ancestor expansion, clinical inference, protein/isoform merge, original input
or publication acquisition, diagnostic job or MOLI Evidence is added. Six-column
summary support does not supply detailed contributors, studies, qualifiers,
modifiers or per-annotation evidence.

The builtin HPO dataset bibliography credits the resource independently of
per-occurrence scientific support. The registry, packaged metadata, source/API/
user documentation and historical catalog describe this bounded development reader.

## Live receipt and validation

At **2026-10-07T19:31:22+00:00**, one live GET outside the checkout receives the
complete artifact matching every fixture byte and maps all **44** TPI1 occurrences.
Editable metadata and import path identify this checkout. Archive replay preserves
release, original record/time/hash and assertions with **zero network attempts**.
Receipt: `/tmp/sabueso-followup11-live-receipt.json`; archive:
`/tmp/sabueso-followup11-live.sqlite`; ignored preview:
`recovered_work/current_preview/TPI1.hpo_gene_annotations.json`.
Focused HPO/registry qualification passes **94 tests in 17.26 seconds**, including
**77** new HPO cases, through pytest-receptor with **12 workers**. The full offline
checkpoint passes **4596 tests in 181.27 seconds**, with twelve workers and ten
existing exercised-failure/cut warnings. Ruff check/format (879 files), registry/
generated metadata, frozen shape/schema, strict Sphinx and final diff/integrity
checks pass independently. All 87 original exports retain byte/hash identity,
stash remains intact, index empty and frozen card matches HEAD. Exact receipt:
`/tmp/sabueso-followup11-integrity.json`. This local checkpoint does not trigger
Actions, so no gh-run-receptor inspection is needed. General receipts are in
[validation.md](validation.md).

## Other four resources and next qualification conditions

| Resource | Review and concrete remaining condition |
| --- | --- |
| COSMIC | Current provider terms and public Mutational Signatures pages distinguish no-registration access from applicable use/download/sharing rights. The module now reports v3.6 (May 2026); that label is not a received dataset or an authorization for the historical core somatic-variant scope. No signature/native core dataset or account action is acquired. Require authorized exact module/release/assembly/transcript/sample/count/support and applicable use rights. |
| BioCyc | Public BioCyc/EcoCyc download-page browser checks fail without native data. Preserved service/terms documents distinguish exact organism database and native frame relations, Open versus Limited Database rights, session/subscription and provider-notification distribution obligations. No authenticated session, provider contact or broad licence inference. Require a lawfully obtained exact native database/release artifact and its applicable terms. |
| OMIM | The public NCBI resource page identifies the native provider, but does not grant export rights. Direct OMIM agreement/data routes with prior restrictions are not retried. Native MIM gene/locus, phenotype maps, allelic variants and narrative stay distinct. OMIM pointers in HPO summaries do not make them OMIM records or authorize its data. Require current applicable agreement and an authorized native release. |
| PDBTM | Rechecked unchanged original 1c3w XML and conditional nonprofit/unchanged-content/copyright versus commercial-agreement terms. HPO-specific terms do not qualify this other provider's use. Nonuniform source sequence/PDB endpoints, generated chains, biological matrices, membrane transform and unknown physical units/revisions stay independent. Require exact permitted use/representation scope; no transform, coordinate acquisition, prediction, distribution or canonical projection. |

Primary references: [COSMIC terms](https://www.cosmickb.org/terms/),
[public signature module](https://cancer.sanger.ac.uk/signatures/),
[signature downloads](https://cancer.sanger.ac.uk/signatures/downloads/),
[BioCyc download](https://biocyc.org/download.shtml),
[EcoCyc download](https://ecocyc.org/download.shtml),
[OMIM provider description](https://www.ncbi.nlm.nih.gov/omim/),
[PDBTM native XML](https://pdbtm.unitmp.org/api/v1/entry/1c3w.xml), and
[PDBTM documents](https://pdbtm.unitmp.org/documents).
Prior original receipts and terms remain linked by follow-ups 04 and 10; failed
requests do not establish biological absence or retirement. No account, acceptance
on behalf of an institution, credential search, restricted-route bypass, third-party
substitute, stakeholder message or provider analysis job occurs.

## Remaining material and preservation

The historical catalog now has **55 in use, 17 evaluating, 11 deferred, 3 retired,
1 out of scope and 0 not registered** among its **87** declarations. These counts
are not the full maintained registry. **16** of the original **27** reviewed
candidates now have scoped readers; **11** await integration:
GtoPdb, COSMIC, ELM, BioCyc, OMIM, Interactome3D, PDBTM, 3did, CASTp, ProBiS and
FDA Orphan. Broader capabilities of already recovered sources remain separately
scoped. Every remaining candidate needs its specific access/artifact/terms condition,
not another unchanged failed-route attempt. All 87 original exported files and the
original stash remain intact; the index is empty and frozen schema/card unchanged.
