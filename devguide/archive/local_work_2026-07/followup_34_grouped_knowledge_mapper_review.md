# Follow-up 34: grouped knowledge, structural and translational mapper review

Reconcile **five preserved originals** on **2026-10-08**: four grouped mappers with
**30 `map_*` functions**, plus ten historical enrichment test functions. Current
native implementation covers their useful ready behavior. Additional requested
scientific scopes retain explicit acceptance below, independently of the stash.
No generic Evidence constructor, caller-subject fallback, guessed unit, blanket
curated/experimental label or unqualified clinical interpretation is restored.

## Individual dispositions

| Original | Current bounded coverage | Residual value |
|---|---|---|
| `sabueso/mappings/knowledge.py` (10 mappers) | Source-supported ChEMBL/BindingDB measurements and ligand identity; native PDBe-KB observed sites/interfaces; Reactome event hierarchy; UniProt catalytic Rhea pointers; source-anchored Orphadata/Open Targets disease associations; native HPA categories. GtoPdb remains deferred. | Direct Rhea equations/participants, additional PDBe-KB provider predictions and Open Targets drug/clinical candidates need distinct native query/identity/revision contracts. HPA quantitative expression and GtoPdb signalling/channel properties are not implemented by category summaries or synthetic rows. |
| `sabueso/mappings/protein_priority_sources.py` (3 mappers) | Native LIGYSIS page/residue/correspondence/structure declarations, AlphaFill model/transplants and transcript-aware gnomAD population consequences/pext. | Individual LIGYSIS ligands/other tables and exact source numbering remain independent of selected residues; AlphaFill transplants are model declarations, not experimental binding. Current gnomAD canonical/isoform checks replace the prototype's gene-version stripping and assumed protein relevance. |
| `sabueso/mappings/protein_structural_context.py` (10 mappers) | EPPIC native interfaces/assemblies/residue sides; Interactome3D representative protein table; PDBTM chain/region XML; TCDB literal assignment export; MetalPDB site/coordination context; ECOD domain classification; 3did DMI occurrences. RCSB-integrated membrane context remains distinct. | Interactome3D interaction-pair records and 3did DDI contacts/HMM/global interfaces remain broader scopes. OPM, ConSurfDB and FireProtDB remain deferred under their existing coordinate/rights conditions, with native measurement and alignment scope required. No source declares identity through the wrapper's caller accession. |
| `sabueso/mappings/protein_translational_sources.py` (7 mappers) | Native AlphaMissense and AAindex; GWAS gene associations; PRIDE Archive project metadata; source DrugCentral/TTD target observations; FDA/EMA orphan declarations; CIViC molecular-profile items; DepMap model metadata; ChannelsDB native memberships; ProBiS catalog. | Proteins API peptide/PTM/HPP records, gene-effect/dependency data, qualified therapeutic projection and original pocket/similarity geometry remain separate native scopes. AAindex scales carry no guessed structured unit; scores/predictions/categories are source statements. CASTp stays conditionally deferred. |
| `tests/tools/test_knowledge_enrichment_offline.py` (10 tests) | Current measurement/ligand/site, named composition, identity/disease, native source access, storage/deck and notebook/report tests supersede synthetic Evidence/card fields and general `consulted` metadata. | Useful measurement comparators, repeated observations, current source payloads, filters, exact storage and unknown-versus-failed states remain acceptance requirements. A synthetic BindingDB row without units cannot establish nM; a generic HTTP404 cannot establish an empty GtoPdb target response. No obsolete intervention-deck facade or schema is required to preserve those tests' intentions. |

The old four mappers retain lists, sometimes discard malformed rows, assume the
caller accession and use helper-generated Evidence-shaped values or field defaults.
Their synthetic tests describe scenarios, not validated original source responses.
Current SourceAssertions, native subjects, source-stated identity, named derived
rules and original independent support replace those mechanisms. Availability of a
provider or an `in_use` registry entry never implies complete scientific coverage.

## Future acceptance retained independently of old code

1. **Peptide/PTM/HPP observations:** obtain provider-native Proteins API or original
   provider records and preserve actual provider provenance (including PeptideAtlas,
   ProteomicsDB and unknown origins), original peptide/sequence/protein identifiers,
   modified forms, assay/sample/project context, references, confidence literals and
   release/sequence/position scopes. PRIDE Archive project metadata is implemented
   but does not state individual peptide/protein identifications. A depositor's
   project text, PTM term or HPP label cannot create experimental Evidence, current
   protein-form identity or canonical coordinate correspondence. Native response,
   completeness, failure and applicable rights need their own qualification.
2. **Drug and clinical-candidate context:** qualify actual native Open Targets
   query/response occurrences, target/gene and source-stated protein products,
   disease and drug identity, modality, original stage/status and clinical-report
   fields, versions and complete requested/returned-page scope. Preserve source
   drug/disease grouping and uncertain identity; neither a symbol nor a name merges
   them. Current Open Targets associations remain distinct from these unqueried
   candidate records. CIViC therapy combinations, DrugCentral/TTD labels, orphan
   designations, approvals and trial observations stay separate source statements;
   no treatment efficacy, indication equivalence or protein target is inferred.
   Stage zero, null/unknown labels and repeated reports must survive literally.
3. **Dependency and quantitative expression:** DepMap gene-effect/dependency work
   needs actual native release/model/gene and screen/condition, normalization,
   replicate and returned-file scope, with declared score semantics and independent
   source support. Current model context does not establish essentiality. HPA RNA,
   protein, assay, quantitative values and isoform scope are not interchangeable;
   retain original units and native dataset/sample/aggregate semantics. Categories
   and gene cross-references do not supply a measured protein form. This complements
   [the GTEx requirements](followup_32_uniprot_and_specialist_review.md) rather than
   making them a default expression projection.
