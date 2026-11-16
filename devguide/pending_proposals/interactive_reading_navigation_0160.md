---
summary: Compact complete-title disclosure and keyboard access to every backend-retained reading point.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-15
verification: implementation_checkpoint
area: [human-exploration, navigation, presentation, accessibility]
---

# Readable headings and earlier exact readings

The [longer-session native capture](interactive_model_scale_0160.md) exposed a
long literal source heading requiring horizontal scrolling in a split reading.
The existing interface also rendered only the final five backend history points.
The backend already retained exact indexed return points; older points had no
direct trail control in the application. Both are Sabueso presentation work under
#154, independent of supported 3D/2D provider integration.

## Implemented behavior

The portable frontend now wraps the reading content and presents a compact title
when its displayed heading exceeds 48 Unicode code points. It preserves both
the start and end of the text, with an explicit ellipsis. Full reading title is
a native keyboard-operable disclosure containing the complete exact heading.
The title attribute is supplementary, not the only way to access that text.
Original orientation previews retain their existing scientific limits; the
complete original field still opens through its native reader.

The trail keeps five recent buttons and adds Earlier readings for every older
backend-retained point. Earlier buttons show complete original titles within a
bounded vertical list; recent buttons have compact labels and exact original
accessible names/tooltips. Every action sends the native history index, never
a label, a guessed source or an array position reconstructed in the browser.
Repeated labels remain separate points. The existing finite backend history
policy is unchanged; this does not reconstruct discarded history.

Title/history disclosures reset on a different reading, avoiding an unrelated
expanded heading after return. Native Back, source/view/result references, original
text, scientific values/units, query scope and saved meanings are unchanged.
Wrapping reading/trail/action rows prevents long references from forcing the
entire reading into horizontal scrolling. No source is queried by these controls.
No backend API, schema, verifier, scientific label/rule or provider code changes.

## Receiving and limits

The [source-bound receipt](../evidence/interactive_reading_navigation_checkpoint_20261115.json)
owns actual source, compiled assets, diagnostic artifacts, copied tests/fixtures,
native profiles, failed preliminary receiving and resource/cleanup scope.
`receive_navigation.mjs` drives real Qt controls: choose an original source,
disclose its complete heading with Enter, create more than five history points,
expand Earlier readings with Enter, return by its original index and inspect the
exact source/view/result/text and parent Back. It records actual panel width and
horizontal overflow. No input, model event or scientific source state is replaced
to manufacture a successful UI check.

Receive protein, small-molecule and disease presentation in Qt, a narrow live-model
reading, and an original saved Deck in a fresh installed process. The source
navigation helper is an opt-in addition to the existing developer receivers;
ordinary product controls do not expose automation or implementation details.
Native/renderer screenshots complement DOM measurements. They establish neither
human understanding nor complete accessibility across devices or OSes.

The final narrow-panel capture is vertically scrolled below its heading after
source/history navigation. Exact native return is received; scroll-position and
focus restoration across reading changes are not. Receive and refine those UI
behaviors next under #154 without treating them as a source-identity failure.

The subsequent [position/focus increment](interactive_reading_position_0160.md)
now receives that bounded behavior. The original capture and its unqualified
scroll observation above retain their earlier epoch and are not rewritten.

Run the complete source application/package-data gate with the published receptor.
The installed runtime gate selects the copied complete application modules and
excludes only the existing source-tree frontend-declaration check. That check
requires package/lock/source paths by design and passes in the source gate;
the final sdist verifies its exact frontend source, and wheel/installed receiving
verifies the compiled resources independently. Retain the initial missing-source
placement failure, rather than calling it a runtime regression or an installed
pass. Two early 180 s runs were incomplete; the final selected gates have complete
verified receptor streams and their own elapsed budgets.
The final source and runtime gates each retain four expected fixture warning
controls; no skip or failed assertion is counted as a final pass.

The new noneditable diagnostic artifact is unpublished. Original Card/Deck schemas
and SOURCE files remain fixed. A genuine pre-change workspace reopens with Card/
Deck construction, acquisition and optional graphical/provider imports forbidden;
its exact original content and Back remain intact. Actual provider heads and
import paths retain their separate experimental cohort. Local software Qt is not
new platform, GPU or public-installation qualification.

## Functional checkpoint

The [twenty-journey inventory](functional_inventory_review_0160.md) maps accepted
experience to actual implementation, receiving and specific remainders. It starts
S6.3, moving that row to partial without accepting the version. The main plan now
has **20 done, 11 partial and 2 todo**. Supported mapped 3D, implemented/admitted
MolSysSketcher 2D, the reviewed MolSysMT #763 fix, workload budgets, human
observations and #192/#194 version decisions remain open. Exact-final-source
full/hosted/candidate/publication gates retain their owners and authorization;
this increment selects no release or workflow dispatch.
