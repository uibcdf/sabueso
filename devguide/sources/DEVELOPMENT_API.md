# Development native-source API

Unpublished recovery reader/mapping scopes. This is a living API reference, not a
public-release or automatic-enrichment claim. The [main API](../PUBLIC_API.md)
records cards/decks/stores and shared public entry points; source-specific
validation and access are in [the native reference](NATIVE_ACCESS_REFERENCE.md).
File delivery and local native qualification follow [FIXTURE_DELIVERY.md](FIXTURE_DELIVERY.md).

## Development recovery after 0.13.0

- `sabueso.tools.db.fda_orphan.get_page(identifier, client=None)` reads one native
  FDA OOPD detailed page; `map_page` emits standalone
  `annotations.orphan_product_records` on `fda:oopd_page:<locator>`. Designation
  and marketing-approval tables retain independent occurrences and original
  ordered fields, raw HTML/hash/query/time. Online/fixture/bound HTML/gzip/hash/time
  clients preserve original support; live shared transport currently fails with
  HTTP 404. The qualified supplied-artifact reader and imported-original replay
  do not establish restored automated access. FDA does not echo the locator;
  source URL/caller declaration identifies only a page. Unknown revisions,
  blank/N/A/date/name/status/sponsor literals remain separate from inferred
  clinical conclusions, product/protein identity or automatic card intake.

- `sabueso.tools.db.ttd.get_target_listing(identifier, client=None)` receives the
  native four-field target listing and validates every block before exact TTD-ID
  selection. Online/fixture/bound text/gzip/hash/time and replay preserve original
  header release and every repeated/conflicting occurrence. `map_target_listing`
  writes standalone `annotations.therapeutic_target_listing` on `ttd:target:<ID>`.
  UNIPROID entry names/placeholders stay literal; no accession inference, protein/
  gene/complex merge, clinical conclusion or automatic card intake. Data grant
  remains NOT-STATED with unknown use/sharing; qualification stays local unreleased.

- `sabueso.tools.db.iptmnet.get_substrate_report(identifier, client=None)` receives
  the original public base-accession HTML report and validates every substrate
  tab/table/header/row. `map_substrate_report` records standalone
  `annotations.ptm_report_rows` on independent `iptmnet:report_group:<native tab>`
  subjects. Missing sites, score0 and hidden source/PMID links survive. Native
  aggregate rows do not pair independent enzyme/source/publication lists or establish
  canonical positions, curation status or experimental confirmation. Online/fixture/
  bound HTML/gzip/hash/time and exact replay retain raw row/identity/full-response
  support. Revisions remain unknown. Database terms: CC BY-NC-SA 4.0.

- `sabueso.tools.db.brenda.get_enzyme_class(identifier, client=None)` reads one
  exact four-component numeric EC class from the documented public SPARQL
  prototype. Online, fixture and bound JSON/gzip/hash/time clients preserve all
  native solution bindings, RDF terms and query support. `map_enzyme_class` emits
  standalone `annotations.enzyme_class_context` on `brenda:ec:<EC>` with independent
  occurrence IDs. Native labels/systematic names/descriptions are source statements;
  they do not assign an EC or catalytic activity to a protein. Dataset/class revisions
  remain unknown. Empty OPTIONAL literals differ from missing bindings and empty
  solutions differ from failed access. No kinetics, linked acquisition or card intake.

- `sabueso.tools.db.pharos.get_target(identifier, client=None)` reads five native
  target fields through exact base-accession GraphQL access. Online, fixture and
  bound JSON/gzip/hash clients retain native null, errors and original-time replay.
  `sabueso.mappings.pharos.map_target` records standalone
  `annotations.target_development_context` on `pharos:target:<accession>` with
  native identity, name, symbol, family and provider TDL. It computes no ranking;
  contributing associations, novelty, ligand counts and card enrichment stay separate.
  Scientific/TDL-rule revisions and a separate data grant remain unknown.

- `sabueso.tools.db.depmap.get_model(identifier, release="24Q4", client=None)` reads
  full native Model.csv from fixed public article 27993248 version 1. Online bytes
  must match the qualified digest; fixture/bound CSV/gzip/hash/time clients preserve
  every native row. `sabueso.mappings.depmap.map_model` emits independent
  `annotations.cell_model_context` on `depmap:model:<ACH identifier>`. Names and
  cross-references do not merge models. All 2105 rows validate before selection;
  individual model/ontology revisions remain unknown. Gene effects, dependencies,
  screen/condition links and card enrichment are separate. This article states CC BY 4.0.

