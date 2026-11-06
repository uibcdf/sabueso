# Development workstation handoff — 2026-11-06

Owner: Sabueso #112/#148. This is the current migration/resumption entry point.
For a conceptual introduction first read [ONBOARDING](ONBOARDING.md); this handoff
then preserves the existing workspace rather than replacing that introduction.
Read it before the older checkpoint chronology, then follow the
[integrated continuation plan](CONTINUATION_PLAN_20261104.md) and
[complete Card exploration inventory](pending_proposals/card_exploration_completion_0150.md).
The full human/agent design and validated exceptional researcher experience remain
required before 0.15.0. **Do not publish 0.15.0, freeze its schema or start staging.**

## Exact state to preserve

The original pre-closeout capture had local `main` at
`03bdb2c005857ac14c86f586bf4807d78f4ea783`, ahead of the recorded
`origin/main` reference `d54b39aef7731e9e5dc1ea73f794f2221eee8d60`.
That initial dirty state and its stopped/narrower test receipts remain historical.

The code is now committed at **`0f197e56b95f5f361cb16778457f652832d05f28`**, with
705 distinct selected local cases, copied consumers, historical science, static/
schema/shape/docs checks and public whole-session receiving. See the
[local code checkpoint](evidence/chemical_saved_checkpoint_20261106.json).
Original clean SDK193 controls remain fixed; they are not relabelled as the new
code's producer. The subsequent documentation closeout is a separate commit.

The [transfer manifest](evidence/workstation_handoff_20261106.json) distinguishes
its original capture from the committed source checkpoint. Do not embed the final
documentation commit's own SHA in its contents. After that commit, the external
`recovered_work/clean_checkpoint_20261106/final-closeout.json` records actual HEAD,
clean status, ahead count and fresh editable SDK/import receiving. Inspect that
record and `git status` before migration; the local commit history is not a push.

The unchanged source payload has 17 code/test/configuration files and 299 original
chemical evidence files. All changed guide files except the manifest itself are
hash-declared. Dirty peer-checkout states are observations at capture time; preserve
any current local work independently. The manifest is a transfer integrity aid,
not full scientific, installed-artifact or release qualification.

| Material | Current state / preservation requirement |
| --- | --- |
| Native and live chemical classification | Source-bound `chemical_classification_context@1`, human `classification` and compact-agent `chemical_classification` are in the local commit; classes/roles do not establish target activity or therapeutic effect |
| Saved reading candidate | Semantic format @15 and separate sharing @16, frozen history/presentation and dispatch are committed at0f197e5 with their original-reader regressions |
| Literal routing correction | Metadata with scientific-looking names, false/null/array contexts and literal `items` links now retain literal ownership; the candidate refuses a metadata object claiming a scientific manifest |
| Original controls | Keep `tests/core/data/chemical_native_sdk192.json.gz` and the now committed `chemical_live_v1.json.gz`; the latter is a genuine clean SDK193 live capture made before its saved reader, not a saved-reader replay |
| Historical rules | 101 original files were rechecked byte-identical to the baseline. Existing formats @1–@14 and native scientific meanings must stay fixed |

See the [chemical contract](pending_proposals/chemical_classification_exploration.md),
[literal correction](pending_bugs/chemical_literal_metadata_routing.md) and
[scoped candidate receipt](evidence/chemical_saved_candidate_20261106.json).

## Transfer more than a remote clone

A fresh **remote** clone still misses local commits until they are pushed, and
Git never carries ignored evidence/protected originals. Preserve committed history
through a private full-checkout transfer or the verified incremental bundle at
`recovered_work/clean_checkpoint_20261106/sabueso-local-migration.bundle` once the
closeout receipt confirms its creation and verification. A bundle records its
prerequisite source; compare it with the destination history before importing.
Never reset later remote work to install a migration snapshot.

No push or release is implied by a clean local tree. Preserve the ignored materials
below separately, and compare the final external closeout record and file hashes.
Verify the transfer container's checksum through the private channel; the manifest
cannot verify its own bytes and is not a complete archive of every peer checkout.

From the destination checkout, this check reads only transferred bytes:

