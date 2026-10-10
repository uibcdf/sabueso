# Data Sources Status (Implemented)

Development FDA OOPD now reads original public detailed-page artifacts on
requested page subjects. Designation and approval tables, procedural dates, blank
exclusivity fields, N/A and sponsor qualifiers stay independent. The HTML does not
echo cfgridkey; the requested URL or supplied declaration binds a page, not a stable
designation, product or protein ID. No target/modality defaults, clinical conclusion,
search completeness or automatic card enrichment. The later shared-transport live
check receives HTTP 404; native supplied-artifact reading is qualified separately
from restored automated access. See
[follow-up 20](archive/local_work_2026-07/followup_20_pending_resource_recovery.md).

## TTD native target listing (development)

- **Acquisition:** one GET of the explicitly advertised public target cross-reference
  export; full original 525950 bytes, 4298 four-field blocks, 613 NOUNIPROTAC values.
- **Revision:** original header 10.1.01 (2024.01.10); individual target/UniProt revision
  unknown. Website citation date is separate.
- **Mapping:** exact TTD ID, independent occurrence assertions on the TTD target;
  names/type labels/inconsistencies and entry-name cross-references stay literal.
  No accession reconstruction, protein/gene/complex merge or clinical inference.
- **Terms:** NOT-STATED, unknown use/sharing, internal retention; original factual
  export local unreleased. Public acquisition is independent of redistribution.
- **Limits:** drug/disease/activity/variant joins and card enrichment stay separate.

## iPTMnet native substrate report (development)

- **Acquisition:** original public report HTML; earlier REST HTTP 503 stays a failure.
  P60174 has 72 native rows in three groups (62/7/3), Q15796 has 60 (42/15/3).
- **Mapping:** separate native report-group subjects, blank sites, source score labels
  and all hidden source/PMID links. Native aggregate support stays one row; no guessed
  enzyme/source/PMID pairing, curated/inferred class or canonical numbering.
- **Integrity:** every identity/tab/table/header/row validates first. Original HTML,
  row/identity support and response hash survive. Per-request form nonce changes
  full-response identity independently of unchanged scientific panels; exact replay
  retains each original response/time. Dataset/sequence/scoring-rule revisions unknown.
- **Terms:** official database CC BY-NC-SA 4.0; software/article/contributing rights
  stay separate. No linked requests, script execution or automatic card enrichment.

## BRENDA EC-class descriptions (development)

- **Native route:** the officially linked public DSMZ SPARQL prototype, one exact
  numeric EC query for label/systematic name/description, without LIMIT or OFFSET.
- **Received originals:** 5.3.1.1 has label and systematic name with a native empty
  description; 2.7.1.1 has nonempty descriptive text; an exact no-match probe has
  zero solutions. All raw RDF nodes and solution occurrences survive.
- **Mapping:** standalone `annotations.enzyme_class_context` on the native EC
  subject; no protein classification/activity or organism assignment. Unknown
  prototype/EC revision is not replaced by the main website release.
- **Rights:** provider data/online-use CC BY 4.0; credit BRENDA/DSMZ and the current
  provider publication. SOAP registration and bulk acceptance are separate routes.
- **Partial scope:** kinetics, inhibitors, cofactors and assay conditions remain
  unqueried. Prior inhibitor HTTP 500 is not retried or represented as no records.

## ASD access conditions and TTD qualification scope

ASD's original download JavaScript lists explicit mixed-release artifacts, requires
licence-application/login state, and states research-only use with no third-party
redistribution. No application or gated archive acquisition occurs. Native site
versus predicted-potential-site and sequence/structure contracts remain required.

TTD's original legacy HTML advertises the current `ttd.idrblab.cn` redirect. Its
linked download component yields a 525950-byte public target/UniProt export with
version 10.1.01 (2024.01.10), separate from the 2026 citation. UNIPROID includes
entry names and NOUNIPROTAC. Names/type labels do not justify accession inference,
identity merging or druggability ranking. Data rights remain unstated beyond the
reserved-rights footer. The scoped native TTD-ID reader and local unreleased fixture
keep sharing unknown under NOT-STATED terms; see the current summary above and
[follow-up 19](archive/local_work_2026-07/followup_19_native_target_and_ptm_context.md).
Earlier acquisition: [follow-up 18](archive/local_work_2026-07/followup_18_pending_source_integration.md).

The index of every resource, with its status and the reason for it, is `devguide/sources/registry.yaml` (`devguide/sources/README.md`). This file keeps the technical detail of the sources in use.

This document is a living checkpoint of the data sources (DBs) currently integrated in Sabueso. It summarizes the quality of each source integration, known issues, and operational notes (online/offline behavior).

## Pharos / TCRD native target metadata (development)

- **Delivered:** exact base-accession `get_target` and `map_target`, online,
  fixture, bound JSON/gzip/hash/time and one-GET archive replay.
- **Original:** P60174/TPI1/Enzyme/Tbio and P31749/AKT1/Kinase/Tchem; P00000
  has native null. Selected provider literals are not Sabueso rankings.
- **Scope:** only the five requested fields; identity and query must agree.
  GraphQL errors never become no-match. Scientific/TDL-rule revisions and separate
  data grant remain unknown. Aggregate associations and automatic enrichment stay separate.

## DepMap 24Q4 public model context (development)

- **Delivered:** exact ACH `get_model` and `map_model`, fixed release v1,
  digest-pinned online access, fixture/bound CSV/gzip/hash/time and archive replay.
- **Original:** unchanged 645696-byte Model.csv, 2105 rows and 47 columns.
  ACH-000019 is the source's MCF7 model. All rows validate before selection.
- **Scope:** descriptive model context; names and RRIDs do not merge identities.
  Unqualified age/media quantities remain raw support, not asserted quantities.
  Public release/article version is separate from unknown individual model/ontology
  revisions. Gene dependencies, matrices, screens and conditions remain separate.
- **Terms:** native article 27993248 v1 states CC BY 4.0 and supplies the exact file
  ID/MD5; this grant is not propagated to collaborator datasets or other releases.

## Interactome3D archived representative protein metadata (development)

- **Delivered:** `get_protein_structures` and `map_protein_structures`, with online,
  fixture and bound native TSV/gzip/hash/time clients, exact uppercase accession
  and qualified archive `2024_12` only. Standalone occurrences retain native support.
- **Original:** human representative proteins.dat, all 18000 rows/1618274 bytes.
  P60174 has one Structure for native `1wyi`/chain A, endpoints 2–249, percent
  identity 100.0 and coverage 99.6. Q8WZ42 has thirty independent occurrences.
  Representative selection is not a single-record or full-current-database claim.
- **Semantics:** ranks, template/PDB IDs, chain case/whitespace, filenames and
  opaque negative score literals survive. Help qualifies percentages; endpoints
  do not establish exact full-chain correspondence or a current canonical map.
  Archived route label is separate from unstated native/PDB/sequence revisions.
- **Scope/terms:** complete tables, interaction pairs/API, coordinates, modelling/
  alignment and automatic enrichment remain separate. Separate data grant is
  NOT-STATED, automated sharing unknown, original factual qualification local
  unreleased. See [follow-up 15](archive/local_work_2026-07/followup_15_source_integration.md).

## ProBiS native reference-chain catalog (development)

- **Delivered:** `get_chain_catalog` and `map_chain_catalog`, with online, fixture
  and bound TSV/gzip/hash/time clients; exact lowercase PDB/case-sensitive chain selection.
- **Original:** all 42270 headerless five-column rows, 1003440 unchanged bytes,
  including first data row, padded opaque columns and repeated selectors. `5a2q.h`
  has three independent occurrences; `2ww9.L` five. `1ytb.B` is not listed while
  `1ytb.A` is; no case repair or representative relation is inferred.
- **Support:** each standalone listing retains original row/line/full-export hash;
  acquisition/archive retains complete raw text and genuine time. Filename date
  is an artifact label, not a scientific/PDB/sequence revision or current completeness.
- **Terms/scope:** NOT-STATED separate data grant, unknown automated sharing,
  original factual artifact local unreleased. Alignment/representative REST access
  remains unqualified; no similarity/function/ligand transfer, protein merge,
  score/weight/unit guess, coordinates, computation job or automatic card enrichment.
  See [follow-up 14](archive/local_work_2026-07/followup_14_source_integration.md).

## PDBTM native chain topology (development)

- **Status:** implemented as standalone native chain occurrences; coordinates,
  transforms, canonical projection and automatic card intake remain separate.
- **Access:** one public per-entry XML GET, unchanged 6866-byte 1c3w fixture and
  source/kind/query-bound XML/gzip/hash/time snapshots with zero-network replay.
- **Quality:** all three chains and 45 regions validate before mapping. Each
  occurrence retains XML-decoded sequence text and source attributes/endpoints,
  with the complete unchanged XML/copyright as support. Duplicate/generated
  chains remain independent; sequence/PDB bounds differ nonuniformly and do not
  imply an offset map. XML character decoding is distinct from document bytes.
  Native history and site labels do not pin current PDB/sequence revisions;
  matrices and raw scores remain uninterpreted XML with units/axes unqualified.
  Failed/unsupported acquisition never becomes negative membrane knowledge.
- **Terms:** embedded conditional nonprofit unchanged-content/copyright and
  commercial-agreement statement, represented by `PDBTM-CONDITIONAL`, unknown
  automated use/sharing and internal retention. Original qualification stays
  local unreleased; no MIT, broad noncommercial or public redistribution grant.
  See [follow-up 13](archive/local_work_2026-07/followup_13_source_integration.md).

## 3did native domain-motif structural instances (development)

- **Status:** implemented for DMI export instances by exact lowercase PDB ID;
  domain-domain residue contacts and HMM profile/global interfaces remain separate.
- **Access:** public download page and native gzip now respond after earlier
  failures. One full export GET; original fixture and bound text/gzip/hash/time
  snapshots plus zero-network replay.
- **Quality:** all 1657 blocks/17478 instances validate before selection. PDB 7m5l
  supplies six independent instances across PCNA_C/PCNA_N motifs. Original pattern/
  date, domain/motif source labels, chain/range/sequence and zero contextual-contact/
  topology literals survive with complete row/parent/hash support. A PDB-number
  span does not state a contiguous sequence slice; lowercase repeated tokens stay
  literal. Revisions and native database completeness are unknown. No motif search,
  protein identity, functional/experimental class or card intake is inferred.
- **Terms:** separate export-data grant NOT-STATED, with 3did/IRB Barcelona and
  original native input attribution. Unchanged factual gzip stays local unreleased;
  no article/software licence or public redistribution grant is substituted. See
  [follow-up 12](archive/local_work_2026-07/followup_12_source_integration.md).

## HPO native gene/disease phenotypes (development)

- **Status:** implemented for exact NCBI Gene occurrences from a dated six-column
  public release, separate from ontology expansion and detailed HPOA assertions.
- **Access:** one dated release asset GET; unchanged TSV fixture and source/kind/
  query/release-bound TSV/gzip/hash/time snapshots; replay uses zero network.
- **Quality:** all 333983 rows validate before selection. TPI1/7167 has 44 native
  occurrences, preserving OMIM/ORPHA context, term names, fractions, HP frequency
  terms and missing `-`. Percentages and future frequency strings remain opaque.
  Full native line/hash/release support survives; individual contributor,
  publication, modifiers and input revisions are unstated in this summary.
  No gene penetrance, clinical inference, protein merge or card intake occurs.
- **Terms:** official JAX website licence component qualifies unchanged HPO files
  with attribution/citation and public date/version display. Software and input
  rights remain separate; local unreleased qualification artifacts and automatic
  unknown-use/internal-retention semantics are explicit. See
  [follow-up 11](archive/local_work_2026-07/followup_11_source_integration.md).

## MEROPS native classification assignments (development)

- **Status:** implemented for exact source-prefixed accession classification
  occurrences, separate from original cleavage/sequence capabilities.
- **Access:** one full public export GET, native TSV fixture and bound TSV/gzip/
  source-kind-query/hash/time clients; replay performs zero network attempts.
- **Quality:** every received line is retained. Three displaced four-column rows
  remain unassigned and one quoted accession stays literal. Named representation
  issues and incomplete-selection qualifiers survive alongside native prefixes,
  duplicate/conflicting assignments and blank/whitespace taxonomy. Revisions and
  native database completeness are unknown. No activity, cleavage, namespace/protein
  merge, sequence, search or automatic enrichment is inferred.
- **Terms:** whole database GNU Library GPL declaration, version unspecified;
  local unshared qualification only. Automated use verdicts/sharing remain unknown.
  Original data/licence support stay local unreleased work. See
  [follow-up 10](archive/local_work_2026-07/followup_10_source_integration.md).

## Pending native acquisition follow-up (development)

The [ninth five-source follow-up](archive/local_work_2026-07/followup_09_source_integration.md)
qualifies CASTpFold tutorial area/volume units and official existing-result examples,
ProBiS' documented representative lookup, and Interactome3D's exact metadata export.
Scientific CASTpFold JSON is replaced by an HTML shell; ProBiS returns 404 and the
Interactome3D file fails TLS. 3did's index is readable but export acquisition fails.
FDA's public filter/date basis is reviewed without another blocked export request.
At that receipt, all five stayed evaluating with no reader or fixture. The later
3did DMI reader above qualifies its changed native access independently. Native data/terms and explicit
scope remain required. Future data attempts need a changed access condition or
an independently qualified supplied artifact rather than the same failed route.

