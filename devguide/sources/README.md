# Source registry

`registry.yaml` records every online resource Sabueso uses, has set aside, or has yet to
review, with the reason for each decision. It is the source of truth. The user page
`docs/content/user/data_sources.md` is generated from it:

```bash
python tools/source_registry.py --write   # regenerate the page
python tools/source_registry.py --check   # validate the registry, compare the page
```

`tests/core/test_source_registry_offline.py` runs the same checks in CI.

## Statuses

| Status | Meaning | Must state |
| --- | --- | --- |
| `queued` | Proposed, not yet reviewed | — |
| `evaluating` | Someone is checking access, licence, coverage and fit | — |
| `in_use` | Sabueso reads it, directly or `via` another source's cross-references | `reason`, `access`, `licence`, `module` |
| `deferred` | Useful, set aside for now | `reason`, `revisit_when` |
| `rejected` | Not suitable | `reason` |
| `retired` | Was used, no longer is | `reason` |
| `out_of_scope` | Not a knowledge source for Sabueso | `reason`, `owner` (the MOLI component it belongs to) |

Every module in `sabueso.tools.db` must be an `in_use` entry.

## Proposing a resource

Open a discussion in the **Data sources** category of the repository's GitHub
Discussions. Its form asks for the resource, what it would bring, access, licence and
overlap. Maintainers can also add a `queued` entry directly.

The category is an intake channel; the decision is recorded here, never only in a
thread. The rules for Discussions across MOLI (when to enable them, standard
categories, their relation to issues) are proposed in uibcdf/moli#23. Sabueso will
align its other categories (removing the unused GitHub defaults) once they are
decided.

## Triage

1. Add the resource as `queued`, with `proposed_by` and a link to the discussion.
2. When someone reviews it, set `evaluating`. A review worth keeping goes in
   `devguide/pending_proposals/<resource>.md` (MOLI reporting protocol) and is linked
   from `links`.
3. Record the decision here, with its date (`since`), `decided_by` and `reason`. For
   `deferred`, state `revisit_when` as a concrete trigger, not "later".
4. Taking a resource into use also means:
   - a `tools.db` module;
   - a licence row in `devguide/LICENSING_AND_COMPLIANCE.md`;
   - a `DATA_SOURCES_STATUS.md` section;
   - fixtures declared in `temp_data/NOTICE.md`.
5. Regenerate the page and answer in the discussion with a link to the commit.

## Confidentiality

This repository is public. Reasons and triggers are stated in general terms ("stage-
resolved expression for eukaryotic pathogens"), never by naming a private project or
its content.
