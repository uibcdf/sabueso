---
summary: Component-owned exploratory workspace using the received fixed MolSysMT cohort without changing the paused shared prefix.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-16
verification: local_development_receiving
area: [human-exploration, development, interoperability]
---

# Checked local explorer workspace

The maintainer authorizes proceeding with adoption of the
[received MolSysMT correction](interactive_model_scale_0160.md#received-provider-correction-2026-11-16-utc).
The existing shared-prefix pause under MolSysSuite #82/#175 remains in force.
Sabueso therefore owns an exploratory overlay under the ignored
`build/explorer-development/`, with a detached local MolSysMT checkout at
`b8c7984748f2ca87d19911f4cc3bf63b688d3641` and its own compiled native extension.
It inherits the existing compatible Conda dependency closure, keeping every
participating source editable. This is local source development, not a new
canonical Conda profile, public installation route or release claim.

## Use the received workspace on this machine

From this checkout:

```bash
python devtools/explorer_workspace.py check
python devtools/explorer_workspace.py run -- --output-directory build/explorer-development/readings
```

`run` forwards the existing explorer arguments, including `--card`, `--deck`,
`--reading` and `--experimental-model`. It needs the normal graphical Qt session;
automated receiving uses an owned Xvfb display. Saved readings belong to the
caller and remain separate from environment/build scratch.

The launcher checks Python 3.14/Linux, editable import origins, this Sabueso
checkout, the exact provider source heads/clean states, selected numerical,
parser, Qt/network/quantity dependency versions and the bound native-extension
digest. The versioned [cohort](../../devtools/explorer_cohort.json) names the
received sources; the ignored `workspace.json` binds the actual local build.
Absent/foreign workspaces, changed bindings, native bytes or declared dependency
versions are refused. There is no fallback to the active shared interpreter.

The launcher replaces itself with the owned interpreter and forwards arguments
unchanged. It caps CPU affinity at four available CPUs and sets the declared
native thread controls to one. Automated runs still use the existing resource
observer for memory/headroom/time monitoring; affinity does not reserve resources.
These are launch-time checks, not a container or protection against later edits
to participating source checkouts.

## Preparation and ownership

The received local setup uses an owned `venv --system-site-packages` over the
compatible Python 3.14 base. Only its own prefix receives editable Sabueso and
fixed-source MolSysMT; shared Viewer/support editables retain their received
source heads. Standard Git, venv and pip provide the setup; the launcher neither
installs dependencies nor updates a colleague's clone. Canonical complete-cohort
installation/migration remains owned by MolSysSuite's existing environment tools.

The provider build uses two Cargo jobs and a copied offline registry/target under
task-owned temporary storage. Those build inputs retire after receiving. The
local workspace retains its source, environment, binding and `OWNERSHIP.json`
under #154 until the next cohort revision or canonical workspace migration.
Inspect active sessions and caller readings before retiring it. A new machine or
changed cohort needs actual origin/native/Qt receiving; a copied binding is not
qualification. Exact commands, build/source identities and observations are in
the [receipt](../evidence/interactive_development_workspace_checkpoint_20261116.json).

## Scope and continuation

This makes the received provider usable for local explorer work without changing
the paused shared prefix or selecting a public provider minimum. Card/scientific
schemas and application/renderer resources are unchanged; editable installation
refreshes generated version metadata. The prior larger-model and first Sketcher
receipts keep their source/artifact epochs.

The original-file matrix and consumer/lifecycle controls are repeated in this
retained workspace. Real Qt receiving exercises the checked launcher itself.
Supported mapped 3D, production Sketcher preparation/Card integration, Interaction
View, broader workloads/native platforms and human/version decisions remain
separate. The main ledger remains **20 done, 11 partial and 2 todo**.
