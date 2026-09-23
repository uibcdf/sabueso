<!--
CANONICAL MOLI GUIDE — component copies should remain synchronized.
Canonical source: https://github.com/uibcdf/moli/blob/main/MOLI_GUIDE.md
Platform architecture: https://github.com/uibcdf/moli/tree/main/architecture_1.0
-->

# MOLI component guide

This guide defines the shared governance rules for components of the MOLI platform.

## Where governance lives

Use `uibcdf/moli` for contracts, terminology, policies, and decisions that affect two or more MOLI components or the platform as a whole.

A component repository remains authoritative for its own implementation, tests, local API, scientific evidence, releases, and component-specific development decisions.

MOLI Platform Architecture 1.0 defines what the platform concepts mean. The MOLI development guide defines how repositories coordinate. Governance documents must not silently redefine frozen architecture.

## MOLI components

The authoritative registry is `moli.toml`. Initial MOLI components are:

- Sabueso — Knowledge context;
- Praxis — Methodological / Know-how context;
- Nextia — Discovery context;
- MolSysSuite — molecular modeling ecosystem;
- MOLI Agent — optional scientific reasoning and agency.

Scientific Context is a conceptual grouping of Sabueso, Praxis, and Nextia; it is not a separate component repository.

MolSysSuite is a MOLI component **with delegated internal governance**. MOLI governs MolSysSuite at the platform/component boundary and owns the shared MOLI engineering baseline. `uibcdf/molsyssuite` governs MolSysSuite's internal members, modeling-domain policies and contracts, adoption/rollout state, enforcement machinery, and explicit domain extensions of inherited engineering policy.

## Ownership rule

> **A concern is governed at the lowest level that owns the shared contract it affects.**

Examples:

- a Sabueso-only implementation bug → `uibcdf/sabueso`;
- a Nextia-only DiscoveryEngine bug → `uibcdf/nextia`;
- a Sabueso ↔ Nextia SourceAssertion/Evidence contract → `uibcdf/moli`;
- a Praxis ↔ Nextia Capability/Protocol invocation contract → `uibcdf/moli`;
- a TopoMT-only bug → `uibcdf/topomt`;
- a TopoMT ↔ MolSysMT shared contract → `uibcdf/molsyssuite`;
- a MolSysSuite ↔ Nextia platform contract → `uibcdf/moli`.

## Reporting bugs and proposals

Report a one-repository concern in the repository that owns it.

Report a shared MOLI-component/platform contract concern in `uibcdf/moli`. Cross-link component-local implementation issues where needed.

For concerns internal to MolSysSuite, follow MolSysSuite governance rather than duplicating them in MOLI.

Until MOLI adopts a more elaborate reporting lifecycle, GitHub issues are the stable identity for bugs/proposals. Durable analysis or decisions may be recorded under the owning repository's `devguide/`.

## Cross-component feedback

When work in one component exposes a missing or limiting capability in another:

1. report the need to the provider repository or its delegated governance domain;
2. include the consuming use case and why it matters;
3. cross-link local workaround or blocked work;
4. escalate to `uibcdf/moli` when the issue changes a contract between MOLI components or requires platform policy.

## MOLI engineering baseline

MOLI owns the shared engineering baseline for its repositories. Applicable policies are registered in `moli.toml` and documented under `uibcdf/moli/devguide/policies/`.

For repositories carrying the `python-package` capability, the baseline includes Python support, CI coverage, Ruff/pytest quality tooling, release-version semantics, repository badge evidence, and archival/DOI rules when applicable.

A component may add stricter local requirements. It must not silently contradict an applicable MOLI engineering policy; deviations require a tracked exception with rationale and an exit condition.

MolSysSuite inherits the MOLI engineering baseline and may add modeling-ecosystem-specific policies for its internally governed members.

## Architectural boundaries

Respect the frozen MOLI distinctions, including:

- Knowledge ≠ Know-how ≠ Discovery;
- SourceAssertion ≠ Evidence ≠ Provenance;
- Capability ≠ Protocol;
- DiscoveryProject ≠ DiscoveryEngine;
- Strategy ≠ Protocol; Campaign ≠ Protocol;
- Artifact ≠ Result ≠ Observation ≠ Evidence;
- semantic ownership ≠ visibility ≠ publication status;
- promotion ≠ publication.

If implementation pressure suggests changing one of these boundaries, open a platform proposal in `uibcdf/moli`.

## Visibility and confidentiality

A public repository may operate on private scientific content. Do not infer publication rights from semantic ownership or open-source code.

Cross-repository reports must not disclose confidential DiscoveryProjects, proprietary Protocols, molecular Candidates, unpublished Evidence, credentials, or restricted data.

## MolSysSuite internal governance

MolSysSuite's status as a MOLI component does not transfer governance of MolSysMT, TopoMT, MolSysViewer, DockingMT, or other MolSysSuite members to MOLI.

```text
MOLI
  └── MolSysSuite        governed by MOLI at platform boundary
        ├── MolSysMT
        ├── TopoMT
        └── ...           governed internally by MolSysSuite
```

Do not use MOLI governance to duplicate MolSysSuite's member-level rollout, enforcement, membership, modeling-domain contracts, or repository-local implementation policy. MOLI owns the shared engineering baseline; MolSysSuite owns how that baseline is adopted and enforced across its governed ecosystem, plus any explicit domain-specific extensions.

## Before finishing cross-component work

Ask:

1. Is the implementation change in the repository that owns it?
2. Did this expose a provider limitation that should be reported at its owning level?
3. Did it change a contract between MOLI components requiring a platform issue?
4. Does it preserve architecture, provenance, visibility, and authority boundaries?
5. Is any temporary workaround cross-linked to its owning issue?

Detailed policies belong in the canonical `uibcdf/moli/devguide/`.
