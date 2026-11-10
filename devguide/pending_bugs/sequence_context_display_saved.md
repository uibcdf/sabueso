---
summary: Distinguish displayed sequence-source context from a clicked original link during current saved receiving.
issue: uibcdf/sabueso#148
status: implemented
opened: 2026-11-10
verification: reproduced
area: [human-exploration, historical-reading, sequence-context]
---

# Saving displayed sequence-source context

The combined public B6 walkthrough reproduces a save refusal after an HsTIM
sequence-change item opens its original related links and filters them to
`role="source"`. The sequence-context verifier treats that display operation as
a link click, cannot find a clicked candidate and raises `Sequence context lost
the clicked original link.` The source values and scientific result are unchanged.
This is a local development observation, not a claim about prevalence in a clean
public installation.

The correction keeps original sequence scientific predicates and earlier format
verifiers unchanged. Current saving selects logical @35 (shared @36) for an
actual non-scientific display operation whose original ancestry reaches a
registered sequence-change result, even without opening a question menu. @35
uses the existing independently frozen literal display predicate for that node;
its original scientific parent is still verified separately. The predicate
checks the displayed selection, complete original payload/cells, typed filter/
sort/presentation operation, request and source context. Source-owned lookalikes
are not scientific ancestry.

The owning regression covers filter, sort, presentation, chained and empty
context displays, source opening and exact back/request preservation. Altered
operands, selected membership and original source cells must still refuse after
resealing. The public combined walkthrough checks separate-process reading with
current science and acquisition forbidden. Qualification belongs to the current
[checkpoint](../CHECKPOINT.md); the issue update remains an internal human
handoff until its concrete material is authorized for publication.