```python
import hashlib
import json
from pathlib import Path

manifest = json.loads(
    Path("devguide/evidence/workstation_handoff_20261106.json").read_text()
)
files = (
    manifest["payload_files"]
    + manifest["documentation_files"]
    + manifest["retained_evidence_files"]
)
for item in files:
    raw = Path(item["path"]).read_bytes()
    assert len(raw) == item["bytes"], item["path"]
    assert hashlib.sha256(raw).hexdigest() == item["sha256"], item["path"]
for check in manifest["documentation_receiving"]["checks"].values():
    for kind in ("resource", "log"):
        path = check[f"{kind}_path"]
        raw = Path(path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == check[f"{kind}_sha256"], path
print("Declared candidate, documentation and evidence files match the snapshot.")
```

| Material | Transfer / destination check |
| --- | --- |
| Committed Git history | Transfer local `main` through full `.git/` history or the verified bundle; code/docs that were dirty at initial capture are now closed by commits. Compare refs, final clean status and hashes before reconciling later remote work |
| `devguide/` | Include the documentation closeout commit, current/initial receipts, analyses and updated plans; the original dirty snapshot is historical, not a patch to reapply |
| `recovered_work/chemical_saved_20261106/` | Retain original/stopped/passing logs, resource receipts, hash controls, candidate exports, useful probes, `RETENTION.md` and the pending #148 report draft |
| `recovered_work/chemical_profile_20261106/` | Retain original SDK192/SDK193 captures and producer manifest, clean-SDK receiving, public walkthroughs and inside/outside editable-route receipts |
| `recovered_work/chemical_classification_20261106/` | Retain the native foundation's source/field ownership records and pending #166/#148 disclosure drafts |
| `recovered_work/workstation_handoff_20261106/` | Retain the documentation-only link/example/checksum, Ruff and fixture-delivery receipts with their owner/review note; these are separate from scientific receiving |
| `recovered_work/onboarding_20261106/` | Retain the complete guide review, offline contributor walkthrough and link/static receiving, with its owner/review trigger |
| `recovered_work/clean_checkpoint_20261106/` | Retain the705-case source/consumer/workload receipts, final HEAD/SDK/clean-status record and verified local Git bundle; original stopped/oracle-diagnostic logs retain their separate outcomes |
| Local-only source inputs | The delivery inventory declares 37 originals, 28,766,656 bytes; all are present at handoff. Preserve them privately under the owner's existing access/terms, keep them ignored, and verify with `python tools/fixture_delivery.py --check --local-inputs` |
| Other retained development evidence | `recovered_work/` is ignored and approximately 10 GiB in total. The three active chemical directories are only about 6 MiB. Preserve the remaining useful evidence with its owning retention note; those three directories are not a complete archive of earlier work |
| Participating component checkouts | Preserve each relevant clone's source revision and local work separately. The manifest records current Git identities for the 19 previously recorded editable routes; it does not claim a new import/runtime check |
| Environment/governance clones | Preserve or deliberately reacquire `../molsyssuite/` with its recipe, `suite.toml` and environment helper, plus `../moli/` with `moli.toml` when using the suite's full-workspace reinstall route. These administrative clones are outside the historical 19 editable routes; record and compare their revisions and local work separately |

For every dirty participating checkout, preserve tracked changes, untracked
inputs and its own retained evidence before installing. A recorded HEAD and
`dirty: true` alone cannot verify those working bytes. Compare each checkout's
source/working-state receipt at its new path; preserve an unresolved difference
for its owner instead of resetting it.

The source Git directory also retains a prunable detached-worktree registration
for `/tmp/recorda-lab15-sabueso`; the registered working directory is absent.
Copying `.git/` preserves that old absolute reference. Review
`git worktree list --porcelain` after transfer and retain this observation with
the handoff. Establish ownership and whether a session still needs its metadata
before any deliberate repair or pruning; an old path is not a destination job
and does not authorize cleanup of other worktrees.

The sibling `moli` checkout is also older than the guide already adopted by
Sabueso: its working guide differs from the accepted `959c6529` source. Sabueso's
local `MOLI_GUIDE.md` still matches the accepted SHA-256 in the
[adoption receipt](evidence/publication_authority_adoption_20261105.json). Do not
downgrade that copy from the stale sibling. Preserve the administrative clone's
state and deliberately reconcile it with its canonical owner before using its
current profile/helper inputs. The manifest records both identities; no fetch,
reset, central-policy change or sibling update was performed by this review.

