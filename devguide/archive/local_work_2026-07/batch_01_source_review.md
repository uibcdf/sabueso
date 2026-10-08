# Batch 01: five historical source candidates (2026-10-06)

Review HPA, GtoPdb, WikiPathways, Monarch and MEROPS together, as requested.
Each has a recorded outcome and implementation requirements. A completed review
does not mean a delivered connector. The native HPA reader is recovered;
the other four remain `evaluating`, with their useful requirements preserved.

| Candidate | Outcome | Useful material | Remaining qualification |
| --- | --- | --- | --- |
| HPA | Scoped reader recovered | Gene-level RNA/protein tissue and cell-type summary categories | Quantitative expression, full assays and isoform/sequence placement remain outside this reader |
| GtoPdb | Reviewed; evaluating | Native target pharmacology, endogenous ligands, transduction and channel context | Authorized native access, multiple target/subunit identity, dual data rights and measurement semantics |
| WikiPathways | Reviewed; evaluating | Public native pathway context and explicit namespaced cross-references | Exact token selection, native cross-reference basis and complete snapshot/coverage handling |
| Monarch | Reviewed; evaluating | Original gene/disease/phenotype association direction, qualifiers and source attribution | Per-source rights, native paging/cuts and exact entity scope |
| MEROPS | Reviewed; evaluating | Peptidase/inhibitor classification and substrate-cleavage context | Native release/export schema, precise database licence and substrate-sequence placement |

Historical catalog counts: **40 in use, 10 evaluating, 11 deferred, 3 retired,
1 out of scope, 22 not registered**. The 22 are unreviewed candidates from the
previous 27, not the complete outstanding implementation backlog. Four candidates
from this batch are reviewed but still lack qualified connectors; prior evaluating
and deferred sources retain their own decisions. No stash or historical file is
deleted. Recovery does not restore the old automatic enrichment profile.

## HPA: recover native categorical gene summaries

The preserved `knowledge.py::map_human_protein_atlas` accepted the first item of
arbitrary lists, selected keys containing `tissue`/`cell type`, and described the
object as `gene_or_total_protein`. That does not qualify an assay, measured protein
form, complete expression coverage or physical quantities. The source idea is
useful; its old projection is replaced.

