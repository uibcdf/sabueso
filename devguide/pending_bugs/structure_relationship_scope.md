---
summary: Bind structural explanations, exclusions and group support to exact retained relationships rather than repeated PDB labels.
issue: uibcdf/sabueso#168
status: resolved
opened: 2026-10-27
closed: 2026-10-28
verification: regression_tests_and_source_receipts
area: [scientific-integrity, human-exploration, agent-access, historical-reading]
---

# Exact structural explanation scope

The #148 structure-context tests at `9d5bd09` reproduced a native explanation
crash on two deliberately synthetic retained relationships sharing one public PDB
label: `(relationship,) = relationships` assumes a unique reference. Both records
are valid, separately identified inputs. Selecting the first would hide ambiguity.

The follow-up also reproduces reference-only support multiplication: a group with
two references and two matching relationships emits four support members. An
excluded fragment's PDB reference can also incorrectly exclude an admitted sibling
with the same label. The cases are synthetic variants of public test context, not
new source claims. No private/pilot material or source queries are involved.

## Named correction and support

`structure_inventory_explanation@2` binds the effective `relationship_id` alongside
original Card pins, structure reference and normalized inventory options.

- A PDB-only request with multiple retained relationships reports `ambiguous`,
  every exact candidate reference and each candidate's original relationship-level
  support. It chooses no item or group.
- A unique or explicitly selected relationship binds its exact original inventory
  row. Missing/wrong-structure ids return `not_on_card`, without another-record
  fallback. Malformed ids fail before inventory work, including skipped digestion.
- Exclusions bind original relationship ids and their actual fragment classes.
  An excluded sibling cannot exclude an admitted row with the same PDB label.
  Unknown sequence states retain their own original scope and reason.
- Group support follows original inventory row ids and state keys, including
  caller-selected coarse ligand state, substitution criteria and explicit reference
  maps. Each exact row appears once. Equal labels never join support across groups
  or Card revisions; supplied numbering maps keep their explicit basis.

The native inventory/classification rules, quantities and original source records
are unchanged. No new SourceAssertion, biological claim, coordinate projection,
Card schema, migration, provider, dependency or shared MOLI contract is introduced.

