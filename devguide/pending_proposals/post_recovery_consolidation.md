---
summary: Consolidate recovered knowledge around safe input delivery and bounded scientific journeys.
issue: uibcdf/sabueso#112
status: active
opened: 2026-10-08
closed:
verification: measured
area: [architecture, source-access, documentation, integration, delivery]
blocked_by: []
supersedes: []
---

# Consolidation after local-work recovery

## Outcome and scope

The maintainer approved the five-step consolidation order from the
[global audit](post_recovery_global_audit.md). The implementation retains Sabueso's
knowledge boundary: source statements and explicit unknowns support Cards/Decks;
derived views name their rules; project Evidence remains Nextia's responsibility.
Provider breadth is not the scientific acceptance criterion.

This report describes the accumulated development checkout, not a new release.
The maintainer authorized its public code checkpoint after the local qualification.
Exact-SHA publication/CI receipts are added separately when complete. Published 0.13.0 and
frozen schema 0.3.12 are unchanged; development schema 0.3.13 remains unpublished.
There is no new schema change in this consolidation.

## 1. Fixture delivery

The exact 86 recovered input files were reviewed: **49 repository-delivery inputs**
and **37 local-only originals**. The [delivery inventory](../sources/fixture_delivery.json)
records paths, hashes, sizes, source terms and file-specific review bases. Local
originals remain unchanged and protected by `.gitignore`; the gate also refuses
forced staging, unreviewed new fixtures and stale source terms. An input-specific
PRIDE or OmniPath grant does not license arbitrary records from those providers.
DisProt's embedded quotation rights remain an explicit local-only boundary.

The default repository-input offline suite skips 25 original-dependent modules
before import and ten mixed native cases. Synthetic parsing/binding/axis tests
remain public. `--local-source-inputs` verifies all original hashes and opts into
their native qualification. Both scopes use the same editable Python 3.14
development environment, pytest-receptor and 12 workers. CI verifies the delivery
inventory before running the repository-input scope.

The absence exercise physically removes the 20 protected input directories from
`temp_data` for the public run, then restores them in `finally`. This proves the
public suite does not silently rely on locally available originals. It does not
qualify all providers' current online availability or future source terms.
See [fixture delivery](../sources/FIXTURE_DELIVERY.md) and [tests](../TESTS.md).

## 2. Guide structure

Complete prior versions of six entry documents are preserved in the
[dated archive](../archive/consolidation_2026-10-08/README.md), including historical
qualification receipts. Current guidance separates status, development order,
public API and common contracts from provider-specific access/mapping details.
The checkpoint is 134 lines at the structural checkpoint, previously 1,430;
the roadmap is 650 lines, previously 1,115. Common source/test guidance is 177
lines each. These are readability measurements, not code-quality scores.

Provider details remain accessible in the maintained
[native reference](../sources/NATIVE_ACCESS_REFERENCE.md),
[development API](../sources/DEVELOPMENT_API.md) and
[mapping conventions](../sources/NATIVE_MAPPING_CONVENTIONS.md).
The foundational and pilot-driven routes and the approved post-0.13.0 sequence
remain intact. Private consumer requirements are described only generically.

## 3. Explicit source capability scope

`tools/source_registry.py` generates a capability view from actual native
getters/mappings, client implementations, declared enrichers and reviewed recovery
inputs. It is packaged in the development metadata catalog and shown in the
[user capability table](../../docs/content/user/source_capabilities.md).
The rule is `source_capability_inventory@1`; generated freshness and declaration
wiring are tested. Catalog reads make no provider calls.

The registry still has 83 `in_use` resources and 24 declared enricher instances.
Native access is distinct from declared card contribution. AST counts exclude
aliases; bespoke existing enrichment routes are not inferred from the declared
registry alone. Input counts describe the reviewed recovery set, not all fixtures.
Live health, consumer acceptance and scientific completeness are explicitly
unassessed by this inventory. No resource is automatically queried or integrated
just to make the table uniform.

## 4. Bounded scientific integration

The protein/comparator journey now saves source-active-site residue context and
selected composition in example format `sabueso.protein_comparison_example@2`.
The caller selects completely supported annotations under
`source_active_site_selection@1`; composition retains `residue_set_composition@1`.
TcTIM selects canonical positions 96/168; HsTIM selects 96/166. Each yields one E
and one H on its own source-supported sequence axis. Those equal compositions
and overlapping residue numbers do not establish a correspondence or selectivity.

Both roles retain exact Card/SourceAssertion pins. The independent reader checks
stored bindings, original sequences and annotation statements without running
residue readers/composition rules, acquiring sources or registering fresh credit.
Reacquisition advances heads while original reports and pins remain readable.
Ten tampering cases exercise missing/altered/misbound original artifacts and new
residue contexts. The reader accepts original `@1` bundles without adding residue
context or filling their historical gaps. A genuine pre-edit `@1` bundle was
retained for guarded independent replay in addition to the structural compatibility
regression. Derived residue operations still lack dedicated execution sidecars;
the report states that gap rather than implying complete runtime observation.

The existing molecule/target and disease/entity journeys remain separate regression
routes. New source readers are selected for integration by a concrete scientific
question, source-stated identity and applicable terms. The larger clinical study
bibliography, non-protein packets, peptide identity and complete derived-operation
observation remain the bounded roadmap work; this slice does not close them.

