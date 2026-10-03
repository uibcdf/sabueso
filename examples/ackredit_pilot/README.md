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
`383a64b2fdbc5472a7cdeb92c464b87433aabd76` with `--no-deps`, using the Conda test
environment, on Python 3.11–3.14 without metadata overrides (ackredit#80). This is a
tracked source test, not a published installation route. All runtime CI installs
the required source provider normally on every supported minor. The dedicated
pilot tests both installed packages outside their checkouts, with only unchanged
integration tests and public fixture access in the temporary working directory.
The provider's portable contract is accepted for the prepared 0.9.0 candidate;
staging and public delivery remain pending (ackredit#22/#75).
The next release requires normal public-provider installation on 3.11–3.14.

The output contains a knowledge store, two detached result attribution records,
their text, CSL-JSON and BibTeX references, and the application's workflow attribution.
Both results credit reused UniProt knowledge. Only the literature result credits
Europe PMC. The workflow contains their union; saved readers add no credit.
Composition supplies `packet.attribution` automatically; this workflow uses no
Sabueso attribution collector to activate it. The records are saved beside packets.

The initial adapter observes completed composition over pinned stored statements.
The explicit source intake is outside that adapter. The records state this scope,
preserve source-record versions without calling them database releases, and list
missing bibliography. The service-description articles are complete; they do not
replace the bibliography of the target article or its annotation provider, and do
not grant reuse rights for text fragments. See `docs/content/user/attribution.md`.

The pinned provider includes the explicit CSL-author BibTeX correction
([Ackredit #78](https://github.com/uibcdf/ackredit/issues/78)). Saved readers render
the corporate UniProt author and Europe PMC's personal names from original metadata.
