# Follow-up 32: UniProt annotation recovery and specialist mapper review

Recover native additional UniProt statements and close a five-file specialist mapper
review on **2026-10-08**. No new provider is activated. Additional comment/feature
coverage is qualified from unchanged existing public UniProt fixtures. Conditional
provider, richer gene/kinetic/context and source-identity requirements remain
self-contained below, independently of the original package tree or stash.

## Qualified native UniProt recovery

Development **card schema 0.3.13** adds five text fields: activity regulation,
domain notes, similarity, source cautions and miscellaneous text. It adds seven
positional fields: chain, lipidation, motif, region, sequence conflict, topological
domain and transmembrane, and activates the existing positional domains field.
The five unchanged native fixtures provide **57 newly retained SourceAssertions**:
**11 text occurrences / 46 feature occurrences**. Distribution: P52789 14,
P35372 27, A0A140VJM9 3, P60174 11 and P52270 2. Native domain occurrences include
two HK2 hexokinase domains and two A0A140VJM9 dehydrogenase domains.

Every new feature preserves native bounds/modifiers, full original feature, source
molecule scope, independent ECO pointers and sequence revision. Missing endpoints
remain missing; malformed endpoint types/objects fail through ConnectorError.
Source molecule labels do not identify the canonical sequence. Residue views retain
unplaced declarations for missing/fuzzy/invalid/foreign-scope or known sequence-
revision mismatches rather than completing an exact interval. Known source sequence
versions are compared only on original supporting UniProt assertions; unknown
revisions remain unknown. Original entry version and retrieval stay separate.
Source cautions live in `annotations.source_cautions`, never quality conclusions;
source similarity is descriptive text, never entity identity. Named current residue
rules remain corrections to their existing exact-source-range contract.

The initial domain-only extension used an existing schema field, but the shape gate
correctly detected changed serialization. The published 0.3.12 schema, shape and
frozen cards are not modified. The unpublished `card_schema_0.3.13.yaml` registers
all 13 optional refresh paths in `SCHEMA_CHANGES`; its shape is recorded with
`python tools/card_shape.py --write` (**1591 paths**). Existing 0.3.12 cards remain
readable as 0.3.12; explicit migration reports missing optional source knowledge,
which only a fresh native read/refresh can supply. No published release or frozen
0.3.13 qualification is claimed.

## Five-file specialist review

The five original grouped mappers contain **43 `map_*` functions**. Each is scoped
against the current registry and native implementations; a status of `in_use` does
not imply that every prototype field or protein projection is already implemented.
No additional ready source mapper implementation is found in these old wrappers.

| Original mapper | Covered/current scoped routes | Remaining bounded acceptance |
|---|---|---|
| `protein_annotations.py` | AlphaFold native model records/qualifiers; MobiDB source sequence/region/modification records; STRING relationships; Complex Portal native complex/participants; native iPTMnet HTML substrate rows; GlyGen glycosylation/phosphorylation; transcript-aware ClinVar summaries. | M-CSA source reference numbering needs an explicit accepted residue mapping; broad Proteins API variant context is a separate source/sequence/revision contract. DoGSite3 is a computation service outside Sabueso's knowledge-source scope. No blanket curated/experimental class or assumed caller-protein numbering is restored. |
| `protein_context.py` | Native IntAct MITAB and SIGNOR causal observations; GTEx tissue terms/gnomAD exon usage; WikiPathways native xrefs; GPCRdb classification/segments/numbering. | Ensembl remains deferred for a demonstrable transcript/gene-tree/paralogue need. SABIO-RK kinetics require native accessible records and compatible terms. GTEx median gene expression is not existing tissue-term/pext coverage; see native gene expression requirements below. |
| `protein_drug_discovery.py` | PubChem BioAssay native bioactivities, Pharos native five-field target metadata, KLIFS kinase/pocket context, Monarch native direct-subject association rows, independent APPRIS transcript occurrences. | Rich QuickGO qualifiers/extensions are a separate native annotation contract; maintained GO currently comes through UniProt. Broader Pharos discovery/ligand-count/family fields need actual query/output qualification. BioLiP2 bulk sites remain deferred and require exact source structure/chain/numbering and stated protein correspondence. No summary label supplies experimental Evidence or a druggability rank. |
| `protein_expansion.py` | OMA source orthology; complete native SWISS-MODEL metadata/alignments; SIFTS correspondences; PDBe native global percentiles; NCBI Gene product identity audit; complete native MEROPS assignment export. | Rich NCBI gene description/summary/aliases/nomenclature are separate gene-scoped metadata; BioGRID needs authorized input/key and exact Gene/taxon/partner identity. PhosphoSitePlus remains retired under its existing restrictive terms. ASD/COSMIC remain conditional deferrals in the independent provider matrix. |
| `protein_specialist.py` | PDB-REDO native original/refined stage context; DisProt independent source-sequence regions; HPO Gene/disease rows; ClinGen native validity CSV; OmniPath aggregate flags and original resource support; AmyPro investigated-sequence regions; BRENDA native EC-class descriptions. | BRENDA kinetics/protein assignments are not EC-class description coverage. ELM/BioCyc/OMIM remain conditional deferrals. Both OmniPath effects/unknown labels survive in current readers; old effect selection and blanket class defaults add no useful recovery. |

