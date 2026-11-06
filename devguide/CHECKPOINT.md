# Sabueso — Checkpoint

Current working-state checkpoint: **2026-11-06**. Start with
[ONBOARDING](ONBOARDING.md) for project context and the
[workstation handoff](WORKSTATION_HANDOFF_20261106.md) for moving this checkout.
This page owns current state; dated receipt histories are linked below.

Destination restoration and complete local offline baseline receiving are complete. The
[destination review](evidence/destination_review_20261106.json) records the new
workstation, reproduced CI failures and parallel calibration; the subsequent
[corrected checkpoint](evidence/destination_checkpoint_20261106.json) records
their repair and 9,276 distinct passing local cases at the source blobs committed
as `7ec81ce`. Its hosted receiving subsequently exposed a Windows-only test
fixture encoding error; the
[UTF-8 follow-up](evidence/windows_chemical_fixture_recovery_20261106.json)
has targeted local receiving and still needs its own hosted result. Continue from the
[current action plan](CONTINUATION_PLAN_20261104.md#destination-review-and-next-actions),
not the original transfer checklist.

## Published and development state

| Scope | Current state and evidence |
| --- | --- |
| Published package | **0.14.0**, source/tag `78623d0`; installed OS/Python gates, public install and Zenodo archive are recorded in the [release receipt](../devtools/conda-build/receipts/sabueso_0.14.0_public_2026-10-09.json) |
| Published schema | **0.3.13**; published versions, shapes and frozen Cards remain immutable |
| Development schema | **0.3.14**, unpublished, 1,985 recorded paths; see [SCHEMA](SCHEMA.md), migrations and the shape gate |
| Packet mapping | Current development default **`packet_aspects@16`**, as declared in `sabueso/core/packets.py`; original mappings retain their own meanings. Packet mapping, Card schema and exploration file format are separate versions |
| Code checkpoint | `7ec81ce` commits the complete public/composed local baseline: 9,276 distinct passed, with [exact hashes](evidence/destination_checkpoint_20261106.json) against transferred parent `0e4d7d4a80e3a32437acea25204bef80b185f981`. The later UTF-8 correction changes three test-helper I/O calls only; runtime, schema and original controls remain identical. Its own hosted qualification remains pending |
| Producer labels | The full local checkpoint ran with imported/distribution/generated label `0.14.0+197.g0e4d7d4` and changed source bound separately by hashes; that label is not a clean producer claim for the correction. Stale source-root egg-info remains preserved outside the import path. Original SDK192/SDK193 controls retain their original labels |
| Saved reading checkpoint | Chemical semantic @15 and sharing @16 are committed with 705 selected local cases plus independent whole-session receiving; exact-final-source hosted, artifact, scientist and researcher acceptance remain separate |
| Machine migration | All 10,654 declared payload files were restored and independently hash-verified, including 37 protected originals. Both ZIPs and auxiliary staging were removed at the maintainer's request. Retained manifests/receipts remain local; the active released receptor checkout is now `../pytest-receptor-1.2.0` |
| Hosted receiving | For `7ec81ce`, governance, Ruff, all four Linux source lanes and all four installed public-Ackredit lanes pass. The first captured Windows source lane fails four tests from one implicit-encoding helper defect; macOS jobs remain queued. The follow-up does not relabel this source as qualified. Original `0e4d7d4` and earlier failed runs retain their own receipts |
| Release target | **0.15.0**, the full agreed exploration design and validated human experience; [consolidation](pending_proposals/release_consolidation_0150.md) remains paused. No release/tag/freeze/staging is authorized |

## Latest implementation and qualification

The [chemical profile contract](pending_proposals/chemical_classification_exploration.md)
connects source-bound native classification, readable molecule classes/roles,
compact typed agent selection and original source/open/back routes. Chemical
membership or a source-stated role does not establish target activity or efficacy.
The locally validated saved checkpoint preserves original native inputs/interpretation, exact
executed requests, typed flags, uncertainty and navigation under independent
original reading. Original scientific rules and earlier saved formats stay fixed.

| Receiving scope | What is actually established |
| --- | --- |
| Earlier candidate | 81 native/live/saved and 428 adjacent cases passed, **before** the extra literal metadata correction; 509 distinct cases are not final-current-source qualification |
| Corrected literal routes | 14 focused regressions pass, including false/null/array metadata, source-looking names, related/back continuity and refusal of a resealed scientific-manifest claim |
| Registry/licensing/delivery | 57 cases and fixture/registry/schema/governance tools pass on the committed source blobs; shape and warning-fatal Sphinx also pass |
| Static checks | Complete root Ruff format/check pass; guide links/examples retain their own scoped receiving |
| Complete corrected source | **95 passed**: saved 38 + live 27 + native 30; source blobs match committed `0f197e5` |
| Historical scientific reading | **123 passed**, three separate 41-case modules. The earlier combined host-reserve stop remains a failed historical attempt |
| Copied payload | Both outer isolated consumers pass, with nested saved 38 and live 27 cases; nested counts are not added to distinct totals |
| Frozen original controls | 101 original files rechecked byte-identical; original SDK192/SDK193 capsules retained. Never regenerate them to make a newer reader pass |

The [new local checkpoint receipt](evidence/chemical_saved_checkpoint_20261106.json)
records **705 distinct selected cases**, source blob identity, separate gates and
public whole-session save/read/resave: two molecules, 114 source/context routes,
zero source queries and preserved original science. All guards observed zero owned
swap. The saved agent page comparison follows resolved typed nodes and values;
opaque session-local lookup tokens are not portable global IDs.

The [earlier candidate receipt](evidence/chemical_saved_candidate_20261106.json)
and [literal routing report](pending_bugs/chemical_literal_metadata_routing.md)
preserve the original stopped/failing and narrower receiving scopes. Do not rewrite
those observations as success. Independent scientist/researcher/consumer and
exact-final-source hosted qualification remain open.

<a id="destination-receiving-and-current-regressions"></a>

## Destination receiving and corrected regressions

The final destination gate passes **95 chemical cases plus two outer copied
consumers**. Their nested 38/27-case runs and an initial repeated 95-case run are
not additional distinct cases. Pip closure, original fixture delivery (81 public
plus 37 protected), registry, schema, governance and C/Rust toolchain checks pass.
Full shared-suite receiving remains incomplete for missing/noninstalled siblings;
this does not invalidate the declared Sabueso scope or certify the whole suite.

The review reproduced **eight failures** locally in 1.98 s: seven older no-row
filter expectations contradicted the explicit current #191 refusal contract, and
one experimental-layout refusal reached display validation before reporting its
unsupported format. The correction retains explicit no-row refusal and adds
logical-format admission after wrapper decoding/resource checks, before display
inspection. The old eight cases and five new malformed/unknown-format controls
pass. Frozen verifiers, scientific rules, original source inputs and schema stay
unchanged. The [review receipt](evidence/destination_review_20261106.json)
preserves the failures; the
[new checkpoint receipt](evidence/destination_checkpoint_20261106.json) owns the
subsequent result.

The complete public scope has **7,723 passed and 10 expected local-input skips**.
The local-original increment has **1,553 passed**, including those ten cases;
exact node accounting establishes **9,276 distinct passed** for the composed
local scope. This is not two independent full-suite executions. All 26 online
cases remain deselected, and nested copied-consumer cases are not added again.
The public parallel phase reports 13 warnings from intentional acquisition
failure/truncation controls; the other phases report none. All phases stay within
their declared resource limits with zero owned swap. B3's actual MolSysMT journey
passes all 28 cases, including positive, uncertain and incompatible contexts;
independent scientist/researcher acceptance remains open.

The workstation exposes 20 physical cores and 60.516 GiB RAM, without an observed
cgroup CPU/RAM quota. Eight-worker calibration passes the same 95 chemical cases
in 23.57 s at about 1.013 GiB peak owned-tree RSS and zero owned swap. The earlier
serial observation is 60.42 s; this warm, nonrandomized comparison does not
qualify every workload. Use the [current profiles](TESTS.md#current-workstation-profile).

## Resume here

1. Preserve the corrected source/test hashes and complete local checkpoint above.
   Keep the original failed review and historical scientific controls unchanged.
2. Complete the UTF-8 test follow-up's hosted CI/governance through the applicable
   authorized route. Earlier passing receipts, local calibration and queued jobs
   do not establish a green exact-source matrix or installed-artifact acceptance.
3. Continue B3's remaining structural transitions and independent acceptance from
   its passing finite MolSysMT gate, then implement the B4–B6
   journeys in the [current plan](CONTINUATION_PLAN_20261104.md#destination-review-and-next-actions).
   The broad inventory and scientist/researcher gates remain required; B2 review
   is still explicitly deferred and B8 publication remains paused.

### Windows test-fixture follow-up — 2026-11-06

CI `42304034292` at `7ec81ce` reveals three chemical original-reader cases that
write unescaped Unicode through the Windows CP1252 default; the copied-payload
outer case consequently fails too. The runtime reader already uses UTF-8.
Explicit UTF-8 on two test writes and one test read preserves the original
capsule bytes, values and all scientific assertions. A bounded CP1252 pathlib
reproduction fails the same three cases before the correction; all **27 owning
cases pass** afterwards, and the **one isolated copied gate passes** with its
nested 27 cases. Nested counts are not added to distinct totals. Ruff passes.
The [follow-up receipt](evidence/windows_chemical_fixture_recovery_20261106.json)
records this narrower scope, not a new complete-suite run or Windows OS emulation.
The library source remains byte-identical to the 9,276-case baseline; a new
exact-source Windows/hosted checkpoint is still required.

## Open work and boundaries

| Block | Current position / next obligation |
| --- | --- |
| B0/B1 | Preview and conservative activity corrections are in technically qualified earlier checkpoints, including accumulated `c5b8af1`; independent scientific/consumer acceptance remains separate |
| B2 | Opt-in measurement correspondence @2 and copy-aware target scope @2 exist; original @1 defaults remain. The maintainer's [six-case scientific review](pending_proposals/measurement_correspondence_review_20261104.md) is explicitly deferred; no default adoption follows from more tests |
| B3 | The accepted [bounded positive/uncertain MolSysMT gate](pending_proposals/structural_journey_acceptance_20261104.md#accepted-assembly-scope--2026-11-06) passes all 28 destination cases. Remaining structural transitions and independent scientific/researcher/workload acceptance stay open |
| B4 | Rich activity/group/measurement/assay/document and shared literature journeys remain required, respecting B1/B2 semantics |
| B5 | Continue from the local chemical checkpoint to independent acceptance and the remaining molecule, clinical and disease profiles, positive/uncertain public tasks and human/agent/saved parity |
| B6 | Rich variant/isoform/tissue/comparative and association profiles remain required with exact supplied identity/axis/source context |
| B7 | Scientist, uncoached researcher, agent, workload, private-pilot and actual-consumer acceptance remain open; passing tests alone cannot establish the wow experience |
| B8 | Consolidation/publication stays paused until accepted scope, preceding gates and maintainer resumption; the release is not authorized by migration |

## Inputs, environment and retained resources

The [historical handoff manifest](evidence/workstation_handoff_20261106.json)
records the transferred source, original controls, protected input hashes and
participating checkout identities. Its documentation hashes describe the original
snapshot; later guide edits do not authorize regenerating that proof.
The fixture inventory currently declares 81 repository inputs and 37 local-only
originals; the originals are private transfer material under their existing terms.
Keep private pilots and external-report drafts within their disclosure authority.

All Sabueso/participating installed workspace packages use local editable sources
in compatible Python 3.14 development. Installed-artifact qualification is separate.
Current destination/cleanup evidence is retained under
`recovered_work/destination_receiving_20261106/`; this review's probes and logs are
under `recovered_work/devguide_review_20261106/`. Corrected complete receiving is
under `recovered_work/checkpoint_recovery_20261106/`, owned by #112/#148/#191
with a retention note. Historical paths/session IDs are not current jobs. Clean only
owned disposable output after actual jobs terminate.

## History and evidence

The [full preceding checkpoint](archive/CHECKPOINT_before_onboarding_20261106.md)
preserves every former receipt and dated pending/source statement. The
[2026-11-04 audit](GLOBAL_AUDIT_20261104.md) remains a dated review; the continuation
plan owns follow-through. Feature contracts/receipts and [DECISIONS](DECISIONS.md)
explain individual changes. Earlier qualified sources such as `c5b8af1` and
`913aad1` keep their exact evidence; qualification never transfers automatically
to the current working candidate.