- `sabueso.tools.db.interactome3d.get_protein_structures(identifier, release="2024_12", client=None)`
  receives the archived human representative protein table through online, fixture
  or bound native TSV/gzip/hash/time clients. `map_protein_structures` emits
  standalone `annotations.structure_model_occurrences` on
  `interactome3d:protein:<native accession>`, preserving every selected occurrence,
  rank/template/bounds/score/filename literal and blank chain. Identity/coverage
  use native-help-qualified percent quantities. All 18000 rows validate first;
  archive route label is separate from unknown native/PDB/sequence revisions.
  Interaction pairs, complete datasets, exact residue mapping, coordinates and
  automatic card intake remain separate. NOT-STATED data grant; original factual
  artifact stays local unreleased.

- `sabueso.tools.db.probis.get_chain_catalog(identifier, client=None)` retains
  the full native headerless reference-chain catalog through online, fixture or
  bound TSV/gzip/hash/time clients. `sabueso.mappings.probis.map_chain_catalog`
  selects one exact lowercase PDB and case-sensitive chain literal, retaining
  each listing occurrence in `annotations.reference_chain_listing` on
  `probis:catalog_chain:<PDB.chain>`. All 42270 native rows validate first;
  unknown columns 1/2/5, padding, duplicate selectors and native row/hash support
  survive. The dated filename is an artifact label; scientific version is unknown.
  Broader representative/alignment, protein/function and card intake remain
  unqualified. Data grant is NOT-STATED; original factual artifact stays local unreleased.

- `sabueso.tools.db.pdbtm.get_topology(identifier, client=None)` receives one
  native lowercase PDB XML through online, fixture or bound XML/gzip/hash/time
  clients. `sabueso.mappings.pdbtm.map_topology` retains independent chain
  occurrences in `annotations.transmembrane_topology` on `pdbtm:structure:<ID>`.
  Original XML/copyright supports each occurrence, with XML-decoded sequence text,
  source attributes and independent sequence/PDB endpoint strings. No chain merge,
  offset map, orientation/function transfer, transform execution or card intake.
  Native history/site labels do not pin current PDB/sequence revisions; matrices
  and scores remain uninterpreted XML. Conditional nonprofit/commercial-agreement
  terms, unknown automated use/sharing and local unreleased qualification remain explicit.

- `sabueso.tools.db.threedid.get_motif_interactions(identifier, client=None)`
  retains the complete native DMI gzip export through online, fixture or bound
  text/gzip/hash/time clients. `sabueso.mappings.threedid.map_motif_interactions`
  keeps independent structural occurrences in `annotations.domain_motif_interactions`
  on `3did:structure:<native PDB ID>`, with original block/pattern/line/hash support.
  Patterns/dates, PDB chain/range/sequence and contextual contact/topology literals
  stay unchanged. No regex execution, lowercase-chain decoding, PDB span arithmetic,
  protein/function transfer or card intake is inferred. DDI residue contacts and
  HMM profile/global interfaces remain separate; scientific revisions and export
  reuse grant are unknown. Original factual gzip stays local unreleased work.


- `sabueso.tools.db.hpo.get_gene_annotations(identifier, release="v2026-09-01", client=None)`
  retains one full dated six-column native export through online, fixture or bound
  TSV/gzip/hash/time clients. `sabueso.mappings.hpo.map_gene_annotations` keeps
  each exact NCBI Gene occurrence in `annotations.gene_phenotype_associations`.
  Original disease, symbol, term and frequency literals survive independently,
  with full-export hash, native line and release support. No ontology propagation,
  gene penetrance, contributor guess, protein identity or card intake is inferred.
  HPO Consortium terms and input rights remain explicit; original files stay
  unchanged and local unreleased, with unknown automated use/sharing verdicts.


- `sabueso.tools.db.merops.get_assignments(identifier, client=None)` reads the full
  native accession export through online, fixture or bound TSV/gzip/hash/time
  clients. `sabueso.mappings.merops.map_assignments` keeps each native three-column
  occurrence on `merops:accession:<literal>` with original prefix/family/taxonomy.
  All 116744 lines survive, including three unassigned four-column rows and one
  quoted accession, with `merops_accession_rows@1` representation issues. A quote
  is not removed, a split accession is not repaired and unresolved rows prevent a
  complete-selection claim. No activity/cleavage, protein identity, namespace
  rewrite, sequence or card intake is inferred. One-GET archive replay keeps
  native hashes/time. GNU Library GPL is preserved as version-unspecified;
  local unshared use is qualified, automatic use verdicts/sharing stay unknown.


