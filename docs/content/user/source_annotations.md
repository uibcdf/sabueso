# Reading source annotations and correspondences

The native reader/mapping extensions described here are delivered in 0.14.0.
Code delivery does not publish protected original qualification inputs, grant
reuse rights or establish current live health or automatic card enrichment.
References to local/unreleased qualification describe those inputs and receipts.

These examples describe the API delivered in 0.14.0. Some native readers require an
original input supplied by the user under its applicable terms; their test inputs
are kept local and are absent from a public checkout. Check the input scope in
{doc}`source_capabilities` before running a fixture example.

## Additional UniProt annotations in development

Published card schema 0.3.13 retains UniProt activity regulation, domain notes,
similarity, source cautions and miscellaneous text with independent source support.
Source cautions are descriptive annotations; similarity does not establish identity.
It also retains positional domains, chains, lipidation, motifs, regions, sequence
conflicts, topological domains and transmembrane features.

```python
from sabueso.tools.db.uniprot import create_protein_card_from_file

card = create_protein_card_from_file("temp_data/P52789.json", retrieved_at="fixture")
domains = card.get("features_positional.domains")
assert len(domains["value"]) == 2
assert any(
    item["field_path"] == "features_positional.domains"
    for item in card.get_residue(16)["annotations"]
)
```

Original bounds/modifiers, source molecule scope, ECO support and sequence revision
remain available. A residue view leaves uncertain or missing intervals, unidentified
isoform numbering and known sequence-revision mismatches unplaced. The annotations
remain stored with support. Published 0.3.12 cards retain their original schema;
explicit migration lists refresh gaps rather than inventing the new knowledge.

## ChEBI native chemical descriptions

```python
from sabueso.tools.db.chebi import FixtureChEBIClient
from sabueso.mappings.chebi import map_chebi_identity

answer = FixtureChEBIClient().compounds(["CHEBI:28445"])
mapping, key = map_chebi_identity(answer["compounds"]["CHEBI:28445"], "2026-09-30")
assert mapping["fields"]["names.canonical_name"] == "vincristine"
assert mapping["fields"]["properties.physchem.formula"] == "C46H56N4O10"
```

Native names and formulas have separate ChEBI SourceAssertions with original
spelling, record and subject support. Optional `chebi=True` molecule-card enrichment
joins only through a matching source-stated standard InChIKey. Names or formulas
never establish identity. Source conflicts remain visible beside selected values;
missing descriptors stay unstated and invalid native types fail explicitly.
Curation stars and modified dates are source metadata, not project Evidence or a
scientific dataset release.

## FDA OOPD page declarations

```python
from sabueso.tools.db.fda_orphan import FixtureFDAOrphanClient, get_page
from sabueso.mappings.fda_orphan import map_page

assertions = map_page(get_page("106597", client=FixtureFDAOrphanClient()))
assert len(assertions) == 4  # One designation and three marketing-approval tables.
assert assertions[0]["subject_ref"] == "fda:oopd_page:106597"
```

The locator identifies a requested source page; FDA's HTML does not echo it or
establish a stable designation, product or protein identity. Source declaration
tables retain independent occurrences, literal dates, N/A, blank exclusivity
fields, repeated name strings and sponsor qualifiers. There is no brand-to-approval
reconstruction, clinical conclusion, modality or protein target assignment.
Online, fixture, bound HTML/gzip/hash/time and original-response replay preserve
support. Missing/error/form responses are not empty designation results. Dataset
and record revisions are unknown; search and database completeness are unqueried.
The FDA website policy allows public-domain reuse unless otherwise noted, with
independent contributing-source and other rights retained. Credit and the original
page URL/date are requested. This does not borrow openFDA's CC0 grant.

The received original pages and supplied-artifact reader are qualified. A later
live check through Sabueso's shared transport receives HTTP 404; restored automated
access is not claimed. Imported-original replay is separate from a new live GET.

## TTD native target listing

```python
from sabueso.tools.db.ttd import FixtureTTDClient, get_target_listing
from sabueso.mappings.ttd import map_target_listing

assertions = map_target_listing(get_target_listing("T59130", client=FixtureTTDClient()))
assert assertions[0]["subject_ref"] == "ttd:target:T59130"
assert assertions[0]["asserted_value"]["UNIPROID"] == "TPIS_PLAFA"
```

The native target name calls this bacterial while its entry name differs in scope;
that inconsistency stays in original support. No accession, taxonomy or protein
identity is repaired. Header release is known independently of target/UniProt
revision. Type labels and placeholders stay source declarations. Data use/sharing
remain unknown; original factual qualification stays local unreleased.

## iPTMnet native substrate report

```python
from sabueso.tools.db.iptmnet import FixtureIPTMnetClient, get_substrate_report
from sabueso.mappings.iptmnet import map_substrate_report

assertions = map_substrate_report(
    get_substrate_report("P60174", client=FixtureIPTMnetClient())
)
assert len(assertions) == 72
```

Three distinct source groups retain 62/7/3 rows, original site/type/score labels
and all hidden source/PMID support. Missing sites, score0 and repeated/conflicting
rows survive. Group tabs do not establish canonical sequence identity; no site
projection, guessed curation status, score recalculation or enzyme/source/PMID
pairing is added. Other report sections remain unqueried. Dataset/sequence/scoring
revisions are unknown; per-request form fields are not scientific releases.
Online, fixture, bound HTML/gzip/hash/time and exact archive replay preserve
original support. Database terms are CC BY-NC-SA 4.0 with independent input rights.

## BRENDA EC-class descriptions

```python
from sabueso.tools.db.brenda import FixtureBrendaClient, get_enzyme_class
from sabueso.mappings.brenda import map_enzyme_class

assertions = map_enzyme_class(get_enzyme_class("5.3.1.1", client=FixtureBrendaClient()))
assert assertions[0]["subject_ref"] == "brenda:ec:5.3.1.1"
assert assertions[0]["asserted_value"]["label"]["value"] == "triose-phosphate isomerase"
```

The class label, systematic name and description are source RDF statements.
Language/datatype nodes, empty literals, missing optional fields and repeated
solutions keep their original support. No EC/activity is assigned to a protein,
kinetic quantity inferred or card automatically enriched. Prototype revision is
unknown. An empty query response differs from failed access. BRENDA data terms
are CC BY 4.0 with provider and publication attribution.

## Pharos target development context

```python
from sabueso.tools.db.pharos import FixturePharosClient, get_target
from sabueso.mappings.pharos import map_target

assertions = map_target(get_target("P60174", client=FixturePharosClient()))
```

The native response identifies TPI1, family Enzyme and target development level
`Tbio`; AKT1 (`P31749`) has `Tchem`. These remain the provider's literal classes.
No druggability ranking is calculated. Names and gene symbols do not establish
identity independently of the explicit source accession. A native null target
means no match in the received query; an access or GraphQL error remains a failure.
Only five selected fields are read, with unknown scientific and TDL-rule revisions.
Omit the fixture client for public API access. Separate data reuse terms remain unstated.

## DepMap public cell-model context

```python
from sabueso.tools.db.depmap import FixtureDepMapClient, get_model
from sabueso.mappings.depmap import map_model

assertions = map_model(get_model("ACH-000019", client=FixtureDepMapClient()))
```

The source's ModelID identifies MCF7 in the fixed **24Q4** public release, article
version 1. The reader checks all 2105 original CSV rows before exact ID selection.
Names, disease labels, RRIDs and catalog references remain source descriptions;
shared names do not merge models. Each occurrence retains its original row and
full-file support. The selected article states CC BY 4.0 and must be credited.
Gene effects, dependency scores, screens and growth conditions require separate
readers. Model metadata alone do not establish essentiality or a protein target.

## Interactome3D representative protein structures and models

```python
from sabueso.mappings.interactome3d import map_protein_structures
from sabueso.tools.db.interactome3d import (
    FixtureInteractome3DClient,
    get_protein_structures,
)

envelope = get_protein_structures("P60174", client=FixtureInteractome3DClient())
assertions = map_protein_structures(envelope)
```

This development example validates all **18000** original rows in the archived
human representative protein table. P60174 has one native Structure, PDB `1wyi`,
chain A and source sequence endpoints 2–249. Identity and coverage are quantities
in percent (100.0 and 99.6), qualified by the native column documentation. The
reported endpoints do not establish an exact full-chain residue correspondence
or current canonical placement. For `Q8WZ42`, all thirty selected occurrences
survive: a representative set can include several partial structures/models.

Each standalone assertion retains its native row/line/full-export hash, rank pair,
structure/model label, PDB/template case, chain and filename. Blank/whitespace
chains stay unchanged. Negative and other score strings remain original source
literals; a template PDB does not state a model's experimental method. Filenames
are pointers and are not downloaded.

Live access omits the fixture client; one public native metadata GET and zero-
network archive replay retain original text/hash/time. The qualified release is
`2024_12`; its selected archive route does not pin native/PDB/sequence revisions.
Complete tables and interaction pairs remain separate. Not listed here is not
biological absence. No coordinates, model/alignment jobs or automatic enrichment.
Separate data grant is NOT-STATED; original factual qualification stays local
unreleased with automated sharing unknown and contributing rights independent.