## MetalPDB native metal sites (development)

- **Status:** implemented for one explicit site query and independent native
  site/metal/ligand/donor parent context; protein and canonical placement remain separate.
- **Access:** one HTTPS site JSON GET; original JSON and bound JSON/gzip/hash/time
  snapshots plus replay. Other API query kinds and linked assets are not acquired.
- **Quality:** native identity/types, false flags, source geometry/counts and
  original PDB numbers/chain case survive. The public Coordination Sphere declares
  angstrom donor distances, independently matched against three rounded API donors.
  Full precision and unit qualification remain explicit. Metal chain/model/assembly/
  insertion and scientific/sequence revisions remain unknown; no function,
  experimental class, computation, protein merge or automatic intake is added.
- **Terms:** separate site-data grant NOT-STATED; original small public JSON and
  declared HTML unit-table excerpt remain local unreleased recovery. See
  [follow-up 08](archive/local_work_2026-07/followup_08_source_integration.md).

## ECOD experimental-domain classifications (development)

- **Status:** implemented for one explicitly selected native experimental UID;
  AlphaFold/DPAM and full-release/broader queries remain separately unqualified.
- **Access:** one explicit public HTTP JSON GET; original JSON fixture and bound
  JSON/gzip/hash/time snapshots plus replay, without protocol fallback.
- **Quality:** native UID/domain/PDB/chain, id/name hierarchy and false/manual flags
  validate before mapping. Range remains opaque and UniProt stays a source pointer.
  Numbering, sequence/model/assembly and scientific revisions remain unknown;
  API v1 and distribution v295.2 are independent. No projection, protein merge,
  search, files, computation or automatic card intake is added.
- **Terms:** separate data grant NOT-STATED; original factual bytes remain local
  unreleased recovery. See [follow-up 07](archive/local_work_2026-07/followup_07_source_integration.md).

## TCDB accession assignments (development)


- **Status:** implemented for native accession-literal to TC-system occurrences;
  namespace resolution, family function and protein/sequence transfer remain separate.
- **Access:** one public full acc2tcid export GET; exact literal selection only
  after all rows validate. Original headerless TSV, bound TSV/gzip/hash/time and replay.
- **Quality:** green for qualified native shape/access. Preserve thirteen blank
  accessions as unbound rows, mixed case/versioned IDs, repeated pairs, multiple
  assignments and five/six-component codes. Original line occurrences remain
  independent. Not-listed differs from a failed or empty export; revisions and
  current database completeness remain unknown.
- **Terms:** separate export grant NOT-STATED; website-text CC BY-SA/GFDL and input
  rights are separate. Original factual bytes stay local unreleased recovery. See
  [follow-up 06](archive/local_work_2026-07/followup_06_source_integration.md).

## ChannelsDB PDB annotations (development)

- **Status:** implemented for independent native PDB annotation DTOs; geometry,
  AlphaFill, preferred assemblies and canonical residue placement remain separate.
- **Access:** one public annotations/pdb GET; original JSON fixture, query-bound
  JSON/gzip snapshots, acquisition trace and one-GET archive replay.
- **Quality:** green for qualified native annotation shape/access; numbering and
  scientific revisions remain unknown. Entry/function/reactions and independent
  ChannelsDB/UniProt residue-comment occurrences retain literal groups, references,
  HTML text, duplicates and conflicts. No caller protein or numbering is assigned.
- **Terms:** separate data grant NOT-STATED; original small fixture remains local
  unreleased work. Frontend/article/input rights are separate. See
  [follow-up 05](archive/local_work_2026-07/followup_05_source_integration.md).

## Legend
- **Status**: implemented / partial / paused
- **Access**: online API / dump (remote) / local file
- **Quality**: green (stable), yellow (works with caveats), red (broken)
- **Notes**: incidents, timeouts, missing fields, or skipped tests

---

The [third five-source recovery review](archive/local_work_2026-07/batch_03_source_review.md)
recorded BioCyc, OMIM, Interactome3D, PDBTM and TCDB as evaluating at that checkpoint, with native
requirements and concrete access/terms/identity boundaries. Public PDBTM/TCDB
probes qualified formats, not delivered connectors or redistribution. TCDB now has
the scoped local assignment reader recorded above; its export rights remain unknown.
With batch 06, the final FDA/EMA candidates are reviewed and no unreviewed
candidates remain from this list. After the sixth integration follow-up, fifteen
reviewed candidates await integration. GWAS association pages, Monarch associations, PRIDE project metadata,
OmniPath interactions, WikiPathways xrefs, EMA designation
pages and CIViC monthly accepted items are recovered. The implemented sections below retain their actual delivered scope.

## Protein / Structure / Chemistry

### GWAS Catalog — native mapped-gene association pages (development recovery)

- One v2 HAL GET for a literal standard mapped-gene symbol, explicit size/page
  and `extended_geneset=false`. Validate every row and exact official-host page
  links/counts; preserve all received independent association occurrences.
- HBB page 0, size 2 receives two associations on independent GCST studies from
  native total 279. Original mantissa/exponent **1, -323**, numeric p-value, risk
  frequency, free-text effect/range, alleles, locations and trait sets remain raw.
  No causal-gene/protein assignment, statistic ranking or unit/assembly guess.
- TPI1's observed empty HAL shape declares zero filter hits, without a biological
  negative. Native totals/cuts do not guarantee ordering or a fixed revision across
  manual pages. Dataset/association/assembly/sequence revisions remain unknown.
- Online, fixture and bound JSON/gzip/hash/time snapshots support one-GET replay.
  EMBL-EBI terms add no restrictions over original owners; summary-statistics CC0
  and software Apache are separate. No page/study/variant/file/article follow-up,
  computation or automatic card intake. GtoPdb/COSMIC/BioCyc/OMIM remain evaluating;
  see [follow-up 04](archive/local_work_2026-07/followup_04_source_integration.md).

### Monarch — native association pages (development recovery)

- One exact direct-subject CURIE page with explicit limit 1–500 and nonnegative
  offset. Native totals/cuts, original entities and categories remain explicit.
- All row occurrences retain negation/qualifiers, original and normalized entities,
  primary/aggregator sources, native agent/knowledge labels, ECO and publication
  pointers. No gene-to-protein transfer, ancestor match or binding class is inferred.
- The unchanged BioGRID-only fixture contains two gene interactions out of native
  total 232. BioGRID explicitly grants MIT rights to its download files; the original
  notice remains alongside the fixture. Arbitrary KG data retain input-specific terms.
- Source/query-bound JSON/gzip/hash/time and one-GET replay are supported. KG,
  association/entity and sequence revisions stay unknown; no automatic pagination.

### PRIDE Archive — native project metadata (development recovery)

- One exact PXD project JSON with complete native depositor metadata. Descriptions,
  protocols, object-valued CV terms, missing DOI, publications, dates, individual
  licence and administrative counts survive on the source-dataset subject.
- Native PXD013616 declares CC0 and PARTIAL submission. That label is not a
  reader cut; metadata is complete within the received response. Unknown project/
  sequence revisions remain separate from API 3.0, route v2 and publication dates.
- Supplied JSON/gzip binds source/project/hash, retains declared original time and
  supports one-GET replay. Per-project rights do not become a blanket archive grant.
- Historical Proteins API peptide/PTM/HPP data have separate PeptideAtlas,
  ProteomicsDB and unnamed origins. No PRIDE relabeling, protein/result projection,
  file/sequence acquisition, analysis job or automatic card enrichment is added.
- See the [third five-source follow-up](archive/local_work_2026-07/followup_03_source_integration.md)
  for both delivered readers and pending MetalPDB/Interactome3D/3did contracts.

### OmniPath — native aggregate interactions (development recovery)

- One native human `omnipath` query for an exact base UniProt partner with the
  explicit academic licence filter; no client cap. All returned rows are validated
  before independent occurrence mapping on native ordered-pair subjects.
- Both effects, all direction/consensus flags, duplicates and original resource/
  reference support survive. Native aggregate support is not reconstructed into
  strict resource-only evidence; filters can retain annotations from other inputs.
- HTTP-200 application errors fail explicitly. Empty arrays remain query-scoped;
  unknown revisions, taxonomy observations and independent totals stay unknown.
- Query-bound JSON/gzip/hash/time and one-GET replay retain source-specific support.
  Arbitrary row reuse requires input-specific rights; the SPIKE/SPIKE_LC fixture
  has separately declared CC BY 4.0 with attribution. No orthology, direct-binding
  class, publication lookup or automatic card enrichment is added.
- The [second five-source follow-up](archive/local_work_2026-07/followup_02_source_integration.md)
  also qualifies the actual MEROPS accession format and displaced rows, preserving
  concrete TCDB/PDBTM/ELM conditions.

### WikiPathways — native pathway cross-references (development recovery)

- One full native JSON GET; validate all 2218 fixture rows before exact namespaced
  token selection across seven original xref fields. TPI1 has nine pathway rows.
- Original field/group/alias positions, species, authors, complete row and native
  pathway date label survive; references in unexpected columns are not repaired.
- The official template uniques/compacts xref groups and truncates descriptions
  at 200 characters. Source-served xrefs do not establish GPML-node coverage,
  experimentally supported participation, mechanisms or cross-database equivalence.
- Original JSON/gzip bytes/hash, declared time, exact snapshot scope and replay
  retain CC0 content terms and source/contributor attribution. Scientific revisions
  remain unknown; no species filter, linked acquisition or card enrichment is added.
- The [five-source integration follow-up](archive/local_work_2026-07/followup_01_source_integration.md)
  also records useful HPO, GWAS, ECOD and ChannelsDB contracts still awaiting intake.


### EMA Orphan — native designation pages (development recovery)

- `get_designations` reads the full official meta/data JSON export, validates all
  3310 native fixture rows and matching declared count before exact EU-number selection.
  File generation, row dates and retrieval time remain separate; revisions are unknown.
- EU/3/23/2858 retains two distinct original pages/dates without suffix stripping,
  date overwrite or product identity merging. Withdrawn status, unresolved number
  literals, empty medicine/product/date fields and native product references survive.
- Independent SourceAssertions retain each original page subject and occurrence,
  full original context/hash/time, bound JSON/gzip and unchanged replay.
- EMA-owned metadata may be reproduced with acknowledgement in each copy;
  third-party material/linked documents and logo rights remain separate.
- No designation-to-authorisation/efficacy/modality conversion, protein/chemical
  identity projection, linked-page acquisition or card intake is added. The
  [final two-source review](archive/local_work_2026-07/batch_06_source_review.md)
  records earlier FDA access/query/terms requirements; the current scoped FDA
  page reader and its live-access limitation are described above.

### CIViC — native accepted molecular-profile items (development recovery)

- `get_molecular_profile_items` receives a complete explicit monthly accepted-items
  TSV and validates every row before exact source-profile ID selection. The
  unchanged 01-Oct-2026 fixture contains 4940 rows; profile 12 has 93 BRAF items.
- Independent directions/significance, disease, therapies and interaction type,
  origin, citation/trial/review context, level/rating/status and flags stay literal.
  Accepted flagged records survive; profiles and therapy combinations stay atomic.
- Native profile subjects, explicit export label, original text/byte SHA/time and
  source-bound TSV/gzip snapshot/replay receipts survive. Unknown entity/sequence
  revisions, not-listed versus failed access and CC0/publication rights are explicit.
- No gene/protein identity merge, treatment projection, strongest-item selection,
  submitted-items/Assertions query or card enrichment is added. See the
  [fifth five-source review](archive/local_work_2026-07/batch_05_source_review.md)
  for ChannelsDB/Proteins API/CASTpFold/ProBiS pending qualification.

### DrugCentral — native drug-target observations (development recovery)

