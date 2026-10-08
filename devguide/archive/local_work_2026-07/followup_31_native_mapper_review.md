# Follow-up 31: native source mapper review

Review five original source mappers on **2026-10-08**: UniProt, InterPro, PDB,
PubChem and TED. Recover PubChem's native summary-page title as an independently
supported molecule description. Other residual scientific requirements are recorded
below with current schema, identity, source and coordinate boundaries.

## Five-file disposition

| Original file | Current implementation and final disposition |
|---|---|
| `sabueso/mappings/uniprot.py` | Current mapper and specialized activity, ligand, identity and source readers replace the old Evidence/flattened cross-reference representation. Recommended/submission names, genes, taxonomy, sequence quantities/checksums, ECO support, reactions, source interactions, GO/classification/publication links, isoforms, variants and experimental/predicted structure context have current bounded routes. Additional comment/feature kinds and unselected record metadata remain scoped future requirements below, not a claim of complete UniProt coverage. |
| `sabueso/mappings/interpro.py` | Current native `site_residues` mapping preserves family sites, member signatures, release and source numbering. UniProt already supplies classification references. The old guessed domain bundles and pooled fragments do not qualify a native protein-domain reader; preserve that separate requirement below. |
| `sabueso/mappings/pdb.py` | Current polymer-entity `has_structure` relationships, structure subjects and detached views cover methods, angstrom resolution, source accession dates, primary citation, assembly/construct/ligand/refinement context. Entry title is a separate future descriptive metadata requirement; no old structure-typed-as-protein constructor or protein-wide flattened metadata is restored. Correct the obsolete guide claim that dates and primary citation remain unmapped. |
| `sabueso/mappings/pubchem.py` | Recover native PUG-REST `Title` into existing `names.canonical_name` with its own SourceAssertion and `pubchem_property: Title`. Request it in the existing compound property GET. Current numerical/method/unit and stereochemical/connectivity distinctions replace old untyped fields and SMILES fallback. |
| `sabueso/mappings/ted.py` | TED remains `retired` after removal of per-database concept cards (#21). The old guessed shapes and classification-as-name do not establish a protein or sequence/model assignment. Preserve the predicted-domain capability's native re-evaluation conditions; no source activation or fabricated fixture. |

## Qualified PubChem description

[Official PUG-REST compound property specification](https://pubchem.ncbi.nlm.nih.gov/pcfe/docs/markdown/pug-rest.md)
distinguishes `Title` (the compound summary-page title) from `IUPACName`. The
mapper keeps the title literally, independently supported on the native PubChem
CID; it does not invent a title from an IUPAC name or a full PC_Compounds record.
Optional missing/null/empty titles produce no name assertion; nontext/blank-only
values fail through a catalog ConnectorError. Descriptive spelling/whitespace is
not normalized. The existing standard InChIKey admission remains authoritative.
Names cannot admit unanchored records or merge distinct molecular structures.
Conflicting supported names remain in the assertion store and conflict alternatives.

One public read-only PUG-REST GET obtains the title and existing requested compound
properties for CIDs 66414, 3717450 and 2244. Save the complete original response
unchanged as `temp_data/pubchem/titles__66414_3717450_2244.json`: **2202 bytes**,
SHA-256 `546d7d0dfda191b17b90986531817b9a71541c593d3039c7f72c577816a95f1a`.
Original retrieval: **2026-10-08T13:28:41.378512+00:00**. The source titles are
`2-Methoxyestradiol`, `Vincristine (free base)` and `Aspirin`, respectively.
This response carries no scientific record revision; retrieval is not a revision.
Source/date/US public-domain policy and separate depositor obligations are declared
in `temp_data/NOTICE.md`. Existing full-compound/property fixtures are unchanged.
The three-record fixture is not silently installed as a replacement for them.

## Remaining native metadata and domains, independent of the stash

These are retained requirements under [#83](https://github.com/uibcdf/sabueso/issues/83)
and [#112](https://github.com/uibcdf/sabueso/issues/112), not unqualified restoration
of obsolete fields. The original code is unnecessary to re-evaluate them.

1. **UniProt additional comment types:** ACTIVITY REGULATION, DOMAIN, SIMILARITY,
   CAUTION and MISCELLANEOUS have original text in existing public fixtures. The
   current typed mapper does not emit the old paths. An additive, unpublished
   schema/API decision is needed for these distinct meanings, including isoform/
   chain restriction, ECO/publication pointers, original retrieval/revision and
   conflict support. A source caution must not be silently promoted to Sabueso's
   quality conclusion; source similarity must never become identity. No blanket
   `knowledge_class: curated` is admitted.
2. **UniProt additional positional types:** native Domain, Chain, Lipidation, Motif,
   Region, Sequence conflict, Topological domain and Transmembrane occurrences
   remain useful requirements. `features_positional.domains` already exists;
   other old paths are not automatically current schema. A qualified reader must
   retain source sequence/isoform and revision, literal endpoint modifiers and
   molecule scope, source IDs and independent ECO support. Missing or fuzzy
   endpoints cannot be completed into an exact interval. Domain notes and domain
   boundaries are separate statements; preserved classifications are not boundaries.
3. **UniProt descriptive metadata:** keep possible entry/secondary identifiers,
   keywords, additional cross-references and citation detail as explicitly scoped
   source statements if a future user need selects them. Several source identities
   already have resolver/relationship routes; a cross-reference dictionary, keyword,
   same name or equal sequence cannot assert entity identity. Avoid duplicate
   blanket fields that lose native types, source occurrence or publication scope.
4. **InterPro matched-domain assignments:** qualify original protein-associated
   entry/member-signature responses, exact source protein/sequence, release/member
   database and occurrence identity before mapping. Keep discontinuous fragments,
   endpoint/DC-status literals, entry type and independent support. Never pool
   locations from unrelated proteins or infer an assignment from an entry's id/name.
   Current family sites stay distinct from domains and from experimentally stated
   active/binding sites. Require native online/fixture/supplied-file equivalence,
   full-response/pagination validation and explicit failure versus no match.
5. **RCSB entry title:** qualify `struct.title` in the actual entry acquisition and
   retain it on the `pdb:<id>` structure context with original support/revision.
   Show it in the corresponding detached structure view; it is not a protein name,
   a primary-citation title or permission to restore a StructureCard constructor.
   Current dates and primary citation are already supported.
6. **TED predicted-domain assignments:** re-evaluate adoption only with documented
   current native access, an unchanged public artifact and rights/release contract,
   plus explicit target sequence/model/parent identity and native boundaries.
   Preserve domain ids, discontinuous ranges, CATH classification and consensus/
   confidence as their separate native concepts. Prediction/calculation provenance
   cannot manufacture Evidence or an experimental class. Sequence/model changes
   need explicit mapping; a protein/domain label alone never authorizes placement.

The public scientific acceptance is recorded in [issue #83](https://github.com/uibcdf/sabueso/issues/83#issuecomment-6061022497),
with implementation scope cross-linked to #112. Local recovery audit details remain
in this report.

## Qualification

Focused PubChem mapping/acquisition/identity gate: **64 passed in 13.74 seconds**,
with two expected fixture failure warnings. Eighteen new scientific/behavioral cases
check three native titles, support, missing/malformed text, literal spelling,
standard-key admission, equal-name distinct structures, explicit conflicts and the
actual online property GET. Fixture licensing plus new description gate:
**22 passed in 2.95 seconds**.

The first full run started before the new fixture's NOTICE declaration was complete;
the licensing guard correctly reported one unlisted fixture (**5494 passed / one
failed in 162.64 seconds**). Complete the declaration, verify the licensing gate,
then rerun the complete suite on the finished inputs. Final full offline checkpoint:
**5495 passed in 168.82 seconds**, pytest-receptor, **12 workers**, existing editable
Python **3.14.7**, 10 expected fixture failure/truncation warnings. No test or guard
is weakened to accept the fixture.

Outside-checkout native replay verifies editable import/metadata, all three original
titles, **42 SourceAssertions**, independent descriptive/key support and distinct
structure identities. Exact scientific documents and snapshots survive card JSON/
SQLite, KnowledgeStore and deck JSONL/SQLite; **zero source requests** occur.
Receipt: `/tmp/sabueso-followup31-replay.json`; artifacts:
`/tmp/sabueso-followup31-replay`.

Ruff lint/format (**939 files**), generated registry, shape/schema alignment, strict
Sphinx HTML at `/tmp/sabueso-followup31-docs-build` and diff pass. Integrity checks
all 87 exported original byte lengths/SHA-256 hashes, 91 accounted paths, unchanged
stash, empty index, unchanged published frozen card and prior native scientific
fixtures. Existing PubChem compound/property fixtures match HEAD; the new three-CID
response matches its complete acquisition bytes/hash. Receipts:
`/tmp/sabueso-followup31-integrity.json` and `/tmp/sabueso-followup31-gates.json`.
This adds no schema or source adoption. All work remains local/uncommitted/unpushed;
no remote code checkpoint or gh-run-receptor inspection is needed for this slice.


## Remaining broader recovery

All five originals receive concrete final mapper-review dispositions in
`inventory.json`; residual capabilities above are self-contained future acceptance,
not ready source adoptions. **26** original file entries still carry the generic
individual-review label, down from 31. Several have earlier partial provider reviews;
this is a file-audit count, not 26 features or providers ready for integration.
Source-sequence/residue, core/schema entry points, specialist metadata/support
parsers and historical scientific artifacts still need reconciliation. Prior provider
and consumer matrices remain independent of the stash. Stash deletion is not yet
recommended. The original stash and all 87 exports remain intact; index empty,
work local/uncommitted/unpushed, existing shared development environment.

## Remaining generic individual-review file labels

These 26 labels need final reconciliation against current equivalents and earlier
partial reviews. They are distinct from the deferred-provider and scientific-artifact
qualification queues.

- `sabueso/__init__.py`
- `sabueso/core/__init__.py`
- `sabueso/resolver/__init__.py`
- `sabueso/tools/db/go.py`
- `sabueso/tools/db/scope.py`
- `sabueso/tools/db/uniprot.py`
- `schemas/card_schema.yaml`
- `schemas/card_schema_0.1.0.yaml`
- `sabueso/mappings/knowledge.py`
- `sabueso/mappings/protein_annotations.py`
- `sabueso/mappings/protein_context.py`
- `sabueso/mappings/protein_drug_discovery.py`
- `sabueso/mappings/protein_expansion.py`
- `sabueso/mappings/protein_priority_sources.py`
- `sabueso/mappings/protein_specialist.py`
- `sabueso/mappings/protein_structural_context.py`
- `sabueso/mappings/protein_translational_sources.py`
- `sabueso/resolver/protein.py`
- `sabueso/tools/protein.py`
- `sabueso/tools/protein_sources.py`
- `tests/resolver/test_protein_resolution_offline.py`
- `tests/tools/test_knowledge_enrichment_offline.py`
- `tests/tools/test_online_protein_priority_sources.py`
- `tests/tools/test_protein_annotation_sources_offline.py`
- `tests/tools/test_protein_priority_sources_offline.py`
- `tests/tools/test_protein_translational_sources_offline.py`