- `sabueso.tools.db.metalpdb.get_site(identifier, client=None)` reads the native
  JSON array for one explicit site ID through online, fixture or query-bound
  JSON/gzip clients. `sabueso.mappings.metalpdb.map_sites` keeps independent
  site occurrences and original metal/ligand/donor parent context on native site
  subjects. Donor distances become angstrom quantity nodes, qualified against the
  public Coordination Sphere header and matching native API values. Geometry,
  patterns/counts, false flags, native PDB numbering and UniProt pointers survive.
  Scientific revisions and metal chain/model/assembly/insertions remain unknown;
  no protein merge, canonical placement, function/experimental class or card intake
  is added. Raw/decoded hashes, original time and one-GET replay are preserved.
  Separate terms remain NOT-STATED; factual fixtures stay local unreleased work.


- `sabueso.tools.db.ecod.get_domain(identifier, client=None)` reads one explicit
  numeric domain UID through the public HTTP JSON API. Online, fixture and bound
  JSON/gzip clients retain original hash/time and one-GET replay.
  `sabueso.mappings.ecod.map_domain` preserves native experimental-origin labels,
  id/name classification, false/manual flags and opaque range/chain literals on
  `ecod:uid:<UID>`. UniProt stays a pointer; axes/revisions remain unknown.
  Predicted domains and full exports require separate qualification. Separate
  data terms are NOT-STATED; the original factual fixture remains local unreleased
  work. No search, file acquisition, projection, protein merge or card intake occurs.


- `sabueso.tools.db.tcdb.get_assignments(identifier, client=None)` receives the
  complete native accession-to-TC-system export, validated before exact literal,
  case-sensitive selection. Online, fixture and query-bound native TSV/gzip clients
  retain original bytes/hash/time and one-GET replay. `sabueso.mappings.tcdb.map_assignments`
  keeps independent occurrences and five/six-component codes without assigning
  accession namespaces, protein identity, substrate, mechanism, role or taxonomy.
  Blank accessions stay unbound in the full export; not-listed differs from failed
  access. Scientific revisions and database total remain unknown. Separate export
  terms are NOT-STATED; original fixture remains local unreleased recovery. No
  sequence/family acquisition, search, calculation or card enrichment occurs.

- `sabueso.tools.db.channelsdb.get_annotations(identifier, client=None)` reads
  one native PDB annotations DTO through online, fixture or source/query-bound
  JSON/gzip clients. `sabueso.mappings.channelsdb.map_annotations` retains
  independent entry/function/reaction and ChannelsDB/UniProt residue occurrences,
  with original text/reference/chain/ID literals, duplicates and conflicts.
  Numbering, sequence/model/assembly axes and scientific revisions remain unknown;
  no canonical placement, geometry join, UniProt identity merge, linked acquisition,
  job or card intake occurs. Original bytes/hash/time and one-GET replay remain
  explicit. Separate data terms are NOT-STATED; the small original public fixture
  remains local unreleased recovery.

- `sabueso.tools.db.channelsdb.get_channels(identifier, client=None)` separately
  reads the full existing PDB channel DTO through online/fixture/bound JSON/gzip
  clients. `map_channel_memberships` retains one native channel header, residue-flow,
  HetResidues and independent per-layer residue/index arrays per occurrence;
  `map_channel_annotations` retains separate original comments/reference rows.
  All twelve category arrays and their membership/annotation records are validated
  before output. Repeated IDs, tokens, conflicting labels and unequal layer/index
  cardinalities stay native. No token parsing, index resolution, heterogen class,
  experimental/Evidence class, same-ID annotation join or chain/protein merge.
  Geometry/physical properties remain uninterpreted in the original DTO; numbering,
  sequence/model/assembly/revision axes stay unknown. No canonical placement,
  coordinate/job acquisition, card shape/schema or automatic enrichment.

- `sabueso.tools.db.gwas_catalog.get_associations(identifier, limit=20, page=0,
  client=None)` reads one standard mapped-gene HAL page. The gene symbol remains
  a literal query; no gene/protein identity or causal-gene assignment is inferred.
  Limits 1–500 are a local reader bound; pages are zero-based. Online, fixture and
  exact source/query-bound JSON/gzip snapshots retain original bytes/hash/time.
  `sabueso.mappings.gwas_catalog.map_associations` preserves each native association
  occurrence, original study/variant/trait/location and all statistical fields,
  with checked page counts/links and explicit cuts. No automatic pagination,
  arithmetic/ranking, guessed units/assembly, summary-statistics acquisition or
  card intake occurs. API labels are separate from unstated scientific revisions;
  EMBL-EBI terms retain original-owner rights rather than a blanket CC0 grant.

