---
summary: Present retained molecular representations, native identity context and property metadata.
issue: uibcdf/sabueso#148
status: in_progress
opened: 2026-11-10
area: [card-exploration, molecule, presentation]
---

# Original chemical context reading

`CardView.chemical_reading` provides detached current presentation under
`chemical_context_reading@1`. It is available on a small-molecule Card's actual
`chemistry` and `properties` field panels, including their saved originals, and
returns `None` on unrelated or scientific-result views. It creates no knowledge,
SourceAssertion or chemical calculation and changes no Card schema or scientific
payload. New sessions record an optional presentation-policy declaration; see
[historical presentation](card_orientation.md#historical-presentation-and-resaving).

## Identity and representation scope

The chemistry context retains canonical SMILES, connectivity SMILES and InChI
values, original representation labels, declared support and exact typed
value/source locations. Original `same_as` relationship support supplies only
the explicitly recognized source-native context:

- ChEMBL parent and active-record identifiers from `molecule_hierarchy`;
- CCD component name, SMILES representations and `pdbx_formal_charge`.

An assertion must match the relationship's exact subject, object and field scope.
Source-owned relationship-shaped values cannot establish that binding. Missing,
null, empty, malformed and mismatched records retain distinct states; all declared
support references keep their original order and duplicate occurrences.

The CCD formal charge number is a source-native integer declaration, not a
computed physical charge or PyUnitWizard quantity. Zero remains distinct from
missing. A dictionary default is never substituted for an absent captured value.
No stereochemical completeness, salt/parent identity or equivalent chemical form
is inferred from a representation, name or similarity. Each source's declaration
remains separately inspectable, including disagreements and unknown scope.

The identity context describes the original captured chemistry panel; a display
filter selects rows without changing those declarations. The property context
instead follows the currently selected property fields. `complete` reports
coverage of those presentation inputs, not complete scientific/source coverage.
Quality counts and locations describe the original Card's declared quality
collections; they do not attribute every conflict to a selected property.

## Property values and method attribution

Each property includes its complete original `field_record`, with value and unit
together, exact typed field location and original support. Source `method`,
`representation` and `determination` metadata remain literal source declarations.
A familiar method name does not establish measured or calculated origin. Missing
determination remains unknown; contradictory source declarations are not resolved.

Method attribution requires the SourceAssertion's `field_path` to match that
property. Declared support with another field scope remains inspectable as
`field_scope_mismatch`; its method is not attributed to the selected property.
The current human property preview follows the same restriction. Historical
default previews keep their recorded presentation; explicit `chemical_reading`
still exposes the current field-scoped reading of the original capture.

Text and HTML share a bounded preview of at most four context/support/property
entries. Long declarations defer attribution rather than accepting an unchecked
prefix. Explicit `chemical_reading` reads the complete retained scope and returns
a detached copy; changing it cannot mutate a Card or saved session.

## Current compact discovery

Current compact discovery also offers `chemical_identity` and `property_context`
under `molecule_literal_topics@1`. These are literal `read` descriptors over the
same detached capture, with exact routes to original names/identifiers, all
relationships, complete physicochemical fields, source assertions, selection
rules and quality. They are not scientific selectors and perform no method,
identity or coverage interpretation. Missing/null/empty/malformed shapes remain
distinct, with raw locations retained when available. This changes no Card or
scientific wire schema. Explicit current discovery is available on saved captures;
an original catalog's stored observation and resaving remain unchanged. The
pre-change SDK260 original and its separate-process reader are retained under
`recovered_work/checkpoint_recovery_20261106/b7-literal-molecule-topics-2/`.

## Public positive input and verification

The public RCSB GraphQL SO4 response retains the native integer `-2`, the exact
request, original wire bytes, decoded component and capture hashes under
`temp_data/pdb_ccd_charge/`. NOTICE and the fixture-delivery registry record its
CC0 terms and direct capture. This is not a fabricated Sabueso acquisition trace.
Older CCD responses without the field continue to report unknown charge.

The owning complete module is `test_card_chemical_reading_offline.py`: public
ChEMBL/CCD/PubChem context, original locations, detachment, value/unit preservation,
source binding, literal determination, field-scope mismatch, bounded rendering,
escaped HTML, fake semantic shapes and separate-process saved reading with
Card construction, fixtures and acquisition forbidden. The CCD query control
checks exact captured field selection and native charge retention.

CHECKPOINT owns current source/copied/diagnostic qualification. Technical controls
do not supply independent chemistry review, researcher acceptance, actual-consumer
receiving or the candidate's hosted/platform/public-package qualification.