- `get_target_relations` receives the full [official TSV/gzip export](https://unmtid-dbs.net/download/drug.target.interaction.tsv.gz),
  validates all 22364 received rows and locally selects exact accession tokens.
  All original columns, compressed/text hashes, unknown scientific revisions,
  original-time replay and source-bound snapshots survive.
- EGFR has 80 observations, with 18 native MOA `1` declarations. Composite target
  observations retain their original groups; they are not distributed to members.
  Native drug IDs, support sources, activity/units/relation/action remain unchanged.
- All received activity-unit cells are empty: no physical unit, log scale or potency
  is guessed. TPI1 not-listed differs from failed access and biological absence.
- [Resource CC BY-SA 4.0](https://drugcentral.org/privacy) retains source attribution,
  change notices and share-alike; linked input/publication rights remain separate.
  No chemical/sequence/SQL search, clinical interpretation or card enrichment.
- The [fourth five-source review](archive/local_work_2026-07/batch_04_source_review.md)
  also records MetalPDB, ECOD, 3did and GWAS Catalog as evaluating.


### ClinGen — native gene-disease validity (development recovery)

- `get_gene_validity` reads the [official native CSV export](https://search.clinicalgenome.org/kb/gene-validity/download)
  through shared transport. Complete preamble/header and every row are validated
  before exact local HGNC selection. Fixture/query-bound CSV/gzip clients preserve
  original text/time, optional byte SHA and independent local/replay receipts.
- The public fixture contains 3702 curations. BRCA1 has two declarations with
  different MONDO diseases, AD/AR, SOP10/SOP7 and dates. `map_gene_validity` keeps
  each occurrence, original index and full response support on a source-gene subject.
- Legacy CGGCIEX and newer CGGV report namespaces both occur. Some classification
  dates omit timezone; UTC is not filled. File creation/classification dates remain
  source labels, separate from unknown dataset/gene/sequence revisions.
- TPI1 is not listed in the received export. That differs from a source row declaring
  No Known Disease Relationship, a missing file or failed access. Classifications,
  expert panels and inheritance are not ranked or transferred to proteins/variants.
- [CC0 curated content](https://clinicalgenome.org/docs/terms-of-use/) retains
  requested source/access-date attribution. No report/publication/sequence fetch,
  variant interpretation or automatic card enrichment is added. Other scopes are
  outside this reader. The [second five-source review](archive/local_work_2026-07/batch_02_source_review.md)
  records the original COSMIC/HPO/OmniPath/ELM review; OmniPath is now recovered
  in the second integration follow-up, while the other three remain evaluating.

### Human Protein Atlas — native gene summary (development recovery)

- `get_gene_profile` reads the [documented single-gene JSON subset](https://www.proteinatlas.org/about/download)
  for one exact human ENSG gene. Online/fixture/query-bound JSON/gzip clients retain
  the complete response, optional original-byte SHA and original-time replay.
- Public TPI1 has 22 native RNA/protein categorical declarations. `map_gene_summary`
  retains each field/value on a source-gene subject. Native null and missing keys
  stay distinct; a gene label/UniProt pointer does not establish protein or isoform
  identity, full tissue/assay coverage or an experimental class.
- Quantitative expression/intensity/concentration/prognostic context remains raw
  in the envelope; no normalized measurement is projected. Native scientific
  revisions are unknown. Website release 25.1 is not assigned to the gene record.
- [CC BY 4.0](https://www.proteinatlas.org/about/licence) applies to copyrightable
  database parts with third-party constraints retained. No automatic card intake.
- The [five-source review](archive/local_work_2026-07/batch_01_source_review.md)
  records the original GtoPdb/WikiPathways/Monarch/MEROPS review. WikiPathways and
  Monarch and MEROPS now have scoped recovered readers; GtoPdb remains evaluating.
  Their useful requirements and concrete outstanding qualifications are preserved.

### SIGNOR — native causal declarations (development recovery)

- `get_relations` qualifies the [documented native endpoint](https://signor.uniroma2.it/APIs.php)
  for one exact base UniProt accession and requested organism 9606/10090/10116.
  Original headerless TSV and its optional empty trailer survive, without losing
  the first row. Native TSV/gzip snapshots bind source/query and optional byte SHA.
- HsTIM (P60174, requested 9606) returns three rows, starting with SRC regulating
  TPI1 quantity by stabilization through phosphorylation. The other rows describe
  causal chemical modification of named metabolites, not generic protein binding.
- AKT1 (P31749, requested 9606) returns 456 rows, with native taxa 9606, 10090,
  10116, 9534, -1 and blank. The [curation manual](https://signor.uniroma2.it/documentation/)
  defines -1 as in-vitro context. Complexes, families, indirect relations, self
  interactions, publication `Other`, residue motifs and all contexts stay literal.
- Requesting P31749 with 10090 returns exactly `No result found.`. Preserve it as
  a native query declaration, distinct from failed access and biological absence.
  No independent total or export/relation/sequence/score revision is provided.
- Source scores are not interpreted as physical binding probabilities; historical
  SIGNOR 3.0 score documentation is not assigned as this response's model revision.
  Native DIRECT flags do not create generic binding or experimental classifications.
  Publication pointers/sentences retain original context without article downloads.
- [Official SIGNOR 4.0 terms](https://signor.uniroma2.it/documentation/), reviewed
  2026-10-06, declare CC BY 4.0. Attribute SIGNOR, link the licence and indicate
  adaptations; underlying publications/inputs retain independent rights. No
  pathway/network expansion, current sequence placement or automatic card intake.

### APPRIS — independent native gene annotations (development recovery)

- `get_gene_annotations` qualifies the [official exporter](https://apprisws.bioinfo.cnio.es/apidoc/gold/exporter)
  for one exact human ENSG ID, using provider defaults and one shared JSON GET.
  Fixture and query-bound supplied JSON/gzip access preserve original bytes/time.
- The unchanged TPI1 response has 1010 rows, 60 principal declarations and 21
  distinct transcript references. `ENST00000396705` occurs in five principal rows
  with `PRINCIPAL:1`/`PRINCIPAL:2`, names TPI1-202/TPI1-008, genomic starts
  6867531/6976695 and different RNA lengths. These are alternatives, not overwrites.
- `map_annotations` retains each occurrence on the explicit source-gene subject,
  with original APPRIS/FIRESTAR/CRASH/CORSAIR labels, scores, notes and flags.
  Genomic positions and `pep_position` notes are not current protein coordinates.
  No assembly/dataset/record/transcript/sequence revision is returned in these rows.
  No principal selection, identity merge, protein/card intake or linked acquisition.
- The [official APPRIS licence](https://appris.bioinfo.cnio.es/partials/license.html),
  reviewed 2026-10-06, states CC BY-NC-SA 4.0. Terms and archive retention preserve
  noncommercial, attribution and share-alike obligations; linked input/publication
  rights stay separate. Dataset bibliography is distinct from underlying support.

### Complex Portal — native complex/participant context (development recovery)

- `get_complex` reads one exact primary CPX accession, with online, fixture and
  query-bound supplied JSON/gzip implementations. [Native API](https://www.ebi.ac.uk/intact/complex-ws/complex/)
  and [provider conventions](https://raw.githubusercontent.com/Complex-Portal/complex-portal-documentation/master/documentation/data_content.md).
- `map_complex` preserves the full complex response; `map_participants` preserves
  every native participant occurrence with original complex support, types/roles,
  stoichiometry and feature/range/reference alternatives. Equal rows are not merged.
- Three unchanged native fixtures qualify the route: `CPX-2158` (hemoglobin,
  including heme), `CPX-3055` (translocon) and `CPX-14819` (ML-predicted complex
  including public HsTIM). The latter has five participants with null stoichiometry,
  native `ECO:0008004` and confidence score 1; no experimental class/probability is
  assigned. Native ECO support is distinct from MOLI Evidence.
- Feature links can refer to objects absent from this response; `?-?` ranges stay
  unknown. No direct binary interaction, graph closure, participant equivalence,
  shared-species inference or current UniProt placement. Record/sequence revisions
  are unstated; `releaseDates` does not provide them or versioned CPX suffixes.
- Detached acquisition, native hashes and original-time replay retain one GET,
  with dataset credit. Snapshot metadata remains caller-declared; missing files
  and HTTP failures are separate. Search, secondary IDs, linked resources and
  jobs are not followed. No card enrichment or frozen schema change.
- [Official CC0 1.0 data grant](https://raw.githubusercontent.com/Complex-Portal/complex-portal-documentation/master/about/license_privacy.md)
  explicitly covers webservice data, reviewed 2026-10-06. Software/branding are
  separately Apache 2.0; linked resources/publications keep their own rights.

### CATH — explicit native domain summaries (development recovery)

- Online/fixture/query-bound snapshot clients and `get_domain_summary(identifier,
  release)` read one native structural domain on a caller-selected fixed route.
  Official API: [provider documentation](https://github.com/UCLOrengoGroup/cath-api-docs).
- Four unchanged public summaries qualify the format: `1htiA00`, `1cukA01`,
  `3g06A01`, `3a85A01`, all requested on `v4_4_0`. The response itself does not
  state release, record or sequence revision. Route labels never fill those gaps.
- `map_domain` retains the complete nine-level classification, native family/group
  labels, independent ATOM/COMBS sequences and every original residue/segment.
  `3g06A01` has 325 COMBS/316 ATOM residues and nine unstated PDB locations;
  `3a85A01` has two discontinuous segments with independent SEQRES/PDB bounds.
- GO/EC alternatives/support and extra context remain literal on a CATH-domain
  subject. No UniProt entity equivalence, independent functional/experimental class,
  canonical offset, structural coverage extrapolation or automatic card intake.
- Single-GET transport/archive access retains original times, hashes and dataset
  credit. Bound supplied JSON/gzip files validate exact source/query and optional
  original-byte digest, without claiming remote access. HTTP errors are failures.
  Other domains, linked records, alignments, coordinates and jobs are unqueried.
- [Official CATH CC BY 4.0 statement](https://www.cathdb.info/), reviewed 2026-10-06;
  attribution and modification notices apply, with separate parent-resource rights.

### UniProt — explicit native isoform sequences (development recovery)

- **Access:** full parent JSON then only the explicitly selected isoform FASTA;
  online and supplied-file clients use shared transport/archive. No query for other
  isoforms or linked providers. Parent success survives a subsequent FASTA failure.
- **Mapping:** P60174 names `1`, `2`, `3` correspond to IDs `P60174-1`, `P60174-3`,
  `P60174-4`, with native lengths 249, 286, 167. Exact header IDs and native parent
  declarations establish the association. Displayed sequence equality is checked;
  Described VAR_SEQ pointers stay raw and are not reconstructed or projected.
- **Revision:** observed parent entry version 212/canonical sequence version 4 and
  live release 2026_03 remain separate from unknown isoform sequence revision.
- **Scope:** missing/partial declarations, explicit not-listed/empty arrays and
  unknown/external/not-described statuses remain distinct and query no speculative
  sequence. Multiple/wrong FASTA records, cuts and malformed context fail closed.
  Unavailable files and HTTP failures do not establish biological absence.
- **Use:** detached assertions can supply the existing source sequence residue
  reader without card mutation, canonical/structural remapping or automatic intake.
  Canonical exact-sequence candidates remain canonical-only. Data are CC BY 4.0.

### SWISS-MODEL Repository — native metadata (development recovery)

- **Access:** one unfiltered public v2 JSON GET for a base UniProt accession,
  shared transport, supplied-file fixture and archive replay.
- **Mapping:** P60174 returns 30 occurrences (29 PDB, one SWISSMODEL), with 57 paired
  alignments on its returned 249-residue source sequence. Every provider, method,
  template, chain, score dictionary, ligand/complex context and download pointer
  stays native. Target peptides, paired columns and outer bounds are validated.
- **Identity/scope:** MD5 hashes the target sequence, not a model. Coordinate/
  ModelCIF URLs are mutable; equal hashes/templates do not merge occurrences.
  API/query/creation/release dates are separate from unknown record/model/sequence
  revisions. CRC64 stays literal. Scores and template numbering remain source-scoped;
  no current UniProt equivalence, author/label projection or quality class is inferred.
- **Terms/limits:** CC BY-SA 4.0 for provider-generated data, with attribution/
  share-alike and separate parent-resource/article rights. Explicit empty arrays,
  unavailable files and HTTP failures stay distinct. No structure selection,
  coordinate/template/publication query, modelling job or card enrichment is added.

### AmyPro — investigated-sequence aggregation context (development recovery)

- **Access:** one public complete-JSON-export GET, fully validated before selecting
  an explicit native entry ID. The whole received array and original time/hash stay
  in the envelope. Shared fixture/archive access follows the same native checks.
- **Mapping:** 125 received entries contain 156 regions. AP00015 (alpha-synuclein)
  supplies one independent context assertion and three regions on `AmyPro:AP00015`,
  under subject `amypro:AP00015`. Native category/prion strings, parent UniProt/PDB
  pointers, bounds, mutations and entry-level PubMed references remain literal.
- **Scope:** regions match the investigated sequence; parent correspondence is
  not inferred. Native AP00012/AP00009 parent bounds disagree with entry lengths
  and remain unprojected. Empty region dictionaries do not erase entry context.
  No native total, current export/entry/sequence revision or per-region method/
  publication support is supplied. Site/footer and HTTP dates are not revisions.
- **Limits:** individual `.json` downloads currently contain Python literals and
  are not queried/evaluated. No sequence search, current UniProt lookup, entity merge,
  experimental class, coordinate/publication download or card enrichment is added.
  Separate data reuse licence remains unstated; the article's rights are separate.
- **Related prototypes:** ConSurfDB and FireProtDB are deferred after official
  access/reuse review. Their native scoring/measurement/sequence contracts and
  applicable reuse scope must be qualified before restoring the synthetic adapters.

### AlphaFill — precomputed model ligand context (development recovery)

- **Access:** existing public AFDB-derived metadata GET, shared transport/archive
  and unchanged native HsTIM fixture. No coordinates or calculation job is requested.
  Built-in live access from outside the checkout passed on 2026-10-06 with one
  received response and one network attempt in the shared development environment.
- **Mapping:** one declared model and 86 transplant alternatives from 55 hits.
  Model fragment, compound/analogue labels, donor numbering and zero-based native
  alignment starts remain literal. RMSD and transplant clash score use angstrom
  quantity nodes; PAE, distances and optional validation stay raw source context.
- **Scope:** model/transplant assertions describe source calculations, not observed
  target binding. Software 2.1.1 and run date 2023-12-22 are not the unknown metadata
  revision; native input file paths do not establish current AlphaFold identity.
  No UniProt residue projection, coordinate URL fabrication or automatic card intake.
- **Terms:** provider permits use/redistribution with attribution and parent
  AlphaFold conditions. BSD software is not assigned as a data licence.

### LIGYSIS — public segment site declarations (development recovery)

- **Access:** one explicit accession/segment public HTML GET, shared transport/archive
  and full unchanged HsTIM segment-1 fixture. Six inline JSON declarations are read;
  no scripts, linked assets, coordinate downloads or private server paths are requested.
  Built-in live access from outside the checkout passed on 2026-10-06 with one
  received response and one network attempt in the shared development environment.
- **Mapping:** two sites, with 20 and 7 residues respectively, native IDs/clusters,
  DS/MES/FS scores, percent RSA and original numbering. Native totals are 9 ligands
  and 8 structures; neither their individual records nor other segments are acquired.
- **Scope:** source-calculated site context with unknown source sequence/revision.
  Site IDs convey no functional ranking. Changed page format, unsafe expressions,
  duplicate keys, inconsistent counts and membership fail closed. No canonical
  placement, reconstructed ligand identities or automatic card intake.
- **Terms:** public/commercial website access and MIT software are separate from
  unstated data redistribution rights; source data terms remain `NOT-STATED`.

### GlyGen — source-scoped modification records (development recovery)

- **Access:** native public protein-detail GET without pagination, shared transport
  and original-time archive replay; full unmodified public HsTIM fixture.
  Public native download succeeded; subsequent built-in live qualification exhausted
  both 30- and 60-second waits, and repeated curl also timed out. Online service health
  remains unqualified; fixture mapping and mocked shared-transport replay pass.
- **Mapping:** three glycosylation and thirteen phosphorylation rows on the declared
  P60174-1 sequence. Retain native categories, glycan/kinase context, support pointers
  and comments about provider-stated P60174-3 correspondence. Peptide `site_seq`
  is distinct from the native `residue`; alternatives are not collapsed.
- **Scope:** complete modification tables require exact native `section_stats` totals.
  Other raw sections remain unqualified. Ranges, missing numbering and out-of-axis
  numbers stay native metadata without single-residue placement. No guessed curated
  or experimental class, sequence reconstruction or current UniProt equivalence.
  Introduction release history and Swagger service version are not record revisions.
- **Limits:** no automatic card enrichment or direct access to referenced iPTMnet,
  GlyTouCan, publications or other contributing resources. Current residue-knowledge
  views do not yet admit these PTM assertions. CC BY 4.0 applies to GlyGen database
  sets with attribution; contributing-source and publication rights remain separate.
- **Related source:** iPTMnet now has a scoped native HTML report reader. Earlier
  P60174/P37840 REST HTTP 503 failures stay independent; GlyGen pointers themselves
  do not establish direct iPTMnet acquisition or a canonical sequence mapping.

### EPPIC — source-calculated structural interpretations (development recovery)

- **Access:** native REST v3 `job/pdb`, `job/interfaces`, `job/assemblies` responses
  for one four-character public PDB ID, through shared transport and native fixtures.
- **Mapping:** nine 1HTI interfaces and three assemblies, including unit-cell ID 0,
  alternatives and literal EPPIC/pdb1 method calls. Areas are explicit square-angstrom
  quantities. Chain/operator namespaces and EPPIC IDs are not UniProt positions or
  wwPDB assembly identifiers. Negative score/confidence sentinels are preserved.
- **Scope:** three separate component acquisitions and original timestamps/hashes;
  prediction/statistical record revision remains unknown. Native EPPIC version/build
  `NA`, UniProt run version and releaseDate remain separate context. The native
  exhaustive-assembly flag is preserved independently of output truncation.
- **Residue detail:** separate explicit `get_interface_residues` reads native
  interface context plus one selected residue table in two component acquisitions,
  retaining per-side serials, zero/NaN, region/entropy and square-angstrom ASA/BSA.
  The annotation bundle does not request these rows. Other interface residue tables
  remain unqueried.
- **Limits:** no coordinate downloads, numbering projection, geometry calculation,
  experimental confirmation, automatic assembly selection or card enrichment.
  Separate prediction-data reuse licence remains unstated; software/API licences
  are not data licences. A failed later component retains earlier access receipts.

### PDB-REDO — existing databank refinement context (development recovery)

- **Access:** public `data.json` and separately requested `versions.json` files,
  observed online/fixture access and original-time HTTP archive replay.
- **Mapping:** literal deposited, Refmac baseline, restrained-refinement and final
  R-factors for 1CBS; null, zero and absent keys stay distinct. Input revisions and
  native software `used` flags remain separate source context. Full other properties
  and original/redo residue arrays remain raw rather than becoming guessed quantities.
- **Scope:** pipeline 8.22 and entry creation date 2026-09-02 are not a databank
  revision. No current-coordinate revision or scientific improvement is inferred.
- **Limits:** no remote job submission, coordinate download, automatic model replacement,
  fabricated coordinate URL or card enrichment. Native 1HTI access returned HTTP 500
  during recovery; this is a service failure, not evidence that a record is absent.
  Official reuse policy permits original redistribution and commercial/non-commercial
  use with stated attribution and parent-data conditions; no CC licence is inferred.

### PDBe Validation — entry-wide metrics (development recovery)

- **Status:** explicit single-entry access and independent structure-subject
  assertions; no automatic card enrichment or structure-selection heuristic.
- **Access:** `/pdbe/api/validation/global-percentiles/entry/<pdb_id>` through shared
  transport, frozen public response bytes and original-time archive replay. The
  current official OpenAPI documents this route with four-character PDB IDs;
  its service version 2.10.9 is not a validation/statistical revision.
- **Coverage:** exact entry identity, raw values, archive-wide and optional
  comparable-entry percentile ranks (native 0–100 scale). Unknown numeric metrics
  and additional source context remain literal. Missing metrics are not zero.
- **Qualification:** native 1HTI has three metrics and 1CBS has five, including
  zero RSRZ/Ramachandran outliers and DCC R-free 0.1871. Invalid identities,
  malformed/non-finite values, out-of-domain percentiles, missing fixtures,
  API failures and original-time replay are guarded.
- **Limits:** no per-residue projection, quality threshold, inferred experimental
  method or normalized raw-value units. Validation software, statistical revisions
  and comparison population counts are unstated. EMBL-EBI terms are reviewed;
  a separate licence for this API response is not established.

### MobiDB — source annotations and modifications (development recovery)

- **Status:** direct native v1 export and independent disorder/modified-residue
  mappings; no automatic card enrichment.
- **Access:** single canonical `/api/v1/protein/<accession>/export?format=json`;
  online shared transport and public body/header fixtures. Scope headers remain
  available in archive replay. Legacy document endpoints are not the new contract.
- **Coverage:** native sequence/release, all annotation sets, interval provenance,
  residue series, semantic/unit definitions, stored versus normalized coverage and
  explicit representation issues. `mobidb_valid_region_sets@1` excludes sets with
  issues while preserving the complete raw export. Homology, prediction, curation
  and derived bases stay separate; PTM experimental basis may be unstated.
- **Qualification:** native P60174 (30 disorder intervals, 19 modifications) and
  P37840 (43 disorder intervals, 4 modifications), with negative identity, release,
  interval, scope and replay cases. Native database release is 7.0 / 2026_07, API v1.
- **Limits:** canonical access only; no current-UniProt/isoform projection or inferred
  ontology IDs. Raw series are not automatically turned into probabilities/tracks.
  The AlphaFold-disorder series is smoothed relative solvent accessibility.

### SIFTS — explicit structural correspondences (development recovery)

- **Status:** direct single-entry segment access and independent structure-subject
  assertions; no card enrichment or calculated residue mapping.
- **Access:** PDBe `/api/mappings/uniprot/<pdb_id>` and public fixture files.
- **Coverage:** exact PDB identity, all native protein/isoform references, entities,
  author/label chains, UniProt ranges and internal/author endpoint numbers and
  insertion codes. Source identity/coverage fractions are retained literally.
- **Qualification:** native 1HTI maps chains A/B to P60174 positions 2–249, with
  internal positions 1–248. Negative/missing numbering, insertions, distinct
  references, incomplete/failed access and original-time replay are guarded.
- **Limits:** four-character PDB IDs; source and reference-sequence revisions are
  unstated. Endpoints do not establish per-residue linear correspondence through
  gaps. EMBL-EBI general terms are reviewed; a separate SIFTS-wide licence remains
  unstated, rather than borrowing PDBe-KB's CC BY licence.

### AlphaMissense — precomputed variant predictions (development recovery)

- **Status:** implemented direct access and independent assertion mapping;
  no automatic card enrichment or new inference.
- **Access:** source-declared canonical human `amAnnotationsUrl`, following one
  exact full descriptor in AlphaFold DB discovery. Online shared transport and
  native public fixtures keep separate host/artifact acquisitions and archive replay.
- **Coverage:** full native CSV validation before output caps, byte hashes/literals,
  unique reference-checked substitutions, finite [0, 1] scores, missing values,
  native/future classes and computed substitution-grid coverage.
- **Qualification:** native HsTIM discovery/CSV and negative integrity, empty/
  unavailable/failure and archive-replay cases. Bounded live access on 2026-10-06
  received two responses and mapped all 4731 substitutions independently.
- **Limits:** full canonical human descriptors only; fragmented/ambiguous contexts
  are refused and isoform/genome artifacts are unqueried. Score revision is unknown;
  AlphaFold model v6 and host sequence dates are separate metadata. Source sequence
  binding does not establish current UniProt placement. Predictions retain their
  provider meaning, separate from clinical observations. Data terms are CC BY 4.0.

### UniParc — exact sequence candidates (development recovery)

- **Status:** implemented direct checksum search and explicit candidate tool;
  no automatic entity resolution or card enrichment.
- **Access:** official REST `/uniparc/search`, shared online transport and native
  fixture files under `uniparc/search__<MD5>.json`.
- **Coverage:** bounded validated pagination, native totals/releases/pages,
  source sequence and UniProtKB reference list, historical revision preservation,
  isoforms explicitly unqueried, and independent archive assertions. Candidate
  checks compare full current canonical UniProt sequences and exact primary
  accessions, with optional exact NCBI taxon filtering and explicit failures/caps.
- **Qualification:** native HsTIM search fixture, synthetic negative/pagination
  regressions and original-time archive replay. Live search on 2026-10-06 returned
  four distinct current canonical matches (P60175, P60174, A0A7N5JJ02, V9HWK1);
  two entries were inactive, and Q6FHP9 redirected to another primary accession,
  recorded as failed validation. The report remains partial with eight accesses.
- **Limits:** only the returned UniProtKB search references are checked; other
  database references and publications are not fetched. `.N` native associations
  do not prove current sequence identity; isoform sequences are not fetched.
  Equal sequences never establish entry equivalence. Database CC BY 4.0 does
  not grant rights in linked sources. Release headers are not sequence revisions.

### AAindex1 — amino-acid reference indices (development recovery)

- **Status:** implemented direct access; no automatic protein enrichment.
- **Access:** shared HTTP transport to the official AAindex1 download;
  `OnlineAAindexClient.index` / `get_index(identifier)` and supplied native files
  through `FixtureAAindexClient(directory)` (`aaindex/aaindex1`).
- **Coverage:** strict complete-document validation, native paired amino-acid order,
  20 numeric literals including `NA`, description/authors/title/journal/reference
  pointers, download hash and detached acquisition. `map_index` produces separate
  amino-acid-type SourceAssertions, never a protein-position prediction.
- **Qualification:** synthetic offline regressions; manually parsed seven requested
  indices from the official download on 2026-10-06. This does not validate every
  scientific scale or create a redistributed native fixture.
- **Limits:** release and structured units are unstated in the artifact; neither is
  inferred. Linked publications are not acquired. Reuse licence remains unknown
  (`NOT-STATED`); this download is not licensed by Sabueso's MIT licence.

### DisProt — source-scoped disorder regions (development recovery)

- **Status:** implemented direct access; no automatic card enrichment.
- **Access:** native `/api/search?acc=<canonical-UniProt-accession>` through shared
  HTTP transport, fixture files or a bound `SnapshotDisProtClient` file.
- **Coverage:** native sequence/record identity, integer region coordinates/revisions,
  ontology terms, publication pointers, record counts and default-region subset.
  `map_disorder_regions` selects only structural-state `IDPO:0000002`, preserving
  DisProt sequence identity/hash instead of assuming current UniProt numbering.
- **Qualification:** offline integrity, supplied-file, empty/unavailable/failure and
  archive-replay regressions; a trimmed native P37840 response retrieved 2026-10-06
  keeps all 22 returned regions while retaining the declared count of 40.
- **Limits:** global release remains unstated; region revisions are not global
  versions. Underlying publications are not acquired. Database CC BY 4.0 does
  not grant rights to quoted article fragments or establish coordinate equivalence.

### UniProt
- **Status**: implemented
- **Access**: online API, local JSON
- **Quality**: green for the listed coverage. Offline tests on five fixtures, including HsTIM (P60174) and TcTIM (P52270), compare mapped counts against the raw records (uibcdf/sabueso#13).
- **Coverage**:
  - identifiers, canonical name, organism;
  - free-text comments: function, pathway, subunit, tissue specificity, PTM, polymorphism; development 0.3.13 also retains activity regulation, domain notes, similarity, source cautions and miscellaneous text;
  - catalytic activity as `{reaction, ec_number, rhea_id, molecule?}`;
  - subcellular location as `{location, topology?, orientation?, molecule?}`;
  - sequence: primary, length, molecular weight in Da, CRC64/MD5 checksums;
  - positional features: binding and active sites, modified residues, disulfide bonds, glycosylation, natural variants and mutagenesis (substitution, verbatim description, `VAR_` id and cross-references; uibcdf/sabueso#33). A deletion ("Missing") is `substitution.missing` (#80);
  - isoforms (ALTERNATIVE PRODUCTS: ids, names, synonyms, sequence status, `VSP_` ids; events and note) and alternative sequences, linked to the isoforms the entry lists for them (#80);
  - secondary structure (helix, strand, turn), each segment with the PDB entries it was read from (#80);
  - PDB cross-references as `has_structure` relationships (method, resolution, chains, UniProt-numbered ranges, coverage), shown through `Card.structures()`;
  - GO cross-references as `annotated_with` relationships (aspect, term, GO code, assigned by; ECO in `source_metadata`);
  - InterPro, Pfam, Gene3D (CATH), SUPFAM, PANTHER, PROSITE and CDD cross-references as `classified_in` relationships;
  - curated INTERACTION comments (IntAct binary interactions) as `interacts_with` relationships;
  - UniProt evidence qualifiers kept per SourceAssertion as `source_metadata.eco`.
- **Known limits**:
  - development 0.3.13 recovers native domains, chains, lipidation, motifs, regions, sequence conflicts, topological domains and transmembrane features. Original bounds/modifiers, full source feature, molecule restriction, ECO and sequence revision remain supported; fuzzy/missing/foreign or known revision-mismatched locations stay unplaced. Source caution text is `annotations.source_cautions`, never a quality conclusion; source similarity never supplies identity. Other kinds (for example cross-link, initiator methionine and SEQUENCE CAUTION) remain unmapped;
  - explicit native isoform FASTA access is available in development (see the isoform section); automatic resolution/reconstruction from alternative sequences remains unimplemented;
  - UniProt's secondary structure comes from the PDB entries each segment cites, often several; it describes those structures, not the protein in every state or construct;
  - the stated effect of a variant or mutagenesis is free text, kept verbatim: "thermolabile" or "abolishes ligand binding" is not turned into a category;
  - isoform restrictions (`molecule`) are part of the value for catalytic activity and subcellular location. For free-text comments they are on the SourceAssertion (`source_metadata.molecule`, since 0.3.6), since the value is the stated text;
  - identical repeated values in one record share one SourceAssertion id.
  - INTERACTION comments are UniProt's curated subset of binary interactions: 3 for human TIM, while its IntAct cross-reference reports 75. Full interaction data would need IntAct, STRING or BioGRID directly.
- **Notes**: stable online tests

### RCSB PDB — polymer-entity mapping (GraphQL)
- **Status**: implemented (uibcdf/sabueso#6, step 4b)
- **Access**: online GraphQL (`OnlineRCSBClient`), 25 entries per request (`fetch_structures`, `entries(entry_ids: [...])`, #98); saved entries (`FixtureRCSBClient`, `temp_data/rcsb/`). For 40 EGFR entries: 5.6 s batched against 13.1 s one at a time, with the same knowledge (content id).
- **Quality**: green for the listed coverage. Verified on 1HTI, 1KLG, 1TCD, 1SUX, 2OMA, 2VOM, 3Q37, 4HHP and 4UNK, and live on every entry of TcTIM and HsTIM (2026-09-25).
- **Coverage**:
  - `has_structure` relationships per UniProt accession aligned to polymer entities: chains, UniProt-numbered ranges, method, resolution;
  - since schema 0.3.4, what choosing a structure needs:
    - R-free and R-work, deposit and release dates;
    - the construct: length, expression host and tags;
    - mutations as RCSB marks them, placed in UniProt numbering;
    - sequence differences against the UniProt sequence;
    - per chain, the UniProt ranges with coordinates (`SCHEMA.md`);
  - since schema 0.3.6, per chain, helices and strands (`HELIX_P`, `SHEET`) in UniProt
    numbering, with the assigning program (`provenance_source`, e.g. PROMOTIF; #80);
  - polymer entities, the other entities present, and bound ligands;
  - structure facts keep `pdb:<id>` as SourceAssertion subject;
  - `EntityResolver` resolves `pdb:<id>` to the structure record and its proteins.
- **Notes**: one request per entry. Each ligand carries its per-instance neighbour residues (`rcsb_ligand_neighbors`), mapped to UniProt numbering through the entity alignment. Ligand lists include every non-polymer entity (buffers and solvents too). Each ligand carries the PDB "subject of investigation" flag and its provenance (`Author`, or `RCSB` for older entries), which `ligand_deck` uses by default (uibcdf/sabueso#25, item 3). RCSB returns entities in no fixed order, so the mapping sorts them.

### PDB (RCSB) — entry metadata cards (removed)
- **Status**: removed 2026-09-23 (uibcdf/sabueso#21)
- **Notes**:
  - `create_structure_card_*` and `mappings/pdb.py::map_structure` built one card per PDB entry, typed as a protein, with scalar `structure.entry_metadata.*` fields. That was a structure card in all but name, contrary to the decision "no StructureCard" (#6, #20).
  - Structures are now `has_structure` relationships (see *RCSB PDB — polymer-entity mapping* above and the UniProt coverage).
  - Current polymer-entity relationships already retain accession dates and primary citation on the PDB structure context. Entry `struct.title` remains unmapped; qualify its acquisition and structure-subject support before adding it to `Card.structures()`.
  - `tools/db/pdb.py::fetch_pdb_json` (raw REST entry) remains.

### PubChem
- **Status**: implemented
- **Access**: online API, local JSON
- **Quality**: green
- **Coverage**: native summary-page `Title` as independently supported `names.canonical_name` (development recovery; `source_metadata.pubchem_property: Title`), formula, MW, isomeric SMILES (`identifiers.smiles`) and connectivity SMILES (`identifiers.smiles_connectivity`), InChI/InChIKey, XLogP3, TPSA, HBD/HBA, rotatable bonds; PubChem compounds are InChIKey-anchored like any small molecule (uibcdf/sabueso#25)
- **Structure lookup** (#93): `smiles:` and `inchi:` queries are matched by PubChem (POST `compound/<notation>/cids/JSON`; `tools.db.pubchem.get_structure_match`). CID 0 means PubChem holds no such compound, and HTTP 400 that it cannot read the structure.
- **Description semantics**: request `Title` with the existing compound property GET; keep native spelling, CID subject and retrieval, with unknown record revision. Missing/null/empty titles stay unstated; malformed nontext/blank-only titles fail. No IUPAC-name fallback or title-based molecular identity. Full PC_Compounds fixtures do not supply a summary title. Native title replay and conflict/identity guards: `tests/core/test_pubchem_title_recovery_offline.py`; original three-CID public response and terms: `temp_data/NOTICE.md`.
- **Notes**: PubChem's `SMILES` (formerly `IsomericSMILES`) keeps stereochemistry and `ConnectivitySMILES` (formerly `CanonicalSMILES`) does not; the isomeric one used to be dropped (uibcdf/sabueso#10). XLogP3 and rotatable bonds carry their method. Stable online tests.

### ChEMBL
- **Status**: implemented
- **Access**: online API, local JSON
- **Quality**: green
- **Coverage**: identifiers, preferred name, molecule type, formula, physchem (ALogP, HBD/HBA, TPSA, rotatable bonds, aromatic rings, molecular weight as `full_mwt`), `max_phase`, InChI/InChIKey, isomeric SMILES
- **Notes**: numbers ChEMBL serialises as strings are normalized; logP and rotatable bonds carry their method (`ALogP`, `chembl:rtb`) and are compared only within it (uibcdf/sabueso#10). Stable online tests.

### gnomAD — population frequencies
- **Status**: implemented as an enricher of `resolve_protein_card(..., gnomad={})` (uibcdf/sabueso#83)
- **Access**: GraphQL API, dataset gnomad_r4, no key (`OnlineGnomADClient`): the gene's variants, and the variants of each Ensembl transcript UniProt states for the canonical isoform (#85); saved answers in `temp_data/gnomad/`; `tools.db.gnomad.get_variants`, `tools.db.gnomad.get_transcript_variants`
- **Quality**: green for the listed coverage. Verified live on TPI1 (ENSG00000111669, 2026-09-29): 1,668 variants, of which 729 have a protein change. E105D, on the canonical transcript ENST00000396705, is placed at UniProt 105 with its exome and genome frequencies.
  - Placement: 540 placed, 2 of them through isoform P60174-3's map. 184 fall in that isoform's own N-terminal segment, and 2 are on transcripts UniProt does not state. 3 are not placed: two stop-codon changes and one unparsed notation.
  - With the canonical transcript asked too (2026-09-30, #85): gnomAD states each variant's consequence on it, so a change it ranks on another transcript is read on the canonical one when it is a protein change there. For TPI1, 79 changes on isoform P60174-3's transcript are stated as not coding on the canonical transcript (UTR or intron), including the frameshift at isoform Pro40, which the isoform map had placed at canonical Pro3 (on the canonical transcript it is a 5' UTR duplication); 107 stay in the isoform's own segment, 540 are placed, none through the isoform map. Over nine genes, the variants on transcripts UniProt does not state fell from 810 to 533 (EGFR 161 → 88, BRCA1 83 → 38, DMD 237 → 121, MAPK14 12 → 0); checked one by one over 22 proteins (1,682 changes), none of those left is coding on the canonical transcript: 1,205 are intronic or in its 3' UTR, and for 477 gnomAD states no consequence on it. Only the canonical transcripts gnomAD annotates are asked (`not_in_dataset` for newer ones).
- **Coverage**: `annotations.population_variants`, with consequence, transcript, HGVS, flags, and exome and genome allele count, number and frequency as stated
- **Notes**:
  - Found by the Ensembl gene UniProt cross-references.
  - Variants without a protein change are left out and counted.
  - At most 1000 per gene by default, with the cut reported.
  - The API states no release finer than the dataset.
  - Human genes only.
  - Licence: CC0 1.0 (core).
  - pext (2026-10-01, #102): `exon_usage=True` reads the gene's pext (GTEx v10, GRCh38) into `annotations.exon_usage_by_tissue`, and `Card.variant_tissue_usage()` gives each variant the tissues expressing its position (`pext_at_variant@1`). Verified live: PKM's M1 exon is expressed in 23 tissues, up to 0.58 in skeletal muscle, and its M2 exon in all 49. TPI1's isoform-3 segment is expressed in testis only (0.38). GTEx's own transcript-level medians were set aside: for PKM they put the M2 transcript at 217 TPM and the M1 ones at 1-3 in skeletal muscle, because short-read quantification cannot tell two mutually exclusive exons of the same length apart, and GTEx v8 (GENCODE v26) lacks most transcripts UniProt now states.
  - Changes the isoform map would place are asked of gnomAD variant by variant (#102). PKM's 98 changes in its M1 exon and KRAS's 70 in its alternative exon 4 are stated as not coding on the canonical transcript. The isoform map had placed 14 (PKM) and 17 (KRAS) of them on canonical residues.

### ClinVar — variants and their clinical classification
- **Status**: implemented as an enricher of `resolve_protein_card(..., clinvar={})` (uibcdf/sabueso#83)
- **Access**: E-utilities (einfo for the build, esearch by NCBI Gene id, esummary), no key (`OnlineClinVarClient`); saved summaries in `temp_data/clinvar/`; `tools.db.clinvar.get_variants`
- **Quality**: green for the listed coverage. Verified live on TPI1 (GeneID 7167, Build260924-0125.1): 249 records in about 8 s. 110 have a protein change on the canonical transcript NM_000365.6, and those placed include UniProt's natural variants at 42, 105, 171 and 241.
- **Coverage**: `annotations.clinical_variants`, with the classification, review status, conditions and consequences as stated. Positions are in UniProt numbering only through a canonical transcript UniProt states and a matching residue.
- **Notes**: found by the NCBI Gene id UniProt cross-references, never by gene symbol. Every record of the gene by default, up to 5000; a cut is reported. Human genes only. Not for diagnostic use without review by a genetics professional.

### Europe PMC — publications that mention a protein
- **Explicit article metadata (since 0.13.0)**: `get_article(identifier)` queries core
  bibliography by pubmed:/pmc:/doi: with native identifiers, complete returned author
  records, journal/pages/dates and licence literals. The projection excludes abstract
  and full text; service versions are not article revisions. Explicit literal intake
  binds a unique complete source-stated publication identity under
  `article_metadata_binding@1`, preserving support/citations/declared terms through
  replay/refresh. Original access hashes, times, reuse and empty/partial/failure
  outcomes are traced. Fragment permission remains unknown; this is not implicit
  source enrichment or full-article coverage.
- **Status**: implemented as an enricher of `resolve_protein_card(..., europepmc={})` (uibcdf/sabueso#92)
- **Access**: REST search `ACCESSION_ID:<acc> AND ACCESSION_TYPE:uniprot`, cursor paging of 1000, no key (`OnlineEuropePMCClient`); saved search in `temp_data/europepmc/`; `tools.db.europepmc.get_mentions`
- **Quality**: green for the listed coverage. Verified live on HsTIM (service 6.9): 354 articles in about 4 s, 352 in PubMed and 2 preprints.
- **Coverage**: `mentioned_in` relationships to each article whose text states the UniProt accession, with title, journal, year, open access and preprint; SourceAssertions record `origin: text_mining`
- **Located annotations (since 0.12.0)**: `europepmc={"article_ids": "PMC:PMC12400196"}` asks explicit MED/PMC articles through the Annotations API. Only a printed accession with a matching UniProt URI and tag names this card. `mentioned_in` retains native article ids and per-occurrence `locations`, each with its own SourceAssertion, provider, annotation link, section and unchanged quote fragments. Empty answers, missing fixtures and failed requests remain distinct; refresh reuses the explicit article requests. The response states no pipeline release.
- **PDB mention context (since 0.12.0)**: the same explicit route accepts printed four-character PDB codes with matching PDBe tags and native URIs. A source-supported `has_structure` association already mapped on the card grounds derived `structure_mentioned_in` context (`structure_mention_context@1`), retaining both statements. Raw mention assertions are about the PDB entry. No entry identity, chain, residue or author focus is inferred; expanded codes are unhandled. The public 2JK2/Methods annotation has UniProt support; unsupported 7QON occurrences remain explicitly unlinked. Literature separates `structure_mentions` from direct `mentions`; `knowledge_state@4` separates their counts and coverage.
- **Packets (since 0.12.0)**: `packet_aspects@6` includes both mention areas in the literature index and unknowns. Automatic acquisition asks bibliography only; explicit annotations enter through prebuilt cards. An unsaved search fixture is unavailable (`ConnectorError`), never a claim that the source has no articles. Actual source-stated zero hits remain `not_stated`, with the consulted release.
- **Notes**: stated accessions only. The gene and protein annotations are not used: they ground names without the organism (a human TPI paper is tagged with a yeast entry, Q9C401). The search keeps bibliography, up to 5000 articles, newest first; a cut is reported. Located annotations contain article fragments whose terms are reported separately as unknown when unrecorded, and excluded by terms profiles. No annotation becomes a scientific claim or human curation.

### Reactome — pathways and reactions
- **Status**: implemented as an enricher of `resolve_protein_card(..., reactome=True)` (uibcdf/sabueso#83)
- **Access**: Content Service, UniProt mapping and event ancestors, no key (`OnlineReactomeClient`, which names Sabueso: the service refuses Python's default user agent); saved answers in `temp_data/reactome/`; `tools.db.reactome.get_pathways`
- **Quality**: green for the listed coverage. Verified live on HsTIM (release 97): glycolysis and gluconeogenesis, two reactions, and their ancestors up to Metabolism. TcTIM: not mapped.
- **Coverage**: `participates_in` relationships, with kind, name, species, the orthology-inference flag and pathway ancestors
- **Notes**: one request per pathway for its ancestors. The release endpoint (`database/version`) answers plain text, so it is the one Reactome request not checked as JSON (#97). Licence: CC0 1.0 (data).

### Orphadata (Orphanet) — rare disorders and their genes
- **Status**: implemented as an enricher of `resolve_protein_card(..., orphadata=True)` (uibcdf/sabueso#82)
- **Access**: `en_product6.xml` (about 22 MB, dated in its header), downloaded and indexed once per process in memory (`OnlineOrphadataClient`); saved disorders in `temp_data/orphadata/`; `tools.db.orphadata.get_associations`
- **Quality**: green for the listed coverage. Verified live on HsTIM (file of 2026-06-23, about 5 s): ORPHA:868, triose phosphate-isomerase deficiency, "Disease-causing germline mutation(s) in", Assessed.
- **Coverage**: `associated_with` relationships to `orphanet:ORPHA:<code>`, with the association type and status, the disorder's type and group, and the validating publications
- **Notes**: joined through the Swiss-Prot accession Orphanet states for each gene; genes without one are not attached. Human genes only. Licence: CC BY 4.0 (cite Orphanet and the data version).

### Open Targets Platform — target–disease associations
- **Status**: implemented as an enricher of `resolve_protein_card(..., open_targets={})` (uibcdf/sabueso#82)
- **Access**:
  - GraphQL API v4, no key (`OnlineOpenTargetsClient`);
  - saved answers in `temp_data/open_targets/`;
  - `tools.db.open_targets.get_associations`.
- **Quality**: green for the listed coverage. Verified live on TPI1 (ENSG00000111669, data 26.09): 483 associations, the first being TIM deficiency (MONDO_0014221, score 0.78). A queried native gene that the source explicitly lacks is not found. An absent upstream Ensembl gene cross-reference is unqueried before client construction, with unknown counts and no source credit ([#142](archive/open_targets_prerequisite.md)); historical stored cards are not reclassified on read.
- **Coverage**: `associated_with` relationships, with the overall score, the per-datatype scores and the rank, as stated.
- **Notes**:
  - Joined through the Ensembl gene UniProt cross-references, only when Open Targets also lists the entry among the gene's products.
  - Every association of the gene by default, up to 5000, in Open Targets' order; a cut
    is reported.
  - Human genes only.
  - Tractability, safety and evidence strings are not mapped yet.
  - Licence: CC0 1.0.

### DISEASES (Jensen lab) — gene–disease associations
- **Status**: implemented as an enricher of `resolve_protein_card(..., diseases={})` (uibcdf/sabueso#82)
- **Access**:
  - the filtered channel files from download.jensenlab.org (`OnlineDISEASESClient`), versioned by their publication date and kept in memory, or in a cache directory when one is given;
  - saved rows in `temp_data/diseases/`;
  - `tools.db.diseases.get_associations`.
- **Quality**: green for the listed coverage. Verified live on HsTIM (ENSP00000229270): 2 curated associations (TIM deficiency, congenital hemolytic anemia) and 42 text-mined ones.
- **Coverage**: `associated_with` relationships, one per disease, channel and Ensembl protein, with DISEASES's scores as stated.
- **Notes**:
  - The text-mining channel's SourceAssertions record `acquisition: {method: database, origin: text_mining}` (#92): imported from DISEASES, which states they were mined from text.
  - Joined only through the Ensembl proteins UniProt cross-references.
  - Text mining links names, not molecules, and is added only when asked for.
  - Human genes only: a non-human protein is `not_queried`, with the reason.
  - Licence: CC BY 4.0.

### ChEMBL indications and ClinicalTrials.gov — the clinical layer
- **Status**: implemented as enrichers of `resolve_molecule_card(..., indications=True)` and `trials={}` (uibcdf/sabueso#81)
- **Access**:
  - ChEMBL `drug_indication` (`OnlineChEMBLClient.indications`, `tools.db.chembl.get_indications`);
  - ClinicalTrials.gov API v2 studies by NCT id, in batches, no key (`OnlineClinicalTrialsClient`, `tools.db.clinicaltrials.get_studies`);
  - saved responses in `temp_data/chembl/indications.json` and `temp_data/clinicaltrials/studies.json`.
- **Quality**: green for the listed coverage.
  - Verified live on benznidazole (CHEMBL110): 4 indications, all phase 4 (ChEMBL_37), and the 16 trials they cite (API v2, data of 2026-09-25).
  - Missing NCT ids require a completed paginated query. Invalid responses and
    unavailable fixture answers do not establish absence (#127, development fix).
- **Coverage**:
  - `investigated_for`: disease term, MeSH heading, maximum phase and cited references;
  - `tested_in`: title, status, phases, study type, enrolment, dates, conditions, interventions as written, lead sponsor, and whether results are posted;
  - `Card.clinical()`.
- **Notes**:
  - Trials come only through the NCT ids ChEMBL cites, never by matching intervention names.
  - Adverse events (openFDA/FAERS) are not covered.
  - Development `get_study_references` retrieves native reference modules separately
    from card clinical assertions. Study/reference acquisition preserves native
    page, version, reuse and failure scope (#108); explicit Europe PMC article
    queries retain complete personal/collective authors (#128). Linked targets are
    never fetched automatically. The public release remains 0.13.0.
  - Licences: ChEMBL CC BY-SA 3.0; ClinicalTrials.gov is a US government work (credit NLM).

### ChEMBL bioactivities
- **Status**: implemented as an enricher of `resolve_protein_card` (uibcdf/sabueso#23)
- **Access**: online API (`OnlineChEMBLClient`), saved responses (`FixtureChEMBLClient`, `temp_data/chembl/`)
- **Quality**: green for the listed coverage, verified on TcTIM (CHEMBL5834) and HsTIM (CHEMBL4880), ChEMBL_37
- **Coverage**: `has_bioactivity` relationships, one per activity record. They carry the measurement, the assay (with target-assignment confidence and assay organism), the document, the tested and parent molecule, and the ChEMBL release (`source.version`). `Card.bioactivities()` gives derived activity classes.
- **Notes**:
  - The target comes from the ChEMBL cross-reference of the UniProt entry. Complex or family targets are not included.
  - Homology-assigned assays (relationship type `H`) are excluded from the default view and reported. Every HsTIM Ki in ChEMBL was measured on rabbit TIM or on TIM of unknown organism.
  - The test concentration of single-point measurements is extracted from the assay description (derived).
  - About 2 KB per measurement. `limit` (default 5000) and truncation are recorded (card size: uibcdf/sabueso#19).
  - Report: `devguide/archive/chembl_bioactivities.md`.
- **Molecules** (`molecules(ids)`, batched): identity (standard InChIKey, hierarchy), `max_phase` and the ChEMBL-asserted properties, for SmallMoleculeCards anchored at the InChIKey (uibcdf/sabueso#25). Fixture: `temp_data/chembl/molecules.json` (275 parent molecules measured on TcTIM or HsTIM).

---

## Interaction Sources

### PDB Chemical Component Dictionary (CCD)
- **Status**: implemented for small-molecule identity (uibcdf/sabueso#25)
- **Access**: RCSB GraphQL `chem_comps` (`OnlineCCDClient`), saved records (`FixtureCCDClient`, `temp_data/pdb_ccd/`)
- **Quality**: green for the listed coverage, verified on BTS, PGA and SO4
- **Coverage**: name, formula (normalized), type, standard InChI/InChIKey (`identifiers.inchi`, `identifiers.inchikey`), and a `same_as` link of `pdb.ligand:<code>` to the InChIKey anchor
- **Notes**:
  - RCSB omits unknown codes from a batch without an error. The client reports them as `missing`.
  - CCD SMILES are kept in the assertion, not in `identifiers.smiles` (a different representation from ChEMBL's; uibcdf/sabueso#10).
  - `ligand_deck` keeps, by default, only the structure ligands the PDB declares subject of investigation (item 3 of #25).

### UniChem
- **Status**: implemented for small-molecule identity (uibcdf/sabueso#25)
- **Access**: REST `compounds` by InChIKey (`OnlineUniChemClient`), saved compounds (`FixtureUniChemClient`, `temp_data/unichem/`)
- **Quality**: green for the listed coverage, verified on BTS (UCI 336651) and 2-phosphoglycolate (UCI 118810)
- **Coverage**: `same_as` links to the InChIKey anchor for ChEMBL, PDB (RCSB and PDBe), PubChem, DrugBank, ChEBI and BindingDB records. The full source list stays in the assertion.
- **Notes**: an unknown key returns HTTP 200 with `"Not found"`, which the client maps to not found. One call per molecule, and no batch query (UniChem recommends its whole-source mapping files for large mappings), so it is opt-in for decks. Lookups for BindingDB's monomers run four at once, at most five per second (#98): EGFR's 1769 monomers took 635 s (about 1.4 s per lookup), where one at a time would take about 40 minutes.

### ChEBI — chemical classes and roles
- **Status**: implemented as an option of `resolve_molecule_card(..., chebi=True)` (uibcdf/sabueso#83)
- **Access**: ChEBI 2.0 API, `POST compounds/` with up to 200 ids per request (`OnlineChEBIClient`; 200 entries in about 12 s); saved entries (`FixtureChEBIClient`, `temp_data/chebi/`); `tools.db.chebi.get_compounds`
- **Quality**: green for the listed coverage. Verified live on vincristine (CHEBI:28445): 8 classes, 7 roles (5 direct, 2 inherited), 3 stars.
- **Coverage**: `identifiers.chebi`, native `names.canonical_name` and `properties.physchem.formula` with independent SourceAssertions, `annotations.chemical_classes` (`is a`), `annotations.chemical_roles` (`direct` for the entry's own `has role`, otherwise inherited through its classes or parent roles; biological, chemical or application, as ChEBI flags them), `annotations.definition` (markup kept in the assertion, plain text as the value), and a `same_as` stated by ChEBI
- **Notes**: reached only through UniChem's link, and joined only when the InChIKey ChEBI states for the entry is the anchor. A secondary id is answered by its primary entry. Licence CC BY 4.0.

### BindingDB — affinities
- **Status**: implemented as an enricher of `resolve_protein_card(..., bindingdb={})` (uibcdf/sabueso#66)
- **Access**: REST `getLigandsByUniprots` (`OnlineBindingDBClient`), saved responses (`FixtureBindingDBClient`, `temp_data/bindingdb/`), `tools.db.bindingdb.get_affinities`; monomers anchored at their InChIKey through UniChem (source 31)
- **Quality**: verified on TcTIM (17 records: 16 grouped with ChEMBL, one attributed by ChEMBL to another molecule) and HsTIM (23 records: 13 grouped, 3 from a paper ChEMBL lacks for the target, 5 monomers UniChem does not hold, one with another stereochemistry than ChEMBL's)
- **Coverage**: `has_bioactivity` relationships with the ChEMBL layout (`source: BindingDB`, `stated_value` keeps the written precision); measurements shared with ChEMBL are grouped by `measurement_identity@1`
- **Mirror** (#100): `sabueso.mirrors.install("bindingdb")` downloads the monthly `BindingDB_All_<yyyymm>_tsv.zip` (about 600 MB; 9 GB unpacked), checks its published MD5 and indexes it by UniProt accession (release 202609: 3,650,556 records, 704 MB, 154 s). Inside `mirrors.using(...)` cards read it (`access: mirror`, `version`). Parity with the REST service: identical for TcTIM (17) and HsTIM (23); for EGFR, 29,470 of 32,346 identical, 2,876 differing only because the REST service rounds values (112 where the release states 112.4), and about 0.2 % differing between the live service and the monthly release. The release's InChIKeys drop the stereo layer (39 of 112 sampled EGFR monomers against UniChem's standard key), so identity stays with UniChem.
- **Notes**: the REST service sometimes answers a 200 whose body is not JSON (three times in eight pilot builds, 2026-10-01); since 0.9.0 it is asked again and recorded in `quality.retries` (#97). The REST records carry no origin (BindingDB curation or ChEMBL import) and no record id; licence treated as CC BY-SA 3.0. Up to 5000 records by default (`bindingdb={"limit": n}`), ordered by `bindingdb_record_order@1` (monomer id, affinity type, value); a cut is reported (#98). EGFR (P00533) holds 32,346 records of 16,463 monomers. BindingDB's monthly `BindingDB_CID.txt` (monomer → PubChem CID) is not used for identity: on a sample of EGFR monomers, 5 of 52 CIDs name another structure than the one UniChem states for BindingDB's (stereo layer, tautomer, or another compound).

### PubChem BioAssay — results linked to a protein
- **Status**: implemented as an enricher of `resolve_protein_card(..., pubchem_bioassay=True)` (uibcdf/sabueso#68)
- **Access**: PUG REST: every result of the target in one request (`assay/target/accession/<acc>/concise`, #98), assay summaries (depositor and its assay id) and compound InChIKeys in batches (`OnlinePubChemBioAssayClient`); saved responses (`FixturePubChemBioAssayClient`, `temp_data/pubchem_bioassay/`); `tools.db.pubchem_bioassay.get_assays`
- **Quality**: verified on TcTIM (13 assays, all deposited by ChEMBL, 492 results) and HsTIM (11 assays: 10 by ChEMBL, 1 by BindingDB)
- **Coverage**: `has_bioactivity` relationships with `source: PubChem BioAssay`; copies carry `copy_of` (depositor and its assay id) and are grouped with their originals by provenance; ChEMBL assays a copy names but the card lacks are fetched from ChEMBL (`retrieved_via`)
- **Notes**: up to 5000 result rows by default (`pubchem_bioassay={"limit": n}`), ordered by `pubchem_row_order@1` (confirmatory rows with a value, then other rows with a value, then rows without one); a cut is reported. Rows of another protein in a multi-target assay are left out. For EGFR: 53,534 rows of the protein in 6569 assays, fetched in about 21 s (one request per assay took more than 27 minutes). The concise table does not state the relation of a value (`>`), so copies never vote for a group's class when the original is present; PubChem's CID can carry another stereochemistry or salt form than the depositor's compound, reported as `stereo_differs`.

### NCBI Taxonomy — ranks and ancestors
- **Status**: implemented as an enricher of `resolve_protein_card(..., taxonomy=True)` (uibcdf/sabueso#67)
- **Access**: NCBI Datasets API `taxonomy/taxon/<ids>` in batches (`OnlineNCBITaxonomyClient`), saved records (`FixtureNCBITaxonomyClient`, `temp_data/ncbi_taxonomy/`), and `tools.db.ncbi_taxonomy.get_taxon`
- **Quality**: green for the listed coverage, verified on T. cruzi (species 5693), its strain CL Brener (353153, whose ancestors include 5693) and Homo sapiens
- **Coverage**: `annotations.taxonomy`, the organism's taxon with its rank and every ancestor with name and rank; two requests per card (the taxon, then its ancestors)
- **Notes**: no data release is stated (only the API version); licence: US public domain (NLM policy).

### NCBI Gene — gene products (identity across gene databases)
- **Status**: implemented, consulted by the resolver's identity audit with `resolve(..., ncbi_gene=True)` (uibcdf/sabueso#69)
- **Access**: Entrez E-utilities `efetch` (XML), no key (`OnlineNCBIGeneClient`); saved records (`FixtureNCBIGeneClient`, `temp_data/ncbi_gene/`); `tools.db.ncbi_gene.get_gene`
- **Quality**: green for its one use, verified on GeneID 3550449, whose record lists both a Swiss-Prot and a TrEMBL entry of one *T. cruzi* gene
- **Coverage**: gene id, symbol, locus tag, taxon, update date, and the UniProtKB accessions (Swiss-Prot and TrEMBL) of the gene's products. NCBI's lists can include secondary accessions; only the entries compared are matched.
- **Notes**: asked only for candidate pairs whose loci are in databases that do not overlap; NCBI's rate limit (3 requests per second without a key) is not approached. Licence: US public domain (NLM policy).

### PHI-base — phenotypes of pathogen mutants
- **Status**: implemented as an enricher of `resolve_protein_card(..., phi_base=True)` (uibcdf/sabueso#83)
- **Access**:
  - `OnlinePHIBaseClient`: versioned PHI-base 5 releases on Zenodo (concept record 10722192), downloaded once and checked against their MD5, then indexed by UniProt accession. The index is kept in memory for the process, or written to a cache directory only when one is given (`cache_dir=`, `$SABUESO_CACHE_DIR`; `CACHE_POLICY.md`);
  - `FixturePHIBaseClient` reads saved sessions from `temp_data/phi_base/`;
  - `tools.db.phi_base.get_phenotypes`.
- **Quality**: green for the listed coverage.
  - Verified live on release 5.6 (2026-09-27): about 11,300 genes, 339 pathogen species and 5,747 curation sessions.
  - First load about 30 s, with a peak of about 750 MB while parsing. The cache on disk is 76 MB; later reads take about 1 s.
- **Coverage**: `annotations.pathogen_phenotypes`, one item per pathogen-host interaction, pathogen or gene-for-gene phenotype whose pathogen genotype includes the gene. Each item holds:
  - PHIPO term, extensions and high-level terms;
  - the whole genotype;
  - pathogen and host (taxon, strain);
  - diseases, conditions and method (PHI-base's `evidence_code`);
  - PHI ids, publication and the curator's comment.

  GO, interaction and expression annotations are not mapped.
- **Notes**:
  - PHIPO terms keep their ids; their labels are not fetched, and `high_level_terms` gives PHI-base's readable summary.
  - Coverage of trypanosomatids is small (11 *T. cruzi* genes in 5.6), and TcTIM is not in it. That absence is `not_stated`, never evidence.
  - Licence: CC BY 4.0 (cite PHI-base and the release).

### AlphaFold DB — predicted structures
- **Status**: implemented as an enricher of `resolve_protein_card(..., predicted_structures=True)` (uibcdf/sabueso#57)
- **Access**: AlphaFold DB API `prediction/<accession>` (`OnlineAlphaFoldClient`), saved responses (`FixtureAlphaFoldClient`, `temp_data/alphafold/`), and `tools.db.alphafold.get_prediction`
- **Quality**: green for the listed coverage, verified on TcTIM and HsTIM (model v6, mean pLDDT 97.3 and 96.7) and on an unreviewed entry with no experimental structure (A0A6A5BWU3, v6, mean pLDDT 96.2)
- **Coverage**: `has_predicted_structure` relationships, one per model, with the model version, tool, mean pLDDT and its bands, the UniProt range, and whether the modelled sequence is the entry's current one (MD5)
- **Notes**:
  - Models are never experimental structures: `Card.structures()` does not count them.
  - A missing accession answers 404, mapped to not found.
  - Licence: CC BY 4.0; cite AlphaFold and AlphaFold DB.

### PDBe-KB — ligand binding sites
- **Status**: implemented as an enricher of `resolve_protein_card` (uibcdf/sabueso#28)
- **Access**: PDBe graph API `uniprot/ligand_sites/<accession>` (`OnlinePDBeKBClient`), saved responses (`FixturePDBeKBClient`, `temp_data/pdbe_kb/`)
- **Quality**: green for the listed coverage, verified on TcTIM (6 ligands) and HsTIM (10 ligands)
- **Coverage**: `has_ligand_site` relationships: residues each ligand contacts, in UniProt numbering, over all structures of the protein, with PDBe-KB's descriptors
- **Notes**:
  - Ligand copies are aggregated. The per-residue chain is one representative, so it cannot tell one ligand contacting two chains from two copies (in 1HTI, Asn12 is attributed to chain B and His96 to chain A, while the only PGA instance contacts chain B). Chain spanning is read from RCSB per-instance contacts instead.
  - `is_solvent` and `significance` do not separate crystallisation additives on TIM: glycerol, PEG, sulfate and hexane are not flagged as solvents, and glycerol has the same significance as BTS. Both are kept as PDBe-KB states them.
  - `chembl_id` is empty for every TIM ligand.
  - An accession without data answers 404, mapped to not found.
  - Licence: CC BY 4.0, academic and commercial use; cite the PDBe-KB consortium paper.

### PDBe-KB — interface residues
- **Status**: implemented as an enricher of `resolve_protein_card(..., interfaces=True)` (uibcdf/sabueso#40)
- **Access**: PDBe graph API `uniprot/interface_residues/<accession>` (same clients as ligand sites)
- **Quality**: green for the listed coverage. Verified on TcTIM (2 partners) and HsTIM (7 partners).
- **Coverage**: `has_interface_with` relationships, one per partner chain: the interface residues of this protein in UniProt numbering, and the entries and chains where each is observed
- **Notes**:
  - A "partner" is any chain PDBe-KB finds at an interface, so it is not necessarily a biological partner:
    - TcTIM lists TbTIM (P04789), only because 3Q37 is a TcTIM/TbTIM chimera whose entity maps to both;
    - HsTIM lists HLA-DR and T-cell receptor chains, from complexes with a TIM peptide.
    `Card.oligomer()` classifies each partner, per structure, and says so.
  - Partners without a UniProt entry (`type` other than `UNP`) keep PDBe-KB's label.
  - Licence: CC BY 4.0, as for ligand sites.

### InterPro — site residues
- **Status**: implemented as an enricher of `resolve_protein_card` (uibcdf/sabueso#28)
- **Access**: InterPro API `protein/uniprot/<accession>/?residues` (`OnlineInterProClient`), saved responses (`FixtureInterProClient`, `temp_data/interpro/`)
- **Quality**: green for the listed coverage, verified on TcTIM and HsTIM (InterPro 110.0, CDD `cd00311`)
- **Coverage**: `features_positional.family_site`: sites a member database places on the protein's sequence, with description and signature
- **Notes**:
  - Positions are placed by the source's family model, so Sabueso never aligns sequences. The same CDD model places TcTIM's catalytic glutamate at 168 and HsTIM's at 166.
  - An empty answer is the same for "no site residues" and "unknown accession"; both are recorded as not_found with that caveat. It is an answer, so it is not asked again as unreadable (#97).
  - The release is read from the `InterPro-Version` response header.
  - Licence: InterPro CC0 1.0; member-database content may carry its own terms. The CDD sites are NCBI work (US public domain, NLM policy).

### M-CSA — evaluated, not implemented (uibcdf/sabueso#28)
- M-CSA links HsTIM and TcTIM to entry 324 (triosephosphate isomerase), but it states catalytic residues and roles only in the numbering of its reference protein (chicken TIM, P00940, PDB 1TPH).
- Placing them on another sequence needs an alignment, which Sabueso does not compute (`devguide/DECISIONS.md`; boundary evaluated in uibcdf/sabueso#30). The InterPro family sites cover the positional part; M-CSA would add mechanistic roles once a source-stated mapping or a MolSysSuite/Praxis result is available.

### STRING
- **Status**: implemented as an enricher of `resolve_protein_card` (uibcdf/sabueso#21, part 2c)
- **Access**: online API (`OnlineStringClient`), saved responses (`FixtureStringClient`, `temp_data/string/`)
- **Quality**: green for the listed coverage, verified on human TIM (STRING 12.0: 78 partners at score ≥ 700; the fixture keeps the 50 most confident, marked `truncated`)
- **Coverage**: `functionally_associated_with` relationships with the combined score, the seven evidence channels, the query parameters and the STRING version (`source.version`)
- **Notes**:
  - STRING edges are functional associations, not physical interactions. The channels show whether an association rests on experiments or on pathways, fusion or text mining.
  - Partners are STRING proteins (`string:<taxon>.<id>`). They are not yet linked to UniProt entities.
  - The species comes from the UniProt anchor. STRING has no *T. cruzi* species-level entry for P52270: it covers the strain CL Brener (e.g. Q4DV43). The enricher records `not_found` and does not attach the strain network silently.

### SKEMPI 2.0 — interface mutations and binding changes
- **Status**: implemented as an enricher (`skempi=True`, #83), card schema 0.3.7
- **Access**: the whole CSV file (1.6 MB), downloaded once per process and indexed by PDB entry; saved subset `temp_data/skempi/skempi_v2.csv` (barnase–barstar)
- **Quality**: green, verified on barnase (P00648). Of its 89 mutations in SKEMPI, the 83 in 1BRS are placed through RCSB's author numbering when 1BRS is loaded, each with a matching residue; K27A has ΔΔG 5.38 kcal/mol under `binding_ddg@1`, as published.
- **Coverage**: `annotations.interface_mutations`, 7085 rows over 345 PDB entries.
- **Notes**:
  - Rows are joined only through the PDB chains UniProt states are the protein. The protein names SKEMPI writes are never used to join.
  - Mutations are in the entry's author numbering. They are placed only through the author numbering RCSB states for the chain (`rcsb_author_numbering@1`) of a structure the card holds.
  - The file states no finer version than the database's (2.0), and the site reports corrections after 2018. The file's SHA-256 is recorded in the enrichment record, so a changed file is told apart.
  - Licence CC BY 4.0 (the site's terms of download and use).

### KLIFS — kinase classification, structure conformations and pocket
- **Status**: implemented as an enricher (`klifs={}`, #83), card schema 0.3.8
- **Access**: REST API `api_v2`, no key (`OnlineKLIFSClient`): the kinase list once per process (`kinase_names`, 1,127 kinases, human and mouse), then per kinase its information, its structures, and one structure's pocket residues; saved answers for STK16 in `temp_data/klifs/`; `tools.db.klifs.get_kinases`, `tools.db.klifs.get_structures`
- **Quality**: green, verified live on EGFR (P00533, 2026-09-30, 6.8 s with one structure loaded): 565 structures with their conformations (306 DFG-in/αC-out, 221 in/in, 17 out/out…); the 85 pocket residues placed through 4HJO chain A, with the gatekeeper T790, the catalytic K745, the hinge L792 and the DFG D855. STK16 (O75716): 85 of 85 placed through 2BUJ chain B.
- **Coverage**: `annotations.kinase_classification`, `annotations.kinase_structures`, `annotations.kinase_pocket`
- **Notes**:
  - Joined only through the UniProt accession KLIFS states for a kinase. A protein with two kinase domains (a JAK) is two KLIFS kinases.
  - The pocket is placed only through the author numbering RCSB states for one structure the card holds (`klifs_pocket_reference@1` chooses it; `rcsb_author_numbering@1` places it), and a matching residue.
  - `interactions_match_residues` answers one structure per request, so one structure places the pocket.
  - KLIFS answers 400 ("unknown kinase ID") for a kinase it lists without structures; that is read as no structures, not as a failure.
  - No formal licence: the FAQ states the data is free and open for academia and industry, and asks to be cited (the registry's "CC BY 4.0" could not be confirmed).

### GPCRdb — GPCR classification, generic residue numbers and structure states
- **Status**: implemented as an enricher (`gpcrdb={}`, #83), card schema 0.3.8
- **Access**: REST services, no key (`OnlineGPCRdbClient`): the receptor by UniProt accession, its residues (`residues/extended`) and its structures (three requests); saved answers for GPR52 in `temp_data/gpcrdb/`; `tools.db.gpcrdb.get_receptor`
- **Quality**: green, verified live (2026-09-30):
  - β2-adrenoceptor (P07550, 8.5 s): 268 residues placed and 135 structures (100 active, 35 inactive), with D113 at 3.32, R131 at 3.50 (DRY), W286 at 6.48 and N312 at 7.39.
  - GLP-1 receptor (P43220, class B1, 6.6 s): 262 residues placed and 60 structures.
  - GPR52 (Q9Y2T5): 270 residues placed and 7 structures.
  - TPI1: `not_found`.
- **Coverage**: `annotations.gpcr_classification`, `annotations.gpcr_segments`, `annotations.gpcr_residues`, `annotations.gpcr_structures`
- **Notes**:
  - Joined only through the UniProt accession GPCRdb states for a receptor.
  - GPCRdb numbers residues on its own copy of the sequence, so its numbers are UniProt's only when that copy is the entry's sequence (`gpcrdb_sequence_numbering@1`); each residue must still match. Otherwise segments and residues stay in GPCRdb's numbering (`sequence_differs`).
  - GPCRdb writes a structure without ligand as a ligand "Apo (no ligand)"; the card records `apo` instead of a ligand.
  - Its mutation data (ligand-binding mutagenesis from the literature, 659 records for β2AR) are not read yet.
  - Licence CC BY 4.0 (data), stated in the legal notice.

### SAbDab — antibody structures of a protein
- **Status**: implemented as an enricher (`sabdab=True`, #83), card schema 0.3.8
- **Access**: SAbDab2's annotations of the PDB (`api/rcsb-pdb-annotations`, about 15 MB of JSON, 22,201 antibody instances), downloaded once per process and indexed by PDB entry; the SHA-256 and the API version (2.1.4) recorded; saved subset `temp_data/sabdab/`; `tools.db.sabdab.get_complexes`
- **Quality**: green, verified live (2026-09-30):
  - EGFR (P00533): 50 antibody instances in 28 structures (38 two-chain, 12 nanobodies), cetuximab in 1YY9 among them; 18.4 s with the download.
  - β2-adrenoceptor: 16 instances, in 1.5 s from the index already in memory.
  - μ-opioid receptor and GPR52 (fixtures): a nanobody, and an scFv bound to a receptor–arrestin complex.
- **Coverage**: `annotations.antibody_complexes`
- **Notes**:
  - Joined only through the PDB chains UniProt states are the protein; the antigen names SAbDab writes are never used, and a hapten, sugar or ion (SAbDab gives it the chain of the polymer it is attached to) never makes a protein an antigen.
  - An antigen is SAbDab's assignment in the structure: every chain it finds bound to the antibody is listed, marked `this_protein` or not.
  - The classic summary file of SAbDab now answers with the SAbDab2 web application; the annotations file of the new API is read instead. It carries no affinities.
  - Licence CC BY 4.0 (the API's description).

### UniRef (UniProt) — sequence clusters
- **Status**: implemented as an enricher (`uniref=True`, #103), card schema 0.3.9
- **Access**: UniProt's REST API: the entry's clusters (`uniref/search`), then the members of its UniRef90 cluster (500 per page, up to 5000); saved answers for P52270 in `temp_data/uniref/`; `tools.db.uniref.get_clusters`
- **Quality**: green, verified live on TcTIM (P52270, 2026-10-01): UniRef100_P52270, UniRef90_P52270, UniRef50_P04789; 6 members `clustered_with` it, among them CL Brener's Q4DV43 (another UniRef100 cluster) and two UniParc sequences of its own UniRef100 cluster.
- **Coverage**: `identifiers.uniref`, `relationships.clustered_with`
- **Notes**: a cluster is UniProt's statement of similarity, never identity; the members stay other entities. Licence as UniProtKB (CC BY 4.0).

### GTEx — the ontology terms of its tissues
- **Status**: implemented as an enricher (`gtex=True`, with `exon_usage=True`; #102), card schema 0.3.10
- **Access**: GTEx Portal API v2, `dataset/tissueSiteDetail` (`OnlineGTExClient`), one request per release, no key; the release is the one gnomAD's pext states (`gnomad_r4 pext (GTEx v10)` → `gtex_v10`); saved answer in `temp_data/gtex/`; `tools.db.gtex.get_tissues`
- **Quality**: green, verified live (2026-10-01): the 49 tissues of the pext of PKM, APP and CD44 each match one GTEx v10 tissue (`gtex_tissue_key@1`), none without a term. GTEx v10 states 54 tissues; the 5 the pext does not name (bladder, cervix, fallopian tube, kidney medulla) are not kept.
- **Coverage**: `annotations.tissue_terms` (`gtex_id`, `name`, `tissue_site`, `ontology_id`, `ontology_iri`); the tissue views list them as `tissue_terms`
- **Request prerequisites** (#135): without pext tissue keys or exactly one
  source-stated GTEx release, the dependent request is `not_queried` with an unknown
  count and its blocking input described. No client is constructed or called;
  conflicting releases are not selected. Received empty and failed GTEx responses
  retain their own source outcomes.
- **Notes**:
  - Terms are GTEx's: UBERON for tissues, EFO for the two cell lines (cultured fibroblasts EFO:0002009, EBV-transformed lymphocytes EFO:0000572).
  - Two GTEx tissues share UBERON:0002037 (cerebellum, cerebellar hemisphere); a term never replaces the tissue.
  - Names are kept as GTEx states them, typos included ("Anterior qcingulate cortex (BA24)").
  - GTEx's transcript expression is not used (#102: its short-read quantification inverts PKM's M1/M2 biology).
  - Terms: GTEx open-access data, free to use with acknowledgement of the GTEx Portal.

### OMA — orthologs
- **Status**: implemented as an enricher (`oma={}`, #83), card schema 0.3.8
- **Access**: REST API, no key (`OnlineOMAClient`): the accession's cross-references, its orthologs (one request), and UniProt's accessions for the orthologs' Swiss-Prot entry names (100 per request); saved answers in `temp_data/oma/`; `tools.db.oma.get_orthologs`
- **Quality**: green, verified live (2026-10-01):
  - human TPI1 (P60174, 22 s): 3,090 orthologs. 2,378 are named by UniProt accession (558 through entry names UniProt resolved; 8 names unresolved) and 712 by OMA id. T. cruzi CL Brener's Q4DV43 is among them, 1:1.
  - With `taxa`, only the chosen species are kept.
  - TcTIM (P52270): `not_found`, because OMA maps it to Q4DV43, whose sequence differs (`seq_match` modified).
- **Coverage**: `relationships.ortholog_of`
- **Notes**:
  - Joined only through an exact match OMA states for the accession.
  - Identical proteins of several strains share one UniProt entry; each OMA protein stays its own relationship (`oma_id` is an identity qualifier).
  - Entry names are resolved to active entries only: a retired entry can keep a name (P00938, demerged, is still TPIS_HUMAN). Fixed after 0.8.0, found in the TcTIM C1 run on 0.8.0: the CL Brener TIM's human ortholog was named P00938 instead of P60174.
  - OMA answers HTTP 502 or 503 to about one request in three (2026-10-01): each request is tried up to 4 times (0.9.0); a failure after that is `error`.
  - Licence CC BY 4.0, from OMA's Terms of Use as published in its browser's source (the site's pages answer 403 to non-browser clients); an older FAQ line says CC BY-SA 2.5 for the browser.

---

## Removed per-concept card tools (2026-09-23, uibcdf/sabueso#21 part 2b)
- **What was removed:** the GO, InterPro, CATH, SCOPe, TED, PhosphoSitePlus and BioGRID
  tools and their mappings.
- **Why:**
  - GO, InterPro, CATH, SCOPe and TED fetched *one term, family or domain* by its own id
    and built a card of it typed as a protein, e.g. `sabueso:protein:go:GO:0005524`.
  - PhosphoSitePlus read a synthetic format (record id "PTM") with no real access
    behind it.
  - BioGRID produced a protein-typed card holding a list of partner names.
- **Where that knowledge comes from now:** the protein itself. GO annotations
  (`annotated_with`), InterPro, Pfam, Gene3D/CATH, SUPFAM, PANTHER, PROSITE and CDD
  classifications (`classified_in`) and curated interactions (`interacts_with`) are
  typed relationships stated by UniProt (see *UniProt*).
- **Not replaced yet:**
  - TED domain assignments, SCOPe domain classification, and positional domain
    boundaries from InterPro;
  - PTM sites from PhosphoSitePlus;
  - the BioGRID interaction enricher, which needs an access key to be verified against
    live data.

## Summary of Open Incidents
- **Selection rules:** resolved by #10. The packaged rules (0.2.0) no longer list CATH,
  SCOPe or TED. The rule for `annotations.domains` remains for a reserved field that no
  mapping produces, since domains are `classified_in` relationships; it is harmless. The
  copy published in the user guide had stayed at 0.1.0 until 2026-09-26, and a test
  now keeps the two identical.