## ProBiS reference-chain catalog

```python
from sabueso.mappings.probis import map_chain_catalog
from sabueso.tools.db.probis import FixtureProBiSClient, get_chain_catalog

envelope = get_chain_catalog("5a2q.h", client=FixtureProBiSClient())
assertions = map_chain_catalog(envelope)
```

This development example keeps **three** independent native listing occurrences
from all **42270** validated rows. Each keeps five original strings, including
padded columns, its native line and the full-export hash. Columns 1/2/5 have
unqualified meanings; they do not become cluster sizes, indices, weights or scores.
Chain case is exact: `5a2q.H` is not listed. The documented alignment example
`1ytb.B` is also not listed, whereas `1ytb.A` is. No repair or representative
relation is inferred from either result; not listed is not biological absence.

For live access omit the fixture client. One native static catalog GET and
zero-network archive replay retain full original export, hashes and genuine time.
The dated filename is an artifact label; scientific/PDB/sequence revisions and
current database coverage remain unknown. Failed/malformed acquisition differs
from a validated not-listed result. Alignment service access, binding sites,
ligand/function transfer, protein identity and automatic card enrichment remain
outside this catalog reader. No coordinates or computation jobs are acquired.

The official public catalog has no separately qualified data grant. Terms remain
NOT-STATED, with original factual qualification local unreleased and automated
sharing unknown. Software/article and input rights stay independent.

## PDBTM native chain topology

```python
from sabueso.mappings.pdbtm import map_topology
from sabueso.tools.db.pdbtm import FixturePDBTMClient, get_topology

envelope = get_topology("1c3w", client=FixturePDBTMClient())
assertions = map_topology(envelope)
```

The development example retains **three** chain occurrences and **45** regions.
Each occurrence keeps XML-decoded sequence text, source chain/type/TM-count strings
and independent sequence/PDB endpoint strings. Identical sequences and generated
chains remain separate. PDB bounds differ nonuniformly from sequence bounds;
they do not establish an offset map, current protein axis, orientation or function.

The entire unchanged original XML and COPYRIGHT support every occurrence. Native
ISO-8859-1 bytes/hash are distinct from XML character decoding and supplied gzip
identity. Source history/site labels do not pin current PDB/sequence revisions.
Matrices and raw scores stay uninterpreted in the original document, with
units/axes unqualified. No coordinates, transform execution, membrane calculation
or automatic card enrichment is added.

The embedded statement conditions nonprofit use on unchanged content/copyright,
and commercial use on an agreement. Automated use/sharing is unknown; original
qualification stays local unreleased. Public redistribution needs separate review.

## 3did domain-motif structural instances

```python
from sabueso.mappings.threedid import map_motif_interactions
from sabueso.tools.db.threedid import FixtureThreeDIDClient, get_motif_interactions

envelope = get_motif_interactions("7m5l", client=FixtureThreeDIDClient())
assertions = map_motif_interactions(envelope)
```

The full native DMI export supplies six independent instances for this PDB entry,
including PCNA_C and PCNA_N motifs. Each retains its original domain/motif source,
opaque pattern/date, PDB chain/bounds, motif sequence, contextual contact count and
topology. The first occurrence has motif bounds `E:2-11`, sequence `QCSMTCFY` and
count `0`: those source declarations stay independent. PDB bounds do not specify
a contiguous sequence slice. Repeated lowercase chain tokens, duplicates and
conflicts are retained without repairs. Patterns are never executed as searches.

For live access omit the fixture client. One existing export GET, bound text/gzip
snapshots and archive replay retain full original support, raw/decoded hashes and
time. The mutable current route and pattern dates do not state scientific/PDB/
Pfam/sequence revisions. No protein identity, function, method or MOLI Evidence
is inferred; no coordinates, linked inputs or card enrichment are acquired.
This is local unreleased development behavior with separate export terms
NOT-STATED, 3did/IRB Barcelona attribution and independent native input rights.
Domain-domain residue contacts and HMM profile interfaces remain separate scopes.


## HPO gene/disease phenotype annotations

```python
from sabueso.mappings.hpo import map_gene_annotations
from sabueso.tools.db.hpo import FixtureHPOClient, get_gene_annotations

envelope = get_gene_annotations("7167", client=FixtureHPOClient())
assertions = map_gene_annotations(envelope)
```

This dated `v2026-09-01` fixture retains 44 TPI1 annotations on `ncbigene:7167`.
Each keeps its original disease and frequency: hypotonia occurs with `1/2` for
`OMIM:615512` and `HP:0040281` for `ORPHA:868`. These are independent disease
annotation representations; they do not estimate gene penetrance or diagnose an
individual. A missing `-` is unknown, not zero. Symbols and term names are literal.
Every received row validates before selection, with full unchanged export, native
line/hash/release/time and acquisition support. No ancestors or protein/isoform
identity are inferred. For live access omit the fixture client; an exact dated
release selects one existing export. Bound TSV/gzip snapshots and replay preserve
original support without fetching publications or original contributor inputs.

This is local unreleased development behavior. Credit the HPO Consortium and
preserve the original file and release version. Custom HPO terms require unchanged
content/logical relationships; input rights remain separate. Automated use and
sharing verdicts remain unknown. Detailed contributors, publications, modifiers,
individual revisions and whole current-database completeness are unstated.


## MEROPS native classification assignments

```python
from sabueso.mappings.merops import map_assignments
from sabueso.tools.db.merops import FixtureMEROPSClient, get_assignments

envelope = get_assignments("swissprot:P29466", client=FixtureMEROPSClient())
assertions = map_assignments(envelope)
issues = envelope["representation_issues"]
```

The selected native occurrence declares family `C14A` and taxonomy literal `9606`
on `merops:accession:swissprot:P29466`. Native prefixes are not rewritten into
UniProt/protein identity. Family membership does not assert enzyme activity,
inhibitor role or substrate cleavage. Original row/hash/time, duplicates and
conflicts, versioned/case-sensitive/quoted literals and blank/space taxonomy survive.
The full export retains three displaced four-column rows and a quoted accession.
These have explicit representation issues, without inferred column or identity
repairs. `selection_complete=False` means an unmatched literal is uncertain;
`truncated=False` describes retained raw lines, not complete interpreted knowledge.

For live access omit the fixture client. One GET retrieves the full existing
export; bound native TSV/gzip and replay preserve original hashes/time and exact
source/query scope. Scientific revisions remain unknown. No sequence/family linked
request, search/job, coordinate projection or automatic enrichment occurs.
MEROPS declares GNU Library GPL without a version. Local unshared qualification
keeps original data/notices; sharing and automated use verdicts stay unknown.
This is development behavior with local unreleased qualification artifacts.

## MetalPDB native metal sites

```python
from sabueso.mappings.metalpdb import map_sites
from sabueso.tools.db.metalpdb import FixtureMetalPDBClient, get_site

envelope = get_site("12ca_2", client=FixtureMetalPDBClient())
assertions = map_sites(envelope)
```

This record retains one native Zn site and three His ligand/donor occurrences
on `metalpdb:site:12ca_2`. Geometry, coordination count, representative false,
PDB numbers and chain literals remain explicit. Donor distances carry angstrom
quantity nodes: the public Coordination Sphere states Distance (Å), with displayed
values matching the API at three decimals. Full API precision remains intact.
The UniProt field stays a pointer; missing metal chain/model/assembly/insertions
and scientific/sequence revisions are not filled. No physiological relevance,
catalytic mechanism, protein identity, canonical residue placement, coordinate
acquisition, geometry job or automatic card intake is inferred. Bound JSON/gzip
snapshots and one-GET replay retain hashes/time/support. Terms remain NOT-STATED;
original factual bytes and the unit-table excerpt stay local unreleased recovery.


## ECOD experimental domains

```python
from sabueso.mappings.ecod import map_domain
from sabueso.tools.db.ecod import FixtureECODClient, get_domain

envelope = get_domain("80374", client=FixtureECODClient())
assertions = map_domain(envelope)
```

This native record identifies domain `e1iepA1`, with hierarchy through family
`206.1.1.20`, on `ecod:uid:80374`. Source PDB/chain and UniProt pointers remain
explicit. Range `A:228-498` stays literal; its axis and sequence revision are
unstated, so it does not place canonical residues. False manual/representative
flags survive. The experimental-structure label is the provider's origin context.
No protein identity, function, experimental method or MOLI Evidence is inferred.
Only this domain is queried; AlphaFold domains, other partitions, coordinates,
FASTA and search/computation remain unqueried. Optional bound JSON/gzip snapshots
and archive replay retain source hash/time. Separate data terms are NOT-STATED;
the original factual fixture remains local unreleased recovery.


## TCDB native assignments

```python
from sabueso.mappings.tcdb import map_assignments
from sabueso.tools.db.tcdb import FixtureTCDBClient, get_assignments

envelope = get_assignments("Q39253", client=FixtureTCDBClient())
assertions = map_assignments(envelope)  # two independent native TC assignments
```

