# Sabueso — Scientific Potential

## Purpose

Sabueso begins as the **Knowledge component of MOLI**: a system for acquiring, normalizing, resolving, and preserving molecular knowledge from heterogeneous sources while retaining the SourceAssertions and provenance behind that knowledge.

Its long-term scientific potential goes substantially beyond data aggregation.

Sabueso should evolve toward a system in which molecular knowledge can be **represented, related, navigated, compared, composed, and scientifically interrogated** while preserving traceability to the external sources from which that knowledge originates.

This document records that direction. It is a **vision document**, not a frozen API, implementation plan, or commitment to implement all capabilities described here. The current vertical pilots should continue to pull the smallest scientifically useful implementation.

## From knowledge containers to scientific knowledge objects

A Card should not ultimately be understood merely as a container of normalized fields.

Conceptually, a Card combines structured knowledge about a molecular entity with SourceAssertions, provenance, and relationships to other entities. A Deck should not be understood merely as a list of Cards: it may represent a scientifically meaningful collection such as TcTIM ligands, TIM homologs, experimental structures, inhibitors, or interaction partners.

Cards and Decks should therefore be able to become **composable scientific knowledge objects**.

## Entity identity comes before knowledge composition

Cross-source knowledge is useful only if Sabueso knows which molecular entity each assertion refers to.

External identifiers are not themselves canonical molecular identity:

    UniProt accession
    PDB entity
    ChEMBL target
    database synonym
    paper name
            |
            v
       EntityResolver
            |
            v
    canonical Sabueso entity

Entity resolution should preserve uncertainty rather than manufacture equivalence. Future identity relationships may need distinctions such as same_as, possibly_same_as, isoform_of, variant_of, and derived_from.

This is distinct from field resolution:

- **EntityResolver** — what entity are these records talking about?
- **FieldResolver** — given assertions about that entity/property, what resolved representation should a Card expose?

A false entity merge is potentially more damaging than an unresolved field conflict and should remain auditable.

## Relationships are first-class knowledge

Molecular entities rarely make scientific sense in isolation.

Sabueso should eventually represent relationships such as:

    Protein -- homologous_to --> Protein
    Protein -- interacts_with --> Protein
    Protein -- binds --> Ligand
    Ligand -- inhibits --> Protein
    Protein -- has_structure --> Structure
    Structure -- contains/exposes --> Feature
    Protein -- has_variant --> Variant
    Ligand -- similar_to --> Ligand
    Protein -- associated_with --> Disease

These relationships must not become untraceable graph edges. A relationship should remain connected to its subject, predicate, object, qualifiers/context, and supporting SourceAssertions.

Qualifiers may be scientifically essential: organism, isoform, mutation, experimental construct, assay, pH, temperature, concentration, cell line, biological state, or other conditions.

Sabueso may therefore expose graph-like behavior without becoming merely a generic knowledge-graph framework. Scientific semantics, context, and provenance matter more than graph representation itself.

## Heterogeneous scientific relationships

Useful operations are not limited to Cards of the same type.

Examples include:

- **ProteinCard × ProteinCard** — sequence/structural relationships, shared ligands, homologs, interactions, functional differences.
- **ProteinCard × LigandCard** — binding knowledge, affinity/activity measurements, inhibition/activation, complex structures, selectivity.
- **ProteinCard × StructureCard** — entity mapping, constructs, conformations, variants, bound ligands.
- **ProteinCard × DiseaseCard** — associations, mechanisms, therapeutic relevance.
- **LigandCard × LigandCard** — chemical relationships, shared targets, activity profiles.

The scientific meaning of an operation depends on the entity types and the assertions available for them.

## Card × Card scientific operations

Two Cards should eventually be scientifically comparable and relatable.

For example, TcTIM Card × HsTIM Card could support questions involving sequence and structural similarity, shared/distinct ligands, known inhibitors, interaction partners, experimental structures, variants, functional differences, and source agreement/disagreement.

A future API might expose operations conceptually similar to:

    tc_tim.compare(hs_tim)
    tc_tim.related_to(hs_tim)
    tc_tim.shared_ligands(hs_tim)
    tc_tim.assertions("oligomerization")

