# Sabueso — Checkpoint

The state of the repository, so that anyone can resume from it. Keep it current: update
it with each release, and whenever a change makes a line below false. History does not
belong here. Decisions go to `DECISIONS.md`, and the previous log is
`archive/CHECKPOINT_log_to_0.4.0.md`.

*Last updated: 2026-10-03, after release 0.11.0.*

## Release preparation

- **Proposed 0.12.0, staged route (#110):** literature context, pinned terms and
  explanations, required Ackredit attribution and bounded source-acquisition traces.
  The committed plan is `devtools/conda-build/release_plan.toml`; reusable draft
  notes are `devtools/conda-build/release_notes_0.12.0.md`.
- Preparation adopts qualified builder `8da628d9b393e184c3bf3722708b19dcfbf7ef0a`
  and extends the exact installed-file matrix with provider origin/API checks,
  copied attribution/acquisition regressions and the public offline workflow.
- Ackredit's real 0.9.0 staging file is independently verified. Fresh Linux
  receiving installs pass all 36 attribution/acquisition cases and the public
  workflow on Python 3.11–3.14 with Sabueso's exact public runtime pins; receipt:
  `devtools/conda-build/receipts/ackredit_0.9.0_staging_2026-10-03.json`.
  This uses a local consumer wheel, not a staged Sabueso Conda file.
- **Build/publication remains blocked:** verify public Ackredit delivery (#22/#75),
  set the actual dependency floor and public pins, remove source overlays/blocker
  together, then generate the frozen 0.3.11 public card from a clean installed
  candidate. No final release SHA, candidate Conda file or 0.12.0 publication is
  claimed. Latest published release remains 0.11.0.

## Release and schema

- **Latest release:** 0.11.0 (2026-10-02).
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
- **Current card schema:** 0.3.11 (`schemas/card_schema_0.3.11.yaml`), unpublished:
  located UniProt accession annotations in explicit articles add optional locations
  and native article ids to `mentioned_in`, and supported PDB mentions add derived
  `structure_mentioned_in` context (#92). Release 0.11.0 writes 0.3.10.
  - Published versions keep their frozen cards in `temp_data/frozen_cards/`: 0.3.0 to
    0.3.10.
  - The recorded shape of 0.3.10 is `schemas/card_shape_0.3.10.json`, fixed; current
    development records `schemas/card_shape_0.3.11.json`.
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

## Development after 0.11.0 (unreleased)

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
  All runtime CI tests real provider commit `383a64b2fdbc5472a7cdeb92c464b87433aabd76`,
  carrying the accepted portable contract for prepared 0.9.0 (ackredit#75).
  Dedicated pilot lanes test the installed consumer/provider outside both checkouts.
  Python 3.11–3.14 use normal source installation under the corrected provider
  interpreter contract (ackredit#80), without metadata overrides. Source testing
  does not establish a publicly released dependency closure.
  Independent installed receiving tests on fresh Linux Python 3.11–3.14 pass 36
  integration cases per minor, the public workflow and pip check against the real
  staging 0.9.0 Conda file from provider source `598abf9`, producer 37136075066
  (SHA-256 `37661090f6ad19a74b8155d8a4d4b4a068c9099f4ceba0743b3abfe887e97fe1`).
  Consumer source `7352cf4` is installed as a local wheel outside both checkouts;
  all 348 source modules and packaged rule/profile/terms resources match that SHA.
  The receipt retains Sabueso's exact public core pins, installed archive/source
  identity and non-editable origins. This is receiving compatibility, not public delivery.
  The next release is blocked by `dependency_preflight.py --release` until the
  accepted API is published and public dependency closure exists on 3.11–3.14.
  Ackredit's hosted installed descriptor/caller fixes remain molsyssuite#88/#89;
  #78 tracks shared delivery. UniProt/Europe PMC
  description citations are verified offline; other descriptions, target articles
  and annotation-provider bibliography remain explicit gaps. Broader acquisition coverage,
  provider publication, public closure and the shared record boundary remain open.
  Corporate-author BibTeX rendering was reported as ackredit#78 and corrected by
  the provider; the pinned candidate includes it, with CSL-JSON/text/BibTeX reader tests.
- Required source-acquisition traceability (#108, moli#36), first slice:
  built-in UniProt entry/search and Europe PMC mentions/annotations record their
  actual fixture/network/archive route, original versions, retrieval time, response
  hashes/references, retry/attempt counts and distinct empty/unavailable/unqueried/
  failed outcomes. Partial failed batches retain observed transport. Automatic
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

- Offline suite: 1336 tests passed, 26 online tests deselected (2026-10-03, in
  `molsyssuite@uibcdf_3.14`, with all installed workspace packages editable and the
  required real Ackredit source provider available). Run with
  `python -m pytest -m "not online" --receptor=llm`.
- Ruff format and check are clean. The MOLI governance check passes. The recorded card
  shape matches, and the source registry matches its page.
- CI (`.github/workflows/ci.yml`): Linux and Windows × Python 3.11–3.14, macOS
  Apple Silicon 3.14; offline coverage from Linux 3.14 after pushes to main.

## Open work

- Plan and status of every objective: `ROADMAP.md`. It integrates the foundational plan
  and the pilot-driven route.
- **Next:** explicit located UniProt accession mentions now enter cards in development
  (#92), with per-occurrence support, unknown article terms and recorded refresh
  requests (schema 0.3.11, unpublished). Supported PDB mention context is also
  implemented. Own extraction remains open. The public literature draft awaits human
  review before actual curation intake. Further candidates are in `ROADMAP.md`
  ("Next candidates") and in the user
  guide's gaps (`DOCS_GAPS.md`: wave-2 sources and the
  comparative context have no pages of their own).
- **Literature packets:** both mention areas are covered in unpublished
  `packet_aspects@6`, including their index references, rule and unknowns (#71).
- **Waiting on Nextia:** MOLI accepted the index level (uibcdf/moli#22, 2026-10-01). It
  closes with a consumer test (index, an item read by its pin, a Nextia Evidence, a
  citation that survives a new acquisition), when Nextia has its first persistent
  consumer.
- **Postponed by the maintainers (2026-10-01):** local mirrors in real work (#101),
  ChEMBL as a mirror and builds from cached sources.
- **Last pilot run:** 0.10.0, 2026-10-01, from scratch on the published package. The
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
