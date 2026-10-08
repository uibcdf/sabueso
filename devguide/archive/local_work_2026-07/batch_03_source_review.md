# Batch 03: five historical source candidates (2026-10-06)

Review **BioCyc, OMIM, Interactome3D, PDBTM and TCDB** together. Recover their
useful requirements and concrete qualification boundaries. All five are now
`evaluating`; this batch adds no delivered connector or redistributable fixture.
Public format probes stay in `/tmp`, outside package data and card intake.

| Candidate | Useful material | Outstanding qualification |
| --- | --- | --- |
| BioCyc | Organism/database-qualified pathway, reaction and participant declarations | Authorized session and applicable data agreement; native frame relations and database release |
| OMIM | Independent gene/locus–phenotype declarations, MIM identities, inheritance and mapping key | Authorized native export/API and current agreement; gene/locus, phenotype and variant scopes |
| Interactome3D | Separate protein and interaction structures/models with ranks, templates and coverage | Working native response with correct protein/pair queries, complete coverage and applicable data rights |
| PDBTM | Structure-chain topology, original sequence/PDB endpoints and membrane/assembly transforms | Native coordinate/revision qualification and nonprofit/commercial, no-modification terms |
| TCDB | Independent native accession–TC-system assignments and separate family/substrate context | Export-specific terms, accession namespaces and complete native coverage; no function transfer from a TC number |

Historical counts after this batch: **41 in use, 19 evaluating, 11 deferred,
3 retired, 1 out of scope, 12 not registered**. The 12 are unreviewed candidates.
**Thirteen** candidates from the first three batches are reviewed and still await
integration. Six earlier evaluating and eleven deferred decisions remain separate.
The unchanged stash and all 87 original exports remain the recovery backup.

## BioCyc: native frames and organism databases precede pathway projection

The preserved `protein_specialist.py::map_biocyc` accepted synthetic `pathways` or
`results`, supplied fallback IDs, attached the caller's accession and labelled every
row curated. Database, species, role and upstream/downstream fields are useful
requirements, but they do not establish a native pathway membership or reaction
direction. No native BioCyc fetcher was found in `protein_sources.py`.

