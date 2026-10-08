# Batch 04: five historical source candidates (2026-10-06)

Review **MetalPDB, ECOD, 3did, DrugCentral and GWAS Catalog** together. Recover
DrugCentral's native drug-target TSV access and independent source-scoped mapping;
the other four are evaluating with the qualification requirements below. Review
completion, source availability and delivered connector coverage are distinct.

| Candidate | Outcome | Useful material | Outstanding qualification |
| --- | --- | --- | --- |
| MetalPDB | Reviewed; evaluating | Native structure/site, metal/ligand/donor, geometry and support | Native types/axes/revisions, distance units and data-specific reuse terms |
| ECOD | Reviewed; evaluating | Evolutionary hierarchy and independent domain partitions | Accessible exact native release/record, structure origin, partition axes and terms |
| 3did | Reviewed; evaluating | DDI/DMI structural instances, contacts and profile interfaces | Native export/coverage/version/rights and independent PDB versus HMM axes |
| DrugCentral | Scoped reader recovered | Independent native drug-target observations, composite targets, activity/MOA and original support | Quantitative conversion, identity resolution and additional indication/structure scopes remain outside this reader |
| GWAS Catalog | Reviewed; evaluating | Native variant-trait-study associations, gene-set and statistical context | Explicit query/gene-set scope, complete paging, variant/assembly/statistical axes and original terms |

Historical counts after this batch: **42 in use, 23 evaluating, 11 deferred,
3 retired, 1 out of scope, 7 not registered**. **Seventeen** reviewed candidates
from four batches still await integration, independently of those seven unreviewed
candidates and the earlier evaluating/deferred decisions. Keep the original stash
and all 87 unchanged original exports.

## MetalPDB: native site/structure support replaces a universal experimental class

The old `protein_structural_context.py::map_metalpdb` accepted synthetic metal-site
dictionaries, attached the caller protein and labelled every site experimental.
No native fetcher was found in the preserved source module. Its site/context
requirements are useful without that unsupported identity and evidence projection.

