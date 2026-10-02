# Public offline Ackredit pilot

This development pilot composes two packets for public HsTIM (P60174), using the
frozen public UniProt entry and explicitly located Europe PMC annotations declared
in `temp_data/NOTICE.md`. It contains no private vertical-pilot content.

From the repository root, in a development environment with Sabueso and the reviewed
Ackredit source candidate available:

```bash
python -m examples.ackredit_pilot.run --output /tmp/sabueso-ackredit-pilot
```

CI builds and installs Ackredit commit
`4228444cc865a4decb550d1b14b1ffeb046a10eb` with `--no-deps`, using the Conda test
environment, on Python 3.11–3.13. This is a tracked source test, not a published
installation route. Sabueso's ordinary provider-free CI still covers 3.11–3.14.

The output contains a knowledge store, two detached result attribution records,
their text and CSL-JSON references, and the application's workflow attribution.
Both results credit reused UniProt knowledge. Only the literature result credits
Europe PMC. The workflow contains their union; saved readers add no credit.

The initial adapter observes completed composition over pinned stored statements.
The explicit source intake is outside that adapter. The records state this scope,
preserve source-record versions without calling them database releases, and list
missing bibliography. The service-description articles are complete; they do not
replace the bibliography of the target article or its annotation provider, and do
not grant reuse rights for text fragments. See `docs/content/user/attribution.md`.

BibTeX is deliberately not exported here: explicit corporate authors are currently
misrendered by the inspected provider ([Ackredit #78](https://github.com/uibcdf/ackredit/issues/78)).
The original metadata is preserved for a corrected provider reader.
