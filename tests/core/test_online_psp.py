import pytest


@pytest.mark.online
def test_online_psp():
    pytest.skip("PhosphoSitePlus requires licensed data access; no public API assumed")