The [official API help](https://metalpdb.cerm.unifi.it/api_help) documents explicit
site, PDB and UniProt queries, selectable columns and unrestricted-column defaults.
A public [site 12ca_2 request](https://metalpdb.cerm.unifi.it/api?query=site:12ca_2)
returned a **849-byte** JSON array, SHA-256
`4fbde4d64312472953cd7fc7eafe2da327a7fa1b67881bf56a9eddc45f8e68c4`.
Exact first retrieval time is unrecorded. The row keeps source site/PDB identity,
native P00918 reference, representative false, taxonomy and domain/EC labels,
one Zn atom and three His ligand occurrences with chain A, original residue/atom
numbers, donor atoms and distances. Source geometry and coordination remain literal.

The response differs from some documented names/types: `metals` and `pdb`, rather
than `metal` and `pdb_code`; site type and EC/Pfam/CATH/SCOP are native strings in
this probe. Do not treat a type mismatch as permission to fabricate a normalized
record. Preserve each native occurrence, numbering/insertion/model/chain scope,
sequence/PDB revision gaps and source support before canonical projection.
Distance units were not established in the reviewed help/body; no angstrom or
biological metal essentiality is guessed. The [provider site](https://metalpdb.cerm.unifi.it/)
requests its primary publications, but a separate current data reuse grant was
not qualified from the site/API/about pages. Article licences are separate.
The body stays in `/tmp`, not a fixture. No MetalPredator/geometry computation,
coordinate acquisition or automatic card intake is added.

## ECOD: structure origin and independent domain partitions stay explicit

The old `map_ecod` attached a caller protein and a generic inference class to
synthetic domains with fallback IDs; it had no native source fetcher. Preserve
classification/partition requirements without adopting those identity assumptions.

The author [original resource paper](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003926)
describes the ECOD evolutionary hierarchy and discontinuous/multichain domains,
and points to `prodata.swmed.edu/ecod`. The
[current resource paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11701565/)
separates experimental and predicted structures and discusses Pfam family-level
classification changes. A historical release or article licence does not qualify
today's native export, numbering or grant. Preserve native architecture/X/H/T/F
labels and group identities without treating every similar architecture as homology.

The direct official-host HTTPS probe could not establish a connection. The
[official HTTP landing page](http://prodata.swmed.edu/ecod/) was available and linked
distribution/search/help. Its distribution route returned an application shell
without a native release/export. No native domain record or current release was
qualified; the website itself is available. The bare `ecod.org` alternative
returned a parked/domain-sale page and is not used as the scientific provider.
Access failure is not resource retirement or domain absence. Exact native release,
domain/structure/chain/partition identity, original coordinate axes, classification
support and data-specific terms remain required. Experimental PDB partitions and
AlphaFold/DPAM predicted collections remain distinct; no domain prediction,
sequence matching or current-protein projection is recovered.

## 3did: structural contacts and profile-interface positions have different axes

The preserved `map_3did` accepted synthetic interactions with fallback IDs,
attached a protein accession and applied a curated class; it had no native fetcher.
Recover requirements for independently supported structural instances instead.

The [official resource page](https://3did.irbbarcelona.org/index.php), as returned
by the web reader, declares Pfam 37.0 and PDB 2024_12 context, with distinct
domain-domain and domain-motif knowledge. Its
[download documentation](https://3did.irbbarcelona.org/download.php) describes
`3did_flat`, `3did_dmi_flat`, interface/global-interface files and separate SQL data.
Each structural instance has PDB/chain/domain bounds, native scores/topology and
original contacts. Flat contact positions use original PDB numbering; interface
positions use the relevant Pfam HMM profile. Those axes must not be merged by
equal numbers or projected to the caller protein. DDI, DMI, pattern definitions,
individual structural observations and aggregated interface fractions stay distinct.

The SQL documentation additionally encodes lowercase chains as doubled letters;
this is a format-specific rule, not permission to silently normalize every chain.
Native InterPreTS scores are not probabilities or generic interaction confidence.
Direct home/download curl requests returned HTTP 525, so no native export or
current coverage was qualified. Cached/help-page availability is separate from
actual downloadable-data access; the resource is not declared retired. Exact
native version/shape/coverage and current export/contributor rights remain pending.
No contact calculation, model generation, motif search or data fixture is added.

## DrugCentral: recover the complete native drug-target export

The historical generic `map_drug_relationships` guessed ligand identity from
names/aliases, supplied fallback roles/actions/classes, attached the caller protein
and generated interventions whenever indication/status text existed. DrugCentral
had no native fetcher in the preserved source module. Recover its source-specific
observations without that unqualified normalization or clinical projection.

The [official download page](https://drugcentral.org/download) links the public
[compressed drug-target interaction TSV](https://unmtid-dbs.net/download/drug.target.interaction.tsv.gz).
The unchanged fixture is **956583 compressed bytes**, SHA-256
`1908684983a79a067a44da952e1f6fd26b0f34cc36560cd9be0f0843bbfee1e1`.
Its original decompressed UTF-8 TSV is **5472138 bytes**, SHA-256
`d3be9317010da11f90b2213063f4cb8a95dc4173404338d97f8a3b6070088596`,
with **22364** independent rows and 20 exact native columns. The exact first
retrieval time is unrecorded. This export does not state independent database
totals or scientific revisions. Website 2027 and the full SQL dump's date are
separate context, not this file/target/drug/sequence revision.

`tools.db.drugcentral.get_target_relations` receives the complete export in one
GET and validates every row before local matching of one exact base UniProt
accession against native pipe-separated ACCESSION tokens. Fixture and exact
source/kind/query-bound TSV/gzip clients preserve original text/time, optional
original-file SHA and local read receipts. Online receipts separately retain the
compressed download hash and full decoded-text identity. Replay retains original
time/support without fetching source links. No SQL server or new environment is used.

`mappings.drugcentral.map_target_relations` preserves every matching occurrence
with its complete original columns, row index and full export support on the
original source target or target group. Composite targets stay composite subjects;
one member matching the query does not distribute activity among its members.
Repeated identical rows have independent IDs; conflicting rows survive. There are
18 repeated full-row occurrences beyond their first occurrences in this received export. Drug names do not
merge native STRUCT_IDs, targets or chemical entities.

EGFR/P00533 has **80** native observations, **18** with MOA literal `1` and **62**
with that field empty. Activity and mechanism-of-action declarations retain separate
source pointers, relation/action/type/comments and unknown revisions. All received
ACT_UNIT cells are empty. Native ACT_VALUE is preserved as a string: no physical
quantity, logarithmic scale, concentration, affinity, efficacy or potency conversion
is guessed. Empty MOA is not false or proof of no mechanism. P60174 is not listed;
that differs from access failure and does not establish absence of drugs/interactions.

The [official resource licence](https://drugcentral.org/privacy) links
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Attribute DrugCentral
and original contributing sources, link the licence, indicate changes and retain
share-alike where applicable. The fixture preserves the original compressed bytes
unchanged; underlying data/publication rights remain separate. No source-linked
data, chemical/sequence search, indication mapping, clinical interpretation,
automatic card enrichment or frozen card-schema change is added.

## GWAS Catalog: explicit gene-set and paging scope precede interpretation

The old `fetch_gwas_catalog` used v2 mapped-gene paging without preserving native
pages/totals/query receipts, bounding next links or stating its gene-set definition.
The old mapper added a universal curated class to synthetic association collections.
Useful variant/trait/study and native statistical requirements survive.

The [current API documentation](https://www.ebi.ac.uk/gwas/docs/programmatic-access/rest-api/)
supports v2 and states that v1 was retired in August 2026. The
[migration guide](https://www.ebi.ac.uk/gwas/docs/news/rest-api-v2-migration-guide/)
distinguishes the default standard gene set (mapped and nearest Ensembl genes)
from `extended_geneset=true` with broader Ensembl/RefSeq annotation. These are
source mapping declarations, not causal genes, functional protein effects or
uniform association support. The old synthetic protein projection is not recovered.

Public explicitly standard-gene-set probes were received. TPI1 declares zero
elements in **198 bytes**, SHA-256
`4dde3abd2cc12114cc229c93e6acb95e07d1467d2ebee03b3c18376ae1df92b7`.
HBB page zero has **2 of 279** declared associations, **2485 bytes**, SHA-256
`14f63516b1a620e3e41ddbd681acf507bc88f5685229103ece6c61a172b05786`.
Exact first retrieval times are unrecorded. This observed response uses HAL-style
embedded associations and next links; general migration cautions are not used to
invent a different received format. The HBB page is explicitly partial, not a full
association dataset. It includes native association/study/variant/trait identifiers,
mapped genes, genomic locations, risk-frequency strings, effect text and p-value
mantissa/exponent (including exponent -323). Do not round underflow to zero,
infer a genome assembly or turn text such as unit decrease into a physical quantity.

The [official FAQ](https://www.ebi.ac.uk/gwas/docs/faq/) distinguishes curated
Catalog data under EBI Services Terms from summary statistics under CC0 with
individual-study exceptions; code is Apache 2.0. Do not assign summary-statistics
CC0 to this curated API page or override original contributor/publication rights.
Before integration qualify bounded complete paging, explicit gene-set/query and
coverage, original variant/assembly/statistical/ancestry scope and source rights.
Both bodies stay in `/tmp`, not new fixtures. No summary-statistics download,
association ranking, ancestry/effect harmonization or clinical conclusion is added.

## Next batch and retention

The next five unreviewed candidates are **ChannelsDB, PRIDE, CIViC, CASTp and
ProBiS**, followed by **FDA Orphan and EMA Orphan**. Seventeen previously reviewed
batch candidates still await integration, separately from those seven. Keep the
original stash while recovery and a durable code checkpoint remain outstanding.