- `sabueso.tools.db.monarch.get_associations(identifier, limit=20, offset=0,
  client=None)` reads one exact direct-subject CURIE association page. Limits are
  1–500 and offsets nonnegative. `sabueso.mappings.monarch.map_associations` retains
  every category/occurrence, native qualifiers, primary/aggregator support, original
  entities and explicit native totals/cuts. No automatic pagination, ancestor join,
  gene-to-protein transfer or binding/experimental class is inferred. Input-specific
  rights, unknown KG revisions, original JSON/gzip/hash/time and replay remain explicit.
- `sabueso.tools.db.pride.get_project(identifier, client=None)` reads one exact
  public PXD project. `sabueso.mappings.pride.map_project` retains native dataset
  metadata, depositor protocol text, CV objects, dates, publications and individual
  licence declarations on `pride:PXD…`. Source-bound snapshots and replay retain
  original bytes/time; API/route/date labels do not version project or sequences.
  No name matching, result/protein projection, linked files or analysis job occurs.
  Historical Proteins API peptide/PTM/HPP observations remain separately unintegrated.

- `sabueso.tools.db.omnipath.get_interactions(identifier, client=None)` reads one
  native human `omnipath` query for an exact base UniProt partner with the explicit
  academic licence filter. `sabueso.mappings.omnipath.map_interactions(envelope)`
  retains every ordered-pair occurrence, both effect flags, consensus and original
  aggregate resources/references. Dataset/resource filters do not reconstruct strict
  support, and licence filters do not grant reuse rights. Bound JSON/gzip snapshots,
  original byte hashes and time-preserving replay are supported. Unknown revisions
  and totals, resource-specific rights and a separately qualified SPIKE-only fixture
  remain explicit. No orthology translation or automatic card intake is added.

`tools.db.wikipathways.get_pathways_by_xref(identifier, client=None)` receives the
complete native bulk JSON for exact local cross-reference selection. Require one
literal supported namespaced ID (uniprot, ensembl, ncbigene, wikidata, chebi or
inchikey); no symbol/name query or inferred species filter. Validate every row
before selection across all seven original xref fields. Online/fixture/bound
JSON/gzip clients retain original time, bytes/hash and detached acquisition/replay.
`mappings.wikipathways.map_pathway_cross_references` preserves each matching
pathway occurrence, native species/authors/date label, complete row and original
field/group/alias match positions. Native fields can contain other prefixes, empty
aliases or free text; no column repair or alias equivalence is inferred. The provider
uniques/compacts xref groups and truncates descriptions at 200 characters; this
reader does not claim GPML-node coverage, roles or experimental participation.
Dataset/GPML/entity/sequence revisions remain unknown; content retains CC0 and
source/contributor attribution. No linked acquisition or automatic card intake.


`tools.db.ema_orphan.get_designations(identifier, client=None)` receives the full
native orphan-designation pages JSON export for exact local EU-number selection.
Online, unchanged fixture and source/query-bound JSON/gzip clients retain original
metadata, byte hashes, time and acquisition receipts. All rows and declared totals
are validated before selection. `mappings.ema_orphan.map_designations` preserves
independent occurrences on original page subjects, including repeated EU numbers,
conflicting dates, status/substance/medicine/product-reference literals and empties.
Generation/publication dates do not establish retrieval time or scientific revision.
No protein/product identity merge, modality, efficacy, authorisation inference,
linked acquisition or card intake. EMA attribution and third-party rights survive.

`tools.db.civic.get_molecular_profile_items(identifier, *, release, client=None)`
receives a complete native monthly accepted-items TSV, for exact molecular-profile
ID selection. Online, fixture and query/release-bound TSV/gzip snapshot clients
retain full text, byte SHA, original time and acquisition receipts.
`mappings.civic.map_molecular_profile_items` preserves independent occurrences
and all original profile/disease/therapy/direction/significance/support/flag fields
on complete source-profile subjects. Monthly release is explicit; entity/sequence
revisions stay unknown. CC0 content remains separate from publication rights.
No profile/therapy expansion, clinical inference or automatic card intake.

`tools.db.drugcentral.get_target_relations(identifier, client=None)` reads the full
native drug-target TSV/gzip for exact local accession-token selection. Online,
fixture and source/kind/query-bound snapshot clients retain full text, byte hashes,
original time and independent access receipts. `mappings.drugcentral.map_target_relations`
preserves independent rows on native single/composite target subjects. Activity
units/scales, MOA and original sources remain literal; no group expansion, chemical
identity merge, potency/clinical inference or automatic card intake. CC BY-SA 4.0
and unknown scientific revisions stay explicit.


