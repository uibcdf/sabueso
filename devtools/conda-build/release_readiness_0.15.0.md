# 0.15.0 delivery readiness

Owner: Sabueso maintainers, coordinated under #112; exploration acceptance under
#148 and real consumer usefulness under #132. This is a preparation worksheet.
Candidate selection, schema freeze, staging and public publication remain pending
their acceptance prerequisites and maintainer resumption.

The maintainer explicitly defers the independent/uncoached researcher trial until
after 0.15.0 publication. It is no longer a blocking prerequisite for this version;
its status remains `not_reviewed`, not accepted. The
[bounded decision](../../devguide/pending_proposals/researcher_acceptance_0150.md#post-0150-scheduling-decision--2026-11-12)
keeps the trial under #148/#112 and requires a release limitation and exact
candidate-bound record before publication. Other B7 dimensions and required
source/installed-platform gates remain unchanged; this is not B8 resumption.

The [bounded CI correction](../../devguide/pending_bugs/ci_serial_execution_timeout.md)
addresses an observed four-hour installed-lane timeout while preserving all
original selections. Its [local receiving](../../devguide/evidence/ci_bounded_execution_checkpoint_20261111.json)
is development-tool validation, not hosted recovery. The old `3c26790` batch has
failed/cancelled work and cannot qualify later code. The authorized `74308ba`
batch has verified governance but failed CI: twelve scratch stops, a macOS RAM
refusal before pytest and missing coverage input. A [local preflight correction](../../devguide/evidence/ci_preflight_capacity_checkpoint_20261112.json)
records capacity and bounded settling without relaxing limits. Under the later
bounded support exception below, exact-final-head Linux/Windows CI and all
applicable candidate/artifact prerequisites remain necessary; Mac recovery is
required for restoring its prospective support claim.

Subsequent source/installed jobs also stop at the fixed 6 GiB scratch ceiling,
with RAM above the reserve. The local
[original-reader correction](../../devguide/pending_bugs/ci_serial_execution_timeout.md#extracted-original-archives-outlive-their-modules--2026-11-12-utc)
releases five reproducible extracted tar copies after their final module use.
Debug retention, failed outputs, immutable originals, scientific assertions and
execution limits remain fixed. Its selected local checks cannot establish
complete hosted recovery or resume B8.

The completed run supplies a verified full capture and twelve byte-exact
source-bound codec reports, separately from its failed source/installed matrix.
A [single approved capacity observation](../../devguide/evidence/macos_capacity_observation_20261112.json)
now measures the macOS refusal: 2.929 GiB finally available against a 3.400 GiB
one-worker criterion. It starts no pytest and qualifies no platform/package.
The maintainer defers further Mac validation under
[#194](https://github.com/uibcdf/sabueso/issues/194) while a viable route is
identified. The subsequent [bounded support decision](../../devguide/pending_proposals/macos_support_exception.md)
selects Linux and Windows for prospective 0.15.0 support, reviewed before each
later release. macOS is outside the future supported scope until requalified.
Required source/staging matrices follow Linux/Windows × Python3.11–3.14; the
central registry patch is prepared separately for owner review. The earlier
published 0.14.0 platform receipts and actual Mac refusal remain unchanged.
Exact final-source CI/governance and all B7/candidate/artifact gates remain due.

## Required records

| Record | Current disposition |
| --- | --- |
| Functional scope | Use the [broad inventory](../../devguide/pending_proposals/card_exploration_completion_0150.md) and current CHECKPOINT. Close consequential integration gaps and record source-bound tests; older green receipts do not qualify later code. |
| Independent researcher | Explicitly deferred by the maintainer until after 0.15.0; not a blocking prerequisite for this version. Status remains `not_reviewed`; no participant result is claimed. Preserve the [participant section](../../docs/content/user/researcher_review.md), worksheet and public input preparer. Owner #148/#112; revisit scheduling after publication and explicitly reconsider this unmet gate before a later release decision. |
| Candidate-bound researcher deferral | At candidate preparation, record exact source SHA, version 0.15.0 and archive coordinates/digest, decision owner/date, this gate's unperformed status/reason, narrower technical/developer-agent evidence and limits, #148 follow-up and release-note limitation. Those candidate identities are pending; no later source/version receives an automatic exception. |
| Scientific, agent and consumer acceptance | Record each dimension and its exact inputs, results, limitations and reviewer/consumer. Technical scripts do not supply scientist decisions or real consumer usefulness. B2's explicitly deferred default review stays separate. |
| Representative workload | The [public-session receipt](../../devguide/evidence/public_session_workload_checkpoint_20261111.json) measures three walkthroughs and seven saved readings at `89bdb0a`. The [packing-cache checkpoint](../../devguide/evidence/exact_packing_cache_checkpoint_20261111.json) observes current structural saving at 56.076 versus 44.767 s in a fixed-input ABBA comparison, with eight original-reader controls. The maintainer accepts provisional targets of 60 s saving, 30 s reopening and 1 GiB RSS for that measured workload on this workstation. Actual independent task feedback, other useful-scale budgets and complete B7 workload acceptance remain pending under #167/#148. |
| Candidate source and release scope | Pending. Record the immutable commit, canonical version `0.15.0`, final release notes and release tracking issue. `release_plan.toml` still describes published 0.14.0. |
| Full source qualification | Development source `5ae3b1e` has [11,432 distinct local passing outcomes](../../devguide/evidence/packing_full_checkpoint_20261111.json) with matched discovery and an explicit one-function test-only correction; all production code and other 1,348 inputs remain unchanged. Final candidate qualification remains pending: every applicable exact-SHA CI/governance result must actually pass through gh-run-receptor, alongside required installed artifacts. Deferred `[skip ci]`, old-head, missing or skipped runs do not supply that result. |
| Dependencies and public fixtures | Run release dependency preflight and fixture delivery checks, then prove the actual installed public dependency closure. An editable workspace or static metadata check has its own narrower scope. |
| Schema 0.3.14 | Unpublished and not frozen. Generate its frozen public Card with a preliminary local Conda candidate installed in a clean environment, as the existing schema policy prescribes. Preserve 0.3.13 and earlier. Include the accepted freeze in the final source checkpoint before final staging qualification. |
| Staging archive | Pending. Record exact source, version/build, channel/label, filename, SHA-256 and producer run/receipt. A diagnostic local wheel is not this public Conda artifact. |
| Installed platform matrix | Pending for that exact archive. Require Linux and Windows, each on Python 3.11–3.14, with installed provenance, public dependency closure and copied public offline receiving outside source checkouts. Review and record #194's bounded macOS support exception before this and every later release; confirm its central registry disposition. macOS is outside the future claimed scope until an agreed route and actual source/installed qualification restore it. No omitted lane is relabeled as PASS. |
| Stable publication | Pending final acceptance. Check the visible release title, tag and package version are exactly `0.15.0`; promote the same tested archive and verify the public coordinate/digest plus a clean public installation. |
| Archive and coordination | Complete identical-tag Zenodo archival and the release-specific MOLI notice, recording exact public version/source/package coordinates/digest, verification limits and follow-up owners. Update the same notice for later package events. |

The preliminary local schema build is not uploaded. It supplies the frozen input
before the final immutable staging archive is built. A changed final source or
archive invalidates the affected exact-source/artifact qualification; do not
rebuild or overwrite a recorded public coordinate to hide a failed check.

## Handoff fields to fill at candidate preparation

```text
Release tracking issue:
Maintainer acceptance and resumption:
Scientific / researcher / actual-agent / workload / consumer results:
Independent researcher deferral: exact candidate, owner/date, not-reviewed status, limits, #148 follow-up:
Final source SHA and canonical version:
Schema-generation environment, source and frozen-input digest:
Exact-SHA CI and governance runs / gh-run-receptor receipts:
Release dependency and public-fixture checks:
Staging producer run and immutable archive coordinates / SHA-256:
Installed OS/Python matrix receipts:
Stable release URL / exact title and tag:
Public archive verification / clean-install receipt:
Zenodo record:
Central MOLI release notice:
Remaining limitations and follow-up owners:
Temporary-resource cleanup / retained evidence owner and review trigger:
```

Follow the [authoritative staged route](README.md) and
[schema policy](../../devguide/SCHEMA.md). This worksheet grants
no release or workflow-dispatch authority and records no completed candidate gate.
