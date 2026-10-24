---
summary: Individual annotations, native UniProt scope and explicit structural questions with inert historical reading.
issue: uibcdf/sabueso#148
status: open
opened: 2026-10-24
closed:
verification: tested
area: [human-exploration, knowledge-integrity, source-access, schema]
blocked_by: []
supersedes: []
---

# Individual annotations and structural context

This bounded continuation of the [complete exploration design](card_exploration_completion_0150.md)
targets 0.15.0 under #112/#148. The source-mapping correction belongs to
[#160](https://github.com/uibcdf/sabueso/issues/160). It does not complete aggregate,
assembly, model-fragment, broad nature-profile or researcher acceptance work.

## Original source scope before structural navigation

The previous UniProt mapper preserved native inputs, molecule scope, uncertain
endpoints and sequence revisions only for recovered feature types. An explicit
synthetic active-site feature on another molecule with a `LESS_THAN` start instead
became an apparently exact canonical position. Unknown starts could disappear and
an unstated end could become the start. This is confirmed Sabueso input loss, not
a demonstrated provider defect or a claim about a live molecular record.

The [official UniProt manual](https://web.expasy.org/docs/userman.html)
distinguishes canonical/isoform locations, uncertain/unknown bounds and 1-based
numbering. Current mapping retains the complete original feature in
`source_metadata.uniprot_feature`, its stated sequence revision, native modifiers
and unknown endpoints for every mapped feature type. Other/unidentified molecule
scope stays unplaced. Native malformed shapes fail explicitly. Published source
assertions, schemas and original Cards are never rewritten.

Optional retention extends unpublished 0.3.14; the shape has 1,907 paths. Migration
reports missing native feature input on applicable old UniProt assertions and
does not backfill it. Refresh records a new basis while preserving original pins.
Missing sequence revisions remain unknown rather than a promise of agreement.

A separate explicit synthetic case confirms an unresolved input-identity limit
([#162](https://github.com/uibcdf/sabueso/issues/162)): two noncanonical features
with equal normalized values but different native molecules receive the same
assertion ID, so the Card store retains only the last native context. This is not
fixed here. Both remain unsupported by the canonical structural route; resolve
context preservation before claiming broad isoform exploration. Historical lost
associations cannot be recovered merely by reinterpreting the remaining record.

## Human route and exact support

`explorer.view("annotated_regions")` / `answer("annotated_regions")` presents one
original annotation per row. Select by feature type, original axis, start/end or
context state; open the complete original value. Unplaced records remain visible,
and missing, empty and malformed fields have separate retained gaps. Field keys
and list indices keep typed locations; similar descriptions do not merge items.

`annotation_item_support@1` matches each actual subject/field/value with exact JSON
types. A field's other annotation statements are not silently assigned to the
item. `explain()` opens exact original supporting statements with return navigation;
other/missing field references remain inspectable. Declared filter/sort capabilities
match the field panel's actual columns, including existing ligand-instance selectors.

The item's `related()` includes labeled original input sources and one explicit
structural question. `annotation_structure_request@1` binds its annotation, focal
identity, canonical sequence and length to actual retained source values and typed
locations. Native UniProt type/molecule/endpoints/modifiers must agree. Unknown
native scope, unsupported/compound axes, uncertain bounds, invalid positions,
foreign source subjects/records and relevant recorded conflicts cannot silently
produce a structural request. Stated sequence revisions must be consistent;
unstated inputs remain individually identified. Disulfide requests use only the
two endpoints, not the intervening interval.

Opening a ready question explicitly delegates to the existing `region_coverage`
reader. The structural result is shared with equivalent human and technical
`structures` requests; browsing the annotations or preparing links does not invoke
that reader. This does not establish atomic coordinate completeness or recommend
a structure. No acquisition, refresh, sequence alignment, pocket calculation,
biological relevance or identity-by-similarity occurs.

## Saved receiving and remaining scope

Only these new annotation links use `retained_context_links@3`. Historical @1/@2
source/destination memberships stay separately verified. Frozen v1 annotation
membership, support and request predicates verify original inputs; they never
replace a saved result with current science. A saved structural destination must
retain its original annotation question's positions/options. A followed result
reopens inertly; an unmaterialized structural question is `not_saved` rather than
an implicit computation. A blocked question preserves its recorded reason and
return path. No shared envelope or KnowledgePacket mapping changes are introduced.

The generic saved reader also checks each related-operation map against its
originating item's typed location (#161). An offline reproduction previously
accepted an internally resealed swap of two valid link collections. Each collection
had its own correct source basis, but the operation could return another item's
links. The fix binds that missing edge for old and new navigation versions; link
detail operations preserve their intentional empty, nonrecursive context. An
independent expected digest already rejects changed files and remains a separate
artifact pin; internal self-consistency is not source authenticity or truth.

The executable public [annotation journey](../../examples/user_journeys/annotation_structures.py)
is located in the repository's `examples/user_journeys/` directory. It prepares
current-source and historical-missing-context readings without source queries,
then reopens them independently. Technical script/HTML checks are distinct from
observed researcher usefulness. Full compact annotation-topic projection is still
pending; exact source nodes remain available through bounded literal machine
access, and target structural requests reuse the existing scientific adapter.

Source qualification, public examples and gate evidence are retained under
`recovered_work/annotation_regions_20261024/`, owned by #148/#160, review at the next
exploration checkpoint or release. Ninety-two new regressions cover the new source,
annotation, migration/refresh and saved-origin cases. The final selected scope
passes **1,264 cases / 157.77 seconds**, twelve receptor workers and fatal
runtime/SQLite/unraisable guards, with one explicit local-original skip and five
expected fixture warnings. The final committed-SDK full run passes **7,075 cases /
696.73 seconds**, thirteen expected fixture warnings and fatal SQLite/unraisable
guards. Source `17701d9` passes every Linux/macOS and Ackredit remote lane. Windows
finds two new tamper tests decoding the saved UTF-8 JSON with the platform default;
this changes retained text before the intended origin check. An explicit Windows
codepage reproduction confirms the cause. The corrected test uses UTF-8 for both
operations, matching production save/read; runtime/schema bytes are unchanged.
Final corrected-head remote qualification remains pending. Earlier failed attempts
are diagnostic and do not establish a green remote receipt.
Ruff format/lint (1,129 files), schema/shape alignment (1,907 paths), fixture delivery
(51 reviewed / 37 protected), registry, dependency preflight and local governance
pass. All 37 public guide blocks execute offline, syntax/links and Python 3.11
grammar pass, and Sphinx builds with warnings fatal. Three actual public panels
have technical visual inspection without clipping; labels/EXACT repetition and
the historical context's technical field names still merit human polish.
Full exploration and human acceptance remain
required before 0.15.0; candidate preparation/publication have not started.