The current native readers deliberately keep independent record, sequence, gene,
structure, transcript, model and numbering scopes. The old helper `_mapping`
constructs Evidence-shaped values with default classes and caller subject labels;
it is not a generic conversion or current card-admission contract. Synthetic test
bundles do not qualify a provider response. Native classes/scores stay literal,
absence/cuts/failure stay query-scoped and physical quantities require source units.

## Remaining specialist requirements, independent of old code

1. **GTEx gene expression:** qualify exact versioned Ensembl gene and dataset/tissue
   native median-expression response. Preserve complete requested/query/page scope,
   original units, missing/zero values, tissue definitions and sample/aggregate
   semantics. A default `TPM` does not establish a source unit. This is gene-level
   aggregate expression, not protein abundance or isoform usage. Existing GTEx
   tissue terms and gnomAD pext do not implement it; source-stated gene/protein
   correspondence and any current card projection need explicit support.
2. **BRENDA/SABIO-RK kinetics:** require actual provider-native original observations,
   available authorized access/rights, independently declared enzyme/protein/gene/
   sequence or organism context, parameter semantics, comparator, units and native
   temperature/pH/buffer/substrate/cofactor/inhibitor/activator conditions. Keep
   original publications, measured construct and revisions separately. EC class
   descriptions do not supply kinetic observations or enzyme-to-protein identity.
   No class assignment, unit guess, zero-value loss or homology transfer is admitted.
3. **NCBI Gene descriptive metadata:** qualify actual native Entrez records and
   exact Gene/taxon, revision/status/current-id semantics and field occurrences.
   Preserve summary, aliases, nomenclature, chromosome/map location only as gene
   statements, with source support; symbols and summaries do not merge proteins.
   Existing gene-product identity-audit access is not complete descriptive coverage.
4. **QuickGO annotations:** require exact annotation/protein/isoform identity,
   native GO/ECO/publication and with-from pointers, negation/qualifiers, assigned-by,
   date/release/taxon, extension groups and complete returned page scope. Maintain
   annotation semantics independently of GO term descriptions and never fabricate
   project Evidence or experimental classes from a code's spelling.
5. **Richer Pharos/BioLiP/M-CSA/Ensembl context:** qualify each requested native
   field/occurrence under the existing provider status and actual scientific need.
   Preserve Pharos counts/query/revisions, structure/chain/model scopes, original
   discontinuous/inserted author numbering and explicit sequence/transcript/gene
   correspondence. A native descriptor, shared accession label, residue number,
   sequence similarity or orthology does not perform an identity or coordinate join.
