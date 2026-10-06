# Sabueso — Checkpoint

The state of the repository, so that anyone can resume from it. Keep it current: update
it with each release, and whenever a change makes a line below false. History does not
belong here. Decisions go to `DECISIONS.md`, and the previous log is
`archive/CHECKPOINT_log_to_0.4.0.md`.

*Last updated: 2026-10-06, 0.13.0 published and verified; next roadmap approved.*

## Resume here

Read this section, then [the immediate sequence](ROADMAP.md#immediate-resumption-sequence)
and [the journey audit](pending_proposals/independent_user_journeys.md).
The sections below retain detailed capability and qualification records; older
test counts are receipts for earlier slices, not the latest validation baseline.

- **Published:** 0.13.0, qualified tag `7e78d078111ac8dd51e08746c3818108ebd825a4`;
  card schema 0.3.12 is frozen. Release receipts below remain authoritative.
- **Workspace/code checkpoint:** all accumulated changes are committed and pushed
  to `origin/main`: implementation `413cdf6` and UTF-8 regression correction
  `74c8c3d34299a59784b29937361be03da2c29640`. [Exact-head CI](https://github.com/uibcdf/sabueso/actions/runs/37438528677) passes 15/15 jobs;
  [MOLI governance](https://github.com/uibcdf/sabueso/actions/runs/37438528644) also passes. The checkout is clean and
  synchronized at completion. A following documentation/evidence-only receipt
  commit uses `[skip ci]`, as local policy permits, with no executable, test,
  fixture, packaging or workflow changes. The qualified code remains identical.
  No new staged Conda artifact or public release is claimed; older local wheel
  versions/hashes remain historical receipts.
- **Implemented since 0.13.0:** all three independent public SDK journeys; versioned
  molecular knowledge-state correction (#122); exact disease membership/input/member
  support and conservative whole-context admission (#29/#91/#126); MONDO,
  Open Targets, Orphanet, DISEASES, ClinVar and MedGen observation/integrity
  (#108/#123–#125); native ChEMBL indication pointer bibliography; ClinicalTrials.gov
  study/reference observation and integrity (#108/#127), plus native collective
  Europe PMC authors (#128). The original disease example remains `@5`.
- **Latest bounded slice:** explicit registry-reference access and separately
  requested article metadata. It changes runtime/source APIs, preserves existing
  clinical SourceAssertions, and adds no automatic link traversal or clinical
  inference. See [the clinical checkpoint](pending_proposals/clinical_registry_checkpoint.md)
  for exact code, test, fixture and package qualification receipts. Latest gates:
  2272 offline cases pass (693.93 seconds), 178 focused installed cases pass
  with public Ackredit 0.9.0 (19.50 seconds), and warning-fatal Sphinx passes.
- **Open delivery issues:** #122–#128 have fixes in the qualified upstream code
  checkpoint and remain open for public-package delivery. Users of public 0.13.0
  still need that release. #108/#112 remain broader umbrella work.
- **Working environment:** Python 3.14.7 in `molsyssuite@uibcdf_3.14`;
  all 14 workspace packages have verified editable metadata and checkout imports
  outside the repository. Current shared-environment `pip check` fails for
  unrelated installed Amber/preparation packages; details and the passing separate
  installed-candidate environment are in the clinical checkpoint. This replaces
  earlier claims of a passing shared-environment check.
- **Resume action:** integrate explicitly scoped clinical bibliography into a
  versioned saved public journey. The upstream code checkpoint is already verified.
  Use the latest receipts rather than rerunning completed checks without a change.
  Follow the roadmap for remaining query/terms discussions. A release needs its
  own approved substantial scope and full staged qualification.

## Release qualification

- **0.13.0 published (#121):** source/tag `7e78d078111ac8dd51e08746c3818108ebd825a4`;
  exact CI 37308420258 passes 15/15 and governance 37308420271 passes.
  Staging 37309502566 builds `sabueso-0.13.0-py_0.tar.bz2`, SHA-256
  `1e8f80375cbc08c04df452dbbb55084dc4ff41c6242fbb07e3479f0cd4c7361c`;
  all 382 non-version Python/JSON files match source. Installed matrix 37310099058
  passes 13/13: producer plus all 12 Linux/macOS-arm64/Windows × Python 3.11–3.14
  lanes, each with 613 integration cases and the public workflow.
  Release event 37311427178 verifies without rebuilding; promotion 37311466982
  preserves the digest and verifies the public poststate. An anonymous public
  download equals staging; a fresh public-only Python 3.14.7 install passes
  bytes/origins/API, frozen-card read, all 613 cases, workflow and pip check.
  Zenodo [10.5281/zenodo.23162373](https://doi.org/10.5281/zenodo.23162373)
  archives all 960 source files identical to the qualified tag.
  Card schema 0.3.12 is frozen from clean installed local Conda code; existing
  schemas/receipts stay immutable. Complete receipt:
  `devtools/conda-build/receipts/sabueso_0.13.0_public_2026-10-05.json`.
- **0.12.0 published (#110):** qualified source/tag
  `7739317e40623d70513d4c2bb483f015b3f3247c`, with required public Ackredit >=0.9.0.
  CI 37189004296 passes 15/15 and governance 37189004230 passes. Producer 37190652548
  builds `sabueso-0.12.0-py_1.tar.bz2`; all 352 non-version Python/JSON files match
  the source. Installed matrix 37190968604 passes 13/13: producer evidence and all
  Linux/macOS-arm64/Windows × Python 3.11–3.14 lanes, each with 56 integration
  cases and the public three-packet saved-reader workflow.
- Promotion 37191632488 preserves digest
  `8f18330174de99cd8a9c8ff3e281ad27f4e894b9ac9f692b6643253b64d65382` and verifies
  the public poststate. Independent anonymous public download matches staging bytes.
  A fresh public-only Linux/Python 3.14.7 install with a new cache passes installed
  bytes/origins/API, frozen-card reading, all 56 cases, the workflow and pip check.
  Zenodo's 1160 source files equal the tag. Complete receipt:
  `devtools/conda-build/receipts/sabueso_0.12.0_public_2026-10-04.json`.
- The superseded `4ef9ddc`/`py_0` staged archive and original qualification receipt
  remain immutable. Schema 0.3.11 remains the clean-installed frozen public card
  recorded in `sabueso_0.12.0_local_schema_freeze_2026-10-03.json`; runtime RCSB
  traceability adds no fields to scientific serialization.
- **Editable workspace:** all 14 installed workspace packages remain editable in
  `molsyssuite@uibcdf_3.14`. Ackredit's editable runtime/distribution versions agree;
  the current shared-environment pip check has external dependency conflicts
  recorded in the resume section. Provider #81 is closed through #82.
  Separate environments qualify public/candidate distributions.

## Capabilities delivered in 0.13.0

- Persisted public application exercise (#108/#112): `examples/persisted_pipeline/`
  starts independent producer, reader and reuse processes. Original extraction/
  article metadata, full/index packets, pinned item support and workflow attribution
  survive fixture reacquisition and advanced heads. Missing/modified/misbound files,
  inconsistent bibliography/context and overwriting existing stages are refused.
  Saved readers add no credit, retain original versions and need no source fixtures.
  A missing fixture remains unavailable, not external source absence. The manifest
  is local; Nextia interpretation and MOLI ProjectRecord/Recorda reliability and
  transactional delivery remain open. Thirteen regressions run unchanged in
  installed-provider CI and future staging lanes.
- ChEMBL observation (#108): all five built-in logical operations retain normalized
  queries, pages/chunks, native document forms, totals/caps, retries, empty answers,
  unavailable fixtures, archive reuse/replay and partial received-page credit.
  Original scientific returns/exceptions and schema 0.3.11 remain unchanged.
  Source-version origins distinguish status/fixture/client cache and do not claim
  independent release proof for each page.
- Literal literature extraction (#92): `extract_literature_mentions` runs named rule
  `literal_uniprot_mention@1` on identified supplied fragments, with explicit
  namespace/official URL, Unicode offsets, input hash, original acquisition and
  detached Ackredit attribution. Explicit `Card.add_literature_extraction` and
  `ExtractionStore` now preserve original support through storage/refresh and reuse
  supplied original attribution. Payload-only refresh reports missing runtime
  sidecars; inconsistent support, different subjects and unknown fragment terms
  under a terms profile are refused. Explicit `europepmc.get_article` now supplies
  bibliographic support with native identifiers/authors/journal/pages and licence
  literals under `article_metadata_binding@1`. Source-stated identity binds it to
  the fragment publication; alternatives, original support, citations and declared
  terms survive store/card refresh and pinned full/index packet reads. Service
  version is not article revision; no abstract or full text enters the projection.
  Queries retain original wire/archive identity, reuse, empty, partial and failed
  outcomes. Fragment rights, broader statements and validation remain pending;
  extraction never becomes human curation.
- PubChem observation (#108): compound properties, structure matches and BioAssay
  target queries retain requests/POST identities, native per-assay revisions,
  summary/property batches, row caps/order, PubMed pointers, declarative depositor
  context, retries, original archive identities and received subsets on later
  failure. Empty, absent, rejected, unavailable and unqueried outcomes stay distinct.
  Compound/structure versions and missing bibliography remain explicit unknowns;
  assay revisions are not global release or per-row/property proof. Scientific
  payloads/exceptions and schema 0.3.12 are unchanged.
- BindingDB observation (#108): REST/fixture/mirror affinity access retains queries,
  totals/caps/order, native DOI/PubMed forms, original archive identities, retries,
  declared mirror origins and release manifests. Cutoff/retrieval-time
  bases remain explicit; REST versions/origins and bibliography gaps stay unknown.
  Card science/schema are unchanged. The source-local parser fix (#114) recognizes
  documented empty strings as evaluated-empty while malformed responses remain
  failed; original wire/archive identities and times survive replay and card builds.
- Chemical identity observation (#108): CCD component batches and both UniChem
  lookup methods retain normalized queries, POST/wire/decoded identities, original
  retrieval times, retries, empty answers, unavailable fixtures and partial subsets.
  Versions remain unstated; CCD release status/dates and UniChem compound ids are
  not release versions. Linked databases are declarative context, not direct access.
  Resource descriptions retain verified CCD/RCSB and UniChem bibliography.
  Molecular resolution and ligand-deck construction retain detached traces with
  exact result/input pins. Payload-only or ordinarily derived decks add no trace
  or credit. Scientific serialization, mappings and identity policies stay fixed.
- PDBe-KB observation (#108): separate ligand-site and interface-residue aggregate
  queries retain response/wire identities, original archive references/times,
  retries, empty/HTTP-not-found answers, unavailable fixtures and failures.
  Native group indices/identifiers, numbering and structural reference forms stay
  scoped to PDBe-KB; listed providers/entries are not additional direct access.
  Versions and missing underlying citations remain unknown; verified resource
  bibliography is retained. Scientific maps, returns/exceptions and schema stay fixed.
- AlphaFold DB observation (#108): model-list queries retain per-record native ids,
  latest/historical version metadata, original response/archive identities and times,
  retries, empty/HTTP-not-found answers and failed/unavailable/unqueried access.
  Unknown versions, isoform/fragment scope and partly invalid lists remain explicit;
  model versions are not global releases. Declared tools/providers/URLs establish
  no additional source access, coordinate download or local model-generation execution.
  Recommended resource/background bibliography is verified. Scientific maps,
  predicted/experimental separation, card schema and saved-reader behavior stay fixed.
- InterPro observation (#108): family-site residue queries retain native signature
  keys/accessions, member-database/location metadata, header/fixture release bases,
  original response/archive identities and times, retries and reused/empty/failed
  outcomes. Missing releases stay unknown. Empty answers cannot distinguish an
  unknown accession from no site annotation; invalid signatures/envelopes acquire
  no invented completed credit. Verified InterPro bibliography stays separate from
  missing member/signature/site citations. No alignment, InterProScan execution or
  direct member access is claimed; scientific maps, schema and saved reads stay fixed.
- Disease-group explanation (#91): `Card.explain_disease(disease_ref)` reads a
  MONDO group at the exact card pin under `disease_group_explanation@2`, retaining
  association/selected-annotation support, MedGen/MONDO links, hierarchy steps,
  conflicts and whole-card ungrouped context without acquisition or new credit.
  Missing support is partial. `disease_grouping@2` (#115) retains every direct and
  MedGen/MONDO identity path, leaves contradictory targets ungrouped and reports
  unfinished branches as `incomplete_identity`. Names, versions and storage order
  never select identity. Explicit `grouping_rule="disease_grouping@1"` reproduces
  historical lookup/explanation, including its exposed ambiguity, at original pins.
  Alternative labels and hierarchy paths remain visible; stored schema is unchanged.
- Knowledge-state explanation (#91): `Card.explain_knowledge_state` reads exact
  classification inputs at the card pin under `knowledge_state_explanation@1`.
  Selected fields, alternatives/conflicts, source-supported relationships, UniProt
  coverage inference and declared enrichment report/count scopes stay distinct.
  Missing support remains partial even when no classified row survives; report
  locators point to the original pinned card. No negative assertion, per-request
  assertion membership, source access or new credit is invented. The #116 integrity
  fix retains all supporting UniProt versions instead of crashing; the working
  classifications stayed on `knowledge_state@4` in 0.13.0. The local #122 correction
  below introduces new rule versions without changing published card states.
- Design/architecture review (#112): `pending_proposals/design_implementation_review.md`
  maps original plans and scientific functions to code/tests, remaining work, owners
  and bounded acceptance criteria. Peptides, much of the clinical layer and persistent
  consumer acceptance remain gaps; generalized illustrative APIs are directions.
- Local packaging integrity (#113): remove 259 versioned generated `build/` files,
  ignore that cache and check diagnostic wheel membership/bytes against source.
  A stale incremental wheel is rejected; a clean installed wheel passes all 89
  unchanged integration cases and the public three-packet saved-reader workflow.
  Published Conda artifacts and their qualification receipts remain immutable.
- Measurement/bioactivity explanations (#91): `Card.explain_measurement` and
  `Card.explain_bioactivity` retain exact pinned source inputs and actual grouping,
  provenance selectors, precision quantities, included records and class voters.
  Copies, ambiguity, strongest-class selection, discordance, source versions,
  original units, thresholds and checks survive. Whole-card grouping/glossary
  context stays explicit; stored identity locators invent no assertion membership.
  Missing support is partial, missing items are not inactivity, and readers add
  no acquisition or credit. Scientific rules and stored schema are unchanged;
  other derived explanations remain pending.
  The #117 fix retains missing activity-only originals as `original_not_on_card`
  with exact raw pointers. Later provenance/statement resolution removes the
  singleton diagnostic without changing groups, voters or classes. Historical
  pinned reads retain their original diagnostic/support, with no acquisition or credit.
- Ligand crossing/site explanations (#91): `Card.explain_ligand_site` retains
  actual overlap classes, selected annotated fields/conflicts and structural
  instance support. `Card.explain_ligand` retains exact protein/molecule pins,
  source-stated identity, class/name choices, sites, structure flags and native
  deck snapshot/membership context. Duplicate members remain explicit and partial;
  missing support never becomes absence. Readers acquire nothing or add credit.
  The #118 correction defaults to `ligand_measurement_count@2`: distinct included
  groups across matched molecule items, plus explicit source `records`.
  Explicit `@1` reproduces the published numeric counter. Views/comparisons retain
  pinned counting derivations; `ligand_deck_explanation@2` lists counted group and
  record ids with original support. Class/voter/scope policies and storage stay fixed.
- Oligomer explanation (#91): `Card.explain_oligomer()` retains the complete native
  view, actual partner/agreement rules, source assembly alternatives/methods, exact
  family members, selected/competing/conflicting support and original item pins.
  `oligomer_explanation@2` is detached and inert, with relationship-level support
  and explicit unknown qualifier lineage/runtime credit. Missing inputs and
  unconfirmed numbering are partial; absence states and query reports stay distinct.
  The #120 correction defaults to agreement `@2`: confirmed UniProt/1-based
  comparison only, with no conflicting numbering/positions. Unknown/incompatible
  inputs retain reasons and None residue sets; computed empty sets remain lists.
  Explicit agreement `@1` reproduces the legacy view/explanation at historical pins.
  New full/index packets declare `@2`; existing packets and card schema stay fixed.
- Local validation: 1,926 offline cases pass in the Python 3.14 development environment;
  613 unchanged receiving integration cases pass with installed Sabueso and public
  Ackredit 0.9.0 outside both checkouts, including 54 article-metadata cases and
  13 independent persisted-application cases and 77 oligomer explanation cases.
  The diagnostic wheel's modules/resources equal the source, and the public
  three-packet saved-reader workflow and receiving pip check pass. Ruff, schema/card shape,
  source registry, governance, dependency preflight and Sphinx with `-W` pass.
  All eight pilot notebook copies pass with installed public 0.12.0.
  Current exact-candidate CI and installed/public/archive gates are recorded above.
  Coverage incident #119 is resolved; the
  [archived report](archive/codecov_tls_coverage_upload_2026-10-05.md) retains
  the original failures and successful exact-SHA recovery. Diagnostic ranking
  remains independently reported in gh-run-receptor#59.
  A real bundle from installed
  Sabueso/public Ackredit 0.9.0 also reads/reuses in the newer editable consumer/
  provider, keeping original receipts and current execution versions distinct.
- PR #109 / #111 is integrated: applicable local gates by changed behavior, targeted
  regressions, full offline tests at code checkpoints, ordinary unskipped code pushes
  and preserved compatibility/release gates. Exact merge SHA `f2cbe20` has green
  CI/governance; skipped documentation pushes are not passing code evidence.

## Release and schema

- **Latest release:** 0.13.0 (2026-10-05).
  - Expanded acquisition observation, original literature intake/article metadata,
    pinned explanations and versioned identity/count/numbering corrections.
  - Card schema 0.3.12; exact-public-file and source archive receipts are above.
  - Zenodo: [10.5281/zenodo.23162373](https://doi.org/10.5281/zenodo.23162373).
- **0.12.0** (2026-10-04).
  - Public `uibcdf` noarch package for Linux, macOS Apple Silicon and Windows ×
    Python 3.11–3.14, built and promoted without replacing its verified archive.
  - Located article/structural mentions, pinned packet terms and literature explanations.
    Required automatic packet attribution and UniProt/Europe PMC/RCSB acquisition
    traces retain versions, citations, reuse, empty answers and failures.
  - Card schema 0.3.11; runtime trace formats remain separate and provisional.
  - Zenodo archive: [10.5281/zenodo.23134375](https://doi.org/10.5281/zenodo.23134375),
    source ZIP 3,154,834 bytes, MD5 `e471dce4d1b2cd839dabb1395b28b0b0`, all 1160
    files identical to the qualified tag. Conda is distributed separately.
- **0.11.0** (2026-10-02).
  - Published on the `uibcdf` conda channel, as a `noarch` package for Python 3.11–3.14.
  - Staged candidate b1f3b6e; sha256
    `670f2bf6a390c01e45d12b2cd203f79057aa8e9c7fe2166ea3fb1b075058c43f`.
  - The same artifact passed installed-package gates on Linux, macOS Apple Silicon
    and Windows × 3.11–3.14, including the explicit arm64 runner check (run
    [36987191885](https://github.com/uibcdf/sabueso/actions/runs/36987191885)).
  - Promotion and its public poststate passed (run
    [36987747905](https://github.com/uibcdf/sabueso/actions/runs/36987747905)). A clean
    public install on Python 3.14 verified the artifact, sealed quantities, inventory
    explanations, spaced assertion pins, extraction export integrity and located
    annotations. Card schema 0.3.10 and store formats are unchanged.
  - Zenodo archive: [10.5281/zenodo.23099139](https://doi.org/10.5281/zenodo.23099139).
    Its single source ZIP (2,968,369 bytes, MD5 `7e1c8e2dc8eb3d6dd02737e0d28753cb`)
    contains the same 1129 files as the tag. Both concept and version DOIs resolve to
    that record. The Conda package is distributed separately.
- **0.10.0** (2026-10-01).
  - Published on the `uibcdf` conda channel, as a `noarch` package for Python 3.11–3.14.
  - Staged candidate d41c7f7; sha256 `5217c5ce…0248`.
  - The exact staged file passed the installed-package gate on Linux, macOS and
    Windows × 3.11–3.14, and a clean public install on Python 3.14.
  - Zenodo archive: 10.5281/zenodo.23089116, verified to be identical to its tag.
- **0.9.0** (2026-10-01). Staged candidate c6876b8; sha256 `6b73db7b…af9b`. Zenodo:
  10.5281/zenodo.23084553.
- **0.8.1** (2026-10-01), an integrity fix for users of 0.8.0 who read OMA orthologs: a
  Swiss-Prot entry name resolves only to an active UniProt entry. Staged candidate
  ab45a3e; sha256 `3e6b1756…1fca9`. Zenodo: 10.5281/zenodo.23079157.
- **0.8.0** (2026-10-01).
  - Published on the `uibcdf` conda channel, as a `noarch` package for Python 3.11–3.14.
  - Staged candidate 4c4e0f2; sha256 `02f2dfd4…acf2`.
  - The exact staged file passed the installed-package gate on Linux, macOS and
    Windows × 3.11–3.14, and a clean public install on Python 3.14.
  - Zenodo archive: 10.5281/zenodo.23077926, verified to be identical to its tag; 0.7.0
    (10.5281/zenodo.23048186) and 0.6.0 (10.5281/zenodo.23038465) too.
- **Current schema:** 0.3.12 (`schemas/card_schema_0.3.12.yaml`), published/frozen in 0.13.0:
  explicit literal extraction intake adds scientific intake metadata and fragment
  locations. Runtime records remain detached. Shape recorded separately; migration
  is explicit and adds no automatic extraction gaps.
- **Latest published card schema:** 0.3.11 (`schemas/card_schema_0.3.11.yaml`), published in 0.12.0:
  located UniProt accession annotations in explicit articles add optional locations
  and native article ids to `mentioned_in`, and supported PDB mentions add derived
  `structure_mentioned_in` context (#92). Release 0.11.0 writes 0.3.10.
  - Published versions keep their frozen cards in `temp_data/frozen_cards/`: 0.3.0 to
    0.3.11; the clean-installed candidate froze 0.3.11 before publication.
  - The recorded shape of 0.3.10 is `schemas/card_shape_0.3.10.json`, fixed; current
    development uses `schemas/card_shape_0.3.12.json`; published shapes stay fixed.
- **In 0.8.0:**
  - an integrity fix for users of 0.7.0: gnomAD changes next to exons the canonical
    transcript lacks are no longer placed on canonical residues through UniProt's
    isoform map, and a transcript UniProt names no isoform for is no longer canonical
    (#85, #102);
  - card schema 0.3.8: BindingDB and PubChem BioAssay keep the 5000
    ceiling, with a named order (`bindingdb_record_order@1`, `pubchem_row_order@1`)
    recorded in the enrichment; PubChem BioAssay fetches every result of a target in
    one request; UniChem lookups for BindingDB's monomers run a few at once, politely
    paced (`_http.gather`); RCSB entries are asked 25 per GraphQL request (#98);
  - the retrieval archive (#100, phase 1): `RetrievalArchive` with `recording()`,
    `reusing(max_age)` and `replaying(of=card)`, answers kept at `_http.urlopen`,
    retrieval times taken from the answers (`_http.stamp`), each answer attributed to
    its source, retention derived from the licence (`retention_from_licence@1`),
    `quality.retrievals` on the card and `explain` linking statements to answers;
  - UniProt's entry is read once per protein build (the resolver keeps it);
  - ChEBI for small molecules (#83, wave 2): `chebi=True` adds `identifiers.chebi`,
    `annotations.chemical_classes`, `annotations.chemical_roles` and
    `annotations.definition`, joined through UniChem's link and ChEBI's stated
    InChIKey;
  - gnomAD on the canonical transcript (#85): gnomAD is also asked for each Ensembl
    transcript UniProt states for the canonical isoform, its consequence there comes
    first (`transcript_version`), and a change it states is not coding there is not
    placed (`not_coding_on_canonical`, `canonical_consequence`);
  - KLIFS for kinases (#83, wave 2): `klifs={}` adds the classification, the
    conformation of each structure (DFG, αC helix, ligands, quality) and the 85 pocket
    residues, placed in UniProt numbering through one structure's author numbering
    (`klifs_pocket_reference@1`, `rcsb_author_numbering@1`);
  - GPCRdb for GPCRs (#83, wave 2): `gpcrdb={}` adds the class and family, the
    segments and the generic number of each residue in every scheme (in UniProt
    numbering when GPCRdb's sequence is the entry's, `gpcrdb_sequence_numbering@1`),
    and each structure's activation state, ligands and signalling protein;
  - transmembrane segments per chain (`has_structure` qualifier `membrane_segments`,
    #83): the segments OPM and PDBTM assign, as RCSB integrates them, each kept apart;
  - SAbDab's antibody complexes (#83, wave 2): `sabdab=True` adds, per antibody bound
    to the protein in a PDB entry, its chains and every antigen SAbDab assigns,
    joined through the chains UniProt states;
  - OMA's orthologs (#83): `oma={}` adds `ortholog_of`, only when OMA states the
    accession with an exact sequence match, with options `rel_type` and `taxa`;
  - `packet_aspects@3` (#83, #88): KLIFS and GPCRdb in `identity`, `structures`,
    `ligand_sites` and `sequence_features`, SAbDab in `structures`, and the
    `orthology` aspect (OMA), asked only by name; packets of different mappings are
    not compared;
  - tissues of a variant (#102): `exon_usage=True` reads gnomAD's pext
    (`annotations.exon_usage_by_tissue`), and `Card.variant_tissue_usage()` gives each
    variant the tissues expressing its position (`pext_at_variant@1`); changes the
    isoform map would place are first asked of gnomAD variant by variant; and
    `Card.isoform_tissue_usage()` gives per isoform UniProt's statements restricted to
    it and the pext of its own and variable coding bases (`isoform_exon_usage@1`);
  - local mirrors (#100, phase 2): `sabueso.mirrors` (install, status, update policies,
    remove, `using` with `mirror_first` or `offline`); BindingDB's monthly release as
    the first mirror (`MirrorBindingDBClient`), recorded as `access: mirror` with its
    release;
  - knowledge store format 2 (#99): unchanged statements shared across rebuilds
    (`retrieved_at` kept per state), integer keys, zlib compression; format 1 upgraded
    in place;
  - `knowledge_packet@2` (#88): a packet holds each statement once; grouped disease
    statements and the joint structure inventory name what they group (`@1` is still
    read, and revisions of different formats are not compared).
- **In 0.9.0:**
  - card schema 0.3.9 (#103): `identifiers.uniref` and `clustered_with`, UniProt's
    UniRef clusters (`uniref=True`), never identity; `Card.sequence_differences`
    (`equal_length_positions@1`); OMA's `not_found` names the UniProt entry it mapped
    the accession to; `packet_aspects@4` (UniRef in `identity`);
  - OMA's client tries a request up to 4 times on HTTP 502/503: the service answers
    502 to about one request in three;
  - an unreadable 200 answer (a body that is not the JSON asked for) is asked again,
    HTTP 500 joins the retried statuses, and a card lists its build's retries
    (`quality.retries`, #97).
- **In 0.10.0:**
  - card schema 0.3.10 (#102): GTEx's tissue terms (`gtex=True`,
    `annotations.tissue_terms`; UBERON, or EFO for a cell line), listed by the tissue
    views as `tissue_terms` (`gtex_tissue_key@1`); UniProt's Ensembl transcripts per
    isoform (`identifiers.ensembl_transcripts`);
  - `isoform_exon_usage@2`: an isoform without exons says why
    (`no_transcript_stated`, `transcript_not_in_gnomad`), and own bases say whether
    every isoform's exons were known;
  - the pext enrichment record counts its regions (it counted 0 since 0.8.0);
  - `packet_aspects@5`: GTEx's tissue terms in `biological_context` (#102).
  - a packet's level of detail (#88): `KnowledgeQuery(detail="index")` gives what the
    cards hold, by reference (`packet_index@1`), 135 KB instead of 2.1 MB for the pilot
    pair; `knowledge_query@2`, `knowledge_packet@3`.
- **Watched:** card and packet size with the default ceilings (#88).

## In 0.11.0

- `Deck.explain(card_id, structure_ref=..., ...)` explains an inventory item, its
  group or exclusion, and the pinned relationship and SourceAssertion support of
  every group member (`structure_inventory_explanation@1`, #91). It uses the
  inventory's options and existing classification rules; nothing is fetched.
- Pinned assertion reads accept ordinary spaces in existing source identifiers
  (`RCSB PDB`, for example), with identifiers and snapshot hashes preserved (#104).
- These changes leave card schema 0.3.10 and the knowledge-store format unchanged.
- `CurationStore` exports curated literature and supported legacy curations only;
  extractions never become human-curated on rebuild, even after validation (#105).
- The public HsTIM literature review draft and isolated rehearsal are in
  `examples/literature_curation/`; three statements keep their content, outcomes and
  historical support on rebuild. Human validation of the draft remains unset (#92).
- `tools.db.europepmc.get_annotations(article_ids)` returns located accession-number
  annotations for explicitly named articles, keeping the source's ids, provider,
  section, tags and quote fragments. The public fixture includes P60174 in a figure
  of PMC12400196 (CC BY 4.0). It does not enrich cards or extract claims (#92).

## Delivered in 0.12.0

- Explicit located UniProt accession intake uses
  `europepmc={"article_ids": "PMC:PMC12400196"}` through the declared enricher (#92).
  Every occurrence retains native article ids, annotation content and its own
  SourceAssertion. The printed accession and matching UniProt tag state the identity
  basis. Literature shows the locations and qualifier alternatives; no scientific
  claim or human validation is created.
- Schema 0.3.11 adds optional `mentioned_in.article` and `mentioned_in.locations`,
  with per-article request and outcome records. Empty answers, unavailable fixtures
  and failures remain distinct. Refresh preserves explicit requests, historical
  assertion reads and the recorded terms profile unless overridden (#94).
- Located PDB mentions now enter as `structure_mentioned_in` only through
  source-supported `has_structure` associations already mapped on the card. Rule
  `structure_mention_context@1` retains the raw PDB mention and the structural
  relationship and assertions. `literature().structure_mentions` separates this
  context from direct protein mentions. Public 2JK2/Methods exercises the route;
  7QON mentions lack association support and remain explicitly unlinked. No chain,
  whole-entry identity, author focus or scientific claim is inferred. Four-character
  codes and matching PDBe tags are required. `knowledge_state@4` distinguishes
  counts and coverage of both areas; historical direct-only requests do not claim
  PDB coverage. Storage and refresh retain both legs and historical pins.
- Article fragments are judged separately from bibliography, with publication terms
  unknown when the API states no licence. Terms profiles exclude their intake before
  fetching. Raw Europe PMC responses have the separate registry retention licence
  `PUBLICATION-TERMS`; `retention_from_licence@2` reports internal retention and
  sharing unknown, including historical archive records when read (#100).
- The live public P60174 figure annotation passed card intake (2026-10-02), in
  addition to the offline storage/refresh/historical-reference acceptance tests.
- `packet_aspects@6` adds direct and structural mentions to the literature index and
  unknowns (#71, #92). Automatic acquisition asks Europe PMC bibliography only;
  located article annotations require explicit requests on prebuilt cards. Missing
  PDB annotation requests are `not_queried` with an explanation, not an empty answer.
  Index `full_rules` names `structure_mention_context@1`. The public frozen @5 index
  reads unchanged; historical mention and structural-support pins survive later
  acquisition. Packet history now reports mappings/detail levels as non-comparable,
  consistently with `same_knowledge`. Missing search fixtures report unavailable.
  Query/packet/card/store formats are unchanged.
- `Card.explain_literature(publication_ref)` now exposes stored publication links,
  pinned assertions and structural context, including alternatives and unlinked
  request records (`literature_explanation@1`, #91). It reads without acquisition;
  missing links are `not_on_card`, and missing recorded support is `partial`.
- `KnowledgePacket.terms(use, store)` reports represented statement support,
  conflicts and stored dependencies at exact card pins (`packet_terms@1`, #29).
  Full/index agree for `packet_aspects@6`; other mappings need a scope adapter.
  Bibliography never licenses fragments. Disease identity context is broader than
  exact grouping inputs, which were not recorded. The terms registry is the current
  packaged registry with review dates, not a reconstructed historical registry.
  This read-time report changes no stored formats, card shapes or packet hashes.
- Required Ackredit integration (#108, moli#36), first local runtime adapter:
  composition automatically attaches `packet.attribution`; `sabueso.attribution()`
  collects those detached
  `sabueso.packet_attribution@1` records. Actual selected stored support/conflicts
  and relationship dependencies define resource scope; each result retains reused
  resources and contributes to the application's workflow. Packet/card/store payloads
  and hashes are unchanged. Missing/broken providers diagnose failed attribution
  while retaining knowledge and host records;
  saved readers add no credit. The public offline pilot is `examples/ackredit_pilot/`.
  Runtime CI now installs public Ackredit; dedicated pilot lanes pin 0.9.0/py_0
  and exercise the consumer outside the checkout on Python 3.11–3.14. The published
  floor is `ackredit>=0.9.0`, with no source overlay or interpreter override.
  Independent Linux receiving tests first qualified the real staging file from
  provider `598abf9`, producer 37136075066, then ordinary clean public-channel
  installs on all four minors. Each passes 36 acquisition/attribution cases,
  the public workflow and pip check with the exact planned public core pins.
  Provider installed matrix 37152044426 and promotion 37152421084 succeed;
  Ackredit #22/#75/#80 and central #78/#88/#89 are resolved.
  The immutable provider digest is
  `37661090f6ad19a74b8155d8a4d4b4a068c9099f4ceba0743b3abfe887e97fe1`.
  These receipts verify provider delivery/receiving compatibility; Sabueso's
  final `7739317`/`py_1` candidate passes its separate OS/minor matrix and public
  installation under #110; stable publication, promotion and Zenodo are complete.
  UniProt/Europe PMC/RCSB description citations are verified offline; other descriptions,
  target articles and annotation-provider bibliography remain explicit gaps.
  Broader acquisition coverage and the shared record boundary remain open.
  Corporate-author BibTeX rendering was reported as ackredit#78 and corrected by
  the provider; the pinned candidate includes it, with CSL-JSON/text/BibTeX reader tests.
- Required source-acquisition traceability (#108, moli#36), first slice:
  built-in UniProt entry/search, Europe PMC mentions/annotations and RCSB
  single/batch structure clients record their
  actual fixture/network/archive route, original versions, retrieval time, response
  hashes/references, retry/attempt counts and distinct empty/unavailable/unqueried/
  failed outcomes. RCSB batches retain per-entry revisions, primary citations and
  completed subsets alongside all fallback requests. Partial failed batches retain
  observed transport. Automatic
  `acquisition_trace` attaches to cards/resolutions, including resolution without
  a card, final refresh pins and one-call packets; supported public source envelopes
  retain it beside raw records. Other sources/custom clients are explicitly unobserved.
  `AttributionRun.acquisitions` separately collects source events; completed access
  contributes contextual bibliography to the application's Ackredit capture.
  Failures remain host records without completed-acquisition credit. Original JSON
  sidecars survive saved reading without new credit; scientific formats/hashes stay
  unchanged. The public pilot saves and checks both intake and composition.
  MOLI owns future ProjectRecord/Recorda routing and strict recording policy; this
  bounded local experiment does not establish complete project provenance.

## Package layout

- `sabueso/core/`: the domain.
  - Card and Deck.
  - The SourceAssertion and relationship stores.
  - Views and derivation rules: structures, bioactivities and measurements, oligomer,
    ligand sites, ligands, literature, knowledge state, card diff, identity audit, names.
  - Curation and the curation store.
  - Snapshots and the knowledge store; knowledge packets; migration.
  - Quantities; tables.
- `sabueso/resolver/`: the EntityResolver and the FieldResolver, selection rules,
  enrichment profiles, and the UniProt and RCSB clients.
- `sabueso/mappings/`: one mapping per source.
- `sabueso/tools/db/`: source access, one module per source in use (see
  `sources/registry.yaml`).
- `sabueso/tools/card/`: the protein and small-molecule card tools, and file storage.
- `sabueso/enrichers/`: declared enrichers and their runner (#86).
- `sabueso/tools/deck/`: deck file storage.
- `sabueso/tools/resolve.py`: `sabueso.resolve`; `sabueso/tools/packet.py`: `sabueso.knowledge_packet`;
  `sabueso/tools/navigate.py`: `sabueso.expand` (#91).
- `sabueso/_private/`: argument digesters (ArgDigest, one per argument name) and
  diagnostics (SMonitor).
- `sabueso/ops/`, `sabueso/utils/`: thin, kept for layout.
- `schemas/`: card schemas by version, recorded shapes, and the conceptual draft
  (`card_schema.yaml`).
- `tools/`:
  - `card_shape.py` (recorded shape), `validate_schema.py`, `validate_card.py`,
    `validate_deck.py`;
  - `source_registry.py` (registry check and its page);
  - `build_showcase_notebook.py`.
- `devtools/`: conda recipe, release plan and route, verification scripts, the MOLI
  governance check.
- `temp_data/`: frozen public responses used as fixtures, with licences in
  `temp_data/NOTICE.md`; frozen cards.
- `docs/`: Sphinx user guide, API reference, showcase notebook.

## Quality baseline

- Current development offline suite: 2272 tests passed, 26 online tests deselected (2026-10-06, in
  `molsyssuite@uibcdf_3.14`, with all installed workspace packages editable and the
  required real Ackredit editable provider available). Run with
  `python -m pytest -m "not online" --receptor=llm`.
- Ruff format and check are clean. The MOLI governance check passes. The recorded card
  shape matches, and the source registry matches its page.
- CI (`.github/workflows/ci.yml`): Linux and Windows × Python 3.11–3.14, macOS
  Apple Silicon 3.14; offline coverage from Linux 3.14 after pushes to main.

## Open work

- Plan and status of every objective: `ROADMAP.md`. It integrates the foundational plan
  and the pilot-driven route.
- **Next roadmap (#112, approved 2026-10-05):** demonstrate independent-user
  journeys for protein/comparator, molecule/activities and disease/related entities;
  extend the queries, explanations and mandatory traceability those journeys need;
  scope peptide identity and a first scientific use as the next expansion.
  Coordinate Nextia, MOLI recording and modeling exchanges in parallel. Pending
  decisions cover query scope, entity representations, reproducibility/export,
  literature validation and public contract stability. See `ROADMAP.md`,
  "Next roadmap after 0.13.0", for ownership and acceptance criteria.
- **First independent-user journey (#112, development):**
  `examples/user_journeys/protein_comparison.py` resolves public TcTIM/HsTIM, compares
  source-supported fields/ligands, retains original reports/units, and saves both
  proteins, ligand decks and full/index packets with original runtime sidecars.
  Separate saved readers and fixture reacquisition preserve historical item support
  and bibliography. Source subsets and missing-fixture/positional limits stay explicit.
  User pages now cover the journey, molecules and source coverage. Disease/deck
  acceptance and broader molecular/clinical guarantees remain; current gaps are tracked in
  `pending_proposals/independent_user_journeys.md`. The live showcase still needs
  a fresh run/review, and no new publication or consumer acceptance is claimed.
  All seven journey regressions also pass unchanged outside this checkout with
  public Sabueso 0.13.0, Ackredit 0.9.0 and PyUnitWizard 0.27.0 on Linux/Python 3.14.7.
  That slice's primary offline checkpoint passed 1933 cases, Ruff and warning-failing Sphinx.
  The source registry's stale Europe PMC publication label is corrected at
  its canonical origin (#83); generated packaged terms remain unchanged.
- **Molecule/declared-target journey (#112, development):**
  `examples/user_journeys/molecule_target.py` crosses explicitly selected BTS and
  benznidazole cards with TcTIM's ChEMBL activities and requested 1SUX structural
  context. Original identity, assay/target assignments, IC50 and single-point
  quantities, undetermined values, source versions and ChEMBL indications retain
  exact support and named rules. The two-molecule deck and narrow report remain
  separate from the broad target-context index packet. Separate readers preserve
  original reports/citations after fixture reacquisition without new sources,
  derivations or credit; invalid/missing sidecars and molecular/assay bindings fail.
  Other targets and clinical studies are unqueried; the missing benznidazole
  UniChem fixture is unavailable. Aggregate source-record state misclassification
  was found and reported in #122, and is corrected locally below without inventing absence.
  Full explanations produce about 30 MB of JSON per fixture acquisition (#98/#88).
  Broader molecular queries/clinical journey integration remain #71/#108; bounded disease
  acceptance continues below. No new release or consumer acceptance is claimed.
  All eight new regressions pass in the primary editable environment and unchanged
  outside the checkout with installed public Sabueso 0.13.0, Ackredit 0.9.0 and
  PyUnitWizard 0.27.0 on Linux/Python 3.14.7. The full offline checkpoint passes
  1941 cases (342.97 seconds; 26 online cases deselected, five expected fixture warnings).
  Ruff checks all 690 Python files; warning-failing Sphinx, registry and dependency
  preflight pass. Both journeys are wired into public-provider/staged installed
  CI gates; remote qualification of these local workflow changes remains pending.
- **Molecular source-state correction (#122, development):** `knowledge_state@5`
  counts native molecular record ids/UniChem compounds, keeps unusable/unknown
  counts unknown, and reports missing/partial/capped subsets even when no items
  were returned. Clinical indication/study reports have separate areas from identity
  intake. `knowledge_state_explanation@2` retains exact original report indexes and
  counting bases, with scientific support as separate context; per-request assertion
  membership is not invented. Card schema 0.3.12 and published card payloads stay
  fixed. Frozen packets/original reports keep their original rules; saved readers
  acquire/recompute nothing and add no credit. This correction is local; published
  replacement and remote CI remain pending. Disease guarantees continue below.
  The 131 affected state/explanation/packet regressions pass; full offline checkpoint:
  1965 passed in 338.84 seconds, 26 online cases deselected and five expected fixture
  warnings. A scratch wheel (0.13.0+1.gc1bab2d.dirty; SHA-256
  `963d214ffdc46ee0dafba619dc268955cf1e29003668288991829529199e9fb1`) contains
  the exact corrected source bytes and passes 73 unchanged state/explanation/journey
  cases outside the checkout with installed Ackredit 0.9.0 and PyUnitWizard 0.27.0.
  That installed reader also reads the original pre-correction molecule report
  without recomputing it. Schema/card shape, Ruff, warning-failing Sphinx, dependency
  preflight, workflow YAML/bindings and 69 route/dependency regressions pass.
  Sabueso is reinstalled editable with `--no-deps --editable . --no-build-isolation`
  in `molsyssuite@uibcdf_3.14`; outside-checkout source/distribution versions agree,
  all 14 workspace distributions were editable and pip check passed at that receipt. The 60
  attribution/source-acquisition/molecular-state regressions pass after reinstall.
  These receipts do not qualify a new public or staged release artifact.
- **Disease/related-entity journey (#112, development):**
  `examples/user_journeys/disease_entities.py` resolves two separate MONDO-anchored
  disease questions, saves target/drug decks and enriched HsTIM grouping context,
  and preserves exact card/group support plus original membership metadata,
  exclusions, limits, unresolved EFO identity and original partial runtime credit.
  Independent readers inspect saved items and original bases without fetching,
  recomputing or crediting; reacquisition preserves original reports/references.
  Exact membership/input pins are implemented locally below (#91). Complete
  acceptance remains open: disease source/deck operation observation (#108),
  finer support admission (#29) and non-protein packets (#71). Conservative
  whole-context admission is implemented locally below.
  No SourceAssertions or complete bibliography are fabricated from membership
  metadata. Source rows, attempted candidates and built cards remain distinct.
  Local/installed gates are recorded in the journey audit; remote CI and release
  qualification remain pending. No published behavior/schema change is claimed.
  The initial metadata-only `@1` nine journey cases passed locally (44.78 seconds); 63 existing disease
  identity/explanation and 69 route/staging/dependency cases also pass. All 14
  workspace packages remain editable with verified outside-checkout import origins;
  pip check, Ruff, workflow bindings and dependency preflight pass.
  All nine initial `@1` cases also passed unchanged outside the checkout with installed
  public Sabueso 0.13.0/Ackredit 0.9.0/PyUnitWizard 0.27.0 (43.40 seconds;
  Linux/Python 3.14.7, site-packages imports). Warning-failing Sphinx passes.
- **Exact disease membership support (#91, development):** `disease_targets@2`
  and `disease_drugs@2` retain source-native rows/order/counts/indications as
  SourceAssertions in a separate support revision of the original MONDO input.
  Kept, unbuilt, capped and unsupported-product candidates retain exact native
  item pins and disease identity; kept members also retain their actual identity
  and card pins. `disease_deck_explanation@1` reports gaps, wrong bindings and
  rank/score disagreement without acquiring or crediting sources.
  `meta.support` embeds unchanged input and assertion revision snapshots under
  `sabueso.disease_deck_support@1`; save-deck-only persistence is atomic and portable
  JSONL/SQLite reimport preserves support. Card schema 0.3.12/store tables stay fixed.
  `disease_deck_terms@1` includes embedded sources; conservative
  `disease_deck_admission@1` supersedes the initial member-only refusal below.
  Original disease example `@1` reports remain readable;
  the `@2` reader introduced exact membership support (also retained in `@3`). Native science does
  not establish observed access or full bibliography (#108). Delivery remains local;
  the final offline suite passes 2000 cases (443.12 seconds; six expected fixture
  warnings), with 26 online cases deselected. The final diagnostic wheel passes
  133 unchanged support/journey/disease/storage/terms cases outside the checkout
  with public Ackredit 0.9.0 and PyUnitWizard 0.27.0. All 384 non-version Python/JSON
  files equal the checkout. Detailed receipts are in the journey audit; remote CI
  and the OS/minor installed-artifact matrix remain pending.
- **MONDO identity observation (#108, development; integrity correction #123):**
  Built-in term/equivalence queries retain raw/normalized identifiers, native
  identity/reference forms, OBO versions, exact file/lookup hashes and original
  index/download receipts. Memory/archive reuse keeps original versions, response
  identities and retrieval times; current selector/download attempts remain separate.
  Scientific results now preserve that same response time. Invalid OBO/UTF-8 input
  and missing fixture files are connector failures; source absence, fixture subsets,
  empty equivalence, unavailable, unqueried and failed outcomes remain distinct.
  Complete resource-description bibliography contributes to the enclosing Ackredit
  capture; imported terminology/definition citations stay explicit gaps. Direct
  disease resolution retains card/resolution pins and trace copies. The example
  `@3` introduced MONDO observation and original `@1`/`@2` reading without new credit.
  No card field/schema, valid identity/mapping or default persistence changes.
  The final offline suite passes 2031 cases (492.30 seconds; six expected fixture
  warnings), with 26 online cases deselected. The final diagnostic wheel passes
  217 unchanged MONDO/source/disease/journey/storage/terms cases outside the
  checkout with public Ackredit 0.9.0 and PyUnitWizard 0.27.0. Its 385 non-version
  Python/JSON files equal the checkout; original `@1`/`@2` bundles remain readable.
  All 14 workspace packages remain editable; detailed artifact/environment receipts
  are in the journey audit. Delivery and remote qualification remain pending.
  Other disease-source coverage is
  still required for complete acceptance.
- **Association-source/disease-build observation (#108, development; integrity #124):**
  Open Targets retains GraphQL pages/queries/native versions/order/counts and partial
  intake. Changed versions/counts or disappearing entities cannot merge silently.
  Orphadata retains original XML/index origins and scientific/runtime time across
  memory/archive reuse. Scoped absence, fixture unavailability and malformed/failed
  answers stay distinct. Completed access contributes resource bibliography to host
  Ackredit; underlying studies remain explicit gaps. Disease-build traces bind
  original disease input/support, final deck/members, executing version/times,
  rule/limit, source outcomes and exclusions. Existing inputs/custom clients create
  no invented source access. The example `@4` reads genuine `@1`/`@2`/`@3` bundles
  inertly. Valid scientific rules/card schema 0.3.12 and default persistence stay fixed.
  Final source/build/public-envelope gates pass 100 cases; the verified diagnostic
  wheel passes 265 unchanged cases outside the checkout with public Ackredit 0.9.0
  and PyUnitWizard 0.27.0. Its 387 non-version Python/JSON files equal the checkout.
  Original `@1`/`@2`/`@3` bundles remain readable. Detailed receipts are in the journey audit.
  The final full offline checkpoint passes 2079 cases (420.50 seconds, 26 online
  deselected, eight expected fixture warnings) in the primary editable Python 3.14.7
  environment; all 14 workspace packages retained checkout imports and pip check passed
  at that receipt (the current discrepancy is recorded in Resume here).
  Delivery/remote qualification remain pending. At that checkpoint, the next slice
  was DISEASES/ClinVar/MedGen observation; its local implementation is recorded below.
- **Disease channel/variant/identity observation (#108, development; integrity #125):**
  DISEASES retains per-channel publication dates, file hashes and original memory
  index receipts. Header checks do not redate the index; disk/bare index origins
  remain unknown with an explicit legacy client-clock fallback. Native channel
  scores/resource/text-mining pointers stay separate. ClinVar/MedGen retain native
  EInfo/ESearch/ESummary queries/hashes/order/counts, original archive times and
  completed subsets on failure. ClinVar build and variant accession versions differ
  from MedGen database last-update times. Counts/caps are scoped per gene/batch;
  overlapping variant UIDs are not silently deduplicated. Incomplete/ambiguous
  MedGen identity fails explicitly. Invalid protocols, missing fixtures and mixed
  fixture versions cannot establish absence or silently merged knowledge (#125).
  Recorded request/retry/archive identities exclude personal keys. Resource
  descriptions contribute to host Ackredit captures; underlying study/submission/
  terminology bibliography remains incomplete. Example `@5` reads genuine `@1`–`@4`
  reports without acquisition, derivation or new credit. Card schema 0.3.12 and valid
  scientific mappings remain fixed. Sixty-four new regressions pass; the combined
  acquisition/journey gate passes 74 cases, and transport/archive/release gates
  pass 109. The exact diagnostic wheel passes 344 unchanged cases outside the
  checkout with public Ackredit 0.9.0 and PyUnitWizard 0.27.0; all 389 non-version
  Python/JSON files equal the checkout. Imports, pip check and original readers pass.
  Full offline checkpoint: 2143 cases pass in 399.12 seconds, with 26 online cases deselected and six expected fixture warnings. Detailed receipts are in the
  journey audit. Public delivery/remote qualification remain pending; next are
  underlying study bibliography and finer support admission (#29), with non-protein
  packets (#71) and shared consumer guarantees still required.
- **Conservative disease-deck admission (#29; identity correction #126, development):**
  `disease_deck_admission@1` requires complete exact input/member/native support and
  admissible whole embedded context. Unknown/restricted shared terms refuse with a
  detached `admission_report`; finer filtering by terms of use remains pending. Every retained raw
  member SourceAssertion is checked independently of resolved source alternatives,
  including unused statements and unknown raw per-record rights. Excluded members
  retain native/input candidate support and separate historical member identity pins;
  their raw card payloads are not exported or imported into an empty store.
  The #126 fix checks that native candidate identifiers are actually stated by the
  member's bound identity assertions and resolved fields; another candidate's valid
  basis or a changed resolved identifier with unrelated original support is partial
  and cannot be admitted. The unpublished explanation is tightened without changing
  stored card fields, source-stated identity or original saved reports.
  JSONL/SQLite/store reads through advanced heads preserve decisions without source
  access or new credit. Original runtime sidecars remain original. Sixty-five
  admission/support cases pass. Full offline checkpoint: 2182 cases pass in
  706.53 seconds, with 26 online cases deselected and eight expected fixture warnings.
  The exact final diagnostic wheel passes 383 unchanged cases outside the checkout
  with public Ackredit 0.9.0 and PyUnitWizard 0.27.0 (371.81 seconds).
  All 390 non-version Python/JSON files match checkout and installed bytes; genuine
  original `@1`–`@5` bundles remain readable without acquiring, deriving, admitting,
  modifying receipts or adding credit. The initial pre-#126 wheel is superseded and
  preserved separately. Detailed receipts are in the journey audit. No new Ackredit
  contract/workaround is introduced.
  Ordinary/legacy admission semantics remain unchanged; finer filtering by terms of use, raw
  per-record rights, historical registries and wider packet scopes remain #29 work.
  The original receipt was local/uncommitted/unpushed; current code delivery
  is recorded in Resume here. No new public release is claimed.
- **ChEMBL indication reference attribution (#108, development):**
  `chembl_indication_references@1` retains exact native reference forms and every
  occurrence with indication/molecule/disease IDs, received page/query/hash or
  original fixture-result identity. Overlapping disease queries preserve observed
  occurrences even when scientific returns deduplicate the row. Grouped reference
  identifiers remain grouped. Completed pages survive later failures; original
  times, release bases and archive reuse/replay remain scoped explicitly.
  Portable per-operation and enclosing Ackredit captures credit
  `source_cited_reference`, without claiming target access, article identity,
  metadata or permission. Missing/malformed pointers and incomplete metadata stay
  explicit. Scientific returns/SourceAssertions and frozen card schema remain
  unchanged. The example keeps `@5`; genuine original `@1`–`@5` readers preserve
  original reports without acquisition or new credit. Full underlying study
  metadata and ClinicalTrials.gov observation were the next #108 slice; its bounded
  implementation is now recorded in the clinical checkpoint. That slice's local
  checkpoint: 2211 offline cases pass (593.50 seconds), and 425 unchanged installed
  cases pass with public Ackredit 0.9.0 (267.37 seconds). All 391 non-version
  Python/JSON package files equal checkout and installed bytes. Detailed receipts
  are in the journey audit; no public delivery is claimed.
- **Literature follow-up:** explicit located UniProt accession mentions now enter cards in 0.12.0
  (#92), with per-occurrence support, unknown article terms and recorded refresh
  requests (published schema 0.3.11). Supported PDB mention context is also
  implemented. The literal rule, explicit intake/replay and source-stated article
  bibliography/declared terms are released in 0.13.0; broader
  extraction, fragment rights and validation remain open. The public literature draft awaits human
  review before actual curation intake. Remaining capabilities are in `ROADMAP.md`
  ("Capability backlog and dependencies") and in the user
  guide's gaps (`DOCS_GAPS.md`: wave-2 sources and the
  comparative context have no pages of their own).
- **Literature packets:** both mention areas are covered in
  `packet_aspects@6`, published in 0.12.0, including their index references, rule and
  unknowns (#71).
- **Waiting on Nextia:** MOLI accepted the index level (uibcdf/moli#22, 2026-10-01). It
  closes with a consumer test (index, an item read by its pin, a Nextia Evidence, a
  citation that survives a new acquisition), when Nextia has its first persistent
  consumer.
- **Postponed by the maintainers (2026-10-01):** local mirrors in real work (#101),
  ChEMBL as a mirror and builds from cached sources.
- **Last pilot validation:** 0.12.0, 2026-10-04: all eight read-only notebook
  copies execute in a separate public installed-package environment from a fresh
  temporary store. Original traces/portable attribution are saved through temporary
  application instrumentation; original private notebooks remain unchanged. Execution
  success does not prove every source was available or fully observed.
  The previous recorded run was 0.10.0, 2026-10-01, from scratch on the published package. The
  first attempt was repeated, because ChEMBL's API answered HTTP 500 to every request;
  the second was clean. #103 was verified on 0.9.0 and closed.
- **Open issues, by kind:**
  - released, open for a follow-up: #100
    (archive and mirrors: next phases, #101, postponed), #98 (heavily studied targets), #92
    (literature: located mentions, own extraction), #91 (scientific operations), #88
    (default limits and size), #83 (source coverage: next wave), #71 (packets; contract
    in uibcdf/moli#22);
  - waiting on others: #53 (reference form, uibcdf/moli#3), #84 (VEuPathDB and TDR
    Targets terms), #95 (accounts, keys and licences), #22 (BioGRID key);
  - decisions to take: #96 (EFO terms without MONDO), #94 and #29 (terms profiles and
    usage terms, next steps), #20 and #19 (structure and relationship storage);
  - deferred or experiments: #87 (parallel enrichers), #60 step 2 (VEuPathDB), #30
    (ligand proximity), #36 (an ArgDigest experiment).
- Risks: `RISKS_AND_OPEN_QUESTIONS.md`.

## Clinical registry and native bibliography extension (2026-10-06, development)

Built-in ClinicalTrials.gov study and explicit reference lookup preserve native
queries, pagination, registry/API/update-date bases, reuse, empty answers and
partial/failure scope. #127 fixes omitted continuations, false absence, contradictory
duplicates and exhausted generator queries. Missing fixture answers are unavailable.
Registry citations and native reference pointers retain separate roles, raw forms
and exact occurrences, without fetching links or changing clinical SourceAssertions.
Explicit Europe PMC metadata contributes its own original acquisition and complete
returned personal/collective authors (#128). New public fixtures cover NCT00123916
and its three native PMID references. Frozen card schema 0.3.12 remains unchanged.
The disease example and genuine historical reports remain `@5` and earlier.
Final local qualification: 2272 offline cases pass; the corrected installed
178-case clinical/source-envelope/article gate passes with public Ackredit 0.9.0.
All 393 non-version package files match checkout/wheel/installed bytes. Detailed
receipts, the initial client-fixture setup failure and resumption constraints are
in `pending_proposals/clinical_registry_checkpoint.md`. No new public delivery is claimed.