These examples illustrate scientific intent rather than defining a final API.

## Card × Deck and Deck × Deck operations

Scientific questions often concern collections rather than individual entities.

For example:

    Deck A = known TcTIM ligands
    Deck B = known HsTIM ligands

Sabueso could support questions such as:

- Which ligands occur in both sets?
- Which are exclusive to TcTIM?
- Which chemical families are enriched?
- Which molecules have the strongest experimental support?
- Which compounds have associated experimental structures?
- Which relationships recur across independent sources?

Useful conceptual operations may include compare, intersect, difference, filter, group, aggregate, rank, join, expand, neighbors, and subgraph.

The names are illustrative rather than frozen API decisions.

## Asserted knowledge and derived knowledge are different

Sabueso must distinguish what an external source explicitly asserts from what Sabueso derives by operating on assertions.

For example, “ChEMBL reports that Ligand X inhibits Protein A” is epistemically different from “Ligand X belongs to both the Protein A and Protein B ligand sets.”

The second result may be deterministic, reproducible, and scientifically useful, but no external source necessarily asserted it.

Derived knowledge should therefore retain a derivation record containing, where applicable:

- operation;
- inputs;
- parameters;
- underlying SourceAssertions;
- software/Sabueso version;
- source snapshots or retrieval context.

**Derived knowledge must never masquerade as a SourceAssertion.**

## Scientific operations must preserve provenance

Derived knowledge must not erase the origin of the information from which it was obtained.

An operation such as the intersection of TcTIM and HsTIM ligand sets should not merely return molecular identifiers. It should remain possible to inspect why each entity appears, which operation produced it, which inputs participated, which assertions support the underlying relationships, which sources produced those assertions, whether sources agree or conflict, and what context applies.

> **Scientific operations over knowledge should preserve the path back to the assertions and sources that made the result possible.**

## Explainability is a property of scientific knowledge operations

A derived result should, in principle, be able to answer:

> **Why is this in the result?**

Conceptually, an explanation for a compound appearing in an intersection might identify the TcTIM binding assertions, the HsTIM binding assertions, their sources, and the intersection operation that combined them.

The final API may differ. The architectural property is more important than the method name: **derived knowledge should remain explainable in terms of its operation, inputs, context, and supporting SourceAssertions.**

## Conflict is a first-class outcome

Sabueso should not force heterogeneous sources into artificial consensus.

Different assertions about oligomerization, activity, structure, or another property may represent disagreement, context dependence, or genuinely different observations.

Resolution rules may expose a canonical representation when scientifically justified, but the underlying assertions and disagreement must remain inspectable.

Potential future operations such as tc_tim.conflicts() or tc_tim.assertions("oligomerization") illustrate the desired behavior.

## Reproducibility and temporal knowledge

External knowledge changes. A database queried in 2028 may no longer return exactly what it returned in 2026.

Where scientifically relevant, a derived result should be able to retain:

- Sabueso version;
- operation and parameters;
- input Card/Deck identities;
- Card versions or snapshots;
- source versions;
- retrieval dates;
- underlying SourceAssertions.

Important knowledge objects should therefore be compatible with versioning or snapshot semantics.

This is particularly important when Nextia records a Discovery decision based on Sabueso knowledge: future users should be able to determine **what knowledge state informed that decision at the time**.

## Knowledge navigation

Relationships make Sabueso knowledge navigable.

Starting from one Card, future operations could conceptually support neighbors, expansion through homologs/interactions, related ligands, and assertion inspection. A Deck may naturally represent a selected region or working subset of this connected knowledge space.

## KnowledgeQuery as a future semantic interface

MOLI should not need to know the endpoint and schema of every external database.

A future semantic query layer could express questions such as:

- What inhibitors are known for TcTIM?
- Which experimental structures contain bound ligands?
- Which homologs have reported interface inhibitors?

Sabueso could determine which sources and internal knowledge objects are relevant and return Cards, Decks, relationships, SourceAssertions, conflicts, and derivation information.

This should remain a knowledge capability rather than turning Sabueso into an autonomous discovery agent.