The [fixture delivery inventory](sources/fixture_delivery.json) and
[fixture policy](TESTS.md#fixtures) own original-byte identities and distribution
boundaries. Missing local-only originals are an explicit local-qualification gap,
not permission to download substitutes or publish them. Private pilot checkouts
and outputs remain separate, read-only scientific context and never enter public
fixtures, archives, issues or this guide.

Do not transfer an old Conda prefix as the new development environment or assume
that native build caches are portable. Preserve useful old receipts; recreate
the environment/toolchain and receive editable routes at their new paths.
No task-owned test or resource watcher remains running at handoff. Old session
IDs and namespace-local PIDs are historical observations, not destination jobs.

## Verification already obtained

| Scope | Result and limit |
| --- | --- |
| Earlier chemical candidate | 81 native/live/saved cases and 428 navigation/argument/quantity/literal cases passed: 509 distinct cases **before** the additional metadata correction; not final-source qualification |
| Corrected literal routes | 14 focused regressions pass, including source-looking metadata, typed false/zero retention, related/back continuity and resealed manifest refusal; minimal synthetic Cards isolate namespace ownership |
| Registry/licensing/delivery | 57 cases pass; delivery, registry, schema and governance tools pass within their own unchanged scope |
| Static checks | Complete root `ruff format --check .` and `ruff check .` pass. The earlier documentation-only static run used a 32 MiB owned cap; the clean-checkpoint gates use the separately recorded 512 MiB cap and retain the 6 GiB host reserve |
| Copied consumers | Both current outer cases pass with nested saved38/live27 payloads; nested/repeated cases are not added to distinct totals |
| Historical science | Three separate41-case gates now pass,123 total. The earlier combined host-floor stop remains non-passing history |
| Complete corrected chemical source | **95 passed**: saved38 +live27 +native30 at the committed source blobs; earlier host-reserve stops remain failed historical attempts |
| Local checkpoint | **705 distinct selected cases** pass:95 chemical +428 neighbors +123 history +57 metadata +2 outer consumers. Public whole-session save/read/resave preserves114 source/context routes with no queries and engines/Card construction forbidden during independent reading |
| Broad acceptance | Exact-final-source hosted/installed, independent scientific, researcher, consumer/pilot and broader workload acceptance remain separate/open |

The earlier development goal was marked resource-blocked after host-reserve
stops. The initial documentation handoff instead observed31,019,978,752 bytes
of `MemAvailable` (about 28.9 GiB), with free swap. That is a new resource
observation, **not a rerun or acceptance result**. Recheck the destination rather
than inheriting either observation. No scientific tests were started for this
initial documentation-only handoff. Subsequent clean-checkpoint receiving is
recorded separately in the new local receipt.

## Recreate and verify the development environment

The following bootstrap targets **Linux x86_64 with Python 3.14**, matching the
suite recipe and native toolchain checks. Another platform needs its own reviewed
environment and resource-guard route; the Linux receipts do not qualify it.
Use the current
[MolSysSuite environment instructions](https://github.com/uibcdf/molsyssuite/blob/main/devtools/conda-envs/README.md).
The available sibling recipe is `../molsyssuite/devtools/conda-envs/molsyssuite-dev-py314.yaml`.
First create and activate the base from that clone:

```bash
conda env create --file devtools/conda-envs/molsyssuite-dev-py314.yaml
conda activate 'molsyssuite@uibcdf_3.14'
```

If Conda uses multiple environment directories, follow the suite's explicit
`--prefix` creation/activation route and keep using that same prefix. Source
installation can download declared Cargo crates and build native extensions;
receive the destination toolchain and builds before scientific gates.

The suite base alone does not declare Sabueso's complete documentation and test
dependencies. This is a **destination bootstrap plan**, not a newly executed
solver/bootstrap receipt. From the Sabueso checkout, prepare destination-owned
copies of the maintained overlays with bounded channels; the original Sabueso
files do not include `nodefaults`. The base supplies PyYAML. Choose a fresh output
directory; do not overwrite a previous receipt.

```python
import hashlib
import json
from pathlib import Path

import yaml

destination = Path("recovered_work/destination_bootstrap")
destination.mkdir(parents=True, exist_ok=False)
receipts = []
for name in ("development_env", "test_env"):
    source = Path("devtools/conda-envs") / f"{name}.yaml"
    raw = source.read_bytes()
    specification = yaml.safe_load(raw)
    dependencies = specification["dependencies"]
    specification["channels"] = ["uibcdf", "conda-forge", "nodefaults"]
    target = destination / source.name
    target.write_text(yaml.safe_dump(specification, sort_keys=False))
    assert yaml.safe_load(target.read_text())["dependencies"] == dependencies
    receipts.append(
        {
            "source": str(source),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "generated": str(target),
            "generated_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        }
    )
(destination / "recipe_hashes.json").write_text(json.dumps(receipts, indent=2))
```

Provision those copies into the active base **before** installing local editables:

```bash
conda env update --prefix "$CONDA_PREFIX" --file recovered_work/destination_bootstrap/development_env.yaml
conda env update --prefix "$CONDA_PREFIX" --file recovered_work/destination_bootstrap/test_env.yaml
```

The development recipe supplies `gemmi`, Ruff and the Sphinx/theme/extensions
listed in `devtools/conda-envs/docs_env.yaml`; the test recipe also explicitly
requires `nbformat` and the applicable `pytest-cov` versions. Keep the canonical
suite recipe, original overlays, generated copies and hashes with the new
solver/toolchain receipt. Dependencies are preserved rather than naively merged
across duplicate package names; only destination channel lists are normalized.
Inspect the transaction for the declared `uibcdf`/`conda-forge` channels and the
suite's official Qt 6.11.2 stack. Do not use `--prune`. Reactivate the same prefix
after provisioning, then run the following from the MolSysSuite clone:

```bash
python -c 'import sys; assert sys.version_info[:2] == (3, 14); print(sys.executable, sys.prefix)'
python devtools/scripts/development_environment.py toolchain
python devtools/scripts/development_environment.py profile
python devtools/scripts/development_environment.py sources --workspace ..
python devtools/scripts/development_environment.py install --workspace ..
python devtools/scripts/development_environment.py runtime --workspace ..
```

Use the actual parent of the transferred clones for `--workspace` if they are
not siblings. Follow the current qualified profile rather than treating the
historical list of 19 installations as new suite-adoption authority. The
profile-scoped installer/runtime check does not cover all direct MOLI components
or an excluded suite member. Receive any additional participating Python checkout
through its owner's current route, installing it editable with dependency
resolution and build isolation disabled. Conda provisioning can replace provider
distributions, so repeat editable installation/verification after all overlays.

From the Sabueso checkout, after activating that compatible environment:

```bash
python -m pip install --no-deps --no-build-isolation --editable .
python -m pip check
python tools/fixture_delivery.py --check --local-inputs
python tools/source_registry.py --check
python tools/validate_schema.py
python devtools/moli_governance.py
```

Verify Sabueso's import path and imported/distribution version **both inside and
outside** its checkout. Verify participating local component imports against
their new editable origins. Old source-root `*.egg-info`, generated version files
and old absolute `direct_url.json` paths can conceal a mismatched producer stamp.
Do not force the old SDK193 label onto newly changed sources or relabel original
capsules. Reinstall/recheck metadata after the documentation closeout commit and
after later source commits or environment changes.

The old guard/probe scripts in `recovered_work/` are evidence, not portable
installed tools. They use Linux `/proc`, CPU affinity and `taskset`; in particular,
`run_bounded.py` retains an absolute old MolSysMT Cargo-cache path. Use a new owned
copy with correct destination paths and a new receipt name; preserve the original
helper and receipts. Keep one low-priority CPU, numerical/native threads at one,
512 MiB owned-tree RSS, 6 GiB host-available reserve, zero owned swap, a 600-second
elapsed ceiling and a 2 GiB owned-scratch ceiling. At least
6.5 GiB available is required before that scientific guard starts. More host RAM
does not authorize silent budget changes or a return to 12 workers without a
separate resource assessment. Read [TESTS](TESTS.md#local-checks-and-ci-checkpoints).

## First development actions on the destination

1. Verify committed history, file hashes and the external final-closeout record.
   Initial dirty-state lists are historical; do not reapply those changes over the
   same committed checkpoint. Fetch/reconcile remote changes only after preserving
   local history and ignored evidence. Re-read the current contributor/MolI rules.
2. Establish the destination environment/source/import checks above. Retain its new
   solver/toolchain/metadata receiving separately from source-machine evidence.
3. Run the complete source gate as destination receiving under the resource guard:

   ```bash
   python -m pytest --receptor=llm -m "not online" \
     tests/core/test_card_saved_chemical_offline.py \
     tests/core/test_card_chemical_exploration_offline.py \
     tests/core/test_chemical_classification_offline.py
   ```

4. Apply additional historical/adjacent/copied/shape/docs and representative workload
   gates from TESTS to changed source/environment scope. The source checkpoint
   already passes the three separate historical modules, both isolated consumers
   and whole public molecule sessions. Do not reimplement completed work or call
   those old host-floor attempts successful. Keep the separate full64-item structural
   and broad scientific/researcher obligations in their own acceptance scope.
5. The final documentation-HEAD SDK/import checks and committed-SDK95 receiving
   are recorded externally after the clean commit, so in-tree documents never
   claim their own containing commit's hash. Verify those records at transfer.
6. Exact-final-source hosted CI/governance remains pending where not run. Recover it
   through the authorized unskipped push/manual route and gh-run-receptor before
   claiming hosted qualification. Local clean Git/selected gates are not a release,
   installed-artifact matrix or independent scientist/researcher acceptance.

Do not reacquire molecular provider data or regenerate original producer controls
to make these gates pass. The candidate already retains public inputs. Record
failed/stopped outcomes separately and clean only owned disposable outputs after
the actual processes finish.

## Continue the full plan after this checkpoint

The saved chemical block is a prerequisite, not the whole 0.15.0 objective:

| Block | Remaining obligation |
| --- | --- |
| B2 | The maintainer will perform scientific measurement-correspondence review and explicitly left it pending. Keep opt-in policy and defaults separate; additional tests do not authorize default adoption |
| B3 | Finish bounded structural journeys, exact-source qualification and explicit owner/scientist disposition of physical reconciliation, modeling boundaries and remaining source uncertainty |
| B4 | Complete activity/assay/document and shared literature journeys with source-qualified identity and scientific context, respecting B1/B2 prerequisites |
| B5 | Finish molecule properties/targets/clinical context and disease terminology/hierarchy/associations, alongside chemical classification; complete human/agent/saved parity and positive/uncertain public examples |
| B6 | Deliver variant/isoform/tissue/comparative and retained-association profiles with explicit supplied context, axes, identity and support |
| B7 | Integrate all required panels; obtain scientist and uncoached researcher acceptance, compact-agent parity, representative workload results and private pilot/consumer receiving |
| B8 | Release consolidation remains paused; no tag, release, schema freeze, staging, package promotion or archive publication is authorized by this handoff |

The current experience review also records an unresolved human-navigation issue:
conflict/support wording still refers to `native_payload`, and the field-context
destination remains literal inspection. Review a direct alternatives/conflicts
route with researchers; passing tests do not establish the intended wow effect.

The existing #166/#148 technical report drafts remain local pending their scoped
publication permission; copying them to the new private workspace is not public
delivery. Third-party reports still require prior explicit destination/action/
material permission. Preserve public/private boundaries and the
[reporting protocol](../MOLI_GUIDE.md#reporting-bugs-and-proposals).

## Handoff documentation checks

The [onboarding review](evidence/onboarding_review_20261106.json) records the
initial complete guide navigation and offline contributor walkthrough. The
[local code checkpoint](evidence/chemical_saved_checkpoint_20261106.json) and
handoff manifest record the subsequent checks after consolidation. They cover
all active guide documents plus the three newly archived entry pages. The public
example makes no network request and leaves its captured Card unchanged. Complete
root Ruff gates pass; original source/evidence hashes remain intact.

The handoff manifest now declares every changed guide document except itself,
including the review, new onboarding page and archived entries. Its destination
example checks those documents, the 17 code/test/configuration files, 299 original
chemical evidence files and documentation receipt/log hashes. The manifest cannot
verify its own bytes: preserve the private transfer container's checksum too.

The original narrower handoff checks remain historical in their own receipt;
subsequent guide checks live in `recovered_work/onboarding_20261106/` and
`recovered_work/clean_checkpoint_20261106/` with their owner/review trigger.
Fixture delivery retains 81 repository inputs and 37 protected local originals.
The initial documentation review performed no scientific tests or commits; the
later clean-checkpoint work commits the locally checked code and guide. No full
scientific suite, destination bootstrap, push, worktree pruning or release was
performed by either phase.
