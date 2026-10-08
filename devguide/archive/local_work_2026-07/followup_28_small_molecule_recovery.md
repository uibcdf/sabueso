# Follow-up 28: small-molecule requirements and native ChEBI descriptions

Five preserved implementation files were compared with the current small-molecule
workflow on **2026-10-08**. The useful uncovered behavior is now recovered in the
existing ChEBI mapper: source-native names and formulas have their own supported
SourceAssertions. This is a local code checkpoint, not another provider adoption.

## Reviewed block

| Original file | Disposition and current replacement |
|---|---|
| `sabueso/tools/small_molecule.py` | The old unified constructor is superseded by `sabueso/tools/card/small_molecule.py`, `resolve_molecule_card`, current source options and molecule/ligand decks. Bare references and names never create chemical identity. Direct ChEBI input remains a distinct future admission requirement below. |
| `sabueso/tools/small_molecule_sources.py` | Source-specific online/fixture clients already replace the inherited generic HTTP client. Native formats, source terms, retrieval context and missing/failed/unqueried states remain separate. Old guessed/legacy URLs are not restored. |
| `sabueso/mappings/small_molecule_context.py` | Recover the native ChEBI name/formula into `sabueso/mappings/chebi.py`. Current CCD/PubChem/UniChem/ChEBI identity, descriptions, roles/classes and ClinicalTrials mappings supersede the remaining implemented paths. Retain extra chemical descriptors and patent occurrence requirements below. |
| `tests/tools/test_small_molecule_context_offline.py` | Replace obsolete Evidence/card-schema expectations with 26 regression cases for seven unchanged native ChEBI entries, independent support, malformed versus unstated fields, identity gating and explicit formula conflicts. Current molecule identity, ligand deck, clinical, journey and persistence tests cover the supported workflows. |
| `sabueso/core/merge.py` | Current merge plus FieldResolver/aggregation retains all source assertions and explicit conflicts. Do not restore generic list-key identity guesses or fill one source's object with another source's values. The new conflict regression exercises the current selection contract. |

The old test's synthetic chemical inputs disagree on structure keys. A common name
or formula is not an accepted join. Its intervention substring check, invented row
IDs and automatic curated/Evidence classes are not recoverable scientific behavior.
The original patent test describes an authorized connector's desired behavior; its
fabricated record is not qualification of a current provider route or data licence.

## Recovered behavior

For a native ChEBI entry with its own standard InChIKey, the existing mapper now
emits `names.canonical_name` and `properties.physchem.formula` from `name` and
`chemical_data.formula`. Original spelling, source/record/subject, retrieval time
and curation metadata remain literal. Each field has independent assertion support.
The source record's `modified_on` and stars do not become scientific release or
project Evidence. Input is unchanged; no empty assertions or name/formula identity
inference is introduced. Invalid descriptive types and a foreign chemical-data
shape raise ConnectorError rather than appearing as absent data.

Existing optional `resolve_molecule_card(..., chebi=True)` admission still requires
the source-stated InChIKey to agree with the card anchor. Different source formulas
remain separate assertions, with resolver-selected support and explicit conflict
support. There is no schema/shape/physical-unit change, new acquisition route,
fixture, source grant or new mandatory source option.

