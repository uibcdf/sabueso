---
summary: Recruit and prepare independent researcher review without substituting demonstrations for B7 acceptance.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-10
area: [human-exploration, acceptance]
---

# Independent researcher review for 0.15.0

The maintainer requested a shareable documentation section while looking for a
researcher unfamiliar with Sabueso's internals. The
[participant page](../../docs/content/user/researcher_review.md) and
[blank worksheet](../../docs/_static/researcher_review_worksheet.txt) provide the
invitation, core tasks and optional specialist modules. Recruitment and all actual
review results are pending. #148 owns exploration; #112 coordinates acceptance
and delivery, and #132 owns actual consumer usefulness.

## Prepare and hand over the session

Ask for basic Python competence and relevant molecular/biomedical experience;
prior Sabueso knowledge is unnecessary. Record prior walkthrough exposure rather
than excluding a useful specialist. One researcher can begin the core review;
specialist scientific, actual-agent, workload and consumer acceptance remain
separate dimensions and may need different people. The suggested 60–90 minutes
is a scheduling estimate, not benchmark evidence.

Use a qualified development environment with this checkout installed editable,
verified import paths and exact source/runtime metadata. Public 0.14.0 does not
provide the explorer. Do not advertise a public installation route for an
unpublished feature. Prepare the session and check its input manifest before
giving the participant the tasks; no runtime installation or fixture internals
should be part of their ordinary scientific task.

From the repository root, choose a new or empty output directory:

```bash
python examples/researcher_review/prepare.py --fixtures temp_data --output /tmp/sabueso-review-inputs
```

The helper exports three Card JSON inputs, their pins/file hashes, exact source
commit/dirty status and runtime/distribution labels, its own hash and the public
fixture notices. It verifies JSON loading preserves each pin and refuses a
nonempty output. Fixture clients are explicit and socket connection attempts are
forbidden during preparation. It does not run exploration tasks or save solved
histories. A successful run is technical preparation only. An interrupted export
can leave partial caller output; retain it for diagnosis or use a new directory.

The inputs are current public TcTIM P52270 with the 1SUX nonpolymer capture,
ChEMBL CHEMBL110 and MONDO:0014221. The protein retains its broader UniProt-linked
inventory without newly acquiring every structure. The molecule is a property
input, not the full activity/clinical pack. The disease's parent Card is
deliberately not supplied. Keep this preparation separate from frozen schema
Cards: it neither publishes nor freezes schema 0.3.14. The original fixtures and
their [source/rights notices](../../temp_data/NOTICE.md) remain unchanged.

Give the participant the input directory, worksheet, participant page, normal user
guide, prepared environment and a separate output directory. Keep this maintainer
guide and solved scripts until the debrief. They are public documents, so record
prior exposure honestly; separation does not establish secrecy or independence.
Record help when given. Do not silently fix a participant's session and record
it as an uncoached success.

## Maintainer observations to check after the first attempt

These are review controls, not a grading script for the participant. Rehearse
technical controls separately and retain the participant's own interpretation.

| Task | Inspectable control and acceptance question |
| --- | --- |
| C1 | Check original entity/nature, organism or term, complete source versions or explicit unknowns and exact input pins. Does the participant understand captured scope without relying on inventory counts as completeness? |
| C2 | The current TcTIM fixture has source sequence/active-site and 1SUX structural context. Compare the selected source/back route and the distinction between retained annotation, coordinates and an appropriate scientific model. The [structural review](structural_source_review_walkthrough.md) owns positive/gapped and assembly controls. |
| C3 | CHEMBL110 retains molecular weight 260.25 dalton and ALogP method context. Check exact quantities/units/support. ALogP does not supply an experimental method for the weight; unspecified measured/calculated scope stays unknown. The [chemical-context reading](card_chemical_context_reading.md) exposes original representation labels and any source-native parent declarations. Chemical representations do not establish missing charge, stereochemical certainty or parent identity. The separate positive SO4 charge capture is optional specialist input; do not silently add it to the supplied molecule identity. |
| C4 | MONDO:0014221 retains definition, synonyms and broader MONDO:0002908. Hierarchy is not identity. Opening an unsupplied parent reports `context_not_supplied`; it does not acquire a new Card or prove source absence. |
| C5 | Keep not queried, unavailable/failed, not retained, explicit source absence, malformed/null/empty scope and empty display selections distinct. Not every state occurs in these three Cards; record unobserved distinctions as untested rather than manufacture a result. |
| C6 | Compare the original and independently reopened visited value/source/navigation with the original pin. Saved mode differs from LIVE presentation. Unexecuted operations may be `not_saved`. Record the exact saved root and access used. The [scientific request-retention correction](../pending_bugs/assembly_machine_request_retention.md) has owning local controls; CHECKPOINT owns wider qualification. Follow public `back()` navigation to replay the initial context when the saved root belongs to a source destination. |

Additional public inputs and exact scope must be prepared for each specialist
module. S1 can use the [structural review](structural_source_review_walkthrough.md)
and bounded 1TCD positive/uncertain MolSysMT controls. S2 uses the original
molecule-target, activity and literature journeys. S3 uses
[protein context](protein_context_review_walkthrough.md), with supplied Q4DV43
and HsTIM inputs. S4 uses clinical bibliography and retained disease-association
inputs. A solved script is a maintainer reference or explicit training material;
its technical success is not a participant's independent result.

## Record decisions and follow-up

Retain the manifest, preparation/gate logs, worksheet and exact relevant output
digests under a declared owner and review trigger. Do not commit personal details
or confidential scientific observations. Publish sanitized findings only within
the maintainer's concrete authorization; use an owning issue or private handoff
and distinguish observed behavior from a suspected cause.

Record task progress independently from scientific interpretation
(`accepted`, `revision_needed`, `not_reviewed`). Explain the reason, assistance,
unobserved scope, follow-up owner and required retest. Critical lost support,
unit/identity errors or misleading absence prevent acceptance of that affected
scope. Minor usability requests still need a disposition; they are not silently
treated as release blockers or waived requirements.

The B7 closeout must identify actual scientific review, uncoached researcher
observations, actual-agent parity/usefulness, representative workload and real
downstream-consumer results. This kit prepares only the researcher dimension;
ordinary regressions and stand-in consumers do not close the others. B2 remains
explicitly deferred. B8 candidate/schema freeze/staging/publication remains
unresumed and requires its own exact-source/artifact gates and authorization.
