---
summary: Separate declared copies, possible measurement correspondence and experimental independence before rich activity summaries.
issue: uibcdf/sabueso#186
status: open
opened: 2026-11-04
verification: locally_checked_hosted_and_independent_acceptance_pending
area: [bioactivities, scientific-correctness, public-api]
---

# Assay-aware measurement correspondence

The [six-case review dossier](measurement_correspondence_review_20261104.md)
is prepared. The maintainer will perform the scientific review and explicitly
deferred it on 2026-11-04. The review reproduced an additional selection defect,
[#188](../pending_bugs/bioactivity_target_scope.md): copies can bypass their
retained original's indirect-target exclusion. A separate opt-in target-scope @2
addresses this without changing measurement @1 or target-scope @1/defaults.
Neither technical continuation nor the candidate establishes scientific/default
acceptance; unrelated B3 work may continue while review is pending.

Owner [#186](https://github.com/uibcdf/sabueso/issues/186); coordination #112/#148.
This is B2 of the [continuation plan](../CONTINUATION_PLAN_20261104.md).
The [original @1 design](../archive/measurement_identity.md) remains historical
authority for its own interpretation. The first opt-in candidate is implemented
in development; it changes no original @1 function, current default, source
assertion, stored Card or original answer. Independent scientific/default and
consumer acceptance remain pending.

## First opt-in implementation

`measurement_rule="measurement_identity@2"` is available on `Card.bioactivities`,
`explain_measurement`, `explain_bioactivity`, `ligands`, `explain_ligand` and
`compare_ligands`, including activity/ligand tables. One ArgDigest digester and
native preflight checks own the selector. Omission retains original @1. Activity
classification remains a separate option, default @4.

The candidate accepts only declared-copy identity edges with unique original
selectors. It retains original discrepancies, unresolved/ambiguous pointers and
cycles. Exact scalar numeric/publication matches remain possible correspondence;
range/uncertain/unsupported numeric context is outside that candidate comparison.
Reported literal context is not a protocol-equivalence or general prose parser.
Copy-only groups have no original voter and remain inconclusive, preserving each
record's own class. Counts explicitly state that independence is not established.

New measurement explanation @2, activity explanation @3 and ligand explanation @4
carry the opt-in interpretation and exact original support. Original selections
retain their earlier explanation shapes/meanings. Current packet mappings @6–@15
now explicitly select measurement @1; no new packet mapping or saved explorer is
introduced by this implementation. Subsequent adoption requires its own versions
and original-data receiving.

Selected receiving passes 99 cases across the new policy, public PubChem
copy controls and original measurement tests; 360 affected integration cases,
including both isolated copied scopes; and 218 shared explanation/original-reader
cases. Warning-fatal Sphinx passes. These scopes overlap and are not summed as
unique tests. The [candidate receipt](../evidence/measurement_correspondence_candidate_20261104.json)
retains resources, original-input hashes, failures/corrections and remaining
acceptance. Exact-source hosted and independent scientific/researcher/default
acceptance remain pending. This is locally checked implementation, not a released fix.

### Same-input public comparison and integration findings

The original-input inventory above uses @1 and remains unchanged. Later local
candidate comparison uses those same two original pins and two three-source public
fixture rebuilds, with unchanged individual values, qualifiers, units and classes:

| Input | Retained / included / excluded records | Distinct included groups @1 → @2 | Sum of per-molecule group counts @1 → @2 | Changed molecule summary classes |
| --- | --- | --- | --- | --- |
| Retained TcTIM | 510 / 510 / 0 | 494 → 510 | 494 → 510 | 0 |
| Retained HsTIM | 59 / 51 / 8 | 44 → 51 | 44 → 51 | 0 |
| Three-source TcTIM | 1002 / 1002 / 0 | 501 → 517 | 505 → 521 | 1 |
| Three-source HsTIM | 96 / 88 / 8 | 47 → 62 | 49 → 62 | 5 |

A copy family can occur in more than one molecule item, so summing item counts
can exceed the distinct included group count. Neither is an independent-experiment
count. Of the six changed summary bands, five move weak → inconclusive and one
inactive → inconclusive under copy-only abstention. Individual source record bands
remain unchanged. These are candidate-policy differences for scientific review,
not six proven source errors, new measurements or evidence of inactivity/efficacy.

The candidate resolves 485 declared-copy links in the three-source TcTIM input;
seven pointers lack a resolved molecule in their named retained assay. HsTIM
resolves 34 links; three named original assays are not on the Card. These local
scope statements do not establish absence from an external source. Numeric-only
candidates are 15 and 12 respectively, with retained methods/independence unknown.
The actual guide block executes on all four inputs without acquisition.

The complete comparison caught two issues after narrower controls passed. The
initial candidate unnecessarily required a stated copy endpoint; 471 of its 472
unresolved TcTIM pointers lacked that field. Some still lack an unambiguous molecule
selector. A declared named-assay/molecule pointer may
select a unique retained original without filling in the missing endpoint; several
eligible originals still remain ambiguous. Independent positive/ambiguous controls
now cover that distinction.

The same comparison reproduced an existing `KeyError` under @1 and @2 explanation:
a runtime registered anchor can occur as a record of another indexed entity.
The bounded #182 prerequisite enumerates resolved entries actually present in the
serialized glossary at the pin. Aliases and complete indexed context remain
inspectable; no fictitious locator or raw runtime registration is promoted into
pinned knowledge. Tests require exact before/after Card serialization explanation,
unchanged pins and support. `entities.py`, Card serialization, original measurement
functions and saved verifiers are unchanged. This does not close #182's broader
typed-glossary/identity versioning work. Original failed diagnostics remain retained.

## Scientific question

Which retained records are source-declared copies, which may describe one
measurement, and which lack enough context to decide? A separate question is
whether observations are experimentally independent. Neither equal values nor
different database names establish independence or measurement identity.

The audit's wild-type/pH7 versus mutant/pH5 synthetic example reproduces a known
@1 limitation: statement matching ignores assay context. This does not establish
real-source error prevalence. Retaining two records separately must not turn an
uncertain duplicate into two confirmations, just as grouping two records must not
hide potentially different experiments.

## Original-input inventory

The [measured receipt](../evidence/measurement_context_inventory_20261104.json)
uses the exact two public fixture-built Cards retained by the genuine `1290201`
protein-comparison example. At current source `7667754`, original
`measurement_identity@1` yields:

| Public Card | All retained activity records | Groups including singletons | Multi-record statement groups | Accepted statement edges missing one assay description |
| --- | --- | --- | --- | --- |
| TcTIM | 510 | 494 | 16 | 16 |
| HsTIM | 59 | 46 | 13 | 13 |

These denominators include all `has_bioactivity` relationships; they differ from
the class view's direct-assignment inclusion scope. No PubChem declared copies
occur in these two Cards. They cannot qualify copy handling by themselves.

The BindingDB mapping retains no assay description, organism or mutation in these
records. ChEMBL descriptions are populated for all 493/36 records. Thus all 29
accepted cross-source statement edges lack a description on one side. These are
unpopulated **mapped fields**, not proof that BindingDB or the original publication
lacks methods. Reading the original SourceAssertion is the next inspection route;
further acquisition needs its own justified scope. Descriptions alone would not
prove equality even if both were populated.

The inventory preserves original Card pins and database bytes, blocks network
access and removes its disposable database copy. It measures original behavior,
not a new policy or accepted scientific truth. It does not report independent
experiment counts. Original 0.14-era grouping acceptance remains recorded in #66;
the stricter proposal needs a deliberate new interpretation.

## Candidate interpretation for independent review

The candidate implements `measurement_identity@2` as an explicitly selected policy. Do not
change @1 or a published packet mapping in place. The first candidate should
abstain from statement-based identity when no source-supported link establishes
the same measurement; retain the old numeric/publication match as a **possible
correspondence**, with the exact match inputs and missing/conflicting context.
This is an implemented technical candidate, not an adopted default or scientist
acceptance. Review its public-input consequences before adoption.

| State | Required basis and consequence |
| --- | --- |
| Declared copy, original resolved | Preserve the copying source's explicit activity or named-assay link and exact selector. Group the records as a copy family, retain all values/context and flag differences; copies do not become extra confirmations |
| Declared copy, original unresolved or ambiguous | Retain its declared origin, candidates and reason. Do not infer an original from a convenient value or silently treat the copy as an independent observation |
| Possible cross-source correspondence | Retain publication, source-stated target/molecule correspondence, type, qualifier and precision comparison. Leave records distinguishable, report what could match and what is unassessed; no asserted measurement identity |
| Explicitly conflicting context | Retain both context statements and source locations, report the incompatible field and prevent an unsupported statement join. A source-declared copy can still be a copy with conflicting transcription/context |
| Same measurement supported beyond numeric coincidence | Require an explicit source link or a separately reviewed located-measurement contract identifying the actual experiment/result. Equal prose, matching source-local assay labels or a common paper are insufficient by themselves |
| Separate retained records | Report only that the policy did not group them. Experimental independence remains unestablished unless original support actually establishes it |

No NLP interpretation of arbitrary assay text is part of this first candidate.
The synthetic prose counterexample remains a must-not-join case; abstention can
handle it without claiming a validated text parser. Distinct prose is not itself
a proven experimental conflict, and equal prose is not proven equivalence.
Structured comparisons must state their actual field/reference scope. Missing
mutation does not mean wild type; taxon identity does not establish a construct.

### Group construction and support

- Keep original relationships, source statements, quantities, qualifiers and
  glossary identities. Comparison never creates molecular identity or Evidence.
- A source activity link identifies its source and activity; a named-assay link
  still needs an unambiguous original-row selector. Connectivity-based copy
  selection stays visibly distinct from molecule identity, with original review
  flags. Equal rounded values must not choose between incompatible candidates.
- Missing/different target, construct, endpoint or conditions cannot be repaired
  by transitive matches through a third source. Review whole candidate components,
  including same-source multiplicity and unresolved-copy paths.
- Keep exact records and support for every comparison, conflict and uncertainty.
  Do not store the derived assessment as a SourceAssertion. Invalid or unsupported
  inputs need controlled diagnostics and complete original inspection.
- Positive located-measurement matching is unavailable until its input contract,
  source support and independent examples exist; do not fabricate new qualifiers
  on old Cards to make that test pass.

### Counts, votes and classes

The first candidate must expose record count, resolved copy-family/group count,
possible-correspondence scope and independence status separately. A group count
is not a count of independent experiments. Existing `measurement_count` requires
an explicit selected-policy definition and understandable caveat wherever shown;
adding a new field cannot silently change old field meanings.

Declared copies contribute no extra class vote when a non-copy original is
available. Review the current fallback that uses all members when no non-copy
record is present: an unresolved/copy-only set cannot be presented as independent
confirmation. Retain source classifications even when no justified combined
classification can be assigned. Do not silently drop or multiply records.

Uncertain correspondence must not acquire a confidence score through record
counting. Report effects on per-group classes, molecule strongest-band summaries,
discordance and ligand counters separately. B1's class @4 remains a concentration
band/abstention policy, not evidence of efficacy, assay comparability or ranking.

## Independent expected-outcome matrix

Write expected scientific outcomes before implementing the candidate. The
following are required categories, not passing tests or reviewed primary methods:

| Example | Expected conclusion |
| --- | --- |
| Explicit activity-copy link; unequal reported values | Same declared copy family, retained discrepancy and one original vote; no silent numeric repair |
| Unique original within a named assay | Copy relation with the exact selector and its limits, retaining source provenance |
| Named assay has two eligible originals | Ambiguous copy; neither silently selected |
| Copy origin absent; numeric match in another assay | Unresolved declared copy, no independent-confirmation claim |
| Same paper/molecule/type/value; methods absent | Possible correspondence, measurement identity and independence unestablished |
| Wild type/pH7 versus mutant/pH5 synthetic descriptions | No statement-based identity join; no claim that a general prose parser is validated |
| Equal descriptions; construct or endpoint absent | Context insufficient; textual equality does not establish one experiment |
| Stated incompatible construct/isoform/reference or endpoint | No unsupported statement join; exact conflicting statements inspectable |
| Rounded 62 versus 62.46 with otherwise matching inputs | Precision-compatible candidate only, unless separate support establishes the same measurement |
| Different molecule, unresolved molecule or target | No identity inferred from value/sequence/connectivity; keep original uncertainty/review |
| Equal normalized value under different unit policies | Value/unit/qualifier preserved; unit compatibility alone adds no identity support |
| Three-source chain and repeated records from one source | No transitive concealment of incompatible/unknown contexts or ambiguous originals |
| Original explicit @1 and saved full/index packet | Original scientific interpretation and exact stored payload retained without current recomputation |
| Empty, excluded, malformed or copy-only activity scope | Explicit applicability/completeness and controlled recovery; no invented absence or independent votes |

Add actual source-declared PubChem copy controls from existing public fixtures;
the two retained Cards above are insufficient for that category. Verify values,
units and original support under a non-default quantity policy. Measure all
eligible/included/excluded denominators and compare the same exact input pins.

## Human, agent and consumer adoption

The researcher should be able to answer: **"Are these two confirmations or two
records of possibly the same result?"** A short answer might be: "Two source
records may describe the same result. The retained context does not establish
whether they are the same measurement or independent experiments." It must offer
inspection of both measurements, assay context and original publication support.
Missing retained methods should lead to understandable inspection/recovery, not
an internal-schema explanation or a false negative result.

Compact agent output should expose the same state, basis, compared fields,
unknown/conflicting context and exact support, with bounded selection and access
to all candidates. B4 will carry it into rich exploration; direct B2 API answers
and explanations must already explain their own meaning. Review native activity
and ligand views, measurement/class explanations, tables, both comparison sides,
packets and versioned public examples together. Actual consumers own acceptance;
a stand-in or an older green CI run does not provide it.

First qualify an opt-in candidate with explicit original @1. Then compare actual
count/vote/class effects on frozen public inputs, obtain independent scientific
review and record the default/consumer decision. New packet/example meanings need
their own versions and genuine old controls. Current mapping @15 still uses
original measurement @1; it must not inherit a later default silently. New saved
readers require original data predating their verification, with scientific/source
calls forbidden while reading. Do not weaken frozen predicates.

## Next implementation and acceptance steps

1. Finish B1's exact-source receiving; retain its independent acceptance state.
2. Turn the matrix into independently specified positive/uncertain/conflicting
   controls and review precise selector/count/vote semantics. Implement a bounded
   opt-in candidate without changing @1 or current defaults.
3. Measure old/candidate answers on the same public inputs, including declared
   copies, actual downstream consumers and warning/resource/installed gates.
4. Obtain scientist feedback and explicitly adopt or revise the policy. Unknown
   primary methods block only their positive equivalence claim, not conservative
   uncertainty reporting or unrelated plan work.
5. Complete coherent consumer/versioned-packet and B4 human/agent/saved adoption;
   keep observed researcher acceptance separate from technical conformance.

Independent scientific acceptance, new external source access and 0.15.0
consolidation remain unclaimed; the original inventory and later candidate
qualification retain separate scopes.
