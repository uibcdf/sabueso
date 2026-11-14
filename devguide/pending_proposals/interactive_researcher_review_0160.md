---
summary: Prepared public researcher tasks and worksheet for actual 0.16.0 interactive acceptance.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-13
verification: acceptance_material_prepared
area: [human-exploration, acceptance, standalone]
---

# Interactive 0.16.0 researcher review

Status: **prepared, not reviewed**. No maintainer or independent researcher
observation is inferred from automated Qt receiving. The independent 0.15.0
deferral does not waive this 0.16.0 task. #154 owns usability and #153 owns Deck
semantics; the [implementation plan](interactive_implementation_0160.md) owns S6.

## Maintainer preparation

Use the current editable Python 3.14 development environment with the received
optional Qt/aiohttp cohort. This is a checkout workflow, not a public GUI install.
Prepare only the existing declared public fixture responses:

```bash
python devtools/prepare_explorer_walkthrough.py --output-directory /tmp/sabueso-review-inputs
python -m sabueso.explorer --deck /tmp/sabueso-review-inputs/public-mixed-deck.jsonl --output-directory /tmp/sabueso-review-readings
```

Choose new owned paths; do not reuse or overwrite another session's directories.
Record source SHA, dependency cohort, screen/input accessibility needs and the
prepared `inputs.json`. No network is needed for these supplied Card/Deck tasks.
Molecular tasks require a separately supplied public model and the experimental
provider cohort; keep their unestablished correspondence visible. Do not present
the experimental panel as mapped annotation navigation.

## Tasks without coaching

| Task | Observe, without supplying the answer |
| --- | --- |
| Orient in the Deck | Can the participant explain the repeated protein occurrence, original membership and the selected versus complete Deck? |
| Explore P52270 | Can they find organism/sequence/annotations and their original source, and distinguish text positions from structural coordinates? |
| Follow BTS | Search retained content for BTS, inspect its original related Entity, open the supplied small-molecule Card and explain why a matching label would not suffice |
| Inspect activity | Open Targets, measurements and assay context, the supplied target, native group and record; read value/unit and original assay/full publication |
| Return exactly | Return to the original Deck selection and repeated occurrence without silently querying a source or changing the original revision |
| Compare presentations | Choose Cards/Table, inspect complete fields beyond previews, and use a disease relationship graph without treating its edges as new Evidence |
| Save and restart | Save workspace, close and reopen with Open reading; identify retained query/history scope and excluded model/layout/pending jobs |
| Handle uncertainty | Explain `not_saved`, missing source statements, unavailable supplied context and an explicit failed source outcome without interpreting absence as a negative finding |

Separate explicit source-query tasks may use the public fixture receiving service
under maintainer observation. Distinguish frozen-client behavior from live-source
availability, and synthetic latency from a source-speed measurement. Check that
reading stays possible, cancellation discards, and a late result needs explicit
opening after a reading change. Do not require credentials or an LLM.

## Worksheet and decision

Record one row per participant/task:

| Participant role | Task | Completed unaided / assisted / not completed | Time | Expected versus understood meaning | Navigation/accessibility obstacle | Follow-up owner |
| --- | --- | --- | --- | --- | --- | --- |
| Not yet assigned | Pending | Not reviewed | Not measured | Not reviewed | Not reviewed | #154 |

Use public or sanitized observations. Collect task success and understanding,
including keyboard focus, scroll/panel discoverability and confusion between
source declarations, interpretations and project Evidence. Automated screenshots
and passing assertions cannot fill these human fields. The maintainer records
functional acceptance or concrete revisions separately from independent review,
workload budget agreement, exact-source CI, installed artifacts and publication.
No review or acceptance is claimed by creating this worksheet.