- `sabueso.tools.db.clingen.get_gene_validity(identifier, client=None)` receives
  the original public gene-validity CSV for exact local HGNC selection. Online,
  fixture and query-bound native CSV/gzip clients validate the full preamble and
  every row before selection, preserving original time and optional byte SHA.
  `sabueso.mappings.clingen.map_gene_validity` keeps independent native rows with
  classification, inheritance, SOP, expert panel, report and date on a gene subject.
  Legacy report namespaces and dates without timezone survive. Native file/date
  labels are not scientific revisions; not listed differs from an explicit No Known
  Disease Relationship classification. Curated content is CC0. No strongest-class
  ranking, protein/variant inference, linked report fetch or card enrichment.
- `sabueso.tools.db.hpa.get_gene_profile(identifier, client=None)` reads one
  exact human ENSG gene's native HPA JSON subset, retaining all raw fields.
  Online/fixture/query-bound JSON/gzip clients preserve acquisition scope and
  optional original-byte SHA. `sabueso.mappings.hpa.map_gene_summary` maps
  independent native RNA/protein categories and explicit nulls on a source-gene
  subject, with gene label and original UniProt pointers as separate context.
  This summary is not a full assay export; quantitative projection, protein/isoform
  identity merging and card enrichment remain outside it. Scientific revisions
  are unstated. HPA CC BY 4.0 and third-party constraints remain explicit.
- `sabueso.tools.db.signor.get_relations(identifier, taxon_id=9606, client=None)`
  reads one exact base UniProt accession, requesting organism 9606/10090/10116.
  Online, fixture and query-bound native TSV/gzip clients preserve the original
  headerless response. `sabueso.mappings.signor.map_relations` keeps each native
  occurrence, including the first row, regulator/target roles, effect/mechanism,
  DIRECT flags, score and publication/residue/sequence/modification context.
  Requested organism is separate from returned taxonomy. Scientific revisions
  and native completeness are unstated. The exact `No result found.` marker is
  a query declaration, distinct from HTTP failure and biological absence. No
  identity merge, complex expansion, generic binding/experimental class, sequence
  projection, linked acquisition or automatic card intake is added. Data are CC BY 4.0.
- `sabueso.tools.db.appris.get_gene_annotations(identifier, client=None)` reads one
  exact unversioned human ENSG gene through the provider-default JSON exporter.
  Online, fixture and query-bound JSON/gzip snapshot clients retain all native rows.
  `sabueso.mappings.appris.map_annotations` keeps independent occurrences, including
  repeated/conflicting transcript names, genomic ranges and principal declarations.
  No grouping, principal selection, protein identity or residue placement is inferred.
  Assembly/dataset/record/sequence revisions are unstated; scores/notes/flags stay
  literal. Source assertions retain CC BY-NC-SA 4.0 obligations. No automatic card
  intake, additional filters, linked sequence/support acquisition or job is added.
- `sabueso.tools.db.complex_portal.get_complex(identifier, client=None)` reads one
  exact primary CPX complex, with online, fixture and query-bound snapshot clients.
  `sabueso.mappings.complex_portal.map_complex` keeps the complete native context;
  `map_participants` retains independent participant occurrences and original support.
  Native types, stoichiometry, feature/range/reference alternatives, prediction flags,
  ECO codes and confidence stars stay literal. Native release dates are separate from
  unknown complex/participant sequence revisions. No binary interaction expansion,
  protein/name search, entity merge, coordinate projection or automatic card intake.
- `sabueso.tools.db.cath.get_domain_summary(identifier, release, client=None)` reads
  one exact CATH domain on an explicit fixed release route. `OnlineCathClient`,
  `FixtureCathClient` and `SnapshotCathClient` retain unchanged native context;
  the snapshot client binds source/kind/domain/release and optionally verifies
  original-byte SHA-256. `sabueso.mappings.cath.map_domain` preserves one independent
  domain assertion with classification, ATOM/COMBS sequences and native structural
  correspondences. The requested route is separate from unknown response/record/
  sequence revisions. GO/EC context stays literal; no UniProt identity merge,
  canonical projection, coordinate/job query or automatic card intake is added.
- `sabueso.tools.db.uniprot.get_isoform_sequence(identifier, client=None)` requires
  an explicit accession/positive isoform suffix. `OnlineUniProtIsoformClient` and
  `FixtureUniProtIsoformClient` read a full parent declaration, then only the selected
  native FASTA when its sequence status is qualified. `map_isoform_sequence` in
  `sabueso.mappings.uniprot_isoforms` keeps that sequence and parent association.
  Native names do not define IDs; parent entry/canonical versions and database
  release are separate from unknown isoform sequence revision. Missing scope,
  not-listed, unknown/not-described/external status and failures stay distinct.
  Assertions can supply a sequence axis to `Card.residue_knowledge`; no variant
  reconstruction, canonical/structural remapping, implicit resolution or card intake.
