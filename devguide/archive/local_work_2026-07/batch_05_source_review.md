# Batch 05: five historical source candidates (2026-10-06)

Review **ChannelsDB, PRIDE, CIViC, CASTp and ProBiS** together. Recover native
CIViC accepted items by exact molecular-profile ID and explicit monthly release.
The other four remain evaluating with the concrete requirements below. A completed
review, an available website and a delivered connector are distinct outcomes.

| Candidate | Outcome | Useful material | Outstanding qualification |
| --- | --- | --- | --- |
| ChannelsDB | Reviewed; evaluating | Native MOLE/CAVER channel groups and independent literature annotations | Data reuse grant, original structure/assembly/model axes, revisions and unit-bearing geometry contract |
| PRIDE / Proteins API | Reviewed; evaluating | Native peptide/PTM/HPP observations and original provider/sequence/support context | Separate repository/provider identity, exact data terms, feature/PTM coordinates and coverage |
| CIViC | Scoped reader recovered | Independent native accepted items on complete source molecular profiles | Gene/variant identity resolution and additional API/export scopes are separate work |
| CASTp / CASTpFold | Reviewed; evaluating | Precomputed pocket/cavity/channel geometry and distinct predicted function | Existing-result download/schema, data terms, probe/structure/residue/representative context |
| ProBiS-Database | Reviewed; evaluating | Precalculated site alignments and representative-chain relations | Working native database route/record, current release/coverage, structural axes and data terms |

Historical counts after this batch: **43 in use, 27 evaluating, 11 deferred,
3 retired, 1 out of scope and 2 not registered**. **Twenty-one** candidates from
five completed batches await integration. The remaining unreviewed candidates
are FDA Orphan and EMA Orphan. Preserve the original stash and all 87 original
exported files; reviewed candidates do not count as delivered readers.

## ChannelsDB: native groups, annotations and structure scope

The preserved `map_translational_source` consumed synthetic `channels`/`results`,
attached a caller UniProt accession and assigned a universal predicted class.
No `fetch_channelsdb` implementation was found in `protein_sources.py`. Native
precomputed geometry and reviewed annotations require separate source assertions.

