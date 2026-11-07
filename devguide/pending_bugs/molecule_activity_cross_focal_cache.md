---
summary: Scope each native ligand crossing cache entry to the exact focal molecule capture.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-07
closed:
verification: reproduced
area: [exploration, molecule-identity, caching]
blocked_by: []
supersedes: []
---

# Native ligand crossing cache across focal captures

The public cross-Card route at `4859afb` / SDK207 can retain the correct current
molecule explorer while exposing a previously cached native crossing for another
molecule. Full public TcTIM/BTS/benznidazole inputs retain all 493 target records.
No source/provider defect or private pilot data is involved.

Start from BTS with target and benznidazole explicitly supplied, open its native
crossing, cross to the target, ask `measured_molecules`, inspect benznidazole's
original source relationship, follow its declared object to the supplied molecule,
then ask `measured_targets` and open its native crossing. The explorer now names
benznidazole, but `native_payload.molecule_ref` and the complete payload still name
BTS. Reversing the two public compounds reproduces the converse error. Standalone
`Card.explain_ligand` provides the correct native oracle.

A third explicitly synthetic control changes only molecule snapshot metadata.
Both captures keep the same Card ID and original source statements; the explicit
candidate choice selects the second pin. The native payload can legitimately
match, but its retained wrapper still names the first `molecule_card_ref`.
A bare Card ID in the cache key is therefore insufficient.

The current key retains target, all input occurrences and scientific policies.
Explicit focal navigation preserves those inputs and shares scientific caches;
the active molecule must be part of that key. The correction adds the exact
focal capture key. It changes no scientific rule, source assertion, native
classification/grouping/target policy or quantity. The separate #192 flag
aggregation remains unchanged.

Three permanent regressions use public source-relationship navigation rather
than interpreting arbitrary source strings as join instructions. They verify
both molecule orders, exact snapshot selection, full native oracles, repeat
visits, original back/focal context, unchanged inputs and one target-bioactivity
evaluation. Both full-input probes and the two-/three-case red gates remain under
`recovered_work/checkpoint_recovery_20261106/b5-molecule-cross-focal-*`.
The first probe used a generic scalar with no declared reference; its lack of
links was a probe error, not another product defect.

All three controls fail before the correction and pass after it. The full
54-case LIVE cohort, 36 private original cases, 291 shared regressions, 383
native/profile cases and one isolated copied-consumer gate pass in the
[765-case selected checkpoint](../evidence/molecule_activity_cross_focal_checkpoint_20261107.json).
The copied child receives all 54 cases and adds no distinct coverage. Receptor
integrity, exact node/source accounting and resource limits pass; the two expected
offline UniChem warnings are retained and owned swap stays zero.
Before new saved-format admission, qualify the corrected clean producer and
capture supplemental genuine multi-focal routes. Preserve every byte of the
existing SDK205 original and formats @1–@20. The initial 99-wire original has
one focal molecule per case and does not exercise this shared-cache transition.

The corrected clean `142618d` / SDK208 producer passes the 54 LIVE and 36 private
original cases again on its exact committed runtime. Its
[genuine supplement](../evidence/molecule_activity_multifocal_original_20261107.json)
now preserves all three multi-focal routes, 176 human views, 24 machine
requests/pages, full source/publication context and both crossing wrapper pins.
It follows the private kernel and precedes full new saved admission. The SDK205
original remains byte-identical; this capture is not saved-reader acceptance.

Owning report material is prepared as `b5-cross-focal-issue148-draft-1.md` in the
local recovery tree. Concrete publication permission is requested separately;
earlier report approvals do not cover this material. Retain the full reproduction,
source maps and receptor/resource logs under #148/#112 until corrected producer,
supplemental-original and independent saved-reader review.