## Scientific literature as a first-class knowledge source

Structured databases contain only part of the knowledge required for molecular discovery. Important information remains primarily in articles, preprints, supplementary material, methods, tables, figures, captions, and supporting datasets.

In the long term, Sabueso should treat scientific literature as another first-class source of molecular knowledge.

The objective is not merely document retrieval. The conceptual flow is:

    scientific document
            |
            v
    document structure
       /    |     \
    passage table figure/caption/supplement
            |
            v
    entity recognition
            |
            v
    assertion / relationship extraction
            |
            v
    entity normalization
            |
            v
    SourceAssertions
            |
            v
    Cards / relationships / Decks

A paper reporting that a compound perturbs the TcTIM dimer interface might yield normalized entities, a reported relationship, experimental conditions/method, measurements, and a SourceAssertion whose location can point to the relevant Results passage, Figure 3B, Table 2, or supplement.

Fine-grained source location is valuable: provenance should be able to reach the relevant passage, table, figure, caption, or supplementary item rather than stopping at the DOI.

## Extraction provenance

Literature-derived knowledge needs provenance not only for **where the statement came from**, but also for **how it entered Sabueso**.

Useful distinctions may include:

- database-imported;
- manually curated;
- rule-extracted;
- model-extracted;
- model-extracted + human validated.

If AI assists extraction, relevant model/configuration information and the underlying document location should remain traceable.

An AI-generated interpretation is not automatically an external scientific SourceAssertion. Sabueso must distinguish extraction of a statement actually present in a source from generation or inference performed by a model.

## Beyond RAG

Retrieval-augmented generation can locate text relevant to a question. That is useful, but it is not the same problem Sabueso is intended to solve.

Sabueso should increasingly transform external scientific information into explicit, inspectable knowledge:

    databases + literature
              |
              v
         acquisition
              |
              v
        normalization
              |
              v
      SourceAssertions
              |
              v
    entities + relationships
              |
              v
       Cards / Decks
              |
              v
    scientific operations

Language models may help extract, normalize, reconcile, or navigate this information, but the knowledge layer should remain inspectable independently of model memory.

## Patents and other strategic sources

For molecular discovery, relevant knowledge may also exist outside conventional scientific databases and papers.

Future source classes may include patents, clinical-trial registries, regulatory documents, curated internal datasets, and other controlled scientific sources.

Patent knowledge may eventually support questions about reported chemical series, related molecular space, claims, ownership, novelty context, and freedom-to-operate analysis.

These are long-term possibilities, not current Sabueso commitments. Source-specific legal, licensing, access, and provenance requirements must be respected.

## Known, conflicting, missing, and unknown

A knowledge system should not only describe what it knows.

It should preserve distinctions among:

    known / supported
    conflicting
    not found
    not queried
    not available
    unknown
    evidence of absence

In particular:

> **No evidence found is not the same as evidence of absence.**

Such states should not be collapsed into false negatives.

## Knowledge gaps as a bridge to Discovery

Explicit unknowns and conflicts can become scientifically useful outputs.

    Sabueso
    "What do we know?"
            |
            +-- known
            +-- conflicting
            +-- unknown / missing
                      |
                      v
                   Nextia
          "What should we investigate?"

A knowledge gap is not automatically a research question, and Sabueso does not decide what deserves investigation. But it can expose structured gaps that Nextia, MOLI Agent, or a scientist may interpret in Discovery context.

This provides a natural connection to the MOLI learning loop:

    KNOW -> MODEL -> DO -> DISCOVER -> LEARN -> KNOW

## Relationship with Nextia

Sabueso and Nextia must preserve an important epistemic boundary.

Sabueso records what external sources assert and what knowledge can reproducibly be derived from those assertions. Nextia records how information is interpreted within a DiscoveryProject.

A Sabueso SourceAssertion may become relevant to a Nextia Hypothesis, but it does not automatically become Evidence.

> **SourceAssertion != Evidence.**

Sabueso owns traceable external knowledge and reproducible knowledge derivations. Nextia owns project-specific scientific interpretation.