4. **Additional structural observation scopes:** qualify native Interactome3D
   interaction-pair artifacts beyond the existing protein table and 3did DDI contacts,
   profile and global interfaces beyond DMI. Keep source structures/models, chain
   namespaces, assemblies, constructs, insertion/discontinuous residue bounds,
   partner roles, original parameters/units and independent sequence/PDB revisions.
   Actual chain/protein and coordinate correspondence requires source support or
   an explicit accepted supplied map; similarity, shared labels and aligned ranges
   never establish identity. Source predictions/opaque scores remain descriptive.
5. **Conservation, stability and existing pocket geometry:** retain current OPM,
   ConSurfDB, FireProtDB and CASTp deferrals. Reopen only with a concrete scientific
   use, qualified original native data and compatible use/retention/distribution
   conditions. Stability requires measured construct/mutation/sequence, parameter,
   units, sign/comparator and experimental conditions. Conservation grades need
   reference axis/method/revisions, without transferring function. Membrane/pocket
   observations retain source model/chain/parameters, area/volume/energy units and
   coordinate basis. Current ChannelsDB memberships/ProBiS catalog, RCSB-integrated
   membrane segments and [provider deferrals](../../pending_proposals/historical_provider_reactivation.md)
   do not implement these broader scopes; no scans, alignment, modelling or jobs
   are run by Sabueso to manufacture missing source results.
6. **Direct reaction descriptions and provider site predictions:** qualify actual
   Rhea reaction ids/equations/direction/participants/stoichiometry/ChEBI/publication
   and scientific revisions independently of current UniProt catalytic pointers.
   Reaction statements do not identify protein catalysts without source support.
   Additional PDBe-KB prediction providers require original observed-versus-predicted
   scope, native site identifiers/model/chain/sequence/revisions, scores, returned
   numbering and source metadata. A zero score must survive; an arbitrary provider
   name or residue code does not assert a canonical pocket or its composition.
   Current `residue_set_composition@1` summarizes caller-selected source positions,
   keeping duplicates/support/unknown types; it never supplies cavity membership.

Existing native file/hash/rights and online/fixture/supplied-file parity prerequisites
apply to each future scope. These are requirements for re-evaluation, not a pledge
to immediately implement every prototype field or reactivate deferred providers.
Public acceptance is recorded in
[issue #112](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6062086611),
with native source adoption under #83 and access/retention under #95.

## Qualification

The two applicable local gates pass separately, both with pytest-receptor
(`--receptor=llm`), **12 workers**, Python **3.14.7** and the existing editable
`molsyssuite@uibcdf_3.14` environment:

- Integrated measurement/acquisition, pathways, transcript/population context,
  disease identity, ligand decks/sites and residue composition: **221 passed in
  8.71 seconds**.
- Native source access and the relevant structural, variant, proteomic, expression,
  pharmacological/orphan and translational readers: **1394 passed in 18.87 seconds**.

These are **1615 selected cases**, not a new full-suite checkpoint. No executable,
fixture, provider, packaging or schema change occurs. The full code checkpoint
remains follow-up 32's **5549 passed in 176.40 seconds**; no new full run is claimed.

Outside-checkout editable replay preserves **598 SourceAssertions** in a native
TcTIM card with **493 independent ChEMBL measurements**, its supported structure
context, exact card JSON/SQLite/KnowledgeStore documents/pins and a **256-card
ligand deck** with exact scientific JSONL/snapshot round trips. Explicit residue
composition counts three unique positions, retains the duplicate and sequence
support, and never establishes cavity membership. Six standalone native scopes
retain **216 assertions**: HPA 22, PRIDE 1, DepMap 1, CIViC 93, AlphaFill 87 and
EPPIC 12. Envelopes, assertions, detached acquisition and document digests survive
exact JSON round trips without new protein projection. **Zero source requests**.
Receipt: `/tmp/sabueso-followup34-replay.json`; artifacts:
`/tmp/sabueso-followup34-replay`.

Registry, strict Sphinx HTML at `/tmp/sabueso-followup34-docs-build`, maintained
review links and diff gates pass. Original integrity verifies **87 original byte
lengths/SHA-256 hashes**, 91 accounted paths, unchanged stash/empty index, all
published schemas/frozen cards, published 0.3.12 shape and unchanged native
UniProt/scientific fixtures. Unpublished 0.3.13 is unchanged by this slice.
Receipts: `/tmp/sabueso-followup34-integrity.json` and
`/tmp/sabueso-followup34-gates.json`. No remote checkpoint or `gh-run-receptor`
inspection is needed for this local review.

## Remaining audit

Generic individual-review labels fall **16 to 11 original files**. This is a
file-audit count, not eleven ready capabilities. The large protein/source wrappers,
remaining annotation/priority/translational tests, public/core exports, GO helper
and conceptual/old schema inputs need reconciliation. Historical scientific cards,
ligand references and exploratory notebooks still require final disposition.
Stash and all 87 exact exports remain intact; no staging, commit, push, deletion,
new environment or additional source activation occurs. Deletion is not yet recommended.

### Remaining individual file queue

- `sabueso/__init__.py`
- `sabueso/core/__init__.py`
- `sabueso/tools/db/go.py`
- `schemas/card_schema.yaml`
- `schemas/card_schema_0.1.0.yaml`
- `sabueso/tools/protein.py`
- `sabueso/tools/protein_sources.py`
- `tests/tools/test_online_protein_priority_sources.py`
- `tests/tools/test_protein_annotation_sources_offline.py`
- `tests/tools/test_protein_priority_sources_offline.py`
- `tests/tools/test_protein_translational_sources_offline.py`
