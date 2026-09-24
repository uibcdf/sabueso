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

Everyone who uses, develops, maintains or operates a MOLI component or UIBCDF support tool must communicate actionable bugs, missing capabilities, improvement opportunities and new feature proposals through the owning GitHub issue. Open a new issue or add concrete evidence to an existing one. This applies equally to Sabueso, MolSysSuite members, pytest-receptor, gh-run-receptor, the Conda build/upload and Sphinx-to-Pages actions, and future repositories. If you cannot open an issue, ask the responsible maintainer to record it. Do not leave the finding only in a chat, local workaround or downstream repository. Reporting does not promise immediate implementation. Follow [MOLI's issue-feedback rule](https://github.com/uibcdf/moli/blob/main/devguide/governance/reporting_protocol.md#universal-issue-feedback-commitment); use private security reporting for exploitable or confidential findings.

Report a one-repository concern in the repository that owns it.

Report a shared MOLI-component/platform contract concern in `uibcdf/moli`. Cross-link component-local implementation issues where needed.

For concerns internal to MolSysSuite, follow MolSysSuite governance rather than duplicating them in MOLI.

GitHub issues are the stable identity for bugs/proposals. Durable analysis or decisions may be recorded under the owning repository's `devguide/`; small findings need no extra report.

## Cross-component feedback

When work in one component exposes a missing or limiting capability in another:

1. report the need to the provider repository or its delegated governance domain;
2. include the consuming use case and why it matters;
3. cross-link local workaround or blocked work;
4. escalate to `uibcdf/moli` when the issue changes a contract between MOLI components or requires platform policy.

## UIBCDF development infrastructure supporting MOLI

UIBCDF maintains four shared resources used by MOLI development. They are [registered separately from scientific components](https://github.com/uibcdf/moli/blob/main/devguide/governance/support_infrastructure.md). Use each where its boundary applies:

| Resource | Use | Report a defect or improvement |
| --- | --- | --- |
| [Pytest Receptor](https://github.com/uibcdf/pytest-receptor) | Python test output for agents and CI | [Provider issues](https://github.com/uibcdf/pytest-receptor/issues) |
| [GH Run Receptor](https://github.com/uibcdf/gh-run-receptor) | Inspect Actions run evidence | [Provider issues](https://github.com/uibcdf/gh-run-receptor/issues) |
| [Conda build/upload action](https://github.com/uibcdf/action-build-and-upload-conda-packages) | Build and publish Conda packages | [Provider issues](https://github.com/uibcdf/action-build-and-upload-conda-packages/issues) |
| [Sphinx-to-Pages action](https://github.com/uibcdf/action-sphinx-docs-to-gh-pages) | Publish Sphinx docs to GitHub Pages | [Provider issues](https://github.com/uibcdf/action-sphinx-docs-to-gh-pages/issues) |

The provider owns its tool, while MOLI owns shared usage policy and MolSysSuite owns member adoption. The receptors also remain MolSysSuite auxiliary members. Link provider issues from any blocked consumer work. A repository without the relevant test, release or documentation route need not add that tool.

## MOLI engineering baseline

MOLI owns the shared engineering baseline for its repositories. Applicable policies are registered in `moli.toml` and documented under `uibcdf/moli/devguide/policies/`.

For repositories carrying the `python-package` capability, the baseline includes Python support, CI coverage, Ruff/pytest quality tooling, applicable UIBCDF support libraries, developer receptors, distribution, release-version semantics, repository badge evidence, and archival/DOI rules when applicable.

Review public API contracts for ArgDigest, optional or heavy dependencies for DepDigest, user-facing diagnostics for SMonitor, and physical quantities for PyUnitWizard. Use each library where its boundary exists; record justified non-applicability or a bounded exception in the component's review issue. Follow [MOLI's support-library policy](https://github.com/uibcdf/moli/blob/main/devguide/policies/python_support_libraries_policy.md) for the exact applicability rule.

## Physical quantities and units

Treat a wrong unit as a scientific correctness failure. A quantity must keep its value, unit and meaning through calculation, storage and communication. Serialized values carry their negotiated unit inside the same object; readers verify the record and explicitly state the expected field and unit or dimension. Never guess from a bare number, field name or session default. Name boundary conversion units explicitly, and test under a non-default unit policy. A consistent but wrongly labelled source also needs domain or cross-source checks. Follow [MOLI's quantity integrity policy](https://github.com/uibcdf/moli/blob/main/devguide/policies/quantity_integrity_policy.md).

PyUnitWizard owns the serialization design and codec. Read its [design record](https://github.com/uibcdf/pyunitwizard/issues/83) and [QuantityRecord implementation](https://github.com/uibcdf/pyunitwizard/issues/82) before designing a persisted representation; Sabueso is the first consumer. Components track their own schema migration and applicable format support. MOLI tracks the shared [quantity contract](https://github.com/uibcdf/moli/issues/12), while MolSysSuite tracks its member adoption.

When an agent runs Python tests, use the published pytest-receptor with `--receptor=llm`; use `--receptor=ci` in pytest CI logs. Use a published gh-run-receptor as the preferred first inspection of Actions runs, with GitHub conclusions authoritative and native `gh run view` as fallback. Follow [MOLI's developer-tools policy](https://github.com/uibcdf/moli/blob/main/devguide/policies/python_developer_tools_policy.md) for versions, safeguards, and exceptions. These developer tools are not runtime dependencies.

The official user-installation route for a public Python component is the `uibcdf` Conda channel with third-party packages from `conda-forge`. A public PyPI route is optional, needs a documented reason, and may be claimed only after its published package and complete dependency closure pass clean-install verification; pytest-receptor uses PyPI for pytest plugin discovery. Install a local checkout for development with `pip install --no-deps --editable .` after provisioning its Conda environment; this is not publication. Keep development and test environments in `devtools/conda-envs/`, align required runtime dependencies between `pyproject.toml` and the Conda recipe, and build public Conda packages through the shared UIBCDF action. Required CI must acquire Conda-only third-party dependencies through a resolvable Conda environment; a tracked, full-commit source route may cover a sibling version unavailable on the configured channels for tests. Follow [MOLI's distribution policy](https://github.com/uibcdf/moli/blob/main/devguide/policies/python_distribution_policy.md) for recipe, CI and release evidence. Do not advertise an unpublished package or channel.

When registering a new direct Python component, declare its `python-package` capability and `python_ecosystem_review` and `python_distribution_review` issues in `moli.toml`. The issues record applicability, adoption evidence, and exceptions. MOLI's registry validation and scheduled component audit guard this onboarding step.

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