- `sabueso.tools.db.swissmodel.get_metadata(identifier, client=None)` reads the
  full unfiltered native v2 response for a base UniProt accession. Independent
  `sabueso.mappings.swissmodel.map_structures` keeps every PDB/model occurrence,
  original target sequence and chain alignment. MD5 hashes the target sequence;
  coordinate/ModelCIF URLs are mutable pointers. Native scores and API/query/
  creation/release dates stay separate from unknown record/model/sequence revisions.
  Shared fixture/archive transport retains original times and hashes. No model
  selection, current UniProt projection, coordinate/template/publication download,
  modelling job or card enrichment is added.
- `sabueso.tools.db.amypro.get_entry(identifier, client=None)` reads AmyPro's whole
  native JSON export, validates all entries and selects one exact `AP` plus five-digit
  ID. The envelope retains the full export. `map_entry` preserves native context;
  `map_regions` keeps independent regions on the investigated entry sequence under
  subject `amypro:<ID>`. Parent UniProt bounds/mutations/categories stay literal;
  no entity merge, parent offset, current UniProt projection, experimental class or
  region-specific publication/method is inferred. Missing selection is scoped to
  this received export. Record/sequence/export revisions and data reuse are unknown.
- `sabueso.tools.db.eppic.get_interface_residues(identifier, interface_id, client=None)`
  reads native context and residue detail for one explicit positive EPPIC interface
  ID on a public PDB entry. `map_interface_residues` keeps each side/serial occurrence,
  ASA/BSA quantity, region, entropy and fraction literal, including zero areas and
  quoted `NaN`. Equal chain names/numbers remain distinct sides. Component times/
  hashes and unknown revisions stay explicit. Serial numbering is not projected
  to UniProt, author/insertion or label positions; rows do not all declare contact
  membership. Residue tables for other interfaces, sequences, coordinates and jobs
  stay unqueried.
- `sabueso.tools.db.intact.get_interactions(identifier, limit=200, client=None)`
  reads one PSICQUIC MITAB 2.7 page for an exact UniProt reference, including an
  explicitly requested isoform. Native count and all 42 columns are validated
  before the output cap. `map_interactions` keeps independent result occurrences,
  primary/alternative ID matches and native participants, methods, publications,
  negation, complex expansion and score literals. Aliases/xrefs never bind identity.
  No direct binding relationship, experimental class, sequence placement or calibrated
  probability is inferred. Source revision is unknown independently of service
  versions/native dates. The single-page ceiling is Sabueso's; later pages and
  linked articles are unqueried. Existing UniProt interaction support stays separate.
- `Card.residue_composition(residues, sequence_ref="canonical", source_assertions=None)`
  returns detached `residue_set_composition@1` counts/fractions for an explicit list
  of positive 1-based positions on one identified sequence axis. Each position is
  counted once; original request order and duplicate occurrences remain visible.
  B/J/X/Z stay unresolved and in the full denominator; U/O remain concrete symbols.
  Original source assertions/revisions, full input hashes and sequence support gaps
  are retained. Noncanonical axes require unambiguous subject-bound native sequence
  declarations. Selection is caller-declared and establishes no cavity membership.
  No geometry, structure projection, source query, card intake or persisted field.
- `sabueso.tools.db.alphafill.get_metadata(identifier, client=None)` reads existing
  AFDB-derived AlphaFill metadata for a base UniProt accession, preserving the
  actual returned fragment, native run context and every transplant alternative.
  `map_model` describes the source model; `map_transplants` describes predicted
  ligand context on that model with explicit angstrom RMSD/clash quantities.
  Compound/analogue labels and donor/alignment numbering remain literal. Run
  software/date is separate from the unknown record revision. Coordinates, jobs,
  observed target binding and current-UniProt residue projection are outside scope.
- `sabueso.tools.db.ligysis.get_result_page(identifier, segment, client=None)` reads
  one explicitly selected public segment as unchanged HTML. Online/fixture clients
  validate six inline JSON declarations without executing JavaScript or loading
  assets. `map_sites` keeps site IDs, counts, provider clusters/scores, percent RSA
  and original residue membership. Unknown source sequence/revision prevents
  canonical residue projection. Changed layouts and inconsistent scopes fail;
  other segments, individual ligand records, coordinates and jobs remain unqueried.
- `sabueso.mappings.ligysis.map_displayed_residues(envelope)` additionally validates
  native `cc`/`newChartData` literals on that same received page. It preserves
  initial-panel row occurrences, UPResNum/MSACol, AA/SS, DS/MES/p, percent RSA and
  original support as standalone `annotations.ligysis_residue_records` assertions.
  Selected site identity and sequence/alignment/result revisions remain unknown;
  no set-matched site identification, canonical location, significance class,
  other-site coverage or automatic card enrichment is claimed.
