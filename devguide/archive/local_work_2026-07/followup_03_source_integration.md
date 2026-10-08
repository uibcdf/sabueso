# Third five-source integration follow-up

Reviewed **Monarch, PRIDE, MetalPDB, Interactome3D and 3did** on 2026-10-07.
Native Monarch association pages and PRIDE Archive project metadata are recovered
in the existing editable development environment. The other three still require
data-specific terms or reachable native transport; no connector is claimed for them.
See [validation.md](validation.md) for the final local checkpoint. The original
stash and all 87 original exported files remain unchanged.

| Source | Delivered behavior or current qualification | Remaining scope |
| --- | --- | --- |
| Monarch | Exact direct-subject expanded page; all native categories/qualifiers/support and explicit limit/offset/total | Arbitrary input rights, pinned KG revision across pages, optional complete paging and card intake |
| PRIDE | Exact public PXD project metadata; native depositor licence, protocols/CV objects/dates/publications | Separate Proteins API peptide/PTM/HPP inputs, linked files/results/sequence axes and card intake |
| MetalPDB | Original site/structure/coordination requirements and native field/type differences retained | Data-specific fixture grant, declared physical units and complete atom/residue/model axes |
| Interactome3D | Correct single-protein route rechecked; independent pair query remains distinct | Working verified TLS/native body, exact query/version/coverage and data rights |
| 3did | Native download route rechecked: HTTP 525, not scientific absence | Working export, exact version/DDI-DMI/profile/PDB axes and data rights |

Historical counts are now **48 in use, 24 evaluating, 11 deferred, 3 retired,
1 out of scope and 0 not registered**. Nine of the original 27 reviewed candidates
have scoped recovered readers; **18** await integration. These counts describe
the 87 historical declarations, not the entire maintained registry. A delivered
project metadata reader does not claim every old PRIDE/Proteins API capability.

## Monarch: preserve native associations and explicit page boundaries

The historical `protein_drug_discovery.py::map_monarch` discarded non-disease
associations, attached the caller protein and imposed a database-inference class.
The replacement maps every received category and row occurrence on its original
association subject. It preserves the native relation identifier, predicate,
original/normalized subject/object, taxa, negation, qualifiers, primary and
aggregator knowledge sources, knowledge/agent labels and original support pointers.
Normalized IDs do not merge entities or transfer gene knowledge onto proteins.
ECO pointers remain source claims and never become MOLI Evidence.