For live access omit the fixture client. One GET receives the full native export,
validates every row and selects exact accession text. Case and version suffixes
matter: the reader does not assume UniProt or RefSeq identity. Duplicate pairs and
multiple assignments remain separate; TC codes with an extra component stay literal.
The full export retains rows whose accession is blank, explicitly unbound. Selection
not-listed does not mean biological absence or an unavailable export.

Assignments do not supply substrate, mechanism, transporter role, taxonomy or
sequence. No family or sequence record, search/job or automatic card enrichment is
requested. Received export coverage is separate from current database completeness;
scientific revisions are unstated. Query-bound native TSV/gzip files retain caller
declarations and original hashes/time without treating the first row as headers.
Export-specific data terms remain NOT-STATED; the original public factual fixture
is local unreleased recovery, with website-text and input-resource rights separate.

## ChannelsDB PDB annotations

```python
from sabueso.mappings.channelsdb import map_annotations
from sabueso.tools.db.channelsdb import FixtureChannelsDBClient, get_annotations

envelope = get_annotations("1tqn", client=FixtureChannelsDBClient())
assertions = map_annotations(envelope)  # one entry and 22 UniProt-group occurrences
```

For live access omit the fixture client. One GET receives existing entry function,
reaction and name literals plus independent ChannelsDB/UniProt residue comments.
Original references, HTML entities, chain labels and residue IDs remain unchanged;
repeated or conflicting declarations are retained. Equal numbers do not establish
a common numbering axis, tunnel membership or canonical protein location. The
UniProt pointer does not merge PDB/protein identity. No channel geometry, assembly,
coordinates, calculation or automatic card enrichment is requested. Source revisions
are unknown; full received DTO coverage is separate from database completeness.
Query-bound supplied JSON/gzip clients retain caller declarations and original hash/
time. The small public fixture remains local unreleased work: separate data reuse
permission is not established (`NOT-STATED`).

## ChannelsDB native tunnel membership

```python
from sabueso.mappings.channelsdb import map_channel_memberships, map_channel_annotations
from sabueso.tools.db.channelsdb import get_channels

channels = get_channels("1tqn", client=FixtureChannelsDBClient())
memberships = map_channel_memberships(channels)  # 26 native channel occurrences
comments = map_channel_annotations(channels)  # 7 independent reference/comment rows
```

Each membership assertion preserves a native channel header, ResidueFlow,
HetResidues and every layer's Residues/FlowIndices arrays. The public 1tqn response
contains 910 layers across twelve categories. The original lists remain independent
and literal, including repeated labels, Backbone tokens and differences between
MOLE/CAVER. In CAVER data, the field called HetResidues can include ordinary residue
labels; this reader does not classify its members chemically. Residue/index lists
can differ in length and membership and are not zipped, repaired or deduplicated.

Separate annotation rows retain their names, descriptions and native references;
equal IDs do not attach them to a channel or merge occurrences. Source categories,
Type and Auto literals do not assign an experimental or Evidence class. No residue
token is interpreted as a canonical protein position. Chain/numbering/model/assembly/
sequence context and scientific revisions remain unknown. Geometry and physical
properties stay in the unchanged original DTO and are not mapped by these functions.
No structure-coordinate download, analysis job, preferred-assembly lookup or
automatic card enrichment. The URL or supplied declaration binds the PDB context,
not an echoed structure ID. JSON/gzip snapshots retain original file hash, declared
time/terms and separate local read time. Data sharing remains unknown (NOT-STATED).

## GWAS Catalog association pages

```python
from sabueso.mappings.gwas_catalog import map_associations
from sabueso.tools.db.gwas_catalog import FixtureGwasCatalogClient, get_associations

envelope = get_associations("HBB", limit=2, client=FixtureGwasCatalogClient())
assertions = map_associations(envelope)
assert envelope["truncated"] is True  # two associations out of native total 279
```

For live access omit the fixture client. The reader requests one standard mapped-
gene page, using the literal symbol, `extended_geneset=false`, a size from 1 to
500 and optional zero-based `page`. The size cap belongs to this reader. Native
row symbols, counts and official-host page links must agree with the request;
links are retained without automatic continuation. Each received association
keeps its own study, traits, alleles, location strings and original statistics.
The mapped/nearest gene annotation does not establish a causal gene or a protein
identity. Repeated or conflicting records remain independent occurrences.

Mantissa/exponent and the supplied numeric p-value remain separate; the reader
does not recalculate, rank or round them. Effect/range/frequency text stays native,
without guessing physical units, assembly or a clinical interpretation. Native
zero, null, missing and empty values remain distinct. TPI1's zero-result page is
a filter result rather than a claim that the gene has no associated traits.

Use `SnapshotGwasCatalogClient(path, source_metadata={"source": "GWAS Catalog",
"kind": "mapped_gene_associations", "query": envelope["query"]},
expected_sha256=...)` for original JSON/gzip with exact page binding. Supplied time
and terms stay declared; no new remote access is credited. API v2 and mapping dates
are separate from unknown dataset/association/assembly/sequence revisions. Manual
pages do not have a pinned ordering/revision guarantee. EMBL-EBI terms retain
original-owner rights; summary-statistics CC0 is separate. No linked study, variant,
summary-statistics file, article, job or automatic card intake is added.

## Monarch associations about original entities

```python
from sabueso.tools.db.monarch import FixtureMonarchClient, get_associations
from sabueso.mappings.monarch import map_associations

envelope = get_associations("HGNC:12009", limit=2, client=FixtureMonarchClient())
assertions = map_associations(envelope)
assert envelope["truncated"] is True  # two rows out of native total 232
```

The reader requests one exact direct-subject CURIE page, with a limit from 1 to 500
and an optional nonnegative offset. For live access omit the fixture client. It
keeps all returned categories and row occurrences, including original/normalized
entities, negation/qualifiers, primary/aggregator sources and native knowledge/agent
labels. `direct=true` controls exact subject matching; it does not assert binding.
ECO pointers remain source declarations. Gene relationships are not transferred
to proteins or isoforms. Totals/cuts describe one page; later pages are explicit
requests, without a stable ordering or pinned KG revision guarantee across them.

Use `SnapshotMonarchClient(path, source_metadata={"source": "Monarch", "kind":
"associations", "query": envelope["query"]}, expected_sha256=...)` for original
JSON/gzip with exact page binding. Original time and native revisions remain unknown
unless declared. Input-specific rights survive; the BioGRID-only fixture's MIT
notice does not grant rights to arbitrary graph sources or linked publications.

## PRIDE Archive project metadata

```python
from sabueso.tools.db.pride import FixturePrideClient, get_project
from sabueso.mappings.pride import map_project

envelope = get_project("PXD013616", client=FixturePrideClient())
assertion = map_project(envelope)[0]
assert assertion["subject_ref"] == "pride:PXD013616"
```

One original project JSON retains native depositor descriptions/protocols, CV
objects, taxonomy categories, publication/date labels, licence and administrative
counts. The native PARTIAL submission label does not mean the metadata reader cut
the response. Protocols remain text; no physical values or biological results are
extracted from them. Listed modifications/instruments do not establish particular
protein/peptide observations or current canonical residue positions.

`SnapshotPrideClient(path, source_metadata={"source": "PRIDE", "kind": "project",
"query": envelope["query"]}, expected_sha256=...)` binds original JSON/gzip to the
exact project and optional byte hash. The PXD013616 fixture declares CC0; each other
project's native terms must be considered independently. API/route/date labels
are separate from unknown dataset/sequence revisions. No title/protein search,
linked file/peptide/protein download, analysis job or automatic card enrichment is
performed. PeptideAtlas/ProteomicsDB data from Proteins API keep their actual origins.

## OmniPath aggregate interaction declarations

```python
from sabueso.tools.db.omnipath import FixtureOmniPathClient, get_interactions
from sabueso.mappings.omnipath import map_interactions

envelope = get_interactions("P60174", client=FixtureOmniPathClient())
assertions = map_interactions(envelope)
row = assertions[0]["asserted_value"]
# row["is_stimulation"] == False; row["is_inhibition"] == True
# row["sources"] == ["SPIKE", "SPIKE_LC"]
```

The development reader receives one human `omnipath` dataset query for an exact
base UniProt partner, using the explicit academic licence filter. All received rows
are validated, retained and mapped independently on native ordered-pair subjects.
Stimulation, inhibition and consensus are independent booleans; opposing effects,
duplicate occurrences and original resource-prefixed references survive.

Source/dataset filters select aggregate interactions and can retain annotations
from other resources or datasets. The reader keeps this original support without
reconstructing strict source-only evidence. An HTTP-200 application error is a failed
query; a native empty array is empty within the requested scope. Neither supplies
a biological negative claim or complete current database coverage.

Dataset/interaction revisions and observed participant taxonomy are unstated.
Human request scope does not identify sequences or establish direct binding or an
experimental class. Mouse/rat orthology translation is not requested. Snapshots use
`SnapshotOmniPathClient(path, source_metadata={"source": "OmniPath", "kind":
"interactions", "query": envelope["query"]}, expected_sha256=...)` for original
JSON/gzip with exact scope, optional original-byte hash and declared original time.

