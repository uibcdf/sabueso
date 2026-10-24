---
summary: Original AlphaFold checksum, identity and sequence-range context with conservative coverage.
issue: uibcdf/sabueso#148
status: open
opened: 2026-10-24
closed:
verification: tested
area: [knowledge-integrity, predicted-structures, human-exploration, schema]
blocked_by: []
supersedes: []
---

# Original AlphaFold sequence context

This continues the [broad exploration plan](card_exploration_completion_0150.md),
after [distinct derivation applications](relationship_derivation_applications.md).
It supplies model/sequence input integrity and readable original support, not
complete model/region/assembly integration or researcher acceptance.

## Source contract and reproduced limits

The [official prediction API schema](https://alphafold.ebi.ac.uk/api/openapi.json),
`NewEntrySummary.sequenceChecksum`, declares MD5. Its schema document was retained
on 2026-10-24 with exact bytes/hash; API schema version is not a database release.
The older [BigQuery contract](https://github.com/google-deepmind/alphafold/blob/main/afdb/README.md)
uses CRC64 for the same column name. They are not interchangeable. No new molecular
queries were used to verify the documentation or implement the correction.

The previous mapper labeled every unequal accession an isoform. Explicit synthetic
input confirms that unrelated accession names alone produce that label, without a
source-stated isoform relationship. The prior native projection also divides model
range by current Card length regardless of a false/unknown checksum comparison.
These are Sabueso interpretation defects, not demonstrated provider defects.
AST comparison confirms both reproduced functions are identical in published tag
`0.14.0` and `40eb9c2`. The published-version impact is therefore confirmed at
source level; a narrow patch/backport delivery should be evaluated under #112,
separately from the paused 0.15.0 consolidation and mandatory artifact gates.

## Original mapping inputs

`alphafold_sequence_context@1` retains source model identity, original focal
accession, exact MD5 argument, original UniProt checksum/length/isoform assertion
references, original model range and unknown reasons. The original model stays
unchanged in its AlphaFold SourceAssertion. Derived `isoform`, `sequence_matches`
and `sequence_context` belong only to scoped relationship qualifiers/derivation,
with `#156` application/output binding. No derived finding becomes a SourceAssertion.

Only exact declared focal identity permits focal sequence interpretation. Isoforms
require UniProt's explicit isoform declaration, including alternative stated IDs;
neither suffix, name, shared sequence nor unequal accession establishes membership.
Other/unstated identity stays explicit. MD5 hex case is normalized for comparison;
invalid, missing or competing inputs remain unknown, never silently first-selected.
Standalone supplied arguments retain their argument basis without fabricated source
support or computed whole-reference coverage.

Native `predicted_structure_scope@1` checks stored applications and replays the
actual original source assertions/argument. Current selected Card sequence fields
never substitute for them. Whole-reference coverage is computed only for a valid
whole range/length and supported matching focal checksum. The fraction describes
the source-declared span of the **original input sequence**, not observed atoms,
alignment, experimental equivalence or current-field coverage. Partial model
checksums are not interpreted as whole-sequence mismatch: fragment coverage remains
uncomputed in this slice. Several recorded contexts remain alternatives: this
slice neither silently chooses the first execution nor declares their scientific
agreement. A missing selected binding is a migration gap; retained alternatives
with a valid selected binding are not falsely called missing history.
`coverage_scope`, `context_state`, detailed original
context and separately preserved historical flags make the limit inspectable.

## Human, saved and packet receiving

The source pane shows readable identity/context/rule/coverage and bounded reasons.
Its direct input links distinguish reference checksums, reference length, isoform
declarations and model metadata. Each opens the exact retained source node with
return navigation. These are original mapping records; the pane does not rerun
science or attribute a derived flag to AlphaFold itself.

`retained_context_links@2` adds those declared input destinations. Original `@1`
membership remains separately verified; its saved link decisions/wording are never
replaced with current destinations. New saved model reading remains inert, without
Card construction, relationship merging, live context rules or source access.

`packet_aspects@9` declares the model context/scope rules and retains actual model
and UniProt input support in full/index terms. Query/envelope formats and acquisition
areas/options remain unchanged. `@6`/`@7`/`@8` use the exact prior predicted projection
frozen from `40eb9c2`; their original full facts/index rules/terms do not substitute
the new model reader. Existing ligand-site and disease historical adapters remain
as before. Cross-mapping equivalence remains indeterminate. Coordinate producer
qualification through MOLI #36 without redefining architecture/shared envelopes.

## Schema, migration and qualification

Optional context/derivation accumulates in unpublished 0.3.14, with recorded shape
and `SCHEMA_CHANGES`. Migration identifies missing/invalid original model basis by
reading retained inputs only; it never creates the lost execution. Refresh records
new bases while preserving original stored pins. Published schemas/cards, source
assertions and saved capsules remain unchanged.

All **6,983 local-original offline cases / 641.77 seconds** pass with twelve
pytest-receptor workers, thirteen expected fixture warnings and fatal SQLite/
unraisable guards. Forty-two new regressions cover original inputs, absent/invalid/
conflicting checksums, identity, whole/partial ranges, competing contexts, direct
input navigation, frozen packet projections, original saved reading and refresh.
The final core subset passes **119 cases / 8.70 seconds** with the same receptor/
workers plus fatal RuntimeWarning guards. Earlier 344-case integration checks
precede the last narrow context guard; their count is not transferred.

Ruff format/lint, schema/shape alignment (1,878 paths), source registry, fixture
delivery (51 reviewed / 37 protected), dependency routing, local governance,
374 Markdown targets/anchors, 44 snippet syntax checks / 24 changed Python files
parsed under 3.11 and warning-fatal Sphinx pass. Three actual public/synthetic HTML
panels have technical visual review: values/input labels/unknowns are visible,
while the summary is still dense and its literal isoform placeholder can be
ambiguous beside a known focal context. Compact/grouped presentation and researcher
review remain open under #148; this is not human acceptance.

Exact-head remote qualification remains pending publication. Exact code, schema,
gates, public examples and
environment/remote receipts are owned by #148 in
`recovered_work/alphafold_context_20261024/`, review at the next exploration checkpoint
or release. Owned disposable scratch is removed after use; useful original saved
artifacts and caller/shared resources stay protected. Earlier failed selected
attempts are diagnostic, not passing qualification.

Broader fragment comparison, region/annotation/aggregate/assembly integration,
compact scientific agent selection and measured researcher usefulness remain open.
Legacy conflict quantities (#157) and generic qualifier JSON-type equivalence
(#158) remain separately tracked. Full broad design/human experience is required
before 0.15.0; release consolidation stays paused. This is source-level work, not
installed-release qualification or private consumer acceptance.
