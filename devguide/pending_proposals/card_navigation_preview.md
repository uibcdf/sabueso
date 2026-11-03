---
summary: Make retained questions and destinations discoverable in bounded navigation previews.
issue: uibcdf/sabueso#148
status: implemented
opened: 2026-11-02
area: [human-exploration, presentation, historical-reading]
---

# Discoverable navigation previews

An observed 20-member structure-context view put its scientific question at
original index 19, outside the first ten displayed members. Complete public
filters already exposed it, but the preview did not help a researcher discover it.

`question_destination_preview@1` presents questions first, other destinations
second and source links third, within the existing ten-row preview. Each group
preserves its original relative order. Displayed indices still address the
original `items()[i]`; full membership, ordering, selections, native values,
source support and machine access do not change. Text and HTML show per-category
shown/total counts and complete question/source filter routes. More than ten
questions remain explicitly partial. Displaying a preview does not open links,
resolve identity, query providers or evaluate a scientific question.

New live explorations record the named policy in the existing optional
`presentation_metadata.navigation_preview` namespace. Saved readers reproduce it;
unknown named policies fail rather than silently substituting current behavior.
Genuine old files without that namespace retain their historical prefix preview,
including after resaving. `start_new()` begins a new live policy. This changes
presentation, not the Card schema, scientific rules or exploration format number.
Original scientific and historical verifiers remain byte-identical.

The genuine pre-change format @6 capsule records the original prefix at source
`f2732011c027be0ed65e7c17fb353e0c925bd50a`, SDK `0.14.0+138.gf273201`.
See [its immutable fixture receipt](../../tests/core/data/README.md#original-navigation-prefix-before-question-prioritization).
Owning cases cover source-heavy protein and generic nature contexts, question
overflow, filtering/sorting, original indices, inert repeat saving, old reading
and resealed unknown policies. Broader human/agent/saved gates and exact-source
hosted qualification are recorded in #148/#112. Technical discoverability is not
uncoached researcher acceptance; the broad 0.15.0 inventory remains open.

The final selected integration passes 1,315 cases across 43 files in five serial
pytest-receptor gates (623.87 pytest seconds), including 16 new preview cases.
Sampled owned RSS peaks at 795.2 MiB, genuinely free host RAM stays above 531 MiB,
available RAM above 15.7 GiB and owned swap at zero. One earlier partial run failed
an old test's assumption that new saved presentation metadata was empty; its
updated full-equality assertion preserves both the named policy and unknown
optional metadata on machine resave. The final whole affected group passes.
This is a selected local receipt, not a full-local or hosted qualification.

Local diagnostic evidence belongs to #148/#167 under
`recovered_work/navigation_preview_148_20261102/`. Review it at the next code
checkpoint or before workload acceptance; retain original capsules and useful
receipts, and remove only completed owned scratch.
