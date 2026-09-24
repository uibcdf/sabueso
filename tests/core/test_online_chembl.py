import pytest

import sabueso
from sabueso._private.smonitor.warnings import DeprecatedUsageWarning


@pytest.mark.online
def test_online_chembl_molecule_through_resolve():
    card, resolution = sabueso.resolve("chembl:CHEMBL1161789", unichem=False)
    assert resolution.status == "resolved"
    assert card.get("identifiers.chembl") is not None


@pytest.mark.online
def test_online_deprecated_chembl_card_still_works():
    with pytest.warns(DeprecatedUsageWarning, match="sabueso.resolve"):
        card = sabueso.create_molecule_card_online("CHEMBL1", retrieved_at="2026-02-04")
    assert card.get("identifiers.chembl") is not None
