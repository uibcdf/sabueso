---
summary: Versioned conservative activity interpretation before broad activity exploration.
issue: uibcdf/sabueso#184
status: open
opened: 2026-11-04
verification: local_implementation_in_progress
area: [scientific-correctness, bioactivity, public-api]
---

# Bioactivity interpretation: intervals and assay dose roles

The [global audit](../GLOBAL_AUDIT_20261104.md#scientific-findings) reproduced
unsupported censoring/boundary classes (#184) and selection of a substrate dose
from text as a compound dose (#185). The original `bioactivity_class@3` functions
remain unchanged. Broader assay correspondence is separate #186 work.

## Current default adoption

New development answers now default to @4 through `Card.bioactivities`,
`explain_bioactivity`, `ligands`, `explain_ligand` and `compare_ligands`. Explicit
`classification_rule="bioactivity_class@3"` retains the original interpretation.
Ligand explanation @3 carries the selected current policy; original activity @3
still selects ligand explanation @2 and activity explanation @1. New packet
mapping @15 changes only bioactivity interpretation and inherits @14 elsewhere;
old mappings @6–@14 explicitly select original activity @3.

This technical adoption follows the interval counterexamples and the choice to
abstain when assay prose has not established a tested-compound dose or justified
potency inference. It does not claim independent scientist/researcher acceptance,
validate experimental comparability, or replace the separate #186 grouping work.
The inherited molecule summary still reports the strongest group band and
discordance; it is not a compound-prioritization or efficacy conclusion.

Current activity tables expose the interpretation and `not_interpreted` dose
state as well as original values/qualifiers. A table is not a self-contained
scientific capsule: exact thresholds and complete support remain in the view and
its explanation. Rich activity exploration and its scientific saved reader stay
required B4 work before 0.15.0.

Fresh recomputation of an explicit original rule records the current SDK in its
derivation producer stamp. Its scientific values, rules, inputs and parameters
must match the original interpretation; the old stamp is not fabricated. Inert
stored reading, by contrast, retains the exact original payload and producer stamp.
The post-editable regression checks these two contracts separately.

The [qualified earlier opt-in source](../evidence/bioactivity_opt_in_checkpoint_20261104.json)
is `1290201`: CI 18/18, governance 1/1, all thirteen actual source/installed
summaries, twelve codec producer routes and fresh/installed receiving verified.
That source retains default @3. The later adoption changes need their own final
exact-source qualification. MOLI #22 has received provider-change notice before
rollout; actual consumer acceptance remains with its owners.

## First bounded implementation at source 1290201

That first source introduced explicit `classification_rule="bioactivity_class@4"`
on `Card.bioactivities()` and `Card.explain_bioactivity()` while omission retained
original @3. It established the policy and compatibility before the adoption above;
it did not close B1 or claim original default answers corrected.

The new policy classifies a positive concentration only when its entire permitted
interval falls within one configured band. Thus `IC50 >= 100 uM` is inconclusive
under default thresholds, `> 100 uM` is inactive, and an upper bound inside the
weak band is inconclusive because it also permits active-band values. Closed
ranges must fit one band; unknown/approximate qualifiers, invalid/nonpositive
potencies and uninterpreted uncertainty do not become exact numeric bands.
Thresholds must be finite, ordered positive concentrations; the retained percentage
parameter must lie between 0 and 100. Classes describe policy bands, not efficacy,
selectivity or experimentally established comparability.
`single_point_min` is retained for option compatibility and explicitly listed as
unused by @4, since this policy makes no single-point potency inference.

For single-point inhibition, @4 retains the measurement and declines potency
extrapolation. It does not run the old text regex or select any compound dose from
prose; `test_concentration_state="not_interpreted"` distinguishes this policy from
a source failing to state a concentration. The original assay and its supporting
record remain inspectable in the explanation. This closes that unsupported
inference path for explicit @4; a future positive dose-role interpretation would
need separately justified source context and assumptions. No new extraction or
source fact is manufactured.

```python
current = card.bioactivities(classification_rule="bioactivity_class@4")
item = current["items"][0]
why = card.explain_bioactivity(
    item["molecule_ref"], classification_rule="bioactivity_class@4"
)
original = card.bioactivities(classification_rule="bioactivity_class@3")
```

The example requires a Card with at least one included activity item. Discovery
and empty/partial recovery will be part of B4's human exploration journey, not
assumed from this direct API example.

## Explanation and compatibility

@4 measurement results include a readable `interpretation` alongside the
machine-readable class/basis. `bioactivity_explanation@2` records the selected
classification rule and exact original support. Original @3 explanations retain
`bioactivity_explanation@1` and their original shape. Values, relations, units,
source assertions, groups and Card pins are not rewritten by selecting a policy.
This is derived runtime output, not a stored Card/schema change.

One ArgDigest digester owns `classification_rule`. Native validation remains
active when digestion is skipped, before Card pin capture or scientific work;
unknown selectors are refused rather than approximated. Current ligand/packet
adoption is described above; original packet reading remains inert. New explorer
or saved-scientific activity routes are not claimed by the direct API adoption.

## Required evidence and remaining work

The [default-adoption receipt](../evidence/bioactivity_default_adoption_20261104.json)
records 338 affected integration cases, 323 inherited-aspect cases, 115 final
policy/table/quantity/copied-scope cases and warning-fatal Sphinx. These scopes
overlap and are not summed as unique cases. Source class @3 and qualified @4
function bodies remain unchanged. Genuine original full/index packets and both
old public example producers retain their original reading without scientific
calls; thirteen original JSON hashes stay fixed. New reader exports are separate.
The exact same original Card references and reported measurement context are
retained in old/current example comparisons; derived classes change as declared.
Hosted qualification of the new source and independent acceptance remain pending.

The [local qualification receipt](../evidence/bioactivity_interpretation_20261104.json)
records 62 independent policy cases, 232 affected integration cases, one isolated
copied-receiving test (repeating the policy cases outside the checkout), warning-fatal
Sphinx and original-function integrity. Every gate runs serially under the resource
guard with zero owned swap; hosted and scientist acceptance remain pending.

Local public-input comparison now covers two frozen Cards and two Cards rebuilt
only from public UniProt/ChEMBL/BindingDB/UniChem fixtures:

| Public input | Included / excluded records | Changed record classes | Changed molecule classes |
| --- | --- | --- | --- |
| Frozen TcTIM, schema 0.3.9 | 42 / 0 | 7 | 7 of 40 |
| Frozen HsTIM, schema 0.3.13 | 0 / 0 | 0 | 0 of 0 |
| Rebuilt fixture TcTIM | 510 / 0 | 221 | 215 of 256 |
| Rebuilt fixture HsTIM | 51 / 8 | 9 | 8 of 40 |

Every changed record class in this comparison is the deliberate withdrawal of a
single-point potency inference. These are policy differences, not counts of
erroneous measurements. The empty frozen HsTIM Card is a coverage control, not
evidence of absent bioactivities. Original values, support, groups, Card state
and the default @3 answer remain unchanged. The rebuilt examples use fixture
replay with zero online requests; no primary-method interpretation is accepted.
Exact inputs, hashes, pins and changed-record details are retained in the owned
phase for review. This is not a source-wide prevalence or clinical conclusion.

- Independent relation/threshold, closed-range, unit-equivalence, uncertainty and
  invalid-input cases; public class/aggregation/explanation parity and original @3
  compatibility. Controlled helper refusal does not qualify every malformed Card.
- Frozen public-corpus comparison with eligible/included/excluded denominators,
  original/new record and molecule classes, and actual downstream effects. A
  changed classification is a policy difference, not by itself proof the source
  record was erroneous.
- The technical default/consumer decision is now recorded with counterexamples
  and original controls. Independent scientific/researcher review of abstention,
  class meaning and experimental comparability remains pending; the rich human/agent
  activity adapter is subsequent B4 work. Preserve explicit original interpretations
  and genuine historical readers/inputs throughout that work.
- Applicable source, copied installed, original-history, argument, quantity,
  documentation and exact-source CI gates before qualification. The first new
  explanation version does not establish installed or released delivery.

Owner #184/#185, coordination #112/#148. Evidence is retained under
`recovered_work/bioactivity_policy_184_20261104/`, reviewed at the next scientific
checkpoint and before 0.15.0 acceptance. No online acquisition or private pilot
content is part of this implementation.
