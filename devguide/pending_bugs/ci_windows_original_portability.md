---
summary: Preserve original reader checks across Windows checkout, text, member-path and temporary-directory conventions.
issue: uibcdf/sabueso#112
status: open
opened: 2026-11-12
verification: reproduced
area: [testing, ci, portability]
---

# Windows original-reader portability

The SDK266 source matrix in [run 43254731665](https://github.com/uibcdf/sabueso/actions/runs/43254731665)
exposes independent test-input portability failures. The complete Windows Python
3.14 log is retained locally; its failed outcome remains separate from Linux
resource stops and the earlier gzip collection failure. Native corrected-head
Windows qualification remains due.

## Observations and corrections

Git's CRLF conversion reproduces the exact reported sequence/variant frozen-source
checksum differences. `.gitattributes` now pins frozen history Python files to LF
and preserves each `SOURCE.json` byte-for-byte. A real `core.autocrlf=true` checkout
control compares all 55 Python and seven metadata files: the previous attributes
change all 62 hashes, while the corrected attributes preserve all 62. No frozen
file or expected checksum is regenerated.

Three original-member helpers now use `relative_to(...).as_posix()` for archive
members, whose names use `/` on every host. Fifteen text reads/writes in the owning
original-reader controls explicitly use UTF-8, preserving Unicode values and
logical digests under Windows locale defaults. The variant independent receiver
uses the platform temporary directory on Windows and retains its explicit `/tmp`
location on Unix. These corrections preserve original scientific assertions,
resource budgets, payloads and verifiers.

Seven actual original/history controls pass with CP1252 defaults and scoped
Windows path conventions on Linux. This controlled reproduction establishes the
specific corrections; it is not a native Windows passing result. Raw instruments,
source/provider maps and the real checkout control remain owned by #112/#148 in
`recovered_work/checkpoint_recovery_20261106/b7-ci-portability-resource-1/`.

## External child selection identity

The scratch-lifetime child clients previously inherited a configuration root
outside their actual copied tests. Distinct tests with the same function name
then receive identical pathless IDs. The retained synthetic control executes all
three calls but the receptor accounts for only one. Supplying the actual client
directory through `--rootdir` preserves all three identities and their two-pass /
one-fail outcome. The real lifetime controls retain every original assertion and
the repository configuration while setting that explicit child root.

The approved synthetic report is delivered as [pytest-receptor #54](https://github.com/uibcdf/pytest-receptor/issues/54).
The current checkout's runtime matches public receptor 1.2.3; no provider update,
source edit or new dependency bound is part of this correction. The provider owns
handling duplicate external IDs; Sabueso owns correct roots for its child clients.
