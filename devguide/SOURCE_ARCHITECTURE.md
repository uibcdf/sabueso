# Sabueso — Architecture for many sources

Wave 3 of the source coverage plan (uibcdf/sabueso#83, #86). Waves 1 and 2 took Sabueso
from 20 to 28 sources in use, with 24 more under evaluation. This document is how
Sabueso reaches many sources without losing what makes it trustworthy: every statement
traceable, identity never merged by similarity, absences told apart.

## 1. The problem, measured (2026-09-29)

- `resolve_protein_card` is one function of about 1,100 lines, with 17 blocks, one
  per source.
- Adding a source touches about eight places:
  - the function's signature and a block;
  - two argument digesters;
  - the knowledge-state table (`PROTEIN_ENRICHMENTS`);
  - two migration tables (`SCHEMA_CHANGES`, `_enrichment_options`);
  - the packet aspects;
  - the card-shape builder;
  - the registry.

  Forgetting one of them is silent.
- Cross-cutting behaviour is copied per source:
  - human-only coverage (`not_applicable`), in four sources;
  - the not-found and error handling;
  - the truncation records;
  - the user agent: 5 of 23 HTTP clients named Sabueso;
  - release caches: PHI-base and DISEASES each have their own.
- Nothing fetches in parallel: a card with every enrichment asks about 20 sources one
  after the other.

## 2. The enricher contract

An **enricher** is one source's contribution to a card, declared once:

```text
Enricher
  option        the resolve option that asks for it ("clinvar")
  source        the source's name in SourceAssertions ("ClinVar")
  registry_id   its entry in sources/registry.yaml ("clinvar")
  entity_type   "protein" | "small_molecule"
  areas         the knowledge areas it answers ("annotations.clinical_variants")
  area_matches  additional request selectors for each area (empty by default)
  area_counts   the count field for each area ("count" by default)
  area_not_queried_details  why no matching request leaves an area not queried
  organisms     taxa it covers (None: all; (9606,): human only)
  option_kind   "flag" (True) or "options" ({} or {"limit": …})
  client        the online client's factory
  record_kinds the enrichment data kinds this option records (derived from match by default)
  historical_parameters  argument -> record path for restoring older requests
  request_record(context, options)  record including independently copied request_options
  terms_source(options)  terms governing the requested content (source by default)
  run(context, options, client) -> [(mapping, enrichment record), ...]
```

- **`context`** is what the card already states, computed once: the anchor, the UniProt
  entry, the sequence, the organism, and the transcript context of `_hgvs`.
- **`run`** returns mappings and records. It never touches the card, and never
  catches errors itself.
- **The runner** does what every source needs, in one place:
  - organism coverage (`not_applicable`);
  - `RequestPrerequisiteMissing` from request planning → `not_queried`, before
    constructing or calling a client; missing or ambiguous dependent inputs do not
    establish source absence (GTEx pext tissues/release, #135);
  - `RecordNotFoundError` → `not_found`, and `ConnectorError` → `error`, so one failing
    source never hides another's knowledge;
  - truncation;
  - the fixed order of the results.

Before fetching, a terms profile judges `terms_source(options)`. Europe PMC uses
its service terms for bibliography and publication terms for explicit located
annotations, which contain article fragments. An excluded request keeps the
enricher's record, including explicit article ids, so refresh cannot silently turn
it into a bibliographic search. `record_kinds` includes both Europe PMC routes for
the migration map; automatic packet requests still ask only for bibliography.
Refresh preserves the card's recorded terms profile unless the caller overrides it.

Development refresh (#139) also routes through the exact declared `(source, data)`
selectors, including failed, excluded and blocked requests. The runner and terms
gate retain `request_options` before acquisition; client factories and credentials
are never recorded. Historical flags and available parameter paths are restored,
with missing parameters reported as unrecorded. New omitted parameters still use
the client's defaults, so saved arguments do not promise frozen defaults, native
releases or request identifiers. Conflicting requests and missing explicit article
ids require a caller override before any resolution or source access. A single
Europe PMC option cannot express both bibliography and located annotations;
refresh never silently chooses one. Unsupported selectors are listed separately
and are not queried. See [the refresh scope report](pending_proposals/refresh_request_scope.md).

`knowledge_state@5` retains the per-area selectors/count fields introduced in `@4`.
Molecular record intake can count native returned record ids or a UniChem compound;
missing counts remain unknown. ChEMBL indications and ClinicalTrials.gov studies
are classified in separate areas. Their reports and count bases stay inspectable
without inferring per-request assertion membership. Missing/capped/partial subsets
stay incomplete even with zero returned items (#122).
Europe PMC
counts direct UniProt mentions separately from derived structure mention context.
Only requests marked `located_accession_mapping@2` cover the latter; an older
direct-only request or a bibliographic search cannot imply that PDB mentions were
queried. The explicit article route uses source-supported structural associations
already in `context.mappings`, without fetching or selecting extra structures.
`area_not_queried_details` explains required separate requests. For PDB mention
context, a bibliographic search cannot count as querying article annotations.

From the declarations, the other tables are **derived** instead of maintained by hand:
- the knowledge-state rows (area, source);
- the migration map from enrichment records to options;
- the options each packet aspect asks for;
- the `card_options` domain;
- a test that every enricher has its digesters, a registry entry `in_use`, a fixture,
  and a place in the card-shape builder.

## 3. Shared services

- **HTTP** (`tools/db/_http.py`): every client's one way to the network.
  - `gather` asks a service answered one record per request (UniChem) with a few
    threads, no faster than the pace its online client states (`Pace`), and returns
    each answer or failure in the order asked (#98).
  - One user agent naming Sabueso.
  - Retries with backoff for 429, 502, 503 and 504 and for refused or reset
    connections, twice at most, honouring `Retry-After`. Every Sabueso request is a
    read, GraphQL posts included, so a retry changes nothing on the source.
  - A timeout is not retried: the source has had its time, and a retry would multiply
    it. Any other error reaches the client unchanged, so a 404 stays "not found".
  - A test checks that no client imports `urlopen` from `urllib` directly.
- **Keys** (`tools/db/_keys.py`), for sources that take a personal key. Some need one
  (BRENDA, VEuPathDB, BioGRID, Guide to PHARMACOLOGY, Tox21's API); others answer
  faster with one (NCBI, the first user).
  - The user supplies their own key through `SABUESO_<SERVICE>_KEY`, or the client's
    `api_key`. A service, not a registry entry, owns a key: NCBI Gene, NCBI
    Taxonomy and ClinVar share `SABUESO_NCBI_KEY`.
  - Sabueso never stores, logs or ships a key. It is sent only to its own service, is
    scrubbed from error messages, and is left out of the traceback's cause.
  - A card does not say whether a key was used: an optional key changes the rate, not
    what the source states, and cards built with and without one stay identical.
  - A missing required key raises `MissingKeyError` (`SABUESO-E-SOURCE-003`). The runner
    records `not_queried`, with the reason, never an error.
- **Release caches** (`tools/db/_release.py`), for sources published as whole
  versioned releases (PHI-base, DISEASES, Orphadata):
  - the index is kept in memory by default;
  - it is written to disk only when a cache directory is given;
  - it is keyed by release, and checked against the published checksum when one is
    stated.
- **Numbering through stated maps** (`mappings/_hgvs.py`): the rule already shared by
  ClinVar and gnomAD. Author numbering (#73) is its structural counterpart.

## 4. What stays bespoke, and why

- **RCSB structures**: each entry is also a structure record, with author numbering,
  assemblies and partial answers (#74).
- **ChEMBL, BindingDB and PubChem BioAssay**: copies are grouped with their originals,
  and molecules are anchored through UniChem. Their order matters.
- **NCBI Gene**: it takes part in the resolution's identity audit, not in the card.

They keep their code. They adopt the shared services, and are declared as enrichers
for the derived tables.

## 5. Parallel fetching (last; deferred, #87)

Independent enrichers can fetch concurrently (a thread pool), with results merged in
the declared order, so a card stays deterministic. It comes last, after the contract,
and only if measured: most sources answer in 1–10 s, and some ask for gentle use.

## 6. Plan, in behaviour-preserving steps

Each step keeps the offline tests, the recorded card shape and the frozen cards
unchanged.

1. **Done (2026-09-29).** The contract and the runner. The seven sources of waves 1–2
   are enrichers: PHI-base, DISEASES, Open Targets, Orphadata, Reactome, gnomAD and
   ClinVar. The knowledge-state rows and the migration map are derived from them, and
   a test checks each enricher's wiring. `resolve_protein_card` went from 1,096 to
   753 lines. Cards are identical before and after: same snapshot ids and same
   enrichment records, for four proteins, with and without failing sources.
2. **Done (2026-09-29).** The remaining simple enrichers: STRING, ligand sites,
   interfaces, family sites, predicted structures and taxonomy.
   - They run in declared stages among the bespoke enrichments, so records keep their
     order.
   - An enricher can share a client argument (PDBe-KB), and can keep a `not_found`
     record without detail, as these always had.
   - `resolve_protein_card` is 595 lines.
   - Cards are identical before and after, for four proteins with and without failing
     sources, and the knowledge-state rows are the same.
3. **Done (2026-09-29).** Shared services.
   - Every client (23 modules) reaches the network through `_http`.
   - PHI-base, DISEASES and Orphadata keep their releases through `_release`.
   - `_keys` has its first users: NCBI Gene, NCBI Taxonomy and ClinVar take an
     optional NCBI key.
   - Cards are identical before and after, for four proteins with and without failing
     sources.
4. **Done (2026-09-29).** Derived packet options and the consistency test.
   - An aspect asks every enricher that answers one of its areas
     (`packets.aspect_options`); only the bespoke sources' options are written by hand.
   - The derivation found two gaps in `packet_aspects@1` (unpublished, so corrected in
     place). `structures` showed predicted structures without asking AlphaFold DB.
     `sequence_features` reported InterPro family sites without asking InterPro.
   - A test checks that every "not queried" unknown in a full packet states why.
   - The wiring test now also asks each enricher for a fixture client and a card in the
     card-shape builder. STRING is the one enricher outside every aspect, declared
     with its reason.
   - `card_options` was already read from the card tools' signatures.
5. **Measured and deferred (2026-09-29, #87).** Parallel fetching.
   - Online, the declared enrichers take 18.8 s of a 39.5 s card for HsTIM, and
     6.3 s of 34.9 s for TcTIM. ClinVar is the largest, at 9.1 s, most of it spent
     on NCBI's side.
   - Running them concurrently would save at most about a quarter of a card's time,
     at the cost of thread safety, diagnostics from threads and gentler use of rate-
     limited sources.
   - #87 states when to re-evaluate.