OmniPath input resources have individual reuse terms. The access filter is not a
grant. The SPIKE/SPIKE_LC-only fixture has separately documented CC BY 4.0 terms
in `temp_data/NOTICE.md`, with resource/contributor attribution. Arbitrary responses
retain unknown source-wide sharing rights and require input-specific qualification.

## WikiPathways cross-references

```python
from sabueso.tools.db.wikipathways import (
    FixtureWikiPathwaysClient,
    get_pathways_by_xref,
)
from sabueso.mappings.wikipathways import map_pathway_cross_references

envelope = get_pathways_by_xref("uniprot:P60174", client=FixtureWikiPathwaysClient())
pathways = map_pathway_cross_references(envelope)
```

The example retains nine source pathway declarations from all 2218 native fixture
rows, on independent pathway subjects. Namespaced references are matched exactly;
original aliases, unexpected column prefixes, species, authors and pathway date
labels survive. No species filter or gene/protein identity merge is inferred.

These are source-served cross-references. The provider's export has unique/compact
xref groups and descriptions shortened to 200 characters; it does not supply every
GPML-node occurrence, pathway role, mechanism or experimental participation.
Pathway edit-date labels do not establish dataset/GPML/sequence revisions.
Online and bound JSON/gzip snapshots retain original hash/time and replay without
fetching links. WikiPathways content is CC0; retain source/author attribution.


## EMA orphan-designation pages

```python
from sabueso.tools.db.ema_orphan import FixtureEmaOrphanClient, get_designations
from sabueso.mappings.ema_orphan import map_designations

envelope = get_designations("EU/3/23/2858", client=FixtureEmaOrphanClient())
declarations = map_designations(envelope)
```

The reader retains the complete native export and validates all rows and its
stated total before selecting the exact EU number. This example keeps two separate
pages and dates. Substance/medicine names, product references, intended use and
procedural status stay as the source states them. A designation does not by itself
establish marketing authorisation, efficacy, drug modality or protein identity.

