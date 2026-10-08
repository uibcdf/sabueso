# Batch 02: five historical source candidates (2026-10-06)

Review **COSMIC, HPO, ClinGen, OmniPath and ELM** together. The useful requirement
and concrete qualification boundary of each are recorded below. ClinGen's native
gene-validity reader is recovered; the other four remain `evaluating`. A completed
review does not establish a delivered connector, fixture licence or clinical claim.

| Candidate | Outcome | Useful material | Outstanding qualification |
| --- | --- | --- | --- |
| COSMIC | Reviewed; evaluating | Native somatic variants, tumor/sample context and source interpretation | Authorized access/redistribution basis and exact release, assembly, transcript and variant scope |
| HPO | Reviewed; evaluating | Separate gene/disease phenotype declarations and original frequency qualifiers | Exact native release, current annotation/input terms and source-scoped phenotype semantics |
| ClinGen | Scoped reader recovered | Independent gene-disease validity classifications with native inheritance, SOP, panel, report and date | Additional dosage/actionability/variant scopes remain outside this reader |
| OmniPath | Reviewed; evaluating | Directed signaling observations, both effect flags and original resource/reference context | Per-resource rights, query filters and complete native coverage; no precedence between opposite effects |
| ELM | Reviewed; evaluating | Motif class definitions and described motif instances with investigated-sequence context | Exact data agreement and native class/instance export; search predictions and canonical placement stay separate |

Historical counts after this batch: **41 in use, 14 evaluating, 11 deferred,
3 retired, 1 out of scope, 17 not registered**. The 17 are unreviewed candidates.
**Eight** candidates from the first two batches are reviewed and still await
integration; the six earlier evaluating and eleven deferred decisions retain their
own scope. The source status is separate from the count of completed reviews.
The original stash and 87 original file hashes remain intact.

## COSMIC: source-scoped somatic variant requirements

The preserved `protein_expansion.py::map_cosmic` accepted synthetic `variants` or
`results` dictionaries and attached the caller's protein accession. It kept useful
gene/change/genomic/tumor/sample/significance/publication fields, but its fallback
IDs and generic curated class did not qualify native variant identity, assembly,
transcript/protein revision, sample deduplication or source interpretation. No
native COSMIC implementation was found in `protein_sources.py`.

The provider's [current terms](https://www.cosmickb.org/terms/) require account
registration and the applicable academic/commercial rights. Academic data disclosure
for publication is specifically scoped; broader sharing/public-facing redistribution
needs its own permitted basis. No registration, credentials, licensed download,
scraping, public fixture or provider contact was performed for this review.

Preserve the requirement for lawfully obtained native source data with original
release and module, assembly, genomic/transcript/protein identifiers and revisions,
variant/change representation, tumor/site/histology, sample/count definitions,
source significance and references. Variant occurrences and source interpretation
must remain separate. A gene name or caller accession does not establish a protein
or residue axis; sample counts are not population allele frequencies. No clinical
interpretation or variant classifier is recovered from the synthetic mapper.

## HPO: phenotype annotations retain disease/provider/frequency scope

The old `fetch_hpo` downloaded `releases/latest/download/genes_to_phenotype.txt`
and used `ncbi_gene_id` selection. `map_hpo` kept gene symbol, phenotype, frequency
and disease pointers, then applied a universal curated class. The requirement is
useful; mutable latest access, native release/coverage, contributor rights and the
actual meaning of each frequency still need qualification.