6. **Provider/job boundaries:** the seven conditional providers remain governed by
   [the reactivation matrix](../../pending_proposals/historical_provider_reactivation.md).
   BioGRID, M-CSA, BioLiP, Ensembl and SABIO-RK retain registry triggers. DoGSite3
   job/geometry work belongs to the computation owner; PhosphoSitePlus requires the
   existing written-rights condition before any query/intake. Do not re-probe
   maintainer-confirmed unavailable access or activate an entire historical profile.

These retained source/capability conditions are owned by #83/#112, with #95 for
access and #131 for qualified supplied-file routes. Native input validators,
original bytes/hash/retrieval/terms, exact scientific identity and online/fixture/
supplied-file equivalence remain prerequisite to any future implementation.

Public native annotation/specialist acceptance is recorded in
[issue #83](https://github.com/uibcdf/sabueso/issues/83#issuecomment-6061746346),
with implementation scope cross-linked to #112. Local recovery receipts remain here.

## Qualification

The final selected mapper/residue/state/schema/migration/literature gates pass:
**148 passed in 8.92 seconds**, including **54 new cases**, pytest-receptor with
**12 workers**. The first broader gate exposed two exact migration expectations
still missing the 13 newly declared refresh gaps (**146 passed / two failed**).
Update both expectations to assert all new gaps; no production guard is weakened.
The shape gate's initial change detection leads to the unpublished schema version
rather than changing the frozen published version.

Final full offline checkpoint: **5549 passed in 176.40 seconds**, pytest-receptor,
**12 workers**, existing editable Python **3.14.7**, 10 expected fixture source-
failure/truncation warnings. No additional environment is prepared.

Outside-checkout replay verifies editable import/metadata and five native cards:
**898 SourceAssertions**, including the **57 newly retained assertions**. Exact
scientific documents, metadata and snapshots survive card JSON/SQLite,
KnowledgeStore and deck JSONL/SQLite. It checks inclusive domain support, the
inter-domain gap, unplaced known sequence-revision mismatches, unchanged published
0.3.12 reading and 13 explicit migration refresh gaps. **Zero source requests**.
Receipt: `/tmp/sabueso-followup32-replay.json`; artifacts:
`/tmp/sabueso-followup32-replay`.

Ruff lint/format (**942 files**), generated registry, recorded shape **0.3.13**
(**1591 paths**), schema/field-path alignment, strict Sphinx HTML at
`/tmp/sabueso-followup32-docs-build` and `git diff --check` pass. Integrity verifies
all **87 original byte lengths/SHA-256 hashes**, 91 accounted paths, unchanged
stash, empty index, all published frozen cards and prior formal schemas, published
0.3.12 shape and all five unchanged native UniProt fixtures. The development
0.3.13 schema has no frozen card and is not claimed as a published qualification.
Receipts: `/tmp/sabueso-followup32-integrity.json` and
`/tmp/sabueso-followup32-gates.json`. No remote code checkpoint occurs; no
`gh-run-receptor` inspection is necessary for this local slice.

## Remaining audit

The five grouped originals now have final individual-review dispositions. Generic
individual-review labels fall from **26 to 21** original files. UniProt's already
reviewed original receives this additional qualified recovery record without being
counted again. This is a file-review queue, not 21 ready features/providers.
Remaining source-sequence/residue, core/schema entry points, other grouped specialist
mappers/tests and historical scientific artifacts need final reconciliation.
Stash and 87 exact exports remain intact. No stash deletion, stage, commit, push,
separate environment or remote checkpoint. Future capabilities above can survive
closure without obsolete runtime code or requiring immediate implementation.

### Remaining individual file queue

- `sabueso/__init__.py`
- `sabueso/core/__init__.py`
- `sabueso/resolver/__init__.py`
- `sabueso/tools/db/go.py`
- `sabueso/tools/db/scope.py`
- `sabueso/tools/db/uniprot.py`
- `schemas/card_schema.yaml`
- `schemas/card_schema_0.1.0.yaml`
- `sabueso/mappings/knowledge.py`
- `sabueso/mappings/protein_priority_sources.py`
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
