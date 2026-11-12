---
summary: Reconcile all 21 required 0.15.0 exploration rows with existing routes and concrete limitations.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-12
verification: implementation_review
area: [functional-closeout, exploration]
---

# Functional inventory review for 0.15.0

Owner #148, coordinated under #112. This is step 1 of the
[functional closeout](functional_closeout_0150.md), against source `c8afce3` /
SDK269. The underlying production implementation is unchanged from `9ab6dd7`.

All **21 rows** of the [broad inventory](card_exploration_completion_0150.md#broad-profile-delivery-inventory)
have an existing public topic/question route, owning implementation tests and
recorded technical evidence. Actual catalog inspection observes 21 protein,
10 molecule, nine disease and four generic topics; all registered questions have
a registered destination. Catalog discovery alone is not successful execution.
No new feature-sized missing family is identified by this reconciliation.

`Implementation present` means a concrete route and its recorded scope exist.
It does not mean universal source coverage, all conceivable transitions, independent
scientific/usefulness acceptance or exact-candidate qualification. Older receipts
below keep their own source epochs. The current [receiving receipt](../evidence/functional_closeout_checkpoint_20261112.json)
owns new selected outcomes and their limits.

| ID / required objective | Actual topic / question | Owning contract and test | Technical evidence and remaining scope |
| --- | --- | --- | --- |
| P1 — Protein: function | `function`; `function` | [Contract](card_human_exploration_api.md); [owning tests](../../tests/core/test_card_protein_exploration_offline.py) | [Recorded receipt](../evidence/card_integration_checkpoint_20261111.json). Source function/organism/sequence scope; no missing prose is invented. |
| P2 — Protein: sequence and annotated regions | `sequence`, `annotated_regions`; `sequence_annotations`, `annotated_regions` | [Contract](card_regional_reading.md); [owning tests](../../tests/core/test_card_protein_source_offline.py) | [Recorded receipt](../evidence/structural_source_review_checkpoint_20261110.json). Original annotations, regional gaps and numbering; unsupported axes remain explicit rather than requiring a new alignment engine. |
| P3 — Protein: experimental structures | `structures`, `assembly_generation`; `region_coverage`, `assembly_generation` | [Contract](structural_source_review_walkthrough.md); [owning tests](../../tests/core/test_card_structure_assembly_navigation_offline.py) | [Recorded receipt](../evidence/destination_checkpoint_20261106.json). Exact declaration/source/component routes and bounded MolSysMT gate; general physical-copy reconciliation is outside the accepted finite gate. |
| P4 — Protein: predicted models | `predicted_structures`; `predicted_models` | [Contract](card_native_model_navigation.md); [owning tests](../../tests/core/test_card_protein_source_offline.py) | [Recorded receipt](../evidence/card_integration_checkpoint_20261111.json). Whole/fragment/source-reference questions exist; missing atomic or experimental equivalence stays unknown. |
| P5 — Protein: sites and molecular contacts | `sites`, `ligand_instances`, `ligand_site_comparisons`; `retained_sites`, `structure_ligands`, `ligand_site_comparisons` | [Contract](card_ligand_site_comparisons.md); [owning tests](../../tests/core/test_card_ligand_site_access_offline.py) | [Recorded receipt](../evidence/structural_source_review_checkpoint_20261110.json). Source sites, original instances and comparisons exist. Grouped investigation flags retain the explicitly deferred #192 limitation. |
| P6 — Protein: variants and isoform context | `variants`, `sequence_changes`; `variant_tissue_context`, `isoform_tissue_context`, `sequence_changes` | [Contract](card_variant_tissue_exploration.md); [owning tests](../../tests/core/test_card_variant_exploration_offline.py) | [Recorded receipt](../evidence/variant_tissue_context_saved_checkpoint_20261108.json). The former B6 continuation is delivered by variant/sequence-change/protein-context profiles; clinical significance or unsupported mappings are not inferred. |
| P7 — Protein: comparative context | `comparative_context`; `related_proteins`, `sequence_differences`, `knowledge_differences` | [Contract](card_protein_context_exploration.md); [owning tests](../../tests/core/test_card_knowledge_comparison_offline.py) | [Recorded receipt](../evidence/knowledge_comparison_saved_checkpoint_20261110.json). Supplied sequence/knowledge comparisons and original saved reading exist; equal positions and similarity do not establish correspondence or identity. |
| P8 — Protein: molecules and measured activities | `bioactivities`; `measured_molecules` | [Contract](card_bioactivity_exploration.md); [owning tests](../../tests/core/test_card_molecule_activity_exploration_offline.py) | [Recorded receipt](../evidence/molecule_context_display_checkpoint_20261112.json). The former broader molecule-context continuation is delivered. B2 default adoption remains deferred; #192 remains a declared structural-flag limitation. |
| P9 — Protein: biological associations | `associations`; `protein_associations` | [Contract](card_protein_context_exploration.md); [owning tests](../../tests/core/test_card_protein_context_offline.py) | [Recorded receipt](../evidence/protein_context_saved_checkpoint_20261109.json). Disease/pathway/interaction records and exact source directions are available; causal interpretation and actual-consumer acceptance are separate. |
| M1 — Molecule: chemical identity | `chemistry`; `chemical_identity` | [Contract](card_chemical_context_reading.md); [owning tests](../../tests/core/test_card_nature_exploration_offline.py) | [Recorded receipt](../evidence/card_integration_checkpoint_20261111.json). Original representations, formal charge and parent declarations are visible; unstated chemistry is not calculated. |
| M2 — Molecule: physicochemical properties | `properties`; `property_context` | [Contract](card_chemical_context_reading.md); [owning tests](../../tests/core/test_card_nature_exploration_offline.py) | [Recorded receipt](../evidence/card_integration_checkpoint_20261111.json). Original values, units, methods and determination scope are retained; a method name alone does not establish measured/calculated origin. |
| M3 — Molecule: chemical classes and roles | `classification`; `classification` | [Contract](chemical_classification_exploration.md); [owning tests](../../tests/core/test_card_chemical_exploration_offline.py) | [Recorded receipt](../evidence/chemical_saved_checkpoint_20261106.json). Source classes/roles and human/agent/saved access exist; they imply neither target activity nor efficacy. |
| M4 — Molecule: target/activity context | `activity_context`; `measured_targets` | [Contract](card_molecule_activity_exploration.md); [owning tests](../../tests/core/test_card_molecule_activity_exploration_offline.py) | [Recorded receipt](../evidence/molecule_context_display_checkpoint_20261112.json). Exact supplied-target joins, assay/publication context and original return/resave are implemented; #192 remains explicitly deferred. |
| M5 — Molecule: indications and clinical studies | `clinical`; `clinical_context` | [Contract](card_clinical_exploration.md); [owning tests](../../tests/core/test_card_clinical_exploration_offline.py) | [Recorded receipt](../evidence/clinical_saved_checkpoint_20261108.json). Indication, cited-trial occurrence and registry record remain separate; citations do not establish an outcome. |
| D1 — Disease: definition and terminology | `definition`; `meaning` | [Contract](card_exploration_v1_contract.md); [owning tests](../../tests/core/test_card_nature_exploration_offline.py) | [Recorded receipt](../evidence/card_integration_checkpoint_20261111.json). Source definition, synonyms and term status are visible; missing status is not current/obsolete evidence. |
| D2 — Disease: classification and related terms | `classification`, `identity`; `classification` | [Contract](card_exploration_v1_contract.md); [owning tests](../../tests/core/test_card_nature_exploration_offline.py) | [Recorded receipt](../evidence/card_integration_checkpoint_20261111.json). Hierarchy and identity remain distinct. Related captures must be supplied; no implicit ontology acquisition is required. |
| D3 — Disease: retained associations | `associations`; `retained_associations` | [Contract](card_disease_association_exploration.md); [owning tests](../../tests/core/test_card_disease_association_exploration_offline.py) | [Recorded receipt](../evidence/disease_association_saved_checkpoint_20261108.json). Occurrence-level MONDO/MedGen/source joins and saved access exist; original direction and unsupported identity remain explicit. |
| S1 — Shared: identity, sources, coverage and full content | `content`, `sources`, `coverage`; `publications` | [Contract](card_agent_access_v1_contract.md); [owning tests](../../tests/core/test_card_context_navigation_offline.py) | [Recorded receipt](../evidence/card_integration_checkpoint_20261111.json). Generic complete inspection and exact typed support exist. #182 remains a separate malformed-inner-input/glossary-versioning concern; its stricter prototype is not adopted. |
| S2 — Shared: literature | `literature`; `publications` | [Contract](card_literature_exploration.md); [owning tests](../../tests/core/test_card_literature_exploration_offline.py) | [Recorded receipt](../evidence/literature_saved_checkpoint_20261107.json). Publication, citation role and original support paths exist across natures; metadata never becomes project Evidence. |
| S3 — Shared: contextual navigation and saved reading | `content`, `sources`; `publications` | [Contract](card_exploration_v1_contract.md); [owning tests](../../tests/core/test_card_context_navigation_offline.py) | [Recorded receipt](../evidence/molecule_context_display_checkpoint_20261112.json). Every delivered scientific profile has an independent original reader; finite observed operations and actual origins are retained. Unvisited requests remain not_saved. |
| S4 — Shared: compact agent access | `content`, `sources`; `publications` | [Contract](card_agent_access_v1_contract.md); [owning tests](../../tests/core/test_card_knowledge_comparison_offline.py) | [Recorded receipt](../evidence/card_integration_checkpoint_20261111.json). Typed access shares scientific values, units, support and finite saved scope; actual-agent usefulness is not proved by conformance alone. |

## Concrete remaining dispositions

- **#192:** the maintainer explicitly defers correction for 0.15.0. Grouped
  investigation flags can depend on occurrence order: native explanations confuse
  negative/unknown combinations, and site summaries can overwrite a positive
  declaration with a later negative. Preserve and inspect original occurrences;
  no new aggregation rule is adopted. See the [owner analysis](../pending_bugs/ligand_investigation_flag_ordering.md).
  This is an accepted limitation, not a missing exploration family or a verified fix.
- **#182:** the stricter typed-glossary prototype was not adopted because original
  interpretation and pin compatibility need versioned treatment. Existing opaque
  parent preservation and native structural refusal remain in force under #181.
  This review does not close #182 or claim complete malformed-inner-input validation;
  it identifies no missing supported-nature panel caused by that issue.
- **Earlier generic continuations:** broader molecule-target work is now supplied by
  M4; comparative/association continuations by P6–P9. Source/region/component routes
  are supplied by P2–P5. Those older phrases do not establish an additional unnamed
  implementation block. A new failing required transition needs its exact input,
  public calls, observed result and owner. Unsupported physical reconciliation or
  inferred sequence correspondence is not silently promoted into a requirement.
- **Acceptance:** the independent researcher trial remains after 0.15.0 and
  `not_reviewed`. Outstanding scientific, actual-agent, workload and real-consumer
  acceptance keep their actual status; this technical audit does not supply them.
- **Delivery:** stopped integrations, missing exact-head hosted/installed gates,
  schema freezing and source/package publication keep their separate records.

## Five interaction refinements

| Required refinement | Concrete implementation / proof | Remaining acceptance |
| --- | --- | --- |
| First contact | `overview()`, source-bound orientation, topic/question catalogs; orientation and human-label tests | Independent comprehension remains unmeasured |
| Scientific questions | Actual registered protein/molecule/disease question maps and public walkthroughs | Scientific usefulness and consumer criteria retain their reviewers |
| Continuous exploration | Context/source/back routes, structure-component and molecule-assay/publication transitions; missing supplied captures are explicit | No claim of arbitrary joins or acquisition |
| Understandable complete reading | Typed values/units, nature-specific wording, complete literal inspection and scope/conflict reasons | #192 limitation remains visible; subjective clarity is not inferred from test counts |
| Python and Jupyter | Shared objects, text/HTML rendering, discoverable calls and saved reading | The independent Python-familiarity trial is explicitly deferred |

The implementation reconciliation is complete at this bounded scope. Final
functional milestone acceptance is a separate maintainer disposition; no tag,
release, scientific default change or unperformed review is created by this record.
