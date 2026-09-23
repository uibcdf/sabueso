<!--
CANONICAL MOLI GUIDE — component copies should remain synchronized.
Canonical source: https://github.com/uibcdf/moli/blob/main/MOLI_GUIDE.md
Platform architecture: https://github.com/uibcdf/moli/tree/main/architecture_1.0
-->

# MOLI component guide

This guide defines the shared governance rules for repositories directly governed by the MOLI platform.

## Where governance lives

Use `uibcdf/moli` for contracts, terminology, policies, and decisions that affect two or more directly governed MOLI components or the platform boundary as a whole.

The component repository remains authoritative for its own implementation, tests, local API, scientific evidence, releases, and component-specific development decisions.

MOLI Platform Architecture 1.0 defines what the platform concepts mean. The MOLI development guide defines how repositories coordinate. Do not use governance documents to silently redefine frozen architecture.

## Directly governed components

The authoritative registry is `moli.toml`. Initial directly governed repositories are:

- Sabueso — Knowledge context;
- Praxis — Methodological / Know-how context;
- Nextia — Discovery context;
- MOLI Agent — optional scientific reasoning and agency.

MolSysSuite is a delegated governance domain. Its internal component governance belongs to `uibcdf/molsyssuite`.

## Ownership rule

> **A concern is governed at the lowest level that owns the shared contract it affects.**

Examples:

- a Sabueso-only implementation bug → `uibcdf/sabueso`;
- a Nextia-only DiscoveryEngine bug → `uibcdf/nextia`;
- a Sabueso ↔ Nextia SourceAssertion/Evidence contract → `uibcdf/moli`;
- a Praxis ↔ Nextia Capability/Protocol invocation contract → `uibcdf/moli`;
- a TopoMT-only bug → `uibcdf/topomt`;
- a shared MolSysSuite component contract → `uibcdf/molsyssuite`;
- a Scientific Context ↔ MolSysSuite platform contract → `uibcdf/moli`.

## Reporting bugs and proposals

Report a one-repository concern in the repository that owns it.

Report a platform/shared-contract concern in `uibcdf/moli`. Cross-link any component-local issue needed for implementation.

Do not duplicate the same authoritative issue across repositories. Use links to express dependencies and implementation work.

Until MOLI adopts a more elaborate reporting lifecycle, GitHub issues are the stable identity for bugs/proposals. Durable analysis or decisions may be recorded under the owning repository's `devguide/`.

## Cross-component feedback

When work in one component exposes a missing or limiting capability in another:

1. report the need to the provider repository;
2. include the consuming use case and why it matters;
3. cross-link any local workaround or blocked work;
4. escalate to `uibcdf/moli` only when the issue changes a shared platform contract or requires coordinated policy.

Provider ownership determines implementation ownership; it does not remove the discovering component's responsibility to communicate the need.

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

If implementation pressure suggests changing one of these boundaries, open a platform proposal in `uibcdf/moli` rather than changing a component silently.

## Visibility and confidentiality

A public repository may operate on private scientific content. Do not infer publication rights from semantic ownership or open-source code.

Cross-repository reports must not disclose confidential DiscoveryProjects, proprietary Protocols, molecular Candidates, unpublished Evidence, credentials, or restricted data. Use sanitized reproductions or private channels when necessary.

## MolSysSuite boundary

MolSysSuite governs its modeling ecosystem. MOLI governs only platform-level contracts crossing that domain boundary.

Do not use MOLI governance to duplicate MolSysSuite's Python, CI, release, membership, or component-level policies.

## Before finishing cross-component work

Ask:

1. Is the implementation change in the repository that owns it?
2. Did this expose a limitation in another component that should be reported there?
3. Did it change a shared MOLI contract requiring a platform issue?
4. Does it preserve architecture, provenance, visibility, and authority boundaries?
5. Is any temporary workaround cross-linked to its owning issue?

This guide should remain concise. Detailed policies belong in the canonical `uibcdf/moli/devguide/`.
