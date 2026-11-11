---
summary: Preserve observed finite scientific requests when a human view is the saved root.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-10
area: [persistence, scientific-requests, agent-access]
---

# Scientific machine requests under a human saved root

The [reported public limitation](https://github.com/uibcdf/sabueso/issues/148#issuecomment-6782871860)
is reproduced on unchanged `2d7dffc` / SDK249. The combined 1SUX producer succeeds
when its human assembly destination is the root, but independent reading cannot
recover the original three-column assembly request. The original finite-agent-root
workaround retains that request and remains a valid bounded historical control.

## Cause and current correction

Scientific selections are recorded in the actual `CardAccess` selection registries.
Human saving previously retained human views and newer profile-specific agent
views, but did not wrap otherwise unrepresented scientific projections. Selecting
the same original scientific result with another column order or query is a
separate finite request; having the full human panel does not retain it.

The current common writer retains only supported scientific requests already executed in accesses
represented by the observed session. A `(actual access instance, selection_ref)`
key prevents equal requests in distinct accesses from being silently coalesced.
Existing profile-specific preparation runs first. The common fallback wraps only
requests it leaves uncovered, preserving the established transport of already
supported clinical, disease, literature and other profiles.
Existing human selections already cover their own exact projection; no query,
native calculation, Card construction or source acquisition is added by saving.

Newly retained machine views use the existing logical @35 / shared @36 transport
and its actual-access-origin manifest. An owned scientific machine-selection record
provides the explicit admission witness; source-owned JSON with matching field
names does not. The shared header includes one bounded witness, while complete
logical views and original native results still receive full verification.
Verified @35 resaves retain that format and their origin bindings. Earlier format
verifiers, native scientific rules, defaults, stored shapes and originals remain
unchanged; no new scientific interpretation is introduced.

A source-navigation destination's explorer is its own actual access, rather than
the initial explorer. The combined example now saves the human assembly view and
uses public `back()` navigation to return to the initial retained task context
before replaying it. It does not invent an unobserved machine request in the
destination's access. The earlier finite-agent-root example still starts at its
own original access.

## Verification and limits

`test_card_assembly_machine_retention_offline.py` covers both original assembly
adapters, human question/detail/filter/source roots, exact column order, distinct
actual accesses, complete agent values/support resolved to their typed original
addresses, a finite filter/order request, forced @36 packing, resaving, unexecuted
`not_saved` scope, resealed projection/machine/source-boundary refusals and genuine
historical @5/@6 reading. Session-local lookup tokens may change; their exact
resolved captured/result addresses and values must agree.

The complete combined structural review supplies the public annotation/region,
chain gaps/numbering, every original contact collection, source/back and twelve
assembly-position control. Its independent reader forbids current science,
Card construction, fixture reads, acquisition and MolSysMT. The 27 owning cases
pass the corrected common-source run. They also cover public and empty structures,
sites and quaternary requests from human and explicit machine roots. The latter
exposed an existing empty-wrapper defect: sites/quaternary wrappers defaulted to
ready instead of retaining their native status and reason. Both now retain the
original outcome. Broader source/copied/diagnostic qualification is
recorded in CHECKPOINT when complete. Earlier setup, address-comparison and header
calibrations remain separate failed observations, not passing qualification.
The first broad current-source run also caught an unintended format upgrade when
the fallback ran before profile-specific preparation. That owned run was stopped,
retained as failed/incomplete and the ordering corrected before requalification.

The consistency verifier does not authenticate an arbitrarily resealed history
without an independent expected digest. A selection-access rebinding alone is not
an established defect: replay can legitimately present an already retained
selection through another explorer. The refusal control instead changes the
actual source-follow boundary prescribed by the retained parent navigation.

This correction does not establish arbitrary-query replay, scientific usefulness,
uncoached researcher acceptance or an installed/hosted release gate. The finite
1TCD MolSysMT integration scope is unchanged. B2 remains deferred; B7 actual
acceptance and B8 authorization/delivery retain their dependencies.
