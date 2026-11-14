---
summary: Explicit source-candidate follow-up, original ambiguity preservation and usable reading space during queries.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-13
verification: implementation_checkpoint
area: [human-exploration, source-access, persistence, standalone]
---

# Explicit source candidates and useful query space

The [living plan](interactive_implementation_0160.md) owns S4 completion.
This increment extends the four-kind entry without silently choosing an identity
or creating a Deck from ambiguous matches. The
[source-bound receipt](../evidence/interactive_source_candidates_checkpoint_20261113.json)
owns actual source/installed/native receiving and its limits.

## Follow-up queries

An original ambiguous UniProt result can offer its exact source-declared protein
candidates. A resolved preference can offer the separately retained alternatives.
An original ambiguous SMILES lookup can offer the exact PubChem CID records
listed by that source. Existing PDB → source-declared protein follow-up remains.
Only supported, finite reference grammars become buttons; unsupported declarations
remain in the complete original report. Duplicate candidate occurrences remain
distinct. The interface shows at most 32 follow-up buttons and explicitly points
to the complete original report when more exist.

A button starts a **separate explicit query** with `identity@1`. PubChem CID
follow-up disables UniChem expansion, just as the initial SMILES query does.
The original ambiguity/preference is not rewritten. It establishes no new link
between the chosen Card and the original structure or other candidates. Source
identity and the new Card's canonical reference come from the native resolver.
Return to previous query restores the exact original report, choices and reading
without another source request. The initial selector still offers UniProt, PDB,
SMILES and disease ID; CID follow-up is a source-record route, not another
automatic search or a disease-name search contract.

Bounded candidate descriptions expose available original organism, reviewed flag,
recorded length or source observation text. False, zero and retained null are
preserved. These are current UI descriptions in `choice_details`, added by the
service to its response; they never enter the original resolution wire or its
saved report. Complete native source decisions/bases remain available below.

## Original saving and compatibility

Whole workspaces retain the new CID report and original ambiguity return point.
Reading is inert. The unpublished workspace-v1 reader additionally recognizes
the explicit PubChem follow-up kind and admits each saved choice only as an
ordered occurrence of its original supported declarations, using canonical
typed comparison. Resealed query/basis changes, reordered occurrences and foreign
references are refused before replacing the reading.

Historical files retain exactly the choices they saved, including an empty list;
newly available follow-ups are not retrofitted on reopening. A genuine PDB-only
workspace produced at `796d20e`, before this implementation, is retained and
received unchanged without constructing a current Card or querying sources.
This adds application capability; it changes no Card schema, scientific rule,
native Card/Deck saved format or public provider dependency.

## Usability correction exposed by receiving

With the query drawer, progress and ambiguity report all visible, the previous
900-pixel layout could leave almost no height for the reading/topic controls.
Real pointer navigation then failed even though the backend remained responsive.
The submitted form now folds after its request is accepted; the researcher can
reopen it, with its text retained, and the toggle describes its visible state.
The reading has a minimum useful height and the outer application can scroll
when the combined content needs more space. This corrects the observed layout;
it is not general accessibility or native-platform acceptance.

The receiving control deliberately fabricates an ambiguous `CCO` response with
two candidate CID references, then queries one actual frozen public compound.
It explicitly labels the ambiguity synthetic and asserts **no chemical identity
between CCO and that compound**. Its purpose is to prove that a follow-up does
not transfer an unestablished identity into the new Card. No new scientific
source fixture is published. Keep the synthetic control separate from public
scientific examples and live-source availability/performance.

Earlier receiver failures are retained: dictionary key ordering after canonical
saving is not a change in ordered candidate references; compare exact typed
reference pairs instead. Waiting for visible query readiness avoids a separate
automation race. The continued pointer failure then exposed the real height
problem, which is received after the product correction. No failed run counts
as passing. Broader enrichment acquisition/presentation, supported 2D/3D mapping,
workload agreement and human review remain open under S4–S6.