- `sabueso.mappings.ligysis.map_residue_correspondences(envelope)` reads native
  `Pdb2UpDict`/`Up2PdbDict` on the same received page. Each directed structure/chain
  dictionary becomes a standalone `annotations.ligysis_residue_correspondences`
  assertion, retaining parent/key case, signed labels, pair order and original
  support. Page query does not bind each chain to its protein; chain identity,
  numbering/insertion context and scientific revisions stay unknown. Directions
  are neither inverted nor repaired/merged; no current canonical placement,
  coordinate access or card enrichment occurs.
- `sabueso.tools.db.ligysis.get_structure_mapping(identifier, segment, pdb_id,
  client=None)` reads four complete native JSON tables through a read-only POST.
  Online/fixture clients require an explicit structure, echoed in both residue
  directions. Protein/segment are caller/transport context, not echoed identities.
  `map_structure_mapping` retains each directed chain dictionary, chain-to-accession
  declaration and remapping separately as `annotations.ligysis_structure_mapping`.
  All parents/labels are validated before output; missing opposite parents and
  conflicting/non-bijective declarations survive. No cross-table or old-page join,
  current-sequence placement, coordinates, jobs or card enrichment. Chain2acc
  namespace, residue numbering/insertions and scientific revisions remain unknown.
- `sabueso.tools.db.glygen.get_protein(identifier, client=None)` reads the full
  native detail response for one base UniProt accession. Online/fixture clients
  retain original transport/file receipts; both modification table totals must
  equal received rows. `map_glycosylation` and `map_phosphorylation` preserve
  source categories, glycan/kinase context, native support pointers and the explicit
  GlyGen sequence. Ranges or unlocated sites never become single-residue placement;
  categories never become guessed experimental/curated classes. Introduction history
  is not the unknown current revision. No card enrichment or current-UniProt projection.
- `sabueso.tools.db.eppic.get_annotations(identifier, client=None)` bundles three
  unchanged native responses (entry, interfaces, assemblies), with separate retrieval
  times/hashes and observed online/fixture acquisition. `map_interfaces` and
  `map_assemblies` preserve native method calls, alternatives, scores/sentinels,
  EPPIC IDs and chain operators, with square-angstrom interface quantities. A later
  failure retains earlier access receipts and raises; it never fabricates an empty
  component. Residue/coordinate downloads and automatic card enrichment are absent.
- `sabueso.tools.db.pdb_redo.get_entry` and `get_versions` read existing public
  databank statistics and separately requested input/software revisions for one PDB
  ID. `map_refinement` preserves deposited/baseline/restrained/final R-factor stages;
  `map_versions` keeps source input revisions and software/use flags. Pipeline
  version/date is not the unknown databank revision. No calculation, model replacement,
  coordinate URL fabrication, computed improvement or card enrichment occurs.
- `sabueso.tools.db.pdbe_validation.get_global_percentiles(identifier, client=None)`
  reads native entry-wide validation metrics for one four-character PDB ID with
  online/fixture clients. `sabueso.mappings.pdbe_validation.map_global_percentiles`
  keeps one independent structure-subject assertion per metric, including raw,
  archive-wide and optional comparable-entry percentiles on the native 0–100 scale.
  Source/statistical revisions and population counts remain unknown. No quality
  classification, automatic structure selection or card enrichment is added.
- `sabueso.tools.db.mobidb.get_annotations(identifier, client=None)` reads one
  canonical v1 protein export, retaining the complete native sequence, release,
  annotation sets, per-residue series and representation issues. Online/fixture
  clients validate export/header scope. `map_disorder_regions` and
  `map_modified_residues` in `sabueso.mappings.mobidb` keep native bases, labels,
  providers and provenance on the explicit MobiDB axis. Sets with reported issues
  remain raw and are excluded from mapping under `mobidb_valid_region_sets@1`.
  `Card.residue_knowledge` accepts MobiDB's native disorder feature on an explicitly
  selected, subject-bound source sequence, without inventing a DisProt ontology ID.
- `sabueso.tools.db.sifts.get_mappings(identifier, client=None)` reads one native
  UniProt mapping response for a four-character PDB ID, through online/fixture
  clients. `sabueso.mappings.sifts.map_sequence_mappings(envelope)` retains
  independent structure-subject segment assertions, all protein/isoform references,
  author versus label chains and original endpoint numbers/insertion codes.
  Release and sequence revisions remain unknown. No offset extrapolation, entity
  merge or automatic card enrichment occurs.