The [official download contract](https://www.proteinatlas.org/about/download)
documents `ENSG….json` as a subset of search data. The unmodified TPI1 response
is a single object with native Ensembl identity `ENSG00000111669`, gene label
`TPI1`, UniProt reference `P60174` and **22** categorical declarations across
RNA/protein contexts. The **9394-byte** fixture has original-byte SHA-256
`62b81e47662b8c4d74a51cb41c4ba68803cf339150a34441f49ae37f9b85401a`.
The exact first retrieval timestamp is unrecorded.

`tools.db.hpa.get_gene_profile` retains every native field. `map_gene_summary`
supplies independent literal category/null assertions on `hpa:ENSG00000111669`.
Missing keys, native nulls and failed access are distinct. Quantitative nTPM,
nCPM, pTPM, intensity, concentrations, scores and prognostic fields remain in the
raw envelope and are not projected as normalized measurements. RNA and protein
labels are not collapsed; animal brain fields are not labeled human measurements.
The gene's UniProt pointer does not merge gene and protein/isoform entities.
Native dataset, gene and sequence revisions remain unknown; website release 25.1
is not assigned to the response as a scientific revision.

Online/fixture/query-bound JSON/gzip clients, original-byte SHA checks, detached
acquisition and original-time archive replay are qualified. Source assertions
remain standalone; no frozen card change, card enrichment or linked acquisition.
The [official licence](https://www.proteinatlas.org/about/licence) states CC BY 4.0
for copyrightable database parts, with third-party input constraints retained.
Credit the resource, specific gene/data URL and appropriate primary publications.

## GtoPdb: keep pharmacology requirements, qualify authorized native access

The historical `fetch_gtopdb` selected the first returned target and queried seven
different endpoints. It turned 404 into an empty target result and kept endpoint
errors in an aggregate that the mapper did not expose as acquisition coverage.
`knowledge.py::map_gtopdb` selected `affinity or affinityMedian`, losing a valid
zero, and assigned generic ligand types and a universal curated class. These
shortcuts cannot establish protein/target/subunit identity or assay support.

The [current official REST contract](https://www.guidetopharmacology.org/webServices.jsp)
requires registration and an API key, recommends the `GTP-API-Key` header and
documents a rate limit around 60 requests/minute. No authenticated request,
credentials, account creation or provider contact was used in this review.
Database rights (ODbL) and content rights (CC BY-SA 4.0) are separate requirements.

Recover only after receiving a lawfully obtained native response or qualifying
authorized access: preserve every target candidate, exact native target/subunit
scope, endpoint-specific receipts/failures, ligand/entity types, species,
endogenous/context declarations, original references, measurement relation/ranges,
zero values and declared units. Logarithmic affinity parameters are not a guessed
molar measurement. Native assay and revision context must precede any projection;
the first returned target is never selected as a protein identity shortcut.

## WikiPathways: exact cross-references replace substring/name selection

The historical `fetch_wikipathways` used lowercase substring matches for UniProt,
Ensembl and gene symbols. Prefixes and shared names could select unrelated pathways;
stripping a gene revision also erased request scope. `map_wikipathways` attached
the requested protein and a generic curated class without native occurrence support.

The production [terms](https://www.wikipathways.org/terms.html), successfully
retrieved directly, state CC0 content and request scientific attribution. The
production transition notice retires the classic web service, not the working
bulk JSON route used here. The original
[findPathwaysByXref export](https://www.wikipathways.org/json/findPathwaysByXref.json)
returns **2218** pathway rows, **12084935 bytes**, SHA-256
`09da862b2d2dc08c98c0a0d98640892c076668d5ad251ee373502dcf89bbce22`.
This public review body remains in `/tmp`, not a licensed/qualified test fixture.
Its exact first retrieval time is unrecorded.

Cross-reference values contain comma-separated groups and semicolon-separated
aliases with explicit prefixes. Exact `uniprot:P60174` tokens occur in nine
received rows: WP143, WP1946, WP2456, WP4018, WP4628, WP5178, WP534, WP5355,
WP5570. This observation establishes source-served cross-reference context, not
experimental protein participation or a verified GPML DataNode occurrence.

The next implementation must validate the full source object before selection,
match exact namespace/token identities, preserve species and all aliases/native
row occurrences, expose received/selected coverage and retain original pathway
revision strings. A pathway edit date is not a dataset/sequence revision. Gene
symbols, similar names and inferred cross-database equivalence are not query
identity. Pathway references do not by themselves assert a protein mechanism,
physical interaction, pathway role or universal experimental/curated class.

## Monarch: original association scope and source-specific rights

The historical `fetch_monarch` requested up to 100 associations on a gene.
`protein_drug_discovery.py::map_monarch` filtered disease-looking categories,
attached the caller's protein accession and assigned `database_inference`.
Primary/aggregator source fields were worth preserving, but native original
identifiers, gene-level scope, negation, qualifiers and paging were incomplete.

The documented [association API](https://monarch-app.monarchinitiative.org/FastAPI/Endpoints/)
still answers the prototype route. A deliberately small public query for subject
`HGNC:12009`, limit 2, returns native TPI1 gene context, **2 items**, offset 0,
**total 232**, and BioGRID primary knowledge source. The **5205-byte** body has
SHA-256 `0456c3b120f0922eab4a0508f4169ac253ba973a5191bce625da65cc2607e858`.
It remains a `/tmp` review probe, not a new redistributable fixture. The exact
first retrieval time is unrecorded; two items do not establish full query coverage.

The [licensing guidance](https://monarch-app.monarchinitiative.org/Licensing/)
separates BSD 3-Clause software from recommended data licences and gives individual
repository licences precedence. Review the
[original input sources](https://monarch-app.monarchinitiative.org/Sources/)
and their actual grants before intake; do not assign a blanket BSD or CC0 data grant.
The next connector must keep exact gene/entity subject and object, direction,
original identifiers, primary/aggregator sources, native `knowledge_level` and
`agent_type`, negation, qualifiers, taxa, evidence/publication pointers and page
totals/cuts. A gene association does not establish an association on every encoded
protein/isoform; absence from a partial page is not a source negative.

## MEROPS: recover source scope after host/release/export qualification

The preserved `protein_expansion.py::map_merops` accepted synthetic `cleavages`
or `results` rows, substituted caller accession as substrate, generated fallback
IDs and copied positions/assay/relevance into a universal curated class. No native
cleavage reader in `protein_sources.py` qualified those rows or their sequence axis.
The useful requirement is original protease/substrate/cleavage support, not this
unsupported projection.

The old Sanger download URL returned HTTP 410. The resource remains available at
[EMBL-EBI](https://www.ebi.ac.uk/merops/), with website release 12.5. Its
[download list](https://www.ebi.ac.uk/merops/download_list.shtml) still labels the
SQL export 12.4 and distinguishes unit-only from full-length sequence libraries.
Neither label proves the release of a future received cleavage row or its numbering.

The [database availability statement](https://www.ebi.ac.uk/merops/about/availability.shtml)
names GNU Library GPL for the full database content and links the general LGPL
page. Record the precise applicable database licence/version and actual native
export before classifying redistribution or adding fixtures. A paper's licence,
website footer or newer generic software licence cannot substitute for that grant.
Preserve independent native protease and substrate identities, investigated
sequence/unit bounds, cleavage numbering and P1/P1-prime context, original assay,
physiological-relevance qualifiers and references. In-vitro observations do not
establish physiological cleavage or current canonical positions. No similarity
search, BLAST job or automatic protease-family inference is recovered.

## Next batch and retention

The next five unregistered candidates in the existing order are **COSMIC, HPO,
ClinGen, OmniPath and ELM**. Complete their review as a batch; do not count a
source as implemented merely because its requirements have been preserved.
WikiPathways is a promising implementation follow-up from this batch.
The original stash remains the backup until remaining useful material has been
classified and actual recovered work has its own durable checkpoint.
