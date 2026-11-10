---
summary: Make the schema-alignment CLI fail when it reports inconsistent paths.
issue: uibcdf/sabueso#112
status: implemented
opened: 2026-11-10
verification: reproduced
area: [developer-tools, schema-validation]
---

# Schema-alignment process status

`tools/validate_schema.py` reported missing schema/FIELD_PATHS entries but exited
with status 0. Four isolated synthetic CLI cases reproduce the failure. The
actual repository schema remains aligned; this finding does not establish a
Card-schema defect or corrupted user data.

The CLI now returns 1 for either mismatch and 0 for alignment, preserving its
diagnostics. Seven complete subprocess cases cover alignment, each mismatch,
both mismatches, allowed wildcard descendants and a similarly named unrelated
path. The real aligned-schema invocation remains a separate positive control.
No Card schema, source assertion or scientific interpretation changes.

Qualification belongs to the current [checkpoint](../CHECKPOINT.md). The owning
#112 update has a reviewable internal draft; publication remains a human handoff.