The frozen public file `temp_data/chebi/compounds.json` was already retained by the
current client and declared in `temp_data/NOTICE.md`; all seven entries are replayed.
It is the client's saved native entry selection, not a newly captured complete wire
response. Primary [ChEBI tools](https://www.ebi.ac.uk/chebi/tools) describe the current
REST/JSON access; [ChEBI downloads](https://www.ebi.ac.uk/chebi/downloads) distinguish
chemical data and additional structure/identity data. Public documentation checks
are separate from scientific acquisition; this recovery makes no dataset request.

## Requirements retained independently of the stash

These residual requirements are tracked in the owning
[#83](https://github.com/uibcdf/sabueso/issues/83) source review and broader
[#112](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6057351190) implementation review. This table
is sufficient to re-evaluate them without importing the historical implementation.

| Requirement | Acceptance needed before additional integration |
|---|---|
| Direct source-ID admission for a ChEBI entry | An accepted public input contract, ArgDigest validation, exact source-reported standard structure identity and failure/absence/unsupported distinctions; reuse existing source terms and preserve identity support. Current optional linked ChEBI enrichment does not establish this new public route. |
| ChEBI secondary identifiers, synonyms and cross-references | Read source-specific, qualified native structures and identity basis. The saved entries supply secondary IDs but no native synonym/cross-reference collection. Keep source alias declarations distinct from chemical identity; do not synthesize native fields or revive the old dict-shaped schema. |
| Charge, average mass and monoisotopic mass, including CCD metadata | Preserve zero charge, original precision and source scope. Establish exact quantity kind/unit from source documentation or qualified native metadata before mapping mass; use PyUnitWizard quantity nodes and a reviewed additive unpublished schema where needed. Average and monoisotopic mass are separate. Native CCD release/type/atom/bond/nonstandard descriptors need independently qualified formats and support. |
| Patent document occurrences and sections | Retain document ID, source-supported chemical link, native section/locator, publication date, family/authority and original support when actually supplied. A text-mined mention is neither a claim, legal conclusion nor chemical identity. SureChEMBL stays deferred under its existing registry conditions until the bounded document/filter/bulk requirement and authorized original input are qualified. |
| Clinical named interventions and replay | Keep explicitly named intervention observations separate from structure identity, drugs, products and trial outcomes. Additional acceptance should cover native exact match basis, conflicting names, missing/failed/unqueried states, true source update dates and saved-card/deck round trips; never adopt the legacy substring join or fabricated NCT IDs. Current clinical API already implements its own supported route. |

## Remaining recovery assessment

This closes the individual review of these five originals; it does not declare all
87 preserved files disposable. Other assessment areas still include generic card
input configuration, specialist native metadata/support, source-sequence/residue
views and persistence, report/notebook reproducibility and consumer projection
requirements. Their existing recoveries and current implementations must be checked
for residual gaps. Provider conditions remain independently documented in
[the reactivation matrix](../../pending_proposals/historical_provider_reactivation.md).
Notify the maintainer when all useful remaining behavior is integrated, superseded,
or explicitly retained with its re-evaluation conditions. Stash deletion is the
maintainer's subsequent decision; no deletion is performed here.

## Validation

Focused ChEBI/identity/conflict gate: **33 passed in 3.25 seconds**.
Full offline code checkpoint: **5472 passed in 155.74 seconds**, pytest-receptor
with **12 workers** in the existing editable Python **3.14.7** environment,
10 expected fixture failure/truncation warnings. The initial broader targeted run
had 81 passes and one incorrect new assertion: selected-value support was expected
to include an alternate conflicting value. The test was corrected to check selected
support and retained conflict/store support separately; runtime selection was not
changed. The focused and complete gates then passed.

Outside-checkout replay verifies the editable import/metadata, seven native records,
14 independently supported descriptions and unchanged 21988-byte ChEBI fixture
SHA-256 `a18aef085c243fa0f95e9df27de345c3e5e19524e41de8d2b42f814d8cae82bd`.
No scientific source requests occur. Receipt: `/tmp/sabueso-followup28-native.json`.

Ruff lint/format (**935 files**), generated registry, strict Sphinx HTML,
shape/schema and diff gates pass. Strict docs: `/tmp/sabueso-followup28-docs-build`.
Integrity checks 87 original byte lengths/SHA-256 hashes, 91 accounted paths,
unchanged stash/index, published frozen card and previous scientific fixtures.
Receipts: `/tmp/sabueso-followup28-integrity.json` and
`/tmp/sabueso-followup28-gates.json`. The public source-coverage requirement is
recorded in [issue #83](https://github.com/uibcdf/sabueso/issues/83#issuecomment-6057338702);
local recovery details remain in this report.


The original stash and 87 exports remain intact, all 91 original paths are
accounted, and the index is empty. No commit/push, remote CI, separate environment,
published card/schema mutation or stash deletion. Broader recovery remains open.