A separate audit observes a focal-subject admission gap in the unchanged native
inventory ([#169](https://github.com/uibcdf/sabueso/issues/169)): a foreign-subject
relationship stored on a Card can still appear as a focal row. This correction
does not redefine inventory admission. Correct that separately under a new named
native contract before broader structural/model/assembly integration.

`Deck.explain(..., relationship_id=None)` is the additive public selector, with its
own ArgDigest digester and early backend guards. Human items already carry their
exact row id. Human and compact agent selections use one captured native result
and original source/structure destinations; no reader reruns when following it.

## Original saved reading

The structural transport adapter remains `structure_exploration@1`: its inventory,
columns, quantity codec and typed support contract remain unchanged. A new
`context.explanation_rule` selects @2 explicitly and participates in result identity.
Unknown versions fail. Existing exploration formats retain this named policy;
older contexts without the selector use unchanged frozen @1 predicates.

`card_structure_history_v2` supplies retained-only native/coverage/support callbacks
to the frozen `structure_explanation_scope_v2` policy. Verification never constructs
a Card or invokes current science, source clients or fixture reads. It compares
all original result/metadata values, group/exclusion/source membership and effective
relationship ids before restoring the saved view. Resealed substitutions of another
valid row, another group's support, an exclusion id or an unsupported rule fail.

Original @1 code/capsules are not rewritten. The genuine original @2-format
scientific capsule keeps its original explanation @1 even when the new policy is
forbidden. Hashes verify internal consistency, not source authenticity or truth.

## Repeat machine-save root (#167)

The independent compact-reader test also observed that repeated saving of one
unchanged selection adds another transport root. Reuse only that exact selection
object's existing original machine root, with no origin/display request and the
same summary presentation. This preserves repeated artifact bytes without merging
scientific/source records or deleting history. Literal/scientific live and saved
selections have regression coverage; broader #167 size/speed/scaling budgets remain
open, with no new performance claim.

## Qualification and retained proof

`test_structure_relationship_scope_offline.py` covers direct/Deck explanation,
public selector/backend refusal, repeated equal labels with same/different states,
coarse and mapped substitution groups, cross-Card identical local ids, mixed
admitted/excluded/unknown declarations, exact human/agent/source parity,
independent inert reading, original @1 compatibility, semantic substitutions and
byte-stable repeated machine saves. Existing structural/support/argument tests use
new @2 expectations for new production; original historical expectations stay @1.

Run the full offline suite with `--local-source-inputs --receptor=llm` and fatal
runtime/SQLite/unraisable guards, with bounded workers under the current memory
constraint. Use an unskipped push and exact-head CI/governance through
`gh-run-receptor`, checking full captures, every applicable job and actual summaries.
The owning #168/#148/#112 issues hold source-bound local/remote receipts; earlier
green source checkpoints never qualify newer bytes automatically.

Owned proof: `recovered_work/structure_identity_168_20261028/`, owner #168/#148/#112,
review at the next structural or pre-0.15.0 checkpoint. Retain original inputs,
useful source/environment/resource/reader evidence and remove completed owned
scratch. The broad exploration inventory, actual researcher/workload acceptance
and 0.15.0 release consolidation remain separate work.


The full local-original offline checkpoint passes **7,577 cases /2,857.56s**,
with 26 online cases deselected and 13 declared fixture failure/truncation warnings.
It runs serially through pytest-receptor with fatal runtime/SQLite/unraisable
guards. All 13 changed Python source/test files precede that run and retain the
recorded byte hashes; four original @1 verifier modules match preceding source
exactly. The 34-case owning gate passes /20.72s and overlaps the full scope.

The successful full run peaks at **869 MiB sampled owned RSS**, at least
**2.4 GiB genuinely free /16.7 GiB available host RAM**, and **zero owned swap**.
Its limits are 1.25 GiB owned RSS, 1.5 GiB free, 12 GiB available and 16 MiB owned
swap. Two earlier full attempts stopped at more conservative global free-RAM
floors (4 GiB/two workers and 3 GiB/one worker); neither is qualification. Their
stop logs are retained and completed owned scratch is removed. The final limits
use both free and reclaimable memory while protecting other work; no cache flush,
swap reset or unrelated process termination is performed.

The two changed structure-guide blocks execute over unchanged public inputs and
an explicitly synthetic duplicate with a supplied user choice, without queries or
reader mutation. This is scripted technical verification, not uncoached usability.
Applicable static/link/snippet/Python 3.11, fixture, dependency and governance checks
pass; warning-fatal Sphinx and final editable-label/source/hosted checks have their
own receipts in #168/#148/#112. A local passing suite is not a remote result.

## Windows qualification correction

The first unskipped source `8eceb17` passes Linux/macOS and the four installed
provider lanes, but its Windows/Python 3.14 run reports four failed semantic-forgery
assertions (6,020 other cases pass). The test reads a UTF-8 artifact with the Windows
default encoding and then reseals altered Unicode metadata; production correctly
rejects metadata identity before the intended semantic check. A local cp1252
round-trip of the exact producer's synthetic original reproduces that diagnosis;
the UTF-8 round-trip verifies.

The follow-up changes only explicit UTF-8 reads/writes in the owning test and this
receipt. Its 34-case owning gate passes /20.13s before the final source label.
It does not broaden the expected rejection regex or change production verification.
The full 7,577-case local checkpoint remains evidence for identical runtime bytes;
it is not a claimed full rerun of this test-only follow-up. The failed hosted head
never recovers the deferred CI backlog. The corrected source needs fresh exact-head
CI/governance, with actual final source/SDK/receipts recorded in the owning issues.
