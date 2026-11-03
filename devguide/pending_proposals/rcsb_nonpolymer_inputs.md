---
summary: Original nonpolymer identifiers before assembly reconciliation.
issue: uibcdf/sabueso#173
status: open
opened: 2026-11-03
verification: owning_offline_qualification
area: [source-access, structural-context, human-exploration]
---

# Original nonpolymer instance inputs

The previous RCSB query retained nonpolymer component descriptions and investigation
scores, but did not request native instance identifiers. Polymer neighbor references
are a different basis; matching a component code or author chain label cannot
promote them into complete instance records or physical assembly membership.

The [RCSB entity schema](https://data.rcsb.org/rest/v1/schema/nonpolymer_entity)
defines entry/entity identifiers and native versus author instance lists. The
[instance schema](https://data.rcsb.org/rest/v1/schema/nonpolymer_entity_instance)
defines native `asym_id`, separate `auth_asym_id`, entry/entity/component IDs and
author residue numbering. Record IDs have distinct entry/entity and entry/instance
forms. These fields establish no identity across entries, assertions or revisions.
The [Data API](https://data.rcsb.org/#graphql-api) exposes this source through
REST and GraphQL; both schema inputs were reviewed on 2026-11-03.

## Acquisition and storage

Single, batch and polymer-instance-feature fallback queries additionally request
`assembly_nonpolymer_entities: nonpolymer_entities`, with native entity/instance
record IDs, entry/entity IDs, component IDs and separate label/author identifiers.
The existing ligand-summary/contact query stays independent. No matrices,
translations or geometry are acquired or computed.

When this dedicated GraphQL alias exists, unpublished schema 0.3.14 stores its
complete requested value at `asserted_value.assembly_component_inputs.nonpolymer_entities`
in the supporting RCSB SourceAssertion. Native record order, duplicates, null,
empty and unsupported values remain literal and detached from callers. A missing
alias adds no field. Legacy ligand summaries never reconstruct the new inputs.
Source revision and retrieval remain bound to the same assertion. No pooling
across source assertions or revisions is performed.

`SCHEMA_CHANGES` marks the addition explicit-only. Loading/migration do not fill
historical inputs; refresh acquires a new source basis, retaining the old Card/pin
when a store is supplied. Published schemas, old fixtures and historical stored
Cards remain unchanged. Shape recording is required even though asserted values
are opaque to its path inventory; no normalized biological field is added.

## Exploration and scientific limits

The structure's existing source link opens its supporting statement and the new
input field when retained. Human literal inspection, compact typed locations and
saved reading expose the same original records. Reopening does not acquire,
remap or calculate a new correspondence. Unsupported input remains inspectable.

This is input delivery, not a completed scientific panel. Native generation
@1–@4, component/operator and occurrence rules remain unchanged: even with the
new field, original neighbor references stay `referenced` under @4. The following
[opt-in generation @5 / component-key @2](assembly_nonpolymer_binding.md) now reads
that native instance basis. Its independent saved verification must qualify
adapter adoption; default @4 and existing saved readers remain unchanged. Other component roles remain unknown. Neither source membership
nor declared occurrences establish physical uniqueness, contacts or biological
relevance. Full #173 reconciliation and broad #148 acceptance remain open.

## Public qualification and resource ownership

`temp_data/rcsb_nonpolymer_instances/` holds separate captures for already tracked
public controls 1SUX, 2V5B and 1HTI. Exactly three attempts returned 61,728 complete
response bytes on 2026-11-03 UTC. The prepared scope allowed six attempts,
20 seconds each within 120 seconds, 2 MiB per response/8 MiB total and no secondary
queries. No confidential pilot content entered requests or fixtures.

Exact request/response bytes and decoded/re-encoded entries are distinguished.
The capture index records hashes, UTC retrievals, native revisions and acquisition
traces. Its SDK148 metadata describes the capture host before the source commit;
the actual executed working-tree query is bound to its exact scope digest and
stored request bytes, not retrospectively relabeled as a published query.
[The notice](../../temp_data/NOTICE.md) and
[delivery inventory](../sources/fixture_delivery.json) record data CC0 terms,
authored metadata and credit, verified against the
[RCSB usage policy](https://www.rcsb.org/pages/usage-policy).

1SUX retains SO4 instances C–I and BTS instance J; 1HTI retains PGA instance C,
author label B and author residue 549. 2V5B's new field is null; it does not
establish an empty assembly or the role of generator label B. No missing label is
completed from a description or composition.

Owning tests cover exact wire/query identity, native IDs/revisions, null/missing
and unsupported input, immutability, unchanged qualifiers, query fallback scope,
unchanged native @4 interpretation, refresh versus inert migration, original store
retention and independent human/compact saved reading. Historical request tests
now bind to their original capture's query digest, rather than today's query.
Selected source/native/persistence/schema/fixture gates and an unskipped exact-source
hosted checkpoint qualify this change. Pending/cancelled runs never qualify it.
This does not complete #173, #167 workload acceptance or paused 0.15.0 consolidation.

Owner #173/#148/#112; useful capture/source/gate proof stays under
`recovered_work/rcsb_nonpolymer_inputs_173_20261103/` until native interpretation
review or pre-0.15.0. Original committed fixtures remain owned here. Remove
completed test/build scratch and redundant capture copies after their last use.

The local qualification helper initially added a 256 MiB `MemFree` refusal floor.
Three storage invocations stopped on that heuristic despite at least 15.55 billion
bytes `MemAvailable`, owned RSS below 185 million bytes and zero owned swap. These
are incomplete observations, not passing gates. The owned helper was corrected
explicitly to use the kernel's available-without-swapping estimate, retaining a
4 GiB available floor, 1 GiB owned RSS ceiling, zero owned swap, 2 GiB scratch and
serial execution. True free RAM remains measured. See the
[kernel definition](https://docs.kernel.org/filesystems/proc.html#meminfo).
The original selection is rerun under this separately recorded guard; earlier
receipts are not relabeled. This corrects a local development heuristic, not a
Sabueso runtime budget or an institutional working instruction.

The final selected local gates pass **617 cases across 25 files** in four serial
receptor invocations (41 + 79 + 263 + 234; 345.29 pytest seconds). Peak owned RSS
is 318,590,976 bytes, minimum host available RAM 15,695,187,968 bytes and owned swap
zero. The entire 234-case storage selection passes on its new invocation; no
stopped prefix is counted. Shape recording retains exactly 1,967 paths, with no
shape diff. All 98 preceding delivery rows and existing source fixture bytes are
unchanged; 67 checked native mapping/policy/verifier files remain byte-identical.
Warning-fatal Sphinx, Ruff, source-registry, fixture-delivery, schema alignment, local governance and
Markdown/Python gates pass. Final-source hosted qualification remains pending
until actual full receptor receipts are reviewed.
