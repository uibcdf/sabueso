# Sabueso — Card Schema Notes

## Schema Location
The frozen draft schema lives at:
- `schemas/card_schema.yaml`
The formal schema (versioned) lives at:
- `schemas/card_schema_0.3.0.yaml` (current; `card_schema_0.2.0.yaml` is kept as history)

This is a **conceptual** schema meant to be refined into formal validation later.

## Nested Structure
Cards are **nested** to preserve hierarchy and order. Each card type (protein, peptide, small molecule) inherits from a shared base.

## Field Path Contract (Approved)
Canonical field paths use **dot‑separated notation**.

Examples:
- `names.canonical_name`
- `properties.physchem.molecular_weight`
- `annotations.catalytic_activity`
- `features_positional.binding_site`
- `sequence.length`

Identifier paths are **direct**:
- `identifiers.uniprot`
- `identifiers.pdb`
- `identifiers.chembl`
- `identifiers.pubchem`
(No `secondary_ids` level.)

## SourceAssertion Mechanism (Critical)
**A SourceAssertion records what an external source asserts about an entity or property.**
All fields in all cards are resolved from SourceAssertions through the same protocol:

1) **Card fields store the resolved value only**
   - Each field has `value` and `source_assertion_ids`.
   - `source_assertion_ids` lists the assertions that support the resolved value.
   - This keeps the card readable and deterministic.

2) **All assertions from all sources live in `source_assertion_store`**
   - One SourceAssertion per value asserted by one source record (see the contract
     below). Alternative and contradictory assertions are kept.
   - The store is serialized with the card.

3) **Selection rules are explicit**
   - `selection_rules` is a map keyed by field path.
   - Rules never delete SourceAssertions.

4) **Conflicts are explicit**
   - `quality.conflicts` lists fields whose SourceAssertions disagree, with the
     competing values and their `source_assertion_ids`.

This mechanism is **homogeneous** across all fields and all card types. It is a core design decision.

### What a SourceAssertion is not
MOLI Platform Architecture 1.0 (`uibcdf/moli`) distinguishes `SourceAssertion ≠ Evidence ≠ Provenance`:
- **Evidence** belongs to Nextia: project-contextual scientific information that
  supports, contradicts or informs a Question or Hypothesis. Sabueso never produces it; a
  DiscoveryProject may cite SourceAssertions as the basis of its own Evidence.
- **Provenance** is cross-cutting: origin, lineage, transformations and production
  context of any object. A SourceAssertion *has* provenance (source, record, version,
  retrieval, mapping); it is not provenance itself.
- Qualifiers a source attaches to its own statements (UniProt ECO codes, cited PubMed
  IDs, ChEMBL assay descriptors) are stored in `source_metadata` under their source-native
  names; Sabueso defines no generic `evidence` field.

## SourceAssertion Contract (Approved)
Field names follow the conceptual contract of MOLI Platform Architecture 1.0
(`uibcdf/moli`, `schemas/sabueso_source_assertion_conceptual_schema.md`).
Every SourceAssertion stored in `source_assertion_store` must include:

**Required**
- `id: string` (deterministic, prefix `SA_`)
- `subject_ref: string | null` — stable reference to what the source record describes,
  `<namespace>:<record_id>` (e.g. `uniprot:P52789`, `pdb:2NZT`); `null` when the source
  record has no identifier
- `field_path: string` (canonical field path)
- `asserted_value: any` (the value as the source asserts it)
- `source: { type: string, name: string, record_id: string, version?: string }`
- `retrieved_at: date`

**Optional**
- `normalized_value: any` (only when Sabueso normalization changes the asserted value;
  the resolver then works on it)
- `source_metadata: dict` (source-native qualifiers such as UniProt ECO codes)
- `provenance_ref: string` (reference to a provenance record, e.g. mapping version)
- `timestamps: { published_at?: date, updated_at?: date }`
- `confidence: float` (only when reported by the source)

`source.type` is one of `database`, `literature`, `patent`, `curated`, `other`.

## Card Identity (Provisional)
MOLI Architecture 1.0 requires important scientific objects to be serializable and
referencable independently of process, file, database or service location. Every card
built by the aggregator therefore carries:
- `meta.card_id`: stable reference `sabueso:<entity_type>:<subject_ref>`, e.g.
  `sabueso:protein:uniprot:P52789`, taken from the subject of the primary identifier
  assertion (`identifiers.uniprot`, then `chembl`, `pubchem`, `pdb`) unless given
  explicitly;
- `meta.schema_version`: card schema version (`0.2.0`).