Original page occurrences, missing-number literals and empty fields survive.
File generation and row dates stay separate from actual retrieval time; scientific
revisions are unknown. Online access and bound supplied JSON/gzip use the same
scope; replay retains the original response/time without new network calls.
[EMA-owned material requires acknowledgement in every copy](https://www.ema.europa.eu/en/about-us/about-website/legal-notice),
with third-party and linked-document rights separate.

## CIViC monthly molecular-profile items

```python
from sabueso.tools.db.civic import FixtureCIViCClient, get_molecular_profile_items
from sabueso.mappings.civic import map_molecular_profile_items

envelope = get_molecular_profile_items(
    "12", release="01-Oct-2026", client=FixtureCIViCClient()
)
items = map_molecular_profile_items(envelope)
```

The reader validates the full monthly export before selecting the exact source
profile. Profile 12 retains 93 BRAF V600E items, including both Supports and
Does Not Support directions. Profiles combining variants and therapy combinations
remain complete. Disease, significance, rating/level, citations/trials, original
review dates and accepted/flagged status are retained without consensus or treatment
recommendations. Not-listed differs from failed access or a negative association.

Online access uses the same explicit release. Supplied native TSV/gzip files bind
source, profile, dataset and release; replay keeps original bytes/time and release.
The monthly label does not establish entity/sequence revision. CIViC content has
[CC0](https://docs.civicdb.org/en/latest/about/faq.html#how-is-civic-licensed);
original citations and linked-publication rights remain separate.


Development DrugCentral supplies independent native drug-target observations with
full raw activity/MOA/source context and original composite-target scope. It does
not infer potency, molecule identity, clinical effects or automatic card enrichment.
Data retains [DrugCentral CC BY-SA 4.0](https://drugcentral.org/privacy), original
provider attribution, modification notices and applicable share-alike.

## ClinGen gene-disease validity declarations

```python
from sabueso.tools.db.clingen import FixtureClinGenClient, get_gene_validity
from sabueso.mappings.clingen import map_gene_validity

envelope = get_gene_validity("HGNC:1100", client=FixtureClinGenClient())
curations = map_gene_validity(envelope)
```

The reader retains the full original CSV and validates every received row before
selecting the exact gene. The frozen public export has 3702 curations. BRCA1 has
two declarations with distinct diseases, inheritance and SOP/date context; both
survive independently. Classification, expert panel, original report and date stay
native, without a strongest-class selection, numeric rank or protein/variant merge.
Legacy report namespaces and dates without timezone are retained. File creation and
classification dates are not retrieval times or dataset/gene/sequence revisions.

TPI1 is not listed in this received export. This differs from a row explicitly
classified No Known Disease Relationship, a missing file or failed access. No
independent database total is stated; no clinical recommendation is generated.

`SnapshotClinGenClient(path, source_metadata={"source": "ClinGen", "kind":
"gene_validity", "query": {"hgnc_id": "HGNC:1100", "dataset":
"gene_disease_validity"}, "retrieved_at": None}, expected_sha256=...)` reads
original native CSV/gzip with exact binding and optional original-byte SHA.
Its source-specific parser keeps the CSV preamble; the generic snapshot reader
expects a first-row header. Supplied metadata adds no remote access credit.

[ClinGen's curated content is CC0](https://clinicalgenome.org/docs/terms-of-use/),
with source/access-date attribution requested. Linked reports and publications are
not acquired and retain separate rights. Dosage sensitivity, actionability, variant
interpretation, sequence placement and automatic card enrichment are separate scopes.

## Human Protein Atlas categorical gene summaries

```python
from sabueso.tools.db.hpa import FixtureHpaClient, get_gene_profile
from sabueso.mappings.hpa import map_gene_summary

envelope = get_gene_profile("ENSG00000111669", client=FixtureHpaClient())
summary = map_gene_summary(envelope)
```

HPA's [single-gene JSON route](https://www.proteinatlas.org/about/download)
returns a subset of search data. The native TPI1 response contains 22 categorical
RNA/protein declarations; each retains its original field name/value and support
on a source-gene subject. Missing categories and explicit nulls remain distinct.
A gene label or UniProt reference does not merge gene and protein/isoform identity.
The reader retains all raw context. Quantitative nTPM/nCPM/pTPM, intensity, blood
concentration, score and prognostic fields are not normalized by this mapping.
This access is not full tissue or assay coverage. Native dataset/gene/sequence
revisions remain unknown; no website release is assigned as a record revision.

`SnapshotHpaClient(path, source_metadata={"source": "Human Protein Atlas",
"kind": "gene_profile", "query": {"gene_id": "ENSG00000111669", "format":
"single_gene_json_subset"}, "retrieved_at": None}, expected_sha256=...)` accepts
original native JSON/gzip, exact query binding and optional original-byte SHA.
Caller metadata does not establish a new remote acquisition. Failed access and
missing files do not mean absence of expression. Categories remain standalone
assertions; no automatic card enrichment occurs. [HPA CC BY 4.0](https://www.proteinatlas.org/about/licence)
retains attribution and third-party input constraints. Credit the resource,
specific gene/data URL and appropriate primary publications.

## Original SIGNOR causal interaction declarations

Development SIGNOR access reads one exact base UniProt accession and an explicit
organism request (9606, 10090 or 10116), preserving every original headerless row:

```python
from sabueso.tools.db.signor import get_relations
from sabueso.mappings.signor import map_relations

envelope = get_relations("P60174", taxon_id=9606)
relations = map_relations(envelope)
```

The HsTIM fixture contains three declarations, including the first row describing
SRC regulating TPI1. Regulator A, regulated B, causal effect/mechanism, DIRECT,
score, publication and residue/sequence/modification context stay native. Each
occurrence has separate response/index support. These declarations do not become
generic physical binding relationships, experimental classes or current sequence
positions. Complexes and protein families are not expanded into member interactions.

Requested organism is separate from each returned TAX_ID. The native AKT1 fixture
requested with 9606 includes other taxa, blank context and in-vitro -1. No returned
species is changed or filled from the request. Dataset/record/sequence/score
revisions and independent result totals are unstated; the website's release number
is not assigned to individual rows. The exact `No result found.` response means
no result for that source query, distinct from a failed request or biological absence.

`FixtureSignorClient` reads the frozen native responses.
`SnapshotSignorClient(path, source_metadata={"source": "SIGNOR", "kind":
"causal_relations", "query": {"accession": "P60174", "requested_organism": 9606},
"retrieved_at": None}, expected_sha256=...)` reads original headerless TSV or gzip,
with exact source/query binding and optional original-byte SHA-256 verification.
It inserts no header. Supplied metadata stays caller-declared without remote credit.

[SIGNOR's official CC BY 4.0 statement](https://signor.uniroma2.it/documentation/)
requires attribution, a licence link and indication of modifications. Original
publication pointers and source-served sentences retain their context; underlying
articles and input resources keep independent rights and are not acquired. No
network/pathway expansion, calculation job or automatic card enrichment occurs.

## Native APPRIS declarations for an explicit human gene

Development APPRIS access preserves the complete received provider-default
exporter for one exact human Ensembl gene, without collapsing repeated transcripts:

```python
from sabueso.tools.db.appris import get_gene_annotations
from sabueso.mappings.appris import map_annotations

envelope = get_gene_annotations("ENSG00000111669")
annotations = map_annotations(envelope)
```

The frozen public TPI1 response has 1010 rows, 60 principal-isoform declarations
and 21 distinct transcript references. The same transcript can have different
names, genomic coordinates or principal labels in different occurrences. Each
row retains its original source/method, score, flags and notes with response/hash
support. No declaration overwrites another, and no principal isoform is selected.
Genomic coordinates and `pep_position` notes remain source context. Assembly,
dataset, transcript and sequence revisions are unstated in the returned rows;
those coordinates are not placed on a current UniProt sequence or card.

`FixtureApprisClient` reads the frozen native response.
`SnapshotApprisClient(path, source_metadata={"source": "APPRIS",
"kind": "gene_annotations", "query": {"gene_id": "ENSG00000111669",
"species": "homo_sapiens", "filters": "provider_default"},
"retrieved_at": None}, expected_sha256=...)` accepts native JSON/gzip with exact
binding and optional original-byte verification. Supplied metadata remains caller
declared; it creates no remote access credit. Missing files and HTTP failures stay
separate from an explicitly empty received array. No dataset completeness is claimed.

[APPRIS's stated CC BY-NC-SA 4.0 licence](https://appris.bioinfo.cnio.es/partials/license.html)
requires noncommercial use, attribution and share-alike for adaptations. These
obligations remain attached to source terms and archive retention. Linked methods,
input sequences and publications retain independent rights and are not acquired.

## An explicitly selected Complex Portal declaration

```python
from sabueso.tools.db.complex_portal import FixtureComplexPortalClient, get_complex
from sabueso.mappings.complex_portal import map_complex, map_participants

record = get_complex("CPX-14819", client=FixtureComplexPortalClient())
complex_context = map_complex(record)
participants = map_participants(record)
```

This native complex contains public HsTIM among five participants. Its source
prediction flag is true, its ECO code is `ECO:0008004`, and stoichiometry is null.
The reader preserves those declarations and confidence stars without inferring
experimental support or probability. Cofactors, nested complex/set references,
isoforms, native features and unknown ranges retain their original context.
Membership does not become a binary interaction or canonical sequence placement;
linked feature objects may be absent from the received response. Native release
dates are separate from unknown complex/participant sequence revisions.

For an arbitrary supplied JSON/gzip file use
`SnapshotComplexPortalClient(path, source_metadata={"source": "Complex Portal",
"kind": "complex", "query": {"complex_id": "CPX-14819"}}, expected_sha256=...)`.
The optional SHA-256 checks original bytes; source/query metadata remains caller-
declared. Native primary identity and full response shape are validated. These
are standalone source assertions; card intake and linked-resource queries are
not automatic. [Provider data terms](https://raw.githubusercontent.com/Complex-Portal/complex-portal-documentation/master/about/license_privacy.md)
explicitly cover service data under CC0 1.0.

## An explicitly selected CATH domain

Development CATH domain access reads one explicit structural domain on a fixed
release route. Its assertion preserves classification, separate ATOM/COMBS sequences
and original residue/segment numbering, including unresolved PDB locations and
discontinuous segments. Native GO/EC context does not identify the domain with a
UniProt protein or independently establish function. Requested release and unknown
response/sequence revisions stay distinct; no canonical residue offset is inferred.

```python
from sabueso.tools.db.cath import FixtureCathClient, get_domain_summary
from sabueso.mappings.cath import map_domain

record = get_domain_summary("1htiA00", "v4_4_0", client=FixtureCathClient())
domain_assertions = map_domain(record)
```

For a supplied JSON/gzip file at an arbitrary path, use
`SnapshotCathClient(path, source_metadata={"source": "CATH", "kind": "domain_summary",
"query": {"domain_id": "1htiA00", "release": "v4_4_0"}}, expected_sha256=...)`.
The optional digest verifies original file bytes; metadata is caller-declared,
and the reader validates native source identity/shape. These remain standalone
assertions, without automatic card intake or coordinate downloads.

Development source access returns independent source records and
SourceAssertions. Their coordinates, annotation bases and missing information
remain explicit. These tools do not enrich cards automatically.

## An explicitly selected UniProt isoform sequence

```python
from sabueso.tools.db.uniprot import get_isoform_sequence, FixtureUniProtIsoformClient
from sabueso.mappings.uniprot_isoforms import map_isoform_sequence

record = get_isoform_sequence("P60174-3", client=FixtureUniProtIsoformClient())
assertions = map_isoform_sequence(record)
assertions[0]["asserted_value"]["length"]  # 286
assertions[0]["source_metadata"]["native_isoform_declaration"]["name"]["value"]  # '2'
```

Omit the fixture client to read the full parent JSON and one selected native FASTA.
The [native isoform ID](https://web.expasy.org/docs/userman.html#CC_line) is independent
of its name: HsTIM names `1`, `2`, `3` correspond to `P60174-1`, `P60174-3`,
`P60174-4`, with native lengths 249, 286, 167. Request an explicit ID; the helper
never guesses from names or queries every isoform automatically.

Every parent declaration is checked before selection. Missing/partial declaration
scope is `not_stated`; an ID not listed in explicit declarations is `not_declared`
in that parent observation. Neither makes a speculative FASTA query or claims
biological absence. External, not-described and unknown sequence statuses retain
parent context without following sequence references. Unavailable files and HTTP
failures remain separate, including a successful parent observation before a
failed sequence request.

Native `Displayed`/`Described` declarations permit one selected sequence request.
The [qualified reviewed-isoform FASTA format](https://www.uniprot.org/help/fasta-headers)
must name that exact ID. Multiple records, canonical fallback, gaps, stops and
sequence repair are refused. Displayed sequences must equal the parent sequence.
Described VAR_SEQ pointers remain native context; the helper does not reconstruct
variants, establish atomic parent/FASTA revision equivalence or infer residue offsets.

Parent JSON and FASTA retain independent times/hashes. Parent entry version 212,
canonical sequence version 4 and database release 2026_03 remain separate from an
unknown isoform sequence revision. The provider's alternative-isoform FASTA format
does not carry canonical `PE`/`SV` fields. Data retain [UniProt CC BY 4.0](https://rest.uniprot.org/help/license).

On an existing HsTIM card, pass the original assertions to the residue reader:

```python
view = card.residue_knowledge(
    3, sequence_ref="UniProt:P60174-3", source_assertions=assertions
)
view["amino_acid"]  # 'E', on this isoform; canonical position 3 is 'P'
view["stored_annotations"]  # None: canonical annotations are not projected
```

This reads the supplied sequence with original support. It does not change the card,
add a persisted field or acquire other knowledge. Existing exact-sequence candidates
and implicit resolution remain canonical-only.

## SWISS-MODEL Repository models and experimental references

```python
from sabueso.tools.db.swissmodel import get_metadata, FixtureSwissModelClient
from sabueso.mappings.swissmodel import map_structures

record = get_metadata("P60174", client=FixtureSwissModelClient())
structures = map_structures(record)
len(structures)  # 30 independent occurrences: 29 PDB, one SWISSMODEL
model = next(
    a
    for a in structures
    if a["asserted_value"]["native_structure"]["provider"] == "SWISSMODEL"
)
model["asserted_value"]["native_structure"]["template"]  # '4poc.1.A'
model["source_metadata"]["sequence"]["value"]  # returned source sequence
```

Omit the fixture client to query the [public metadata API](https://swissmodel.expasy.org/repository/api-docs).
The full unfiltered response retains every provider, target sequence, chain and
alignment. The P60174 fixture contains 57 paired alignments. Target peptides match
the returned source sequence; template/PDB numbering keeps its native basis. Native
entry/isoform references do not establish current UniProt sequence equivalence.

Each `native_structure` preserves provider/method/template, target bounds, coverage,
oligomer, scores and ligand/complex context. QMEAN stays a score dictionary. Missing,
null, zero and negative scores remain distinct; no probability, ranking or quality
class is derived. Raw ligand/complex labels do not establish target binding.

The native MD5 hashes the **full target sequence**, rather than an individual model.
Independent occurrences survive even when hashes/templates coincide. The sequence
axis includes its SHA-256. CRC64 stays a source literal and is not recomputed.
Coordinate/ModelCIF links are [mutable download pointers](https://swissmodel.expasy.org/docs/repository_help),
not immutable model IDs or acquired files. Native API/query/model-creation/PDB-release
dates remain separate from unknown record/model/sequence revisions. Explicit empty
structure arrays, unavailable files and failed requests stay distinct.

No linked coordinates, templates, sequences or publications are queried. Source
data retain [CC BY-SA 4.0 attribution and share-alike](https://swissmodel.expasy.org/docs/terms_of_use);
parent PDB/UniProt and publication rights remain separate. Acquisition includes
the resource and modelling citations and original query/time/hash; source mapping
creates no new acquisition credit or automatic card enrichment.

## AmyPro aggregation regions on an investigated sequence

```python
from sabueso.tools.db.amypro import get_entry, FixtureAmyProClient
from sabueso.mappings.amypro import map_entry, map_regions

record = get_entry("AP00015", client=FixtureAmyProClient())
context = map_entry(record)
regions = map_regions(record)
print(len(record["record"]), len(regions))  # 125, 3
print(context[0]["asserted_value"]["uniprot_id"])  # P37840
print(regions[0]["asserted_value"]["location"]["sequence"])
# {"sequence_id": "AmyPro:AP00015", "indexing": "1-based", "start": 35, "end": 44}
```

Omit the fixture client to read the [official JSON export](https://amypro.net/data/amypro.json).
Each request receives and validates the whole export, then selects one exact AmyPro
ID. The [provider help](https://amypro.net/#/help) documents downloads;
individual `.json` entry downloads currently contain Python literals, so this client
uses the valid full export. No script or literal expression is evaluated.

The entry assertion preserves the investigated sequence, native category and prion
strings, parent UniProt bounds, mutations and publication/PDB pointers. Regions
match that investigated sequence and retain independent native region IDs, including
equal or overlapping declarations. Entry subjects remain `amypro:<ID>`; a parent
pointer does not merge identities. AP00007 describes processed lactoferrin with
parent bounds 20–710: its region 538–545 stays on the 691-residue AmyPro sequence.
AP00012's parent bounds and sequence length disagree; no offset is applied.

Native PubMed references support the entry context. The export supplies no
per-region publication/method assignment, so it does not gain an inferred
experimental class. The [resource paper](https://doi.org/10.1093/nar/gkx950) describes
database curation separately. Linked articles, parent sequences and coordinates
are not queried. Empty region dictionaries retain the entry assertion; a missing
entry is only not listed in this received export. No native total or current export,
entry or sequence revision is supplied. Original hashes/times and supplied-file
receipts remain explicit, and archive replay preserves original access time.

Separate data reuse rights remain unstated. Open download and the resource paper's
licence do not establish permission to redistribute the export.

## Direct IntAct interaction observations

```python
from sabueso.tools.db.intact import get_interactions, FixtureIntActClient
from sabueso.mappings.intact import map_interactions

record = get_interactions("P60174", client=FixtureIntActClient())
observations = map_interactions(record)
print(record["scope"]["total_results"], len(observations))  # 80, 80
print(observations[0]["asserted_value"]["native"]["confidence"])
# author score:LacZ4|intact-miscore:0.37
```

Omit the fixture client to query IntAct's current PSICQUIC endpoint. One first page
is read with a caller limit of 1–200, using MIQL `id:<accession>` and MITAB 2.7.
The [MIQL reference](https://psicquic.github.io/MiqlReference27.html) defines the
primary/alternative ID columns searched by `id`. The connector verifies the exact
requested `uniprotkb` reference there; aliases, xrefs and equal identifiers in
another namespace cannot bind the query. Explicit isoforms remain distinct.

Each result occurrence keeps all [42 native MITAB columns](https://psicquic.github.io/MITAB27Format.html),
including methods, publications, participants/roles, host, negation, complex
expansion, features, dates and scores. The fixture has 67 spoke expansions and
13 records with no expansion stated. Its types include association, physical
association and proximity; these observations do not establish direct binding.
The negative flag remains literal, including `-`, without an invented declaration.

Original text and count/service headers remain with observed/returned/query-total
counts under `intact_mitab_page@1`. Smaller caps preserve and validate the full
supplied page, marking truncation. The [REST specification](https://psicquic.github.io/PsicquicSpec_1_4_Rest.html)
defines pagination; this connector leaves later pages unqueried. The 200-row ceiling
belongs to Sabueso. Counts describe query rows, not unique partners or complete
biological coverage. Missing count, malformed pages, missing fixtures and HTTP
errors never become a biological negative.

Record/sequence revisions are unknown, separately from service versions and dates.
Parameter text and confidence retain source meaning; no unit, probability,
experimental class or canonical feature placement is inferred. Linked articles,
sequences and coordinates are unqueried. Original fixture retrieval time is unknown;
supplied body/header hashes and local read time are explicit. Archive replay keeps
the original time. The [official IntAct data terms](https://www.imexconsortium.org/about/#licence)
state CC BY 4.0 for MITAB/service data; linked articles keep their own rights.

## AlphaFill model ligand context

```python
from sabueso.tools.db.alphafill import get_metadata, FixtureAlphaFillClient
from sabueso.mappings.alphafill import map_model, map_transplants

record = get_metadata("P60174", client=FixtureAlphaFillClient())
models = map_model(record)
transplants = map_transplants(record)
print(models[0]["asserted_value"]["model_id"], len(transplants))
# AF-P60174-F1, 86
print(transplants[0]["asserted_value"]["local_rmsd"])
# {"value": 0.178902, "unit": "angstrom"}
```

Omit the fixture client to read the existing public metadata. The model assertion
describes the declared AFDB fragment; transplant assertions have that model as their
subject. Their predictions do not establish experimental binding to the target.
Each alternative keeps native `compound_id` and `analogue_id` without inferring
chemical equivalence. Model placement and donor author/label chain numbers remain
distinct; native alignment starts, including zero, are not converted into canonical
UniProt positions. No sequence revision or coordinate equivalence is assumed.

Global/local RMSD and transplant clash score carry explicit angstrom quantity nodes,
as defined by the [AlphaFill method](https://www.nature.com/articles/s41592-022-01685-y).
The full original clash distances, PAE and optional validation remain source context;
missing and null stay distinct. Native software/run date does not identify the
unknown record revision or a current AlphaFold model. Source file paths remain
literal metadata; coordinates and jobs are not requested. The
[provider API](https://alphafill.eu/man/alphafill-api/) describes the separate routes.
The served schema differs from actual native fields, so the connector validates the
supported payload directly and never silently rewrites it.

The [AlphaFill data terms](https://alphafill.eu/license) allow use/redistribution with
acknowledgement and the parent AlphaFold conditions. Software licensing is separate.

## LIGYSIS segment binding-site summaries

```python
from sabueso.tools.db.ligysis import get_result_page, FixtureLigysisClient
from sabueso.mappings.ligysis import map_sites

record = get_result_page("P60174", segment=1, client=FixtureLigysisClient())
sites = map_sites(record)
print(
    [(s["asserted_value"]["site_id"], s["asserted_value"]["site_size"]) for s in sites]
)
# [(0, 20), (1, 7)]
print(sites[0]["asserted_value"]["relative_solvent_accessibility"])
# {"value": 21.1, "unit": "percent"}
```

The segment is required explicitly. Online access reads one public result HTML page,
and the fixture retains the unchanged native HTML and original byte hash. The parser
reads six inline JSON declarations under `ligysis_result_literals@1`; it executes no
JavaScript and loads no scripts or assets. Changed layouts, duplicate declarations,
expressions, non-finite JSON and inconsistent identity/counts/membership fail closed.
The original exact remote retrieval time of this fixture is unknown; its local
read time is recorded separately under `sabueso.ligysis_supplied_html@1`.

Assertions retain the complete site's residue membership, native cluster and DS/MES/FS
scores. RSA is a percent quantity; native `"NaN"` remains explicit in source metadata
and has no quantity value. A zero is still a stated score. The provider's
[help](https://www.compbio.dundee.ac.uk/ligysis/help) explains these quantities and
that arbitrary site IDs do not express functional importance. No local functional
classification is calculated. Source sequence and revision are unstated, so native
residue numbers never become canonical locations. The initially displayed residue
table covers one site; it is not treated as the full set of binding residues.

The initial residue-panel literals can also be read from this same record:

```python
from sabueso.mappings.ligysis import map_displayed_residues

residues = map_displayed_residues(record)
print(len(residues))  # 20 rows in the preserved public fixture
print(residues[0]["asserted_value"]["native_fields"]["UPResNum"])  # 12
print(residues[0]["asserted_value"]["relative_solvent_accessibility"])
# {'value': 1.11, 'unit': 'percent'}
```

These independent source-scoped assertions retain column order, UPResNum/MSACol,
AA/SS and DS/MES/p literals, percent RSA, repeated row occurrences and original
page support. `"NaN"` and zero remain distinct. This is the initial displayed
table; its selected site is not identified by its literals or inferred by matching
residue sets. Other site tables remain unqueried. An empty displayed table does not
establish an absence of binding residues in the segment. No current canonical
location or significance class is assigned, and no card is modified.

The same preserved page also contains directed residue correspondence dictionaries:

```python
from sabueso.mappings.ligysis import map_residue_correspondences

correspondences = map_residue_correspondences(record)
print(
    [
        (
            a["asserted_value"]["native_direction"],
            a["asserted_value"]["native_chain_key"],
            a["source_metadata"]["received_pair_count"],
        )
        for a in correspondences
    ]
)
# [('Pdb2UpDict', 'A', 245), ('Pdb2UpDict', 'B', 246),
#  ('Up2PdbDict', 'A', 245), ('Up2PdbDict', 'B', 246)]
```

Each assertion retains one full native directed structure/chain dictionary and its
original support. Parent/key case, signed/zero labels and pair order remain literal;
opposite directions are not reconstructed, merged or repaired if they disagree.
Both directions come from the same page. The page query does not establish which
protein belongs to each chain. Chain-to-accession identity, chain/numbering namespaces,
insertion codes and scientific revisions remain unknown. These declarations are
source context for later qualified mapping, with no current-sequence placement.

For an explicit structure, a separate original mapping response supplies declared
chain identities and native remappings:

```python
from sabueso.tools.db.ligysis import get_structure_mapping
from sabueso.mappings.ligysis import map_structure_mapping

mapping = get_structure_mapping("P60174", 1, "7t0q", client=FixtureLigysisClient())
mapping_assertions = map_structure_mapping(mapping)
print(len(mapping_assertions))  # 14: four directed tables, two identities, eight remaps
```

`chain2acc` explicitly declares A and B as P60174 in this native response; each
declaration retains its own identity basis. Both residue directions name 7t0q.
Protein/segment request context is not echoed, and unrelated/isoform accessions
remain literal when a source declares them. Chain tables need not have the same
parents; declarations are not merged to fill gaps or repair contradictory mappings.
The response does not state chain2acc/residue namespaces, insertion codes or
scientific revisions. The current provider code describes the remapping direction,
but does not version this dataset. This newer response is kept separate from the
older HTML and does not establish a current canonical residue location.

Native segment totals describe nine ligands and eight structures, but their records,
other segments and coordinates remain unqueried. The website's free/commercial access,
MIT software and paper rights do not establish data redistribution permission;
the [source terms](https://www.compbio.dundee.ac.uk/ligysis/about) stay `NOT-STATED`.

## Disorder and modified residues from MobiDB

```python
from sabueso.tools.db.mobidb import get_annotations, FixtureMobiDBClient
from sabueso.mappings.mobidb import map_disorder_regions, map_modified_residues

record = get_annotations("P60174", client=FixtureMobiDBClient())
disorder = map_disorder_regions(record)
modifications = map_modified_residues(record)
print(record["version"], len(disorder), len(modifications))  # 7.0, 30, 19
```

Omit the fixture client to query the current public API. The v1 JSON export retains
the original source sequence, release, annotation sets, regional provenance,
residue arrays, measurement definitions and representation issues. Export
counts and continuation headers are validated; an unconsumed page fails instead
of appearing complete. API version `v1` is separate from database release `7.0`
and release period `2026_07` in these fixtures.

Each mapped interval keeps `provider_basis` exactly as MobiDB states it: curated,
derived, homology or prediction, or unknown when unstated. Homology never becomes
curation. PTM labels keep their complete native text; MobiDB explicitly states
that the original evidence for these UniProt modification records was not retained.
Those records are not independently verified experimental findings.

`mobidb_valid_region_sets@1` excludes annotation sets with reported representation
issues; those sets and issues remain in the full export. Missing intervals never
become inferred positive regions. Series remain separate: the AlphaFold-disorder
series in these records describes smoothed relative solvent accessibility, not
`1 - pLDDT` or a calibrated disorder probability. No new scores are calculated.

Mapped positions refer to `MobiDB:P60174` and its complete original sequence/hash.
An accession or identical sequence does not place them on a current UniProt card.
The detached residue reader supports an explicitly selected MobiDB axis:

```python
view = card.residue_knowledge(
    1, sequence_ref="MobiDB:P60174", source_assertions=disorder
)
```

This example requires a card whose exact subject is `uniprot:P60174`. The default
canonical view reports the MobiDB intervals as unmapped. No ontology identifier
is invented for MobiDB's native `feature="disorder"` declaration.

## Source-declared structure correspondences from SIFTS

```python
from sabueso.tools.db.sifts import get_mappings, FixtureSIFTSClient
from sabueso.mappings.sifts import map_sequence_mappings

record = get_mappings("1HTI", client=FixtureSIFTSClient())
segments = map_sequence_mappings(record)
print(len(segments))  # 2 native chain segments
```

Each assertion has the structure subject `pdb:1HTI`, with the native UniProt
reference, entity, author chain, label asym ID, UniProt range and PDB endpoints.
Internal residue numbers, author numbers and insertion codes stay distinct.
Endpoint ranges are source claims; they do not justify extrapolating a linear
offset through gaps or reconstructing individual residue mappings. All native
protein and isoform references remain separate. The response states neither a
SIFTS release nor a referenced UniProt sequence revision; those gaps stay unknown.

An explicit empty mapping collection is distinct from a missing fixture or a failed
API route. Built-in clients for both resources support shared HTTP archive replay
with original retrieval times and the required scope headers. Reading fixtures or
mapping saved envelopes does not claim a new remote acquisition.

## EPPIC residue detail for a selected interface

```python
from sabueso.tools.db.eppic import get_interface_residues, FixtureEPPICClient
from sabueso.mappings.eppic import map_interface_residues

record = get_interface_residues("1HTI", interface_id=1, client=FixtureEPPICClient())
residues = map_interface_residues(record)
print(len(residues))  # 496 per-side rows, including zero buried area
print(residues[0]["asserted_value"]["native_chain"])  # B
print(residues[0]["asserted_value"]["accessible_surface_area"])
# {"value": 123.05148315429688, "unit": "angstrom ** 2"}
```

Omit the fixture client to read native interface context and the selected residue
table (two GETs). An interface ID is required explicitly; it must exist in the
received context before residue access. Context and detail retain separate original
times/hashes, rather than implying one atomic calculation revision. Other interface
details, assemblies, sequences, coordinates and jobs remain unqueried.

The source maps `side=False` to `chain1` and `side=True` to `chain2`. Equal serials
or chain names on the two sides do not merge their occurrences; native interface
and symmetry-operator context stay attached. In the supplied 1HTI interface 1,
248 rows refer to B and 248 to A. The table includes zero buried areas, surface/
other regions and 44 literal `"NaN"` fractions; it is not a list declaring that
all 496 residues are contacts. Native region codes and entropy scores are preserved,
including unknown codes and sentinels, without a new biological classification.

The provider's [residue service](https://github.com/eppic-team/eppic/blob/b5fd5b39a9f63383c48d16cf4719ad9f15e44d43/eppic-rest/src/main/java/eppic/rest/service/JobService.java)
and [data adaptor](https://github.com/eppic-team/eppic/blob/b5fd5b39a9f63383c48d16cf4719ad9f15e44d43/eppic-cli/src/main/java/eppic/DataModelAdaptor.java)
document native serials and the ambiguous basis when SEQRES is missing. These numbers
never become canonical UniProt, author/insertion or label positions. Source sequence,
record and calculation revisions are unknown; matching another source's number does
not establish correspondence. ASA/BSA retain EPPIC's BioJava surface-area convention
as square-angstrom quantities; original numeric values remain in native metadata.

Explicit empty arrays differ from unavailable fixtures, malformed rows and failed
HTTP. A failed second request retains the successful context receipt. Original fixture
retrieval is unknown, independently of its original byte hash and local read time.
The existing [EPPIC data terms](https://www.eppic-web.org/downloads) remain `NOT-STATED`;
software and paper licences are not substituted for prediction-data rights.

## Entry-wide validation metrics from PDBe

```python
from sabueso.tools.db.pdbe_validation import (
    get_global_percentiles,
    FixturePDBeValidationClient,
)
from sabueso.mappings.pdbe_validation import map_global_percentiles

record = get_global_percentiles("1HTI", client=FixturePDBeValidationClient())
metrics = map_global_percentiles(record)
print(len(metrics))  # 3 native metrics, each about pdb:1HTI
```

Omit the fixture client to query the current API. Every assertion retains the
native metric name and `native_values`: `rawvalue`, `absolute`, and `relative`
when present. `absolute` compares against the archive; `relative` compares against
comparable entries, such as similar-resolution X-ray structures. Percentile ranks
keep the native 0–100 scale. They are not raw outlier percentages or probabilities.
See the [PDBe API](https://www.ebi.ac.uk/pdbe/api/) and
[wwPDB validation guide](https://www.wwpdb.org/validation/2016/XrayValidationReportHelp).

The 1CBS fixture has five metrics, including a raw RSRZ-outlier value of `0.0`
with percentiles of `100.0`, and DCC R-free `0.1871`. The 1HTI response omits
those two metrics. Missing values stay unstated rather than becoming zero.
The response does not state validation software/statistical revisions or comparison
population counts. Its raw metric definitions remain native; no units, experimental
method, aggregate score, quality class or automatic structure choice is invented.
Metrics concern the structure entry, without per-residue or protein projection.

Native response fixtures keep original byte hashes and unknown exact original
retrieval times. Built-in online/archive replay retains actual observed acquisition
and original times. An empty entry metric object differs from a missing fixture or
failed API route. Reviewed [EMBL-EBI terms](https://www.ebi.ac.uk/about/terms-of-use/)
remain distinct from a separately unestablished API-response licence; PDBe-KB
terms are not transferred to these responses.

## EPPIC interface and assembly interpretations

```python
from sabueso.tools.db.eppic import get_annotations, FixtureEPPICClient
from sabueso.mappings.eppic import map_interfaces, map_assemblies

record = get_annotations("1HTI", client=FixtureEPPICClient())
interfaces = map_interfaces(record)
assemblies = map_assemblies(record)
print(len(interfaces), len(assemblies))  # 9, 3
print(interfaces[0]["asserted_value"]["area"])
# {"value": 1683.6265653733565, "unit": "angstrom ** 2"}
```

The bundle contains three unchanged native responses with separate original
acquisitions, retrieval times and hashes. These separate accesses do not establish
an atomic snapshot or a shared calculation revision. The entry identifies the exact PDB parent
and run parameters. Each interface retains chain names/operators and literal method
scores/calls/reasons. Scores from different methods are not interchangeable; native
`-1.0` sentinels remain literal rather than becoming probabilities. Areas carry
explicit square-angstrom units, as the official EPPIC interface table states.

Assemblies retain alternatives and unit-cell ID `0`, native composition, cluster
references and EPPIC/pdb1 calls. EPPIC assembly IDs are not wwPDB assembly IDs.
Provider interpretations do not establish experimental confirmation or automatically
select an assembly. Source coordinate/chain context does not establish current
UniProt placement. Interface residue and coordinate endpoints are unqueried.
The native exhaustive-enumeration flag remains separate from `truncated=False`,
which describes absence of a client output cap. A later component failure raises
with earlier acquisition receipts instead of fabricating an empty or complete bundle.

See [EPPIC downloads](https://www.eppic-web.org/downloads) and its
[method description](https://github.com/eppic-team/eppic). The response states no
prediction-record revision: EPPIC version/build `NA`, UniProt run version and entry
releaseDate remain separate native context. A prediction-data reuse licence is not
established; software and served API licences are not transferred to these data.

## Existing PDB-REDO refinement and version context

```python
from sabueso.tools.db.pdb_redo import (
    get_entry,
    get_versions,
    FixturePDBRedoClient,
)
from sabueso.mappings.pdb_redo import map_refinement, map_versions

record = get_entry("1CBS", client=FixturePDBRedoClient())
refinement = map_refinement(record)
versions = get_versions("1CBS", client=FixturePDBRedoClient())
provenance = map_versions(versions)
print(refinement[0]["asserted_value"]["r_factor_stages"])
```

The stages keep original deposited, Refmac baseline, restrained-refinement and final
PDB-REDO R-factor keys independently. Null, zero and unstated fields remain distinct.
They do not assert a calculated improvement or replace the deposited model. Full
other native properties and original/redo residue-angle arrays remain in the source
record and assertion metadata. No units are guessed for unprojected properties.

`versions.json` is a separate explicit query, retaining input revisions and every
software version/use flag. Native pipeline `8.22` and entry creation date `2026-09-02`
are not a databank-record revision. The response does not establish the current
original-PDB revision. No coordinates are downloaded, coordinate URLs fabricated,
models merged or new refinement jobs submitted. A missing fixture is unavailable;
HTTP errors, including 404/500, are failed access rather than proven record absence.

See the official [download descriptions and native schemas](https://pdb-redo.eu/download).
The [usage policy](https://pdb-redo.eu/license) permits commercial/non-commercial use
and redistribution of original files; modified files require parent attribution,
and parent PDB conditions apply where applicable. Recorded terms use
`FREE-WITH-ACKNOWLEDGEMENT`, preserving these conditions without assigning a CC licence.

## GlyGen glycosylation and phosphorylation

```python
from sabueso.tools.db.glygen import get_protein, FixtureGlyGenClient
from sabueso.mappings.glygen import map_glycosylation, map_phosphorylation

record = get_protein("P60174", client=FixtureGlyGenClient())
glycosylation = map_glycosylation(record)
phosphorylation = map_phosphorylation(record)
assert len(glycosylation) == 3
assert len(phosphorylation) == 13
```

Omit `client` to request the public protein-detail record. The response declares
an explicit source sequence. Current online health remains unqualified: the public
native download succeeded, but subsequent built-in 30/60-second checks and repeated
curl access timed out. The fixture example above is qualified offline.

The HsTIM fixture declares
canonical accession P60174-1 and its full sequence. Both modification tables must
contain exactly the row counts stated in `section_stats`; missing tables and cut
responses fail validation. Other response sections remain raw and unqualified.
Explicit empty tables produce zero modification assertions while retaining the
received protein record.

Each annotation keeps native category, residue, peptide, glycan/kinase context and
original support pointers. A peptide in `site_seq` is distinct from `residue`.
Reported, predicted, text-mined and unknown categories stay literal; none becomes
an inferred experimental or curated class. Alternative glycan annotations remain
separate, including one without a stated GlyTouCan accession. Row index/hash
locators distinguish annotations without claiming provider-assigned site IDs.

Single positive sites within the stated sequence carry `GlyGen:P60174-1` coordinates.
Ranges, missing/sentinel and out-of-axis numbers stay in `native_annotation`
without single-residue placement. HsTIM's first two glycosylation annotations
describe a provider correspondence from P60174-3 residue 233 to P60174-1 residue 196;
the original comment survives. Sabueso does not reconstruct the isoform or establish
equivalence to a current UniProt sequence. These PTM assertions are not yet admitted
by the current residue-knowledge view and do not automatically enrich a card.

Introduction history mentioning release 1.8.25 is distinct from the unknown current
record/sequence revision. Listed iPTMnet, GlyTouCan and publication pointers are
source declarations; no linked resource is requested. Fixtures retain original
byte hashes and unknown original retrieval time; archive replay preserves original
live time and adds no fresh remote credit.

See the [GlyGen glycosylation guide](https://wiki.glygen.org/index.php/Protein_details/Glycosylation)
and official [protein API implementation](https://github.com/glygener/glygen-backend-api/blob/master/glygen/protein.py).
The [GlyGen licence](https://www.glygen.org/license.html) applies CC BY 4.0 to database
sets; contributing-source and publication rights remain separate. Direct iPTMnet now has a scoped original HTML report reader. Earlier REST HTTP 503
failures remain independent; GlyGen pointers themselves do not establish successful
direct iPTMnet acquisition or canonical sequence correspondence.

## Inspecting the maintained source catalog

```python
from sabueso.tools.sources import get_catalog

catalog = get_catalog()
profile = catalog["profiles"]["structures_models"]
print(profile["in_use"], profile["other_statuses"])
```

`registry_catalog@1` groups the maintained registry by category and status. Each
resource retains its access route, modules or indirect provider, terms, limitations
and adoption reason. Recorded default limits are generated from the code constants.
The catalog is packaged JSON and works offline without loading the developer-guide
YAML. It reports repository decisions rather than live health or complete scientific
coverage. A profile does not activate sources, run queries or turn deferred resources
into implemented connectors.

Native fixtures and hashes are declared in `temp_data/NOTICE.md`. MobiDB content
uses [CC BY 4.0](https://mobidb.org/about#license). SIFTS links to
[EMBL-EBI terms](https://www.ebi.ac.uk/about/terms-of-use/); this review did not
establish a separate SIFTS-wide reuse licence. Original owners' rights and underlying
provider publications remain separate.

## Read a saved original response

Saved files can use the same native readers as live responses. Choose a client
and declare the exact source, record kind and query that produced the file:

| Client in `sabueso.tools.db` | Source / kind | Exact query | File format |
|---|---|---|---|
| `alphafill.SnapshotAlphaFillClient` | `AlphaFill` / `metadata` | `{"accession": "P60174"}` | JSON |
| `glygen.SnapshotGlyGenClient` | `GlyGen` / `protein` | `{"accession": "P60174"}` | JSON |
| `sifts.SnapshotSIFTSClient` | `SIFTS` / `mappings` | `{"pdb_id": "1hti"}` | JSON |
| `ligysis.SnapshotLigysisClient` | `LIGYSIS` / `result_page` | `{"accession": "P60174", "segment": 1}` | HTML |
| `ligysis.SnapshotLigysisClient` | `LIGYSIS` / `structure_mapping` | `{"accession": "P60174", "segment": 1, "pdb_id": "7t0q"}` | JSON |

```python
from sabueso.tools.db.glygen import get_protein, SnapshotGlyGenClient
from sabueso.mappings.glygen import map_glycosylation

client = SnapshotGlyGenClient(
    "temp_data/glygen/protein__P60174.json",
    source_metadata={
        "source": "GlyGen",
        "kind": "protein",
        "query": {"accession": "P60174"},
        "retrieved_at": None,
        "version": None,
    },
)
protein = get_protein("P60174", client=client)
glycosylation = map_glycosylation(protein)
```

Every listed format also supports gzip. When you know the original file's hash,
pass it as `expected_sha256`; it covers original compressed bytes before decoding.
The receipt records the hash and a separate local read time. Set `retrieved_at` to
the original retrieval time only when known. Leaving it unknown does not replace
it with today's time. These pathways require `version=None` because their native
scientific revisions remain unqualified; model run and API versions stay separate.

The declaration binds context and is recorded as caller supplied. Each native
reader still checks the file content. A correct hash alone cannot qualify a wrong
protein, structure, segment or malformed response. File reading makes no source
requests, and declared terms grant no additional permission. Returned standalone
assertions retain source support and existing numbering/identity limits. Card
integration still follows the applicable source admission contract.