Knowledge learned inside Nextia should not automatically flow back into Sabueso. Promotion into persistent knowledge requires an explicit curation/validation boundary. **LEARN does not mean automatic promotion.**

## Relationship with MolSysSuite

Sabueso knowledge may inform molecular modeling without owning the models themselves.

MolSysMT may consume identifiers, annotations, mappings, or references originating in Sabueso Cards. TopoMT may associate calculated topographical features with Sabueso entities. DockingMT may use known ligands or structures discovered through Sabueso when constructing a docking project.

The boundary remains:

> **Sabueso knows about molecular entities and external knowledge; MolSysSuite models and computes on molecular systems.**

Interoperability should not collapse those responsibilities.

## Two levels of access

Future consumers may need both semantic and source-specific access.

At a semantic level, Sabueso may eventually expose operations such as finding known inhibitors, homologs, structures, disease associations, or mutations.

At a lower level, expert workflows may still need explicit access to source-specific connectors or assertions.

The semantic layer should prevent MOLI from needing to understand every external endpoint while the lower layer preserves scientific control and inspectability.

## Knowledge packets

A useful future composition may be a **KnowledgePacket**: a traceable bundle assembled around a scientific focus rather than a new epistemic primitive.

For example, a packet for selective TcTIM inhibition could contain:

- focus and entities;
- relevant Cards and Decks;
- relationships;
- structures and ligands;
- SourceAssertions;
- derived knowledge;
- conflicts;
- unknowns/knowledge gaps;
- provenance and snapshot information.

A KnowledgePacket should be understood as a composition/view over existing Sabueso knowledge, not as a replacement for Card, Deck, SourceAssertion, or provenance.

## Sabueso as the knowledge layer of Molecular Intelligence

The long-term role of Sabueso can be summarized as:

    heterogeneous knowledge sources
    databases / literature / datasets / ...
                     |
                     v
              entity resolution
                     |
                     v
              SourceAssertions
                     |
              +------+------+
              v             v
           entities     relationships
              |             |
              +------+------+
                     v
                Cards / Decks
                     |
          +----------+----------+
          v          v          v
      navigation  scientific  comparison
                  operations
                     |
                     v
             Derived Knowledge
                     |
          provenance + explanation
                     |
          +----------+----------+
          v          v          v
        known     conflict   unknown/gap
                     |
          +----------+----------+
          v                     v
       Nextia               MolSysSuite
     interpretation           modeling

Sabueso should therefore aspire to become more than a molecular database aggregator.

Its distinctive value is the combination of heterogeneous knowledge acquisition, normalized molecular identity, SourceAssertions, provenance, conflict/uncertainty preservation, relationships, composable Cards/Decks, scientific operations, navigation, explainability, reproducibility, explicit knowledge gaps, and eventually structured knowledge extraction from scientific literature.

## Design constraint for the current MVP

None of the capabilities described above need to be implemented prematurely.

The current TcTIM/HsTIM vertical pilot should continue to pull the smallest useful Sabueso implementation.

However, early design decisions should avoid assumptions such as:

    Card = flat database record
    Deck = list of Cards
    relationship = untraceable identifier
    source = string annotation
    resolved value = knowledge without underlying assertions
    missing value = evidence of absence
    derived result = new SourceAssertion

Instead, the initial implementation should preserve enough structure for future evolution toward:

    entities
        +
    SourceAssertions
        +
    relationships
        +
    provenance
        +
    reproducible derivations
        +
    composable scientific operations

without requiring Sabueso to implement a general knowledge graph, literature-understanding system, scientific query language, or autonomous agent today.

## Guiding ideas

> **Sabueso should not merely collect molecular knowledge into Cards and Decks. Cards and Decks should become composable scientific knowledge objects that can be related, compared, expanded, filtered, joined, ranked, and aggregated while preserving the SourceAssertions and provenance underlying every scientific result.**

> **Scientific literature should become a first-class Sabueso knowledge source: relevant statements from papers should be transformable into normalized, provenance-preserving SourceAssertions rather than remaining only unstructured text for retrieval.**

> **Sabueso should help MOLI answer not only what we know, but why we think we know it, where knowledge conflicts, and what remains unknown.**
