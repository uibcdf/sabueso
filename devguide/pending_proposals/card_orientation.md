---
summary: Present curated original overview fields with exact value/support/version locations.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-10
area: [human-exploration, presentation, acceptance]
---

# Original Card orientation

`explorer.overview().orientation` provides a detached current presentation over
the captured protein, small-molecule or disease Card. `card_orientation@1` names
the presentation policy. It creates no SourceAssertion or scientific finding,
does not execute native readers and changes no Card schema or scientific payload.

The curated fields reuse existing profile paths: protein name, organism, accession,
sequence length, function and catalytic statements; molecule name, InChIKey,
formula, SMILES and InChI; disease term, MONDO identifier, definition, scoped
synonyms and retained term status. `fields_complete` covers this declared curated
set, not all retained Card content or all knowledge about the entity. Other
content remains reachable through `full_content_location` and ordinary inspection.
Unknown natures and non-overview views return `None`.

```python
opening = card.explore().overview()  # card is an already loaded capture
context = opening.orientation
for field in context["fields"]:
    print(field["label"], field["state"], field["value"])
    if field["value_location"] is not None:
        original = opening.explorer.inspect(locator=field["value_location"])
        print(original.native_payload)
    for source in field["support"]["sources"]:
        if source["location"] is not None:
            print(opening.explorer.inspect(locator=source["location"]).native_payload)
```

Each row retains the exact original field/value location, selected value and
support declaration. Missing paths, unrecognized fields/parent containers,
retained null, retained empty and ordinary values (including `False` and zero)
stay distinct. A malformed parent has its own inspectable container location.
The root address uses the exact captured pin/snapshot with typed empty segments;
it does not depend on a session-local lookup handle.

Declared support references keep their original order and duplicate occurrences.
A source entry exposes its original record location and complete retained source
descriptor, including version when present. Missing records, unrecognized
reference declarations and a deliberately empty reference list remain distinct.
Matching a reference does not independently validate that source's claim or
establish that all declared support is scientifically consistent. No alternative
is silently selected. Stored conflict/alternative declarations retain exact
locations and counts only for recognized lists; null and malformed scope are not
reported as zero conflicts.

## Bounded opening and independent reading

Text and HTML use the same policy, with source versions beside retained values.
The preview reads at most four declared support references per field and copies
no complete field body. If a longer reference list cannot be wholly checked
within that limit, attribution is explicitly `not_evaluated` in the preview.
It does not attribute a valid-looking prefix while a malformed tail could invalidate
the whole declaration. Explicit `orientation` retains the complete detached data.
HTML escapes original labels, values and source descriptors. No drawing,
descriptor calculation, new alignment or identity inference is introduced.

The current presentation can also read supported original saved overviews.
Historical values, versions, catalogs, selections and scientific predicates stay
fixed; this does not add an operation to an old file. Field/source addresses use
the same original capture and existing typed inspection/agent protocol. There is
no new agent wire. Source/support labels remain presentation, separate from
Knowledge state and project Evidence.

## Historical presentation and resaving

Integration exposed current orientation replacing original default openings in
the genuine SDK239 protein-context and SDK243 knowledge-comparison controls,
as well as earlier variant and sequence-change histories.
The correction preserves those observed text/HTML results rather than updating
their immutable expectations to match a newer renderer.

New sessions explicitly record `overview_orientation: card_orientation@1` and
`chemical_context: chemical_context_reading@1` in optional
`presentation_metadata`, alongside the existing navigation policy. These keys
select default text/HTML presentation; they are not source assertions or new
scientific adapter declarations. Unknown explicit values for either owned key
are refused rather than silently interpreted as a current policy.

An older file without these declarations keeps its historical default opening
and chemical/property preview. The two exact unmarked orientation producers,
`0.14.0+248.gca4f88e` and `0.14.0+249.g2d7dffc`, keep their already introduced
orientation but do not acquire the later chemical supplement. No broader
producer-version range is assumed. Restoration makes missing policies explicit
as `legacy_card_orientation@1` and `legacy_chemical_context@1` before a resave can
replace the producer label. Saving again therefore preserves that choice.

Explicit `.orientation` and `.chemical_reading` expose current detached readings
of supported original captures regardless of their default display. `start_new()`
opens a new live session under current presentation policies. Neither operation
rewrites the old file or supplies an unobserved scientific request.

The compatibility gate includes the genuine SDK239/SDK243 text/HTML comparisons,
legacy resaving, the unmarked orientation producer and resealed unknown-policy
refusals. Original capsules, values, support, scientific predicates and SOURCE
resources remain unchanged. This optional metadata addition does not introduce
a new Card schema or exploration transport version.

## Acceptance and ownership

The owning regression module is `tests/core/test_card_orientation_offline.py`.
It checks public protein/molecule/disease captures, literal-state distinctions,
source-version alternatives, duplicate/missing/unrecognized support, bounded
long-field previews, escaped HTML and independent inert saved reading. Exact
qualification belongs to [CHECKPOINT](../CHECKPOINT.md), with copied receiving,
package resource checks and hosted/installed limits recorded separately.

Ask independent participants to identify each supplied entity, explain the scope
of one opening value, find its original versioned source, distinguish a retained
unknown from absent knowledge and recover the same source after saved reading.
Record familiarity, assistance, original inputs/checkpoint, interpretation and
friction. Passing technical controls does not establish uncoached researcher,
scientist, actual agent/workload or consumer acceptance. Broader source/profile
integration remains in the [0.15.0 inventory](card_exploration_completion_0150.md).
Owners are #148/#112; B2 review stays deferred and B8/release stays unresumed.