The [current annotation documentation](https://obophenotype.github.io/human-phenotype-ontology/annotations/genes_to_phenotype/)
declares six columns and most-specific terms rather than every ancestor. HPO-team
annotations with OMIM disease identifiers and Orphanet annotations with ORPHA IDs
are separate. Frequencies include fractions, HPO frequency terms and missing-value
literals; they qualify the original disease/phenotype context, not a generic gene
penetrance. Preserve every independent occurrence, exact NCBI Gene/disease/HPO
identifiers, original frequency representation and contributor context. Do not
merge disease rows, infer ancestors or attach all annotations to encoded proteins.

The [current repository licence pointer](https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/LICENSE.md)
names `https://hpo.jax.org/app/license`, which returned HTTP 404 both through the
web reader and direct public curl in this review. The older
[project licence page](https://human-phenotype-ontology.github.io/license.html)
has attribution, visible date/version and content/logical-integrity conditions,
not a blanket CC0 grant. Do not silently substitute that historical page for the
exact current release's annotation/input terms. No new HPO fixture is added until
the applicable release/terms and native header/coverage are recorded. An unresolved
licence route does not mean the scientific resource has disappeared.

## ClinGen: recover the native gene-disease validity export

The old `fetch_clingen` skipped arbitrary preamble lines until a header began
with `GENE SYMBOL`, returning empty curations if no such header existed. It renamed
columns and discarded the original document/row support. `map_clingen` retained
useful classifications, inheritance, SOP, panel and date but added synthetic IDs
and a universal curated class. Missing or malformed headers must instead fail
explicitly; standalone assertions retain all original column names and occurrences.

The [official export](https://search.clinicalgenome.org/kb/gene-validity/download)
is native CSV with three information rows, separator, ten-column header and a
second separator. The unmodified **1129673-byte** public fixture has SHA-256
`979e814b2371a13133ab11ef14b613c58f11967928634b2af128df0632865016`, native
file-creation label **2026-10-06** and **3702** curations. The original exact
retrieval time is unrecorded. Validate the complete received export before exact
HGNC selection, including unrelated rows, CSV quoting and original header width.
There is no independently declared database total or dataset/gene/sequence revision.

BRCA1 (`HGNC:1100`) has two received declarations, with distinct MONDO diseases,
AD/AR inheritance, SOP10/SOP7 and dates. Each survives independently on
`clingen:HGNC:1100`; no strongest-class selection, numeric rank or protein/variant
identity is inferred. Native classifications include Definitive, Strong, Moderate,
Limited, Disputed, Refuted and No Known Disease Relationship. Unknown future labels
remain literal. The export includes **65** legacy `CGGCIEX` report references in
addition to `CGGV`; legacy classification dates can lack timezone. No UTC or
sequence revision is filled from those labels.

`tools.db.clingen.get_gene_validity` retains the original document and detached
selection/coverage receipt. `map_gene_validity` keeps independent matched rows,
original indices, full response hash, file label and scientific scope. Online,
fixture and exact source/kind/query-bound CSV/gzip clients preserve original time
and optional original-byte SHA-256. The native preamble reader is source-specific;
the generic first-header CSV intake is unchanged.

TPI1 (`HGNC:12009`) is not listed in this received export. That is distinct from
a source row explicitly classified No Known Disease Relationship, a failed request
or an unavailable file. Linked reports/publications, dosage sensitivity,
actionability, sequences, variants and clinical interpretation are not acquired.
No automatic card enrichment or frozen schema change is added.

The [official ClinGen terms](https://clinicalgenome.org/docs/terms-of-use/)
dedicate published curated content under CC0 1.0 and request ClinGen/access-date
attribution. Record actual access time independently from the source file label;
linked publications and input resources retain their own rights.

## OmniPath: preserve opposing effects and original resource support

The historical `protein_specialist.py::map_omnipath` chose stimulation first,
then inhibition, so a row with both flags true lost the inhibition declaration.
It also preferred gene labels over native participant identifiers, attached the
caller protein and imposed a universal curated class. The useful requirement is
an independent native interaction observation with original aggregation scope.

The [current query contract](https://omnipathdb.org/queries/interactions) declares
dataset, organism, partner, field, format and licence filters. The official
[client documentation](https://r.omnipathdb.org/reference/omnipath_query.html)
explains academic/commercial filtering and resource-prefixed references. Software
MIT/GPL licences do not substitute for the
[constituent resource rights](https://omnipathdb.org/info).

A small public query requested `partners=P60174`, `datasets=omnipath`,
`organisms=9606`, source/reference fields, JSON and the explicit academic filter.
Its **288-byte** response has SHA-256
`6f5a542228162871e4645e3f7897eba1bc660fb4c9ffc7bf75d9f852030d4e6a` and one
native P29466-to-P60174 directed, inhibitory row supported by SPIKE/SPIKE_LC.
JSON sign/direction/consensus fields are booleans; references retain resource
prefixes. This particular row does not have both effect flags. It demonstrates
native shape, not comprehensive signaling coverage or universal reuse rights.
The body remains a `/tmp` probe, not a new redistributable fixture; the exact first
retrieval time is unrecorded. No licence bypass/password filter was used.

Before intake qualify current resource-specific rights, dataset/organism/query
scope, native revisions and coverage. Keep both effect booleans and consensus
declarations without precedence, participant IDs separate from labels, original
resource/reference support and all occurrences. Aggregation and direction do not
establish direct physical binding, experimental support or a unified mechanism.
An academic/commercial query filter is not itself a source licence grant.

## ELM: native instances differ from class patterns and predictions

The historical `map_elm` accepted synthetic `motifs` or `instances`, copied generic
start/end/sequence/status/logic/context/reference fields onto the caller accession,
and added a universal curated class and fallback IDs. A class pattern, curated
instance and predicted pattern occurrence cannot share that unsupported projection.
No native ELM source client was found in `protein_sources.py`.

The authors' [2024 resource paper](https://academic.oup.com/nar/article/52/D1/D442/7420098)
describes downloadable native knowledge and a separate motif-search REST API.
An [official entry page](https://elm.eu.org/elms/elmPages/DOC_MAPK_MEF2A_6.html),
as returned by primary-domain search, states noncommercial data use under the ELM
Software License Agreement. Direct download-page and academic-agreement probes
timed out; the exact agreement remains unqualified. The article's CC BY licence
does not grant database rights. No data fixture, account/contact or motif search
execution was performed in this review.

Preserve the requirement for exact native class and instance identifiers,
investigated protein/sequence identity and revision, original bounds/peptide,
instance status, functional logic, compartment and supporting publications.
Validate native numbering against its actual sequence support before placement.
Regex consensus matches remain source predictions and never become described
instances by matching a name, sequence or current UniProt residue number. Motif
search execution is separate from source knowledge intake.

## Next batch and retention

The next five unregistered candidates are **BioCyc, OMIM, Interactome3D, PDBTM and
TCDB**. Continue reviews in batches of five. Eight reviewed candidates from the
first two batches still need integration; WikiPathways remains a promising
implementation follow-up. The original stash remains the recovery backup while
the remaining material is classified and actual work awaits a durable checkpoint.