The identifier syntax is provisional (MOLI freezes referencability, not the format).
Card versions and snapshots, which Nextia needs to pin historical knowledge, are not
implemented yet.

## Relationship Contract (MVP)
Agreed in `devguide/archive/entity_resolver.md` (uibcdf/sabueso#6) and
implemented in `sabueso/core/relationship_store.py`.

A Relationship is first-class, traceable knowledge:
- **Fields:** `id`, `subject_ref`, `predicate`, `object_ref`, `qualifiers`, and, when
  present, `qualifier_conflicts`, `source_assertion_ids` and `derivation`.
- **Predicates (vocabulary):**
  - identity: `same_as`, `possibly_same_as`, `isoform_of`, `superseded_by`. For small
    molecules (#25), `same_as` links a source record (`chembl:<id>`,
    `pdb.ligand:<code>`, `pubchem:<cid>`, `drugbank:<id>`, `chebi:<id>`,
    `bindingdb:<id>`) to the anchor `inchikey:<standard InChIKey>`. It is supported by
    the ChEMBL, PDB CCD or UniChem statement of that key. Qualifiers: `name`, and
    `component_type` for PDB components;
  - structures: `has_structure`;
  - knowledge (added in #21, part 2a):
    - `annotated_with` (protein → GO term). Qualifiers: `aspect`, `term`, `go_code` (GO's
      own annotation code, e.g. IDA, IEA) and `assigned_by`;
    - `classified_in` (protein → family, domain, superfamily or site entry). Qualifiers:
      `classification`, `name` and `match_count`. Object namespaces are `interpro:`,
      `pfam:`, `cath:` (Gene3D), `supfam:`, `panther:`, `prosite:` and `cdd:`;
    - `interacts_with` (protein → protein; physical interactions, e.g. IntAct via
      UniProt). Qualifiers: `partner_gene`, `intact_ids`, `experiments`,
      `organism_differ` and `curated_by`;
    - `functionally_associated_with` (protein → `string:<taxon>.<id>`; STRING functional
      associations, not physical binding). Qualifiers: `partner_name`, `combined_score`,
      `channels` (neighborhood, fusion, cooccurrence, coexpression, experiments,
      databases, textmining), `string_id`, `species` and `required_score`. Supporting
      assertions record the STRING version in `source.version`;
  - bioactivities (added in #23):
    - `has_bioactivity` (protein → `chembl:<molecule>`). There is one relationship per
      measurement, identified by the `activity_id` qualifier. Qualifiers: `activity_id`,
      `target`, `molecule_name`, `parent_molecule`, `measurement` (type, relation, value,
      units, pchembl, comments, flags), `assay` (id, type, description, organism,
      confidence_score, relationship_type, variant_mutation) and `document`.
    - Support: the verbatim activity record (`relationships.has_bioactivity`) and the
      assay record (`relationships.has_bioactivity.assay`). The assay record is stated
      once per assay and shared by that assay's activities.
    - Activity classes are derived by `Card.bioactivities()` (`bioactivity_class@2`), and
      only there.
  - ligand sites (added in #28):
    - `has_ligand_site` (protein → `pdb.ligand:<code>`), one relationship per
      protein–ligand pair, from PDBe-KB. Qualifiers: `ligand_name`, `numbering`
      (`uniprot`), `residues` (`start`, `end`, `residue`, `observed_in` with structure,
      entity and chains), `structures`, and PDBe-KB's own descriptors `is_solvent`,
      `significance`, `num_atoms`, `scaffold_id`, `cofactor_id`, `reaction_id`,
      `chembl_id` and `drugbank_id`. PDBe-KB aggregates ligand copies, so its per-residue
      chains do not say whether one ligand contacts several chains; that reading comes
      from the per-instance contacts of `has_structure`.
    - Overlap with annotated sites (UniProt and InterPro family sites) is derived by
      `Card.ligand_sites()` (`annotated_site_overlap@2`), and only there. Each overlap names
      the annotation, its source and the matched positions.

  Any other predicate is rejected, and the vocabulary is extended deliberately. If
  components outside Sabueso (Nextia, MOLI Agent Context Assembly) come to depend on it,
  it becomes a shared contract to raise in `uibcdf/moli`.
- **Identity:** `id = REL_<hash>`, deterministic from subject, predicate, object and the
  predicate's identity qualifiers. `isoform_of` includes `isoform`, and
  `has_bioactivity` includes `activity_id`. `has_structure` is
  identified by the (protein, structure) pair alone: UniProt cross-references do not name
  polymer entities, so entity-level details are qualifiers. This lets UniProt and RCSB
  state the same relationship. The same relationship is therefore recognisable wherever
  it appears.
- **Support:** each relationship is supported by SourceAssertions (asserted by sources),
  by a `derivation` record (inferred by Sabueso: rule, inputs, parameters, Sabueso
  version), or by both. An unsupported relationship is rejected. A derived relationship
  never masquerades as a SourceAssertion.
- **Several sources:** when sources state the same relationship, their support is
  merged. Qualifier values they disagree on are kept in `qualifier_conflicts`, never
  overwritten.
- **SourceAssertions that support a relationship** use
  `field_path = relationships.<predicate>`.
  UniProt binding-site features keep their `ligand` (`name`, ChEBI `id`, and the `label`
  that tells two sites of the same ligand apart).
- **Family sites (#28):** `features_positional.family_site` holds the sites InterPro member
  databases place on the protein's own sequence (e.g. CDD `cd00311`: catalytic triad,
  substrate binding site, dimer interface). Each item has `location.sequence.fragments`,
  the verbatim `description` and its `signature`. They are family-level annotations,
  placed by the source's model, and stay apart from UniProt's `active_site` and
  `binding_site`. Their SourceAssertions have subject `uniprot:<accession>` (InterPro keys
  proteins by UniProt accession), the InterPro release in `source.version`, and the
  member database and signature in `source_metadata`.
- **Explicit SourceAssertion subjects:** a source that keys its records by another
  namespace passes `subject_ref` to `make_source_assertion` (InterPro, PDBe-KB:
  `uniprot:<accession>`). A shared context record uses a sub-path, such as
  `relationships.has_bioactivity.assay` for an assay. Their `asserted_value` is what the source
  states, i.e. the object and qualifiers as given by that source. Source property names
  are kept verbatim (e.g. UniProt's `GoEvidenceType`), while the relationship's
  qualifiers use Sabueso's vocabulary.
- **`has_structure` qualifiers:** `method`, `resolution` (`{value, unit}`, #32), `chains`, `ranges`
  (UniProt numbering, inclusive) and `coverage` (fraction of the canonical sequence).
  From RCSB: `polymer_entities`, `other_entities` (complexes) and `ligands` (`comp_id`,
  `description`, `subject_of_investigation`, `subject_of_investigation_provenance`, and
  `instances`: per ligand instance, the residues RCSB states as its neighbours, with
  chain, structure `seq_id`, UniProt `position` mapped through the entity alignment, and
  shortest stated distance). Instances are never merged: two copies of a ligand in two
  chains are not one ligand contacting both (#28). Methods are
  normalized to UniProt's vocabulary (`X-RAY DIFFRACTION` → `X-ray`); raw values stay in
  the SourceAssertions. The coverage
  class (`full_length ≥ 0.9 > partial ≥ 0.3 > fragment_or_peptide`) is derived knowledge,
  computed by `Card.structures()` with its rule and thresholds (`structure_coverage_class@1`).
  It is never stored as a qualifier.
- **Storage:** relationships live in the subject Card's `relationship_store`,
  serialized with the card. The aggregator rejects relationships that cite
  SourceAssertions absent from the card. The storage decision is to be re-evaluated in
  uibcdf/sabueso#19.

## Quantities (#32)
- Every physical quantity is stored as a node `{"value": x, "unit": "<canonical name>"}`
  (PyUnitWizard's long spelling: `"nanomolar"`, `"angstrom ** 2"`). A unit never lives in
  a field name, in metadata only, or in documentation only.
- Section fields that are quantities carry `unit` next to `value`
  (`sequence.molecular_weight`, `properties.physchem.molecular_weight`: `dalton`;
  `properties.physchem.tpsa`: `angstrom ** 2`). Counts (`hbd`, `hba`, `rotatable_bonds`,
  `sequence.length`) and logarithmic scores (`logp`, `pchembl`) are not quantities.
- Relationship qualifiers: `has_structure.resolution` and contact `min_distance`
  (`angstrom`); `has_bioactivity.measurement.normalized` (`nanomolar` for concentrations,
  `percent` for percentages, `null` when the source unit cannot be normalized). The
  measurement's `value` and `units` stay as ChEMBL states them.
- `Card.to_dict()` writes `quantities`: one PyUnitWizard `QuantityRecordBundle` whose
  entries are columns `"<path template>|<unit>"`. `Card.from_dict()`, and therefore every
  loader, verifies the bundle and checks every node against its column. A change made
  outside Sabueso is refused with `StorageError`. Details and design:
  `devguide/archive/quantities.md`.
- Paths and units are closed: `quantities.NEGOTIATED_UNITS` lists every quantity path
  template and its negotiated units. Writing a quantity elsewhere raises `SchemaError`.
  Reading one refuses the card, with the reader's expected dimensionalities taken from
  that list.
- `Card.quantity(path)` returns a PyUnitWizard quantity, and `Card.quantity_columns(template)`
  returns `{unit: array quantity}`. Views return quantities
  (`Card.structures()["items"][i]["resolution"]`, `Card.bioactivities()` measurement
  `normalized`).

## Quality records (#10)
`card.quality` records how the card was resolved and enriched. Its entries are not fields
stated by a source, so they are not `value`/`source_assertion_ids` nodes:
- `conflicts`: `[{field, type: "disagreement", values, source_assertion_ids}]`,
  disagreements among comparable assertions only;
- `alternatives`: `[{field, type: "not_comparable", compare_within, values: [{within,
  values, source_assertion_ids}]}]`, values of different methods, representations or
  sources, reported and never compared (`devguide/SELECTION_RULES_EXAMPLES.md`);
- `enrichments`: per-source enrichment outcomes;
- `entity_resolution`: the resolution trace.

`card.selection_rules` holds the rules the card was resolved with, the packaged defaults
included.

## SourceAssertion Creation Rules (Approved)
- Each mapped field value must generate **at least one** SourceAssertion.
- SourceAssertion IDs are **deterministic** from `(source, record_id, field_path, asserted_value)`
  (`generate_source_assertion_id`, prefix `SA_`).
- Mappings create SourceAssertions with `make_source_assertion`, **before** any
  selection rules are applied.

## Variants and mutagenesis (#33)
`features_positional.natural_variant` (observed in a population) and
`features_positional.mutagenesis` (a substitution the authors made) are separate fields:
they are different kinds of statement about a position. Each item keeps
`substitution` (`original`, `alternatives` as UniProt lists them), the verbatim
`description`, and for variants the `feature_id` (`VAR_…`) and `cross_references`
(dbSNP). The evidence stays in the item's own SourceAssertion (`source_metadata.eco`).
The description is never parsed into a category.

## Positional Features (Proteins/Peptides)
The schema includes positional features observed directly in UniProt JSON examples:
- Active site, Binding site, Disulfide bond, Glycosylation, Lipidation, Modified residue, Mutagenesis, Natural variant, Region, Motif, Topological domain, Transmembrane, etc.

These are stored as lists of objects with `location`, `description`, and `source_assertion_ids`.

For the exact, verified enumerations, see:
- `devguide/UNIPROT_ENUMS.md`

## Location Model (Sequence + Structure)
Positional features must support **both**:
- **Sequence‑based locations** (start/end indices, sequence ID, 1‑based indexing)
- **Structure‑based locations** (PDB ID, chain ID, residue numbers, optional atom IDs)

This is required for TopoMT integration and visualization.

Real‑ID validation examples:
- `devguide/LOCATION_EXAMPLES.md`

## Location Contract (Approved)
`location` is a typed container that supports multiple contexts:\n\n```\nlocation:\n  kind: \"sequence\" | \"structure\" | \"atom\" | \"substructure\"\n  sequence?: { sequence_id, start, end, indexing, residue_ids? }\n  structure?: { pdb_id, chain_id, residue_id?, residue_number?, atom_ids? }\n  atom?: { atom_ids, atom_id_type }\n  substructure?: { smiles?, smarts?, atom_ids? }\n```\n\nThe exact atom/residue identifier type must always be specified when relevant (e.g., PDB residue IDs, RDKit atom indices).

## Disease Section (ProteinCard)
Protein cards include a `disease` section with disease associations linked to their SourceAssertions.

## Ligands (ProteinCard)
Ligands are not a card section (the reserved `ligands.items` field was removed, #25).
They are relationships of the protein:
- `has_bioactivity`: measured molecules, one relationship per measurement (#23);
- the `ligands` qualifier of `has_structure`: the chemical components of each structure,
  with the PDB `subject_of_investigation` flag and its provenance (`Author`, declared by
  the depositor, or `RCSB`, assigned for older entries).

`Card.ligands(deck)` crosses them with a deck of SmallMoleculeCards anchored at the
InChIKey (`ligand_deck`). A role such as "inhibitor" is a derived activity class
(`bioactivity_class@2`), never an asserted attribute. The mechanism ChEMBL curates, when
present, is its `action_type`, kept in the measurement qualifiers.

## Clinical Layer (Small Molecules)
The schema includes a dedicated `clinical` section for:
- pharmacology, ADMET, clinical trials, pharmacovigilance,
- indications, contraindications, interactions.

This is intentionally separated from the core physchem and bioactivity data.