`get_associations(identifier, limit=20, offset=0, client=None)` requires one exact
CURIE, a limit from 1 to 500 and a nonnegative offset. The service [native OpenAPI](https://api-v3.monarchinitiative.org/openapi.json)
declares expanded page counts and an API version of **0.1.0**, which is separate
from unknown KG, entity, relationship and sequence revisions. The reader sets
`direct=true`. The author's [query implementation](https://raw.githubusercontent.com/monarch-initiative/monarch-app/main/backend/src/monarch_py/implementations/solr/solr_query_utils.py)
shows that this uses exact subject filtering instead of ancestor/closure matching;
it is not a physical-binding assertion. Every returned subject and native page
limit/offset are checked. Missing/malformed totals, contradictory counts and an
empty page before its declared total fail explicitly. An empty offset beyond
the total remains an empty page, without a biological negative claim.

All native occurrences survive, including repeated identifiers, contradictory
negation, future labels and absent versus null/empty support. Assertions carry
query/page/full-response support and original occurrence indices. Caller offsets
are explicit; the reader never follows pages, linked sources, evidence or articles.
Offsets do not guarantee a stable ordering or pinned KG revision between requests.
`SnapshotMonarchClient` binds original JSON/gzip to exact source/kind/direct-subject/
limit/offset and optional byte SHA; replay retains the original acquisition time.

The unchanged native TPI1 page has **5205 bytes**, SHA-256
`0456c3b120f0922eab4a0508f4169ac253ba973a5191bce625da65cc2607e858`,
two BioGRID gene interactions and native total **232**, offset 0 and limit 2.
It preserves `HGNC:12009` / original `NCBIGene:7167`, `ECO:0000172`, PMID 26344197,
primary `infores:biogrid` and aggregator `infores:monarchinitiative`.
The fresh exact-direct query's bytes match the earlier probe; the fixture's exact
first download time remains unknown (`None`). The [ingest documentation](https://monarch-app.monarchinitiative.org/Sources/biogrid/)
describes method-to-ECO conversion, including approximate/default mappings. Those
source labels are not promoted to an independently established experimental class.

[BioGRID's download repository](https://downloads.thebiogrid.org/BioGRID) explicitly
grants MIT rights to its data. Its linked original licence includes download files,
not just software: **1094 bytes**, SHA-256
`39a74f854f2d9370b8d349ca329cb6bd37390b8b47b6b5edd5825276721a1391`,
with Mike Tyers Lab's 2005 copyright and native Windows-1252 encoding. The unchanged
notice remains beside this fixture. Monarch's BioGRID ingest documentation separately
lists BSD-3-Clause. The original Monarch software licence is also retained, without
assigning it to arbitrary graph data. The [general licensing guidance](https://monarch-app.monarchinitiative.org/Licensing/)
recommends licences and gives individual terms precedence; recommendations do not
grant rights. Registry-wide Monarch terms remain `NOT-STATED` with input-specific
caveats. Linked publications and ontology content keep independent origin/rights.

Live shared-editable validation from `/tmp` at **2026-10-07T06:18:23+00:00** uses
one GET/attempt/response and maps both TPI1 relationships. Native body bytes and
decoded content match the fixture. Canonical response identity is separately
`sha256:cdd10b5ef89cf929d37c2bfa872873f6c57b9df96ff8ddcb27b52fcd654caf78`.
Partial page coverage is explicit; original fixture time is not overwritten.

## PRIDE: recover real project metadata without relabeling other providers

The historical `fetch_pride` actually queried Proteins API's integrated proteomics,
PTM and HPP routes; its mapper applied PRIDE provenance and a curated class to all
results and treated HTTP 404 as empty. The earlier native review found PeptideAtlas,
ProteomicsDB and unnamed support, with individual mapped sequences and peptide/PTM
axes. Those observations are still useful, but are not newly labelled PRIDE projects.
They remain separately unintegrated under their actual input rights and contracts.

The new `sabueso.tools.db.pride.get_project(identifier, client=None)` retrieves one
explicit public PXD project from PRIDE Archive. The [official API specification](https://www.ebi.ac.uk/pride/ws/archive/v2/v3/api-docs)
describes the project route and names API version **3.0**; the URL's **v2** is a
separate route label. Neither establishes scientific dataset/sequence revision.
Actual [PXD013616 native metadata](https://www.ebi.ac.uk/pride/ws/archive/v2/projects/PXD013616)
is a JSON object, despite the route specification's string response declaration.
Native CV/protocol/context arrays also differ from some broad schema string-array
definitions; no automatic stringification, renamed field or schema repair is used.

The complete unchanged metadata fixture is **8484 bytes**, SHA-256
`b5ff728947d5e0e394633022e26ba57622ccbfad2d6e9da46b8a60add6c2de71`.
It preserves the original title/descriptions/protocols, PARTIAL submission type,
publication/submission dates, object-valued CV declarations, empty quantification
methods and project DOI, independent reference DOI **10.1126/sciadv.aay4697**,
listed modification `MOD:01892` and administrative counts. Protocol physical values
remain free text without quantity extraction. PARTIAL is a depositor submission
label, not a reader cut or an inferred absence of results.

`map_project` makes an assertion about `pride:PXD013616`, with every native field,
full response identity and source scope. The depositor's description is retained as
text; it is not imported as a protein result, per-peptide support, clinical conclusion
or MOLI Evidence. Repeated CV/reference occurrences and future categories survive.
Missing per-project licence declarations stay unknown. The native project declares
**Creative Commons Public Domain CC0**, also reflected by its [official project page](https://www.ebi.ac.uk/pride/archive/projects/PXD013616).
Registry-wide terms remain `DEPOSITOR-TERMS`; this project's grant is not assigned
to arbitrary projects, linked publications, files or integrated Proteins API inputs.
Credit PRIDE and original dataset depositors/publications. No file, peptide,
protein, sequence, publication or analysis job is fetched or submitted.

Online, fixture and query-bound original JSON/gzip clients preserve original
byte hashes and unknown/declared acquisition time. Failed HTTP or application/error
payloads never become an empty identified project. Live validation from `/tmp` at
**2026-10-07T06:18:24+00:00** uses one GET/attempt/response, retains/maps the project
and matches original fixture bytes/content. Canonical identity is separately
`sha256:f8db2e80fb7446de6e83ee8b989a82a54eea512968c4cf54cb2099177090f8fb`.
Counters and metadata can change without a stated project revision; new response
support remains independent. The original fixture time remains unknown.

## MetalPDB, Interactome3D and 3did: current qualification boundaries

MetalPDB's native **849-byte** `12ca_2` probe and SHA-256
`4fbde4d64312472953cd7fc7eafe2da327a7fa1b67881bf56a9eddc45f8e68c4`
remain unchanged. The [current API help](https://metalpdb.cerm.unifi.it/api_help)
and [provider about page](https://metalpdb.cerm.unifi.it/about) were checked. They
identify query/site/coordination context and the owning project, but do not settle
standalone data redistribution or physical distance units. Native `metals`/`pdb`
and string-valued classifications differ from some documented names/types; source
chain/residue/atom axes and unspecified insertion/model support cannot become
current-UniProt coordinates. Source coordination is not a universal experimental
class or functional metal requirement. No geometry/MetalPredator job is run and
no unit or fixture grant is invented. See [batch 04](batch_04_source_review.md).

Interactome3D's [documented API](https://interactome3d.irbbarcelona.org/help.php)
distinguishes exact single-protein `uniprot_ac` from two-participant
`queryProt1/queryProt2`. One new bounded verified-HTTPS request for P60174 at the
correct single-protein endpoint still fails during TLS establishment (curl 35,
HTTP 000, no native body). No certificate bypass or obsolete HTTP fallback is used.
The native XML root version, complete/representative coverage, rank/model/template
types, per-participant bounds and original input rights remain pending. Aligned
endpoints do not give a full-chain residue correspondence. Access failure does not
establish retirement or no structures. See [batch 03](batch_03_source_review.md).

3did's documented native download route returns **HTTP 525** again. The received
**16-byte** error body has SHA-256
`f28010ee4bebf3921c03ddd425fdde6c937c24298bd0888b701a71ad53030a0e`.
This is a transport/application failure, not a received empty scientific export.
Domain-domain versus motif instances and aggregate profile interface fractions
keep separate scopes. PDB contact numbering and Pfam HMM/profile positions do not
share an axis; score values do not become generic probabilities. Native release,
coverage and actual export/contributor grants remain pending, without motif search,
contact computation or coordinate/model acquisition. See [batch 04](batch_04_source_review.md).

The current registry/packaged metadata, historical catalog/inventory, public API
and source/user/API documentation now describe both scoped readers. Published
schema 0.3.12, release state, source identity and the development environment are
preserved. Further integrations remain separate work; the stash is retained.
