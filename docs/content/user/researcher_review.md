# Help review Card exploration

The independent researcher trial is scheduled for after 0.15.0 publication. These
materials are retained for that review; no completed independent acceptance is
claimed for 0.15.0. If you use molecular or biomedical data, can read basic Python, and have
little familiarity with Sabueso's internals, your experience can help us find
unclear navigation, missing context and misleading scientific presentation.
Arrange a session with the maintainers; no contribution to the code is required.

**Prepared review:** a maintainer will supply a qualified environment for the
exact version under review and public input Cards. The session does not require
querying online sources or supplying private research data. Record the supplied
version and environment with your observations.

## What to expect

Allow about **60–90 minutes** for setup, the core tasks and discussion. This is a
planning estimate, not a measured performance target or a time limit. Specialist
modules can take a separate session, and different people can review different
areas. Tell the maintainer which domains you know and whether you have previously
seen a Sabueso walkthrough or contributed to its development.

Use the ordinary user guide and API help as you normally would. For an independent
first attempt, leave scripted demonstrations and the maintainer's expected
observations until the debrief. If you have already seen them, record that
exposure. Ask for help when needed and record what help you received. A confusing
or unfinished task is a useful result; you are evaluating the software.

The maintainer supplies three files (`protein.json`, `molecule.json`,
`disease.json`), `manifest.json` identifying their exact captured states, and
`SOURCE_NOTICE.md` with source and licence notices. Keep these inputs unchanged.
Choose a separate output directory for your notes and saved exploration sessions.
The input Cards contain retained public data with bounded source scope; they do
not represent complete or necessarily current source databases.

## Begin with the supplied Cards

In the prepared environment, set `inputs` to your supplied directory:

```python
from pathlib import Path
from sabueso.core.card import Card

inputs = Path("review-inputs")
protein = Card.from_json(str(inputs / "protein.json"))
molecule = Card.from_json(str(inputs / "molecule.json"))
disease = Card.from_json(str(inputs / "disease.json"))

explorer = protein.explore()
print(explorer.overview())
print(explorer.topics())
```

See {doc}`card_exploration` for normal navigation and saving help. Work from the
displayed labels, questions and source links. Record where you needed internal
field names or maintainer assistance to make progress.

## Core tasks

Record your attempted route and interpretation before the maintainer discusses
expected observations. There is no required numerical answer in this task sheet.

| Task | What to try and record |
| --- | --- |
| C1 — Orient yourself | Identify each supplied entity, its organism or ontology context where applicable, and the sources and versions you can actually find. Explain which information you would still need before using it. |
| C2 — Follow protein knowledge | Find a function or sequence annotation and an experimental structure. Select something relevant to a question of your choice, follow its original support, and return to the same selection. Explain what the displayed structural information lets you decide and what remains unresolved. |
| C3 — Read a molecule | Find a chemical representation and two physicochemical properties. Read their complete values, units when applicable, and source or method context. Explain whether you can determine how each property was obtained, and what information is missing. |
| C4 — Read an ontology term | Find the disease definition, a broader term and identifier relationships. Explain how you interpret each relationship and try opening a related term. Record what happens when a related Card is unavailable. |
| C5 — Investigate a gap | Find something you expected but could not establish from a supplied Card. Inspect its coverage and support. Record the state you actually find and how it differs from an empty display filter. Recover the original view after a filter matches no items. |
| C6 — Keep and revisit your work | Save a useful visited view into your output directory. Restart Python and reopen it using the normal guide. Try recovering a visited value and its original source/return route. Record the saved root, steps, errors and any difference you observe. |

For every task, note the result, your interpretation, supporting source or saved
reference, assistance, and friction. Preserve actual error messages when useful.
Use `completed`, `partly_completed`, `blocked` or `not_attempted` to describe task
progress; these labels do not certify scientific correctness.

## Optional specialist modules

Ask the maintainer for the corresponding additional public inputs before starting.
The three core Cards alone do not cover all these modules.

| Module | Review question |
| --- | --- |
| S1 — Structural context | Can you connect an annotated region to chain coverage, gaps and author numbering, inspect ligand/contact records, and distinguish source assembly declarations from calculated physical membership? |
| S2 — Activity and literature | Can you trace a molecule–target measurement to its assay, qualifier, units, assignment and publication, then explain which comparisons the retained context supports? |
| S3 — Variants and comparison | Can you inspect supplied protein comparisons and variant/isoform/tissue context, keeping sequence correspondence, missing scope, thresholds and source support explicit? |
| S4 — Clinical and disease associations | Can you follow an indication, cited study or association in its stated direction, distinguish the record types and explain what the original sources actually establish? |

If agents are part of your normal workflow, record their prompts, tools, help and
outputs separately. Automated demonstrations do not replace your own account of
usefulness. Actual agent, workload and downstream-consumer reviews also need
their own recorded results.

## Return your observations

Download the {download}`blank review worksheet <../../_static/researcher_review_worksheet.txt>`.
Fill it in locally and return it to the maintainer through the agreed channel.
Include the input manifest and output references needed to reproduce difficulties.
Do not add private hypotheses, unpublished project data or personal details to a
public issue or commit. Agree any publication of your observations separately.

During the debrief, identify the most useful result, the largest obstacle and one
change that would make you more likely to use Sabueso. The maintainer will record
scientific review and release acceptance separately from task completion. This
page supplies the invitation and task material; completed acceptance needs the
participant's actual observations and a recorded maintainer review.