- `sabueso.tools.sources.get_catalog()` reads packaged `registry_catalog@1`
  metadata and category profiles, preserving every registry status, access/terms
  declarations, limitations and code-derived default limits. It performs no source
  query; profiles do not activate connectors or imply live health/readiness.

- `sabueso.tools.db.alphamissense.get_annotations(identifier, limit=10000, client=None)`
  reads the exact source-declared canonical human CSV after AlphaFold DB discovery.
  Online/fixture clients validate the full artifact before capping returned rows,
  retaining native literals, byte hashes, source sequence and computed grid coverage.
  Host model versions never become AlphaMissense revisions; score version remains
  unknown. Missing declarations cause no score request; declared failures remain
  failures. `sabueso.mappings.alphamissense.map_variants(envelope)` emits independent
  `variants.predicted_effects` SourceAssertions on the explicit source sequence axis.
  Native scores/classes, missing values and predicted context remain separate from
  clinical observations. No card enrichment, isoform placement or new inference occurs.

- `sabueso.tools.sequence.find_protein_candidates(sequence_input, *, taxon_id=None,
  limit=100, uniparc_client=None, uniprot_client=None)` returns
  `exact_sequence_candidates@1`. One raw/FASTA sequence is normalized and searched
  by UniParc MD5; both full archive and current canonical UniProt sequences are
  compared. Every match remains separate, with optional exact taxonomy filtering.
  Native historical/isoform references, row/check caps, failures and unchecked
  scope remain explicit; `status` and `candidate_status` are separate. It makes
  no choice, identity link, alias traversal or card. `sabueso.resolve` retains
  its existing input contract. Review candidates and explicitly choose an accession.
  `sabueso.tools.db.uniparc.get_records(checksum, limit=100, client=None)` retains
  native pages/counts/releases and detached acquisition, through online/fixture
  clients. `map_sequence_records` produces independent archive declarations.

- `Card.to_notebook(path=".", title=None, mode="full", language="en",
  include_code=True, include_card_snapshot=False)` and
  `sabueso.tools.card.write_notebook(card, ...)` render deterministic offline
  reports of stored knowledge and optionally its exact sealed JSON snapshot.
  With code and a saved snapshot enabled, the optional cell checks its exact pin
  and regenerates the report/adjacent card with the original title, mode and language.
  Execute beside the saved pair; moving them together preserves offline replay.
  Runtime provenance sidecars remain separate.
- `Card.get_residue(position, sequence="canonical")` and
  `Card.get_residues(sequence="canonical")` expose `residue_annotations@1` with
  exact sequence scope, item support, original card pins and placement/support gaps.
  No alignment, isoform reconstruction or PDB numbering projection occurs.
- `Card.residue_knowledge(position, sequence_ref="canonical", source_assertions=None)`
  runs `residue_knowledge@1` over the card and explicitly supplied original
  SourceAssertions. Type properties/statistics stay separate from dense/sparse
  position tracks and source disorder regions. Exact original assertion snapshots,
  versions, contexts, units, missing values and unplaced inputs remain visible.
  A noncanonical sequence must have an explicit subject-bound native sequence
  declaration; equal strings/accessions never establish coordinate equivalence.
  This is a detached reader, with no acquisition, intake or stored schema change.
- `sabueso.tools.db.aaindex.get_index(identifier, client=None)` reads a native
  scale with built-in online/fixture acquisition records.
  `sabueso.mappings.aaindex.map_index(envelope)` produces separately supported
  amino-acid-type reference assertions, not positional facts or protein enrichment.
  Native missing values, references and unit/version/terms gaps remain explicit.
- `sabueso.tools.source_snapshot.load_source_snapshot(path, *, source_metadata,
  file_format=None, expected_sha256=None, records_key=None)` reads explicit
  JSON/JSONL/NDJSON/CSV/TSV files or literal UTF-8 HTML/TXT, including gzip, into
  source envelopes. HTML/TXT preserve BOM and line endings without parsing or
  executing content; `records_key` cannot wrap text. Its
  `sabueso.supplied_snapshot@1` receipt retains the original byte hash and caller
  declarations. File reading creates no remote-access claim, acquisition credit
  or card intake. Native source validation remains required.
- `sabueso.tools.db.disprot.get_records(identifier, client=None)` queries an exact
  canonical UniProt accession. Online, fixture and explicit snapshot clients retain
  native record/region counts and incomplete scope. `map_disorder_regions(envelope)`
  selects exact native disorder terms as independent assertions scoped to the
  DisProt sequence, retaining revisions and reference pointers. Card enrichment
  and projection onto current UniProt/isoform sequences are not implemented.