## 5. Consumer coordination and cost

MOLI's report incorrectly left pinned-item integrity pending although Sabueso #79
was implemented and published in 0.5.0. The ready documentation correction is
[MOLI PR #65](https://github.com/uibcdf/moli/pull/65), submitted as a draft for
owner review; MOLI's governance validator passed against the proposed report.
It preserves the open grammar, retention, remote resolution and consumer Evidence
decisions. There was no direct push to MOLI main and no private pilot material.

Remote Nextia README and [Nextia #1](https://github.com/uibcdf/nextia/issues/1)
still describe the initial persistent DiscoveryProject/Evidence slice. A concrete
persistent consumer exercise is therefore not claimed. Nextia owns interpretation;
MOLI #3/#22/#36 own shared reference/query/recording decisions, with Sabueso
#53/#71/#108 carrying provider adoption and implementation. Independent SDK
acceptance continues without inventing a replacement consumer or a stable shared
contract. Owner-local feedback links this consolidation to those existing issues.

Measurements use separate Linux/Python 3.14 processes and the existing development
environment. Elapsed time includes imports; peak RSS is process-local and includes
the complete example, not just the new residue reader. This is a single bounded
run, not a release-performance guarantee. Original reports, support and execution
sidecars are retained in full. The measured artifact/support costs will inform
future #98/#100 work; this does not justify an unmeasured cache/parser rewrite.

| Process | Elapsed, including imports | Peak RSS |
| --- | ---: | ---: |
| Genuine pre-edit `@1` independent reader | 4.15 s | 187.7 MiB |
| Current `@2` producer | 16.65 s | 187.2 MiB |
| Original-only independent reader | 4.96 s | 190.9 MiB |
| Reacquisition | 17.30 s | 184.2 MiB |
| Independent reader of both retained stages | 9.17 s | 228.0 MiB |

The current original report is 18,099,826 bytes; observations are 7,357,513 bytes,
workflow attribution 3,784,676 bytes, and each packet attribution 2,795,886 bytes.
The two residue contexts occupy 5,739/5,713 bytes in compact JSON. The SQLite store
after both acquisitions is 6,279,168 bytes. Preserved support and runtime sidecars
dominate this bounded example. Compare scientific scope and inspect redundant
representations before choosing a future optimization; dropping original support
is not an acceptable size reduction. The genuine `@1` scientific JSON files were
byte-identical after guarded reading. Machine-readable
[measurement receipt](post_recovery_consolidation_costs.json).

MOLI PR #65's governance CI passed at exact head
`1f7052fa1fd982a02e40e8453cb8121d3b1be095`, inspected with gh-run-receptor:
[run 37810530518](https://github.com/uibcdf/moli/actions/runs/37810530518).
One governance job passed; default-branch coverage publication was intentionally
skipped for the PR. This CI qualifies that documentation fix, not Sabueso's tree
or acceptance of the shared contract.

## Current verification

The new protein journey selected gate passed **14 tests / 73.01 s** with receptor
and 12 workers. Registry, fixture-delivery, recorded shape, schema, dependency
routes and Ruff gates passed. The original public-input absence checkpoint passed
4,010 tests with ten explicit native skips before the subsequent catalog/journey
changes. Older checks do not qualify subsequent code edits.

The final repository-input absence scope passed **4,021 tests / 130.19 s**, ten
explicit native skips and ten expected fixture warnings. All 20 directories were
restored; all 37 protected originals passed their digest gate afterwards.
The final verified local-original scope passed **5,574 tests / 164.11 s**, ten
expected fixture warnings and no skips, through pytest-receptor with 12 workers.
The public and local scopes both cover the protein, molecule/target and disease
independent journeys. The difference is 1,543 native-only module cases plus ten
mixed native cases; it does not remove their full local regression coverage.

Warning-failing Sphinx HTML passed, including the new capability/journey pages.
The changed/new Markdown set has 405 checked local file targets and none missing.
All 87 historical originals and every corresponding backup member match their
recorded hashes; the backup archive's hash/size is unchanged. The stash is empty,
private pilots remain clean/read-only, and the local MOLI guide matches its
canonical checkout copy. Published 0.3.12 schema/shape/frozen cards are unchanged.
Ruff checks/formatting, registry freshness, recorded shape, schema paths,
dependency routes, MOLI governance and `git diff --check` passed individually.
Machine-readable [local checkpoint](post_recovery_consolidation_checkpoint.json)
records the tested Python file-set digest, input inventory, test scopes and remote
documentation CI identity. It is a local receipt, not an immutable commit or release.

## Remaining acceptance

- Revalidate current private MOLI consumer workflows after the code checkpoint's
  CI under [#132](https://github.com/uibcdf/sabueso/issues/132), preserving private
  content and original results. SDK receipts are not real-consumer acceptance.
- Create reviewable Sabueso code checkpoints and verify exact-SHA CI before remote
  qualification; qualify installed artifacts/platforms separately before release.
- Requalify protected originals only when their exact delivery conditions are met.
  Their local native regressions remain useful without distributing the inputs.
- Review MOLI PR #65 and decide the shared contracts with real consumer owners.
- Continue the approved bounded scientific roadmap and measure larger workloads
  before optimizing retention or repeated original support.
