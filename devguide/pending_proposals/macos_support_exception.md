---
summary: Suspend prospective macOS support while retaining equivalent Linux and Windows qualification.
issue: uibcdf/sabueso#194
status: partial
verification: inspected
opened: 2026-11-12
area: [platform-support, release, qualification]
---

# Bounded prospective macOS support exception

The maintainer selects Linux and Windows as the supported-platform scope for
0.15.0 preparation and subsequent development releases while the tracked macOS
exception remains necessary. Review it before every proposed release, including
0.16.0; an unreviewed exception is not an indefinite release waiver. This changes
future claims and applicable platform gates, not the published 0.14.0 artifact,
its twelve installed-lane receipts or any historical result. Candidate selection,
B7 acceptance and B8 publication remain separately authorized steps.

## Reason and policy boundary

The actual Apple Silicon runner diagnostic refuses the unchanged one-worker
budget before pytest: 2.929 GiB available against a 3.400 GiB requirement, with
7 GiB physical RAM. The maintainer has no alternative suitable Mac available.
No new numerical/scientific assertion failure is demonstrated. The earlier
16 GiB proposal was execution headroom, not an established minimum RAM requirement
for Sabueso or a universal return criterion.

[MolI's operating-system policy](https://github.com/uibcdf/moli/blob/main/devguide/policies/python_ci_policy.md#operating-system-support)
permits a bounded macOS exception with a reason, owning issue and exit condition,
visible in the component README. [Sabueso #194](https://github.com/uibcdf/sabueso/issues/194)
owns this component exception, resource decision and requalification. Maintainers
retain the required Linux evidence and equivalent Windows evidence for every
claimed Python minor. The central `moli.toml` must separately record
`supported_os = ["linux", "windows"]`, `os_support_review.state = "excepted"`
and `macos_exception_issue = "uibcdf/sabueso#194"`, omitting the macOS architecture
claim. Its reviewable patch is prepared for the owning repository; central
adoption is pending until its authorized update is delivered.

## Applicable future gates

- Source CI: Linux and Windows, each on Python 3.11–3.14; four installed public
  Ackredit receiving lanes remain on Linux. Ruff, coverage publication,
  governance, source/fixture scope and resource guards retain their requirements.
- Exact staged archive: Linux and Windows, each on Python 3.11–3.14. Keep producer
  provenance, archive bytes/digest, public dependency closure and complete copied
  receiving for the same immutable file. No tolerated failure replaces a gate.
- Codec receiving: eight current source OS/Python reports. The earlier twelve
  producer reports retain their historical scope; none is relabeled or deleted.
- The macOS capacity workflow remains manual only as a future diagnostic tool.
  This change authorizes no diagnostic, retry, paid infrastructure or other run.

The package remains `noarch`; that format does not assert support on unqualified
systems. macOS installations may work, but are outside the future supported
scope until qualification is restored. No artificial installation ban or runtime
platform check is added, and no shared provider's support claim is changed.

## Exit condition and recurring review

Before restoring macOS support, record a feasible Apple Silicon execution route,
its resource/cost authority and measured safe headroom in #194. Execute the
applicable source tests and the exact candidate's installed archive/public
closure on Python 3.11–3.14 with representative behavior and explicit arm64
provenance. Review real failures, retain complete receptor/artifact evidence and
obtain the maintainer's support decision. Restore the README, required workflows
and central registry together; neither a solver result nor a capacity probe
supplies runtime qualification.

At every proposed release, record whether this exception still applies, its
owner and exit-condition progress. Any central registry mismatch, missing
Linux/Windows result or unresolved B7 requirement remains explicit. This
exception changes supported OS scope; it supplies no passing candidate result.
