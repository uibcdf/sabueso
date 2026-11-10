---
summary: Captured protein comparative relationships, biological associations and explicit equal-position sequence comparisons.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-09
verification: inspected
area: [public-api, human-exploration, scientific-views]
blocked_by: []
---

# Protein comparative and association exploration

The LIVE `protein_context_exploration@1` profile implements two protein topics:
`comparative_context` and `associations`. Human panels and typed compact-agent
selection share one cached result for each captured focal/input/options context.
The Card schema, source mappings and earlier saved interpretations keep their
existing meanings. No new source is queried or adopted.

## Scientific tasks and row grains

- `related_proteins`: inspect retained `ortholog_of` and `clustered_with` records,
  then choose an explicitly supplied protein capture for a separate comparison.
- `protein_associations`: inspect retained `associated_with`, `participates_in`,
  `interacts_with` and `functionally_associated_with` records. Each stored
  Relationship remains one row with its original subject/predicate/object,
  source channel, qualifiers, conflicts and recorded derivations.
- `sequence_differences`: compare the selected sequences of the focal protein and
  one explicitly supplied capture under existing `equal_length_positions@1`.
  `options={"other_ref": explorer.context["inputs"][1]}` chooses the exact capture;
  a bare accession, unknown capture or non-protein comparator is refused.

Comparative browsing also lists each explicit supplied protein input occurrence.
These rows state the caller's input scope, never a source relationship. Repeated
input occurrences stay separate even when the underlying capture is the same.
A relationship identifier cannot collide with an input-occurrence row key.

Sequence comparison retains the unchanged native result in one pair-level row.
Its difference count and equality flag remain typed integers/booleans or null.
The human table shows both outcomes directly; unavailable comparisons show their
original native basis instead of a numeric count or equality claim.
Equal integer positions do not establish residue correspondence or entity identity.
Different lengths and unstated sequences retain the native unavailable basis;
malformed sequence values are shown as an explicit gap before the native engine.
General knowledge differences and supplied residue-map comparisons remain a
separate B6 increment. No alignment or position transfer is performed here.

## Support and navigation

`protein_context_projection@1` records the projection. Relationship support names
its recorded SourceAssertion references, expected subject/field, retained/missing/
mismatched binding, qualifier conflicts and original derivation applications.
`retained_references` means those references have the expected recorded binding;
it does not independently validate a provider's mapping or scientific claim.
Original values and all support records remain inspectable. Derived relationships
remain labelled as recorded derivations and never become SourceAssertions.

Sequence support binds each selected field to its exact retained SourceAssertions;
a missing or changed value on either side keeps support partial. Its separate
`captured_sequence_comparison@1` record binds the captured inputs. Source metadata,
original fields and whole Cards remain available through exact captured locations.

Human `open()`, `explain()` and `related()` preserve complete original records,
questions and actual back edges. Exact relationship object identifiers can open
supplied Cards; multiple supplied revisions remain ambiguous. A source or object
without an available capture keeps its unavailable context and back route.
`protein_context_links@1` exposes an explicit sequence question for a supplied
comparator; only following that question performs the comparison.

`protein_context_selection@1` provides typed equality, exact item membership,
stable missing-last scalar sorting, bounded pages and atomic value/support/meaning
deferral. Human filters and compact requests preserve the underlying result and
all original support. Null, zero, false and malformed original values remain distinct.
The RelationshipStore merge also preserves recursively typed qualifier alternatives:
integer zero, boolean false and floating zero are different raw values. It keeps the
first selected qualifier and lists distinct alternatives in `qualifier_conflicts`;
relationship identifiers and source references keep their original meaning.

## Original saving boundary and qualification

New context results, their dependent routes and observed sessions advertise saving
as unavailable until a clean producer original and an independent frozen reader
qualify them. Refusal occurs before writing a file. Captured Card export and a
fresh unrelated literal exploration remain available. Earlier saved formats and
all genuine SDK234/SDK230 originals remain fixed.

Run the complete owning module, applicable access/agent/context/nature/source/
comparative/quantity/transport/fixture gates, and original saved regressions. Copy
the complete module and exact public inputs outside checkout; verify controller,
worker and editable-import placement. Both installed routes select the whole module.
CHECKPOINT owns actual passing counts, source epochs and acceptance limits.

Next capture all actual human/agent/source/question/access operations on a clean
qualified producer before implementing independent saved reading. Include public
UniProt/IntAct, UniRef and OMA journeys and public TcTIM/strain sequence comparison,
plus labelled synthetic missing/conflicting/foreign support, recorded derivations,
repeated inputs, ambiguous revisions, malformed values, equal/different lengths,
atomic deferral, source-owned lookalikes and separate human-only/machine-only scope.
B7 scientific, uncoached researcher/agent, workload and actual-consumer acceptance
remains separate; this bounded LIVE increment does not close B6 or authorize B8.