The [official OpenAPI](https://channelsdb2.biodata.ceitec.cz/api/openapi.json)
responds with API schema version 1.0.0. This is not a channel/database revision.
It declares distinct PDB and AlphaFill channel/annotation/download routes, plus
assembly, content and statistics endpoints. The interactive documentation's indexed
load error did not reflect the actual accessible schema and native data.

A [native 1tqn request](https://channelsdb2.biodata.ceitec.cz/api/channels/pdb/1tqn)
returned **751462 bytes**, SHA-256
`f279ce91ee43ec6df7854923b8c46b723c31c2ebca204ae0309c3923ba5dd7f7`.
It contains seven independent `Annotations` and twelve `Channels` groups. The
26 channel occurrences comprise CSA MOLE 3/CAVER 1, reviewed MOLE 4/CAVER 0,
cofactor MOLE 3/CAVER 15; the other six groups are empty. Keep groups, occurrence
IDs, native Auto/Type/Cavity, profiles, layers, lining residues and support literal.
Equal annotation/channel identifiers do not collapse distinct references.

The [provider paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10767935/)
distinguishes PDB/AlphaFold origins and MOLE/CAVER precomputations. The
[official documentation](https://channelsdb2.biodata.ceitec.cz/documentation.html)
and frontend code were inspected. Frontend Apache 2.0 and article CC BY 4.0
are not a qualified native-data redistribution grant. Structure, assembly, model,
residue numbering and sequence correspondence must accompany any normalized
geometry; physical values require documented units before PUW conversion.
No MOLEonline/CAVER job, channel discovery or structure download was submitted.
The format probe remains in `/tmp`, outside redistributable fixtures.

## PRIDE: preserve real Proteins API provider identity

The historical `fetch_pride` called three Proteins API routes, then `map_pride`
labelled all output `PRIDE/Proteins API` and curated. It converted HTTP 404 to
empty objects and aggregated other failures into a payload. That wrapper can
confuse failed access with absence and overwrite the actual input provenance.

The [official Proteins API description](https://www.ebi.ac.uk/proteins/api/doc/)
identifies integrated proteomics repositories and mapped UniProt sequences. It
does not establish that every response is a PRIDE project. The original native
feature/support records are useful; PRIDE archive/project coverage must be
qualified separately. The API's privacy and services terms and each contributing
provider's dataset rights remain relevant; do not borrow the UniProt data grant
for all integrated inputs.

All three historical public P60174 routes returned native JSON with accession,
entry name, taxonomy, sequence and checksum `73844175635F858E`:

| Route | Original bytes | SHA-256 |
| --- | ---: | --- |
| [proteomics/P60174](https://www.ebi.ac.uk/proteins/api/proteomics/P60174) | 163324 | `96c7b9132c2f9304962a6907b47bc4b21c89649647df10607f90ac5fe4099aae` |
| [proteomics/ptm/P60174](https://www.ebi.ac.uk/proteins/api/proteomics/ptm/P60174) | 167927 | `872c8ac93a7dfb5ee68d096800f313833c7275bd88c7e686c36aa537a1785535` |
| [proteomics/hpp/P60174](https://www.ebi.ac.uk/proteins/api/proteomics/hpp/P60174) | 987678 | `7c01f191e52e2b7fafe29f395a34864d29457716217d367fae3f34e55f92a47e` |

The ordinary proteomics response has 226 features and 346 support occurrences:
226 name PeptideAtlas, 102 name ProteomicsDB, and 18 omit a source name. Native
`unique: true` coexists with a support property's multiple protein mappings;
keep each declaration in its original scope rather than resolving that conflict.
PTM entries include peptide-relative modification positions and individual sources;
HPP includes HppMassIVE support. Protein feature positions, peptide positions,
source sequence, provider build strings/links and evidence codes remain distinct.
Counts, probabilities and scores do not establish abundance or universal support.
No peptide search, current-sequence placement, protein/isoform merge, PRIDE
attribution or scientific assertions were added. Probes remain outside fixtures.

## CIViC: complete monthly accepted items on native profiles

The historical GraphQL fetcher selected the first gene matched by symbol. It
paged molecular profiles but requested only the first 100 nested items per profile.
Its generic mapping attached a caller protein and produced treatment relationships
from therapy names, losing full profile/combination scope. Recover the native
source declarations without restoring those projections.

The [official release documentation](https://docs.civicdb.org/en/latest/using/data_releases.html)
provides monthly/nightly TSV/VCF releases. The public release-list GraphQL query
confirmed `01-Oct-2026` and its accepted-items file, alongside a separate nightly
file. The [official TSV formatter](https://github.com/griffithlab/civic-v2/blob/main/server/app/tsv_formatters/evidence_item_tsv_formatter.rb)
qualifies the 25 original columns. The
[official licensing FAQ](https://docs.civicdb.org/en/latest/about/faq.html#how-is-civic-licensed)
grants CC0 1.0 for CIViC content; application MIT and linked-publication rights
are separate. Preserve source citations and contributor attribution.

The unchanged [01-Oct-2026 accepted export](https://civicdb.org/downloads/01-Oct-2026/01-Oct-2026-AcceptedClinicalEvidenceSummaries.tsv)
contains **4940** rows and **4154685 bytes**, SHA-256
`a618939c33c7cc9cc530be5f0a51fc330b29ad46b3f9a5bebeddcd871375e086`.
All rows are accepted; **162** are also flagged. Support includes 4918 PubMed,
19 ASCO and 3 ASH source-type declarations. The first download's exact timestamp
was not recorded and remains `None`; the monthly export label is explicit while
entity, sequence and per-row scientific revisions are not invented.

`get_molecular_profile_items(identifier, *, release, client=None)` validates the
entire native header, all row widths, profile/item identities, accepted status and
permanent ID links before exact local selection. It retains the full text, original
byte SHA, time, release and independent acquisition receipt. Online, unchanged
fixture and source/kind/query/release-bound native TSV/gzip clients use the shared
development environment. Monthly release syntax is exact `01-Mon-YYYY`; `nightly`,
`latest`, names, protein accessions and compound queries are unsupported.

`map_molecular_profile_items` creates independent SourceAssertions on
`civic:molecular_profile:<id>`, with original occurrence index/hash and all 25
literal fields. Molecular-profile combinations, therapy strings/interaction type,
disease/DOID, phenotype, direction, significance, levels, ratings, status, flags,
variant origin, citations/trials and review dates survive. Repeated or conflicting
items are never deduplicated or resolved by a strongest rating. CIViC Evidence
Items and CIViC Assertions remain source terminology, not MOLI Evidence.

Profile **12** (BRAF V600E) has **93** rows, with both Supports and Does Not
Support directions; its rows are unflagged. Profile **32** retains accepted,
flagged item **31** for DNMT3A R882. Profile **5969** retains item **32** on
`ALK F1174L AND RANBP2::ALK Fusion` with Crizotinib/Resistance as one complete
native profile declaration. It is not distributed to ALK, RANBP2 or a generic
protein target. Not-listed differs from failed access and a negative association.

This reader does not acquire submitted items, CIViC Assertions, gene/variant
exports, therapies by name, publications or patient data. It does not normalize
clinical significance, infer treatment efficacy, split therapy/profile combinations,
merge biological identities or enrich frozen protein cards. Replay retains the
original response/time and release without new network calls. Tests and live
qualification receipts are in [validation.md](validation.md).

## CASTp / CASTpFold: existing results are a separate contract

The historical CASTp declaration and synthetic generic cavity mapper do not
contain a native fetcher or qualify an original structure/pocket contract.
The current [official CASTpFold application](https://cfold.bme.uic.edu/castpfold/)
responds with an application shell. Its
[official news](https://cfold.bme.uic.edu/castpfold/news) states free access and
requests citation; a native-data redistribution grant and exact existing-result
schema were not qualified.

The [peer-reviewed provider paper](https://academic.oup.com/nar/article/52/W1/W194/7680624)
distinguishes surface pockets, enclosed cavities and channels, PDB/AF2 origin,
functional predictions and similarity search. AF2 queries can redirect to a
representative structure. Keep requested versus representative identity explicit;
cluster membership or structural similarity cannot transfer pocket/function data
to every member. Area/volume/probe units, pocket atoms and residue numbering,
structure/model/assembly revision and parameters must accompany mapped geometry.
Predicted DeepFRI function and precomputed geometry retain separate support.
No uploaded structure, new job, similarity search, DeepFRI or geometry calculation
was invoked. Article access rights are not assumed to license all server results.

## ProBiS: database reads differ from computation endpoints

The preserved ProBiS generic mapper has no native `fetch_probis` implementation.
It assigns caller protein identity to synthetic binding-site rows. Existing local
alignment records and explicit representative-chain relations are useful without
that identity merge or ligand transfer.

The [official HTTP database documentation](http://probis.cmm.ki.si/?what=database)
works, despite the HTTPS web reader timing out. It documents representative-chain
translation and `get_alignments`, plus structural rendering/download endpoints.
The [webservice page](http://probis.cmm.ki.si/?what=webservices) separately exposes
`align` and CPU-intensive `scan`: these perform new calculations and were not
called. The landing page's July 2015 dataset label does not establish current
native-record freshness or completeness.

A documented [database alignment example](http://probis.cmm.ki.si/rest/get_alignments?structure_id=1all.A&z_score=2.0)
with JSON Accept returned **HTTP 404**, **278 bytes**, SHA-256
`e08c8a049d6b436bc33b97238bf33b996ecf8d79aa0a7f9137a14da501f00c32`.
This is a failed acquisition, not zero alignments or resource retirement.
Qualify an actually working native database route/record, current data-specific
reuse terms, representative query relation, release/coverage/threshold, chain/model/
assembly coordinates and local alignment correspondence. A greater-than-95%
representative relation is not entity identity; Z-scores are not probabilities.
No scan, alignment job, ligand prediction, superposition, minimization or energy
calculation was run. Native database rights cannot be inferred from article or
algorithm licences.

All exploratory probes above were public and unauthenticated. Their exact first
retrieval times were not captured; do not replace them with file modification times.
Only the qualified CC0 CIViC export was introduced as a public test fixture.