The current [official web-service documentation](https://biocyc.org/web-services.shtml)
was readable through direct public curl. It requires a session and returned cookies,
links the BioCyc Databases Limited Use License and requests an average maximum of
one request per second. Native XML requests identify an organism database and
object/frame, with a declared detail level. Foreign-ID lookup is a separate service;
an external identifier does not itself establish a native protein frame or its
pathway/reaction relationships.

The [individual subscription terms](https://biocyc.org/subscription-terms.txt)
limit third-party copying to specified excerpts and restrict scraping and broader
dissemination. The API's linked Limited Use License redirects through JavaScript;
its [current public destination](https://bioinformatics.ai.sri.com/ptools/licensing/all-reg.shtml)
was read without submitting the form. It distinguishes Open Databases (EcoCyc and
the Faecalibacterium prausnitzii A2-165 PGDB) from other Limited Databases. The
former permit modification/reuse with retained notices and modification statements,
and distribution conditions including provider notification, links, credit and logo;
the latter permit use/modification but prohibit redistribution. Free website access
and Open Database status are different. No blanket CC grant is assigned to BioCyc.
No form submission, provider contact, account, credential, session, authenticated
data download or fixture was acquired. Qualify the exact requested database and
applicable subscription/API/data conditions before implementing its access.

Preserve native database/organism identity and release, frame types and IDs,
original gene/protein/reaction/pathway relations, stoichiometry/direction, qualifiers
and source support. Preserve independent relation occurrences. A pathway name,
caller accession or shared external-ID label must not manufacture membership,
upstream/downstream order, biological evidence or a universal curated class.

## OMIM: gene/locus, phenotype and allelic-variant scopes stay independent

The old `map_omim` accepted synthetic `associations` or `results` and attached a
protein accession. Its MIM numbers, phenotype, inheritance, mapping key and
publication pointers are useful, but fallback association IDs and a universal
curated class supply no native identity or biological scope. No native OMIM client
was found in the preserved source module.

The provider-authored [resource paper](https://academic.oup.com/nar/article/43/D1/D789/2439148)
describes registered API keys and separate downloads, including `mim2gene`,
`genemap2`, `morbidmap` and full native entries. This is a historical description,
not qualification of today's authenticated response. The maintained
[NCBI resource page](https://www.ncbi.nlm.nih.gov/omim) still points to OMIM's own
site and API. Direct public agreement/API-documentation requests returned HTTP 403;
the web reader was denied by robots. Those are access failures, not source absence.
The current [agreement](https://omim.org/help/agreement), registration and exact
authorized release/API contract remain requirements. No key, account, restricted
data, third-party replacement export or public fixture was used.

Recover requirements for original MIM identity and entry type, independent gene/locus
and phenotype identifiers, source mapping keys and literal inheritance, record
qualifiers, source dates/revisions and publication support. Native phenotype-map
declarations differ from allelic variants and narrative text. Do not attach gene
or locus knowledge to proteins/isoforms, interpret mapping keys as clinical ranks,
merge disease rows or infer pathogenicity/clinical recommendations.

## Interactome3D: the old requests do not match the documented API

The preserved `fetch_interactome3d` sent `queryProt=<accession>` to both endpoints.
The [official API documentation](https://interactome3d.irbbarcelona.org/help.php)
instead specifies `getProteinStructures?uniprot_ac=<accession>` and
`getInteractionStructures?queryProt1=<accession>&queryProt2=<accession>`.
A protein lookup and an exact interaction-pair lookup are distinct operations;
the old combined single-accession request cannot claim both succeeded.

The old XML helper discarded the root version and flattened child attributes.
`map_interactome3d` then used generic lower-case keys, fallback PDB-based IDs,
caller scope and one inference class. Restore neither without a native response.
Documentation describes 14 protein columns and 22 interaction columns, original
structure/model/domain-model labels, rank pairs, template/PDB/chain/model/biological
unit context, participant-specific identity/coverage/bounds and filenames. Complete
and representative exports differ; a representative result is not full coverage.
Reported aligned endpoints are explicitly insufficient to infer exact full-chain
residue correspondence. The XML root's database version is not sequence revision.

The correctly parameterized P60174 HTTPS probe and a direct help-page probe both
failed at TLS connection establishment. An additional HTTP probe timed out without
a body; HTTPS verification was not disabled. The web reader could return official
help/about text, but no native API record was qualified. This does not establish
resource retirement or a biological no-result. The
[provider page](https://interactome3d.irbbarcelona.org/about.php) identifies the
owning group but did not establish a separate data reuse agreement in this review.
No fixture, coordinate file, model generation, docking or interaction discovery
was performed. Qualify the corrected query, native identity/version/coverage,
independent occurrences and contributing-resource rights before integration.

## PDBTM: preserve source-chain axes, transforms and the embedded agreement

The old `map_pdbtm` expected synthetic JSON entries and attached the caller's
accession. Useful membrane/chain/segment/orientation requirements survive, but
that input did not qualify structure numbering, sequence identity or transforms.
No native PDBTM fetcher was found in the preserved source client.

The current [provider site](https://pdbtm.unitmp.org/) and
[downloads](https://pdbtm.unitmp.org/downloads) were readable through curl.
They display database label `20250404` and server label `v.1.1.2`; those are
separate from an individual record, PDB or sequence revision. The
[manual](https://pdbtm.unitmp.org/documents) describes TMDET placement, manual
validation and a membrane transformation matrix. Source prediction/curation
context is useful without creating MOLI Evidence or a universal inference class.

A public [native 1c3w XML record](https://pdbtm.unitmp.org/api/v1/entry/1c3w.xml)
was received: **6866 bytes**, SHA-256
`37ae24e30f12457eb91fb9198c5a7a6643e46e33efa0c039048784ff5b7ac55e`.
The exact first retrieval time is unrecorded. Its XML declares ISO-8859-1,
a provider namespace and schema, entry ID/TMP flag,
creation/modification history, raw result labels, biological matrices, a membrane
normal/transform and three chain occurrences. Each chain retains its own sequence,
type, TM count and 15 regions with separate `seq_beg/end` and `pdb_beg/end`.
These are endpoints on the source's axes, not a constant-offset map, a current
UniProt coordinate axis or a cross-chain identity merge. Native history dates do
not establish the revision of the current sequence. Matrix/normal components remain
unprojected until axes and physical units are qualified.

The record embeds its own copyright/use statement: nonprofit-institution use is
conditional on retaining unchanged content and the statement; commercial use needs
a licence agreement. This is not CC BY or a general open-data grant. Qualification
must cover raw retention, redistribution and derived representations explicitly;
do not remove the statement or ship a transformed record under Sabueso's MIT.
The body remains an unmodified `/tmp` probe, not package data. No coordinates,
sequence projection, membrane prediction job or automatic card intake is added.

## TCDB: multiple assignments and mixed accession namespaces are native

The old `map_tcdb` copied caller-supplied `classifications` or `results`, attached
the protein accession and used the TC number as record identity. That would collapse
independent occurrences and supplies no native accession/namespace qualification.
There was no native TCDB fetcher in the old source client.

The [official download page](https://tcdb.org/download.php) links separate current
exports for accession-to-TC assignments, family definitions, substrates/ChEBI,
RefSeq, superfamilies, GO, PDB and Pfam. Exports are regenerated from current
information; the page's FASTA modification label is not the mapping-table release.
The public [accession assignment table](https://tcdb.org/cgi-bin/projectv/public/acc2tcid.py)
was received: **486702 bytes**, **24956** headerless two-column TSV rows, SHA-256
`c59e2b2c5293e0f33e75bcc0bf89e0eb6988be54fb7f2121935749bda3feef8a`.
The first row is data, not a header. No independent database total or scientific
revision is declared by this body; exact first retrieval time was not recorded.

The received table contains **129 accessions with multiple row occurrences**,
including two exactly repeated pairs. O00337 has two distinct TC assignments;
P08183 has one, and P60174 is not listed. Native identifiers include UniProt-like,
versioned/unversioned RefSeq and other protein accessions. Do not label every first
column UniProt, strip versions, normalize away duplicates or infer that an absent
accession is not a transporter. Exact assignment does not establish substrate,
mechanism, transporter/auxiliary role, experimental support, species or sequence
revision. Separate linked exports need their own native identity/coverage/support.

The provider's home/download/footer text states CC BY-SA 3.0 and GFDL for website
text. It does not explicitly scope that grant to all mapping/sequence exports or
provide a full database-rights statement there. Do not transfer a software licence,
article licence or a catalogue's database-licence label to the received file.
Before fixture distribution and intake, record the applicable mapping-export grant
and obligations together with the native namespace/version policy. The body stays
in `/tmp`; no BLAST, transporter prediction, sequence acquisition or automatic
protein-card enrichment is performed.

## Next batch and retention

The next five unreviewed candidates are **MetalPDB, ECOD, 3did, DrugCentral and
GWAS Catalog**. Seven more follow: ChannelsDB, PRIDE, CIViC, CASTp, ProBiS, FDA
Orphan and EMA Orphan. Continue in batches of five. Thirteen reviewed candidates
from the first three batches still require integration, independently of those 12.
This batch is a completed review, not five delivered connectors or a decision to
discard their useful requirements. Do not drop the stash while recovery and its
durable checkpoint remain outstanding.
