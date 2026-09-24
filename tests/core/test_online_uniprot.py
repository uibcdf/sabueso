import pytest

import sabueso
from sabueso._private.smonitor.warnings import DeprecatedUsageWarning


@pytest.mark.online
def test_online_uniprot_card_through_resolve():
    card, _ = sabueso.resolve("P52789")
    assert card.get("identifiers.uniprot")["value"] == "P52789"


@pytest.mark.online
def test_online_deprecated_uniprot_card_still_works():
    with pytest.warns(DeprecatedUsageWarning, match="sabueso.resolve"):
        card = sabueso.create_protein_card_online("P52789")
    assert card.get("identifiers.uniprot") is not None
