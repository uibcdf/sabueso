# Follow-up 29: notebook regeneration and reporting review

Review five preserved reporting originals on **2026-10-08** against the current
SourceAssertion/card snapshot workflow. Recover executable offline regeneration
from the optional adjacent saved card, preserving the original report options.
The notebook is rendered from stored knowledge and remains inert until its cell is
explicitly executed. No scientific schema, source access or attribution change.

## Five-file disposition

| Original file | Reviewed outcome |
|---|---|
| `sabueso/tools/card/notebook.py` | Its saved-card regeneration cell is useful and was missing from the adapted renderer: the current cell only loaded and verified a snapshot. Recover regeneration through current public `Card.from_json`/`Card.to_notebook`, preserving title, mode and language and checking the exact scientific snapshot first. Current generic stored-field/relationship/assertion rendering replaces hard-coded old protein/Evidence paths. |
| `tests/tools/test_card_notebook_offline.py` | Current notebook, card and deck persistence tests replace the obsolete API/schema/HK2 count expectations. Add five behavioral cases that execute generated code after moving both files: full/minimal and English/Spanish with quoted titles/filenames, and a valid but different snapshot that must be refused before regeneration. |
| `docs/content/user/protein_notebooks.md` | The current user guide already preserves default/explicit output paths, optional snapshots, modes, language and offline behavior. Extend it with the actual generated-cell execution/regeneration contract. Do not restore obsolete protein constructors, Evidence language or prototype-specific scientific field shapes. |
| `notebooks/README.md` | Its useful requirements are explicit saved knowledge, separate related-molecule decks, independent source coverage, offline regeneration and no inference from empty results. Current card/deck persistence and reporting implement those behaviors. Source-profile counts and the old artifact's coverage assertions are historical descriptions, not qualification of current providers. |
| `notebooks/HK2_human.ipynb` | The 16-cell historical report uses an extended 0.1.0 card/Evidence model and has a commented optional refresh cell. Keep it as a hashed historical artifact; it supplies neither native provider responses nor current-format scientific support. Current reports retain stored values, units, source support, conflicts and explicit missing information without importing its scientific conclusions. No historical report cell is executed. |

## Recovered behavior and acceptance

With `include_card_snapshot=True` and `include_code=True`, the generated notebook
contains one optional executable cell. Run it with the notebook and adjacent
`.card.json` in the working directory. It resolves that adjacent filename, loads
the stored card, checks the report's exact original snapshot ID and regenerates
`<report_stem>_regenerated.ipynb` with a sealed adjacent card. Original title,
`mode` and `language` are passed explicitly. Absolute output derived from the
resolved input keeps the regenerated pair beside the moved saved card, independent
of a caller's script directory. No original-machine absolute path is embedded.

Rendering or opening a notebook executes nothing. Explicitly executing the cell
performs only local load/render/write operations; it does not call resolution or
refresh. Existing generated outputs at that regenerated filename follow the current
replacement policy. The original notebook/card pair remains untouched. A different
valid card cannot replace the expected scientific snapshot silently. The check
retains the existing assertion-based generated-cell guard; normal Python/Jupyter
execution is the qualified route, not optimized Python with assertions disabled.

The four option combinations preserve exact report metadata, markdown cells,
scientific snapshot pin and byte-identical sealed JSON. Quoted filenames and
multiline quoted titles are literal Python strings, and the regenerated notebook
passes nbformat validation. Full and minimal reports remain intentionally different
views; mode changes do not become source absence. Runtime acquisition/attribution
sidecars remain separate and are not recreated or credited by regeneration.

## Residual requirements preserved without the stash

| Requirement | Disposition / future acceptance |
|---|---|
| Curated presentation sections or narrative summaries | The prototype's readable structure/GO/domain/disease/ligand sections are presentation requirements. The current generic full report covers stored content with actual field names, quantities, relations, support and conflicts. A richer presentation may be proposed later using supported current views, without new knowledge, automatic classification or silently omitted alternatives. It is not an unintegrated scientific source reader. |
| Deck-level notebook/bundled report | Retain exact individual card pins and deck membership, with per-item source support, source coverage and missing/failed/unqueried states. Current card reports and JSONL/SQLite deck persistence cover per-card rendering and stored decks; this review adds no public deck-report API or frozen prototype molecule cards. Qualify explicit selection, options, terms/retention and offline reopening before such a new API. |
| Complete runtime replay bundle | Current scientific JSON snapshots deliberately exclude runtime acquisition/attribution sidecars. A future report bundle needs explicit original sidecar association, integrity/retention and exact snapshot references; rendering must not manufacture missing receipts, credit or a source release. Keep this under the existing acquisition/attribution ownership. |
| Exported HK2 snapshot and ligand references | The old report's input is an extended historical card, not native public wire evidence. Any future re-expression needs original provider support, exact chemical/protein identities, current-schema admission and qualified rights. Counts, Evidence IDs or reference-only molecules are not enough. Existing offline TcTIM tests provide a current public qualification system. |

These are bounded future product/qualification requirements. Their conditions are
self-contained here and routed to the existing implementation-review issue
[#112](https://github.com/uibcdf/sabueso/issues/112). They do not require keeping the
obsolete Python tree importable or running its notebook. This five-file reporting
block has no further ready behavior identified after the current replay improvement.
Broader recovery still includes generic card admission, native metadata/support,
source-sequence/residue persistence and consumer contracts; their residual gaps
must be accounted before recommending stash deletion. The remaining historical
HK2 data artifacts are not declared current-format fixtures by this notebook review.

## Validation

Focused notebook/storage gate: **18 passed in 5.67 seconds**.
Full offline checkpoint: **5477 passed in 172.18 seconds**, pytest-receptor with
**12 workers** in the existing editable Python **3.14.7** environment, 10 expected
fixture failure/truncation warnings. Five new behavioral cases qualify executable
regeneration rather than merely compiling the generated cell.

Outside-checkout editable replay in `/tmp` regenerates all four mode/language
combinations from the public TcTIM fixture, preserving 199 SourceAssertions, exact
scientific pin, metadata, markdown cells and sealed-card bytes with zero scientific
source requests. Artifacts: `/tmp/sabueso-followup29-replay`; receipt:
`/tmp/sabueso-followup29-replay.json`. Original notebook cells are not executed.

Ruff lint/format (**936 files**), generated registry, strict Sphinx HTML at
`/tmp/sabueso-followup29-docs-build`, shape/schema and diff gates pass. Integrity
checks all 87 original byte lengths/SHA-256 hashes, 91 accounted paths, stash/empty
index, frozen published card and earlier scientific fixtures. Receipts:
`/tmp/sabueso-followup29-integrity.json` and `/tmp/sabueso-followup29-gates.json`.
Public reproducibility/deck/bundle acceptance is recorded in
[issue #112](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6057570230).
Local implementation/recovery details remain in this report.


The original stash and 87 exports remain intact; all 91 original paths remain
accounted. No stage, commit, push, remote code checkpoint, environment creation,
fixture acquisition or published schema/card mutation. Stash deletion remains the
maintainer's subsequent decision after broader recovery is accounted.
