"""Shared services of source clients (#86): release caches and personal keys."""

from __future__ import annotations

import pytest

from sabueso.core.errors import ConnectorError, MissingKeyError
from sabueso.tools.db import _keys, _release


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.setattr(_release, "_MEMORY", {})
    monkeypatch.delenv("SABUESO_CACHE_DIR", raising=False)
    monkeypatch.delenv("SABUESO_TOY_KEY", raising=False)


def test_no_cache_directory_unless_told(tmp_path, monkeypatch):
    assert _release.cache_directory("toy") is None
    assert _release.cache_directory("toy", tmp_path) == tmp_path / "toy"
    monkeypatch.setenv("SABUESO_CACHE_DIR", str(tmp_path))
    assert _release.cache_directory("toy") == tmp_path / "toy"


def test_a_release_is_built_once_per_process():
    built = []
    for _ in range(3):
        index = _release.remembered("Toy", "v1", lambda: built.append(1) or {"a": 1})
    assert index == {"a": 1} and built == [1]
    assert _release.recall("Toy", "v2") is None
    _release.keep("Toy", "v2", {"b": 2})
    assert _release.recall("Toy", "v2") == {"b": 2}
    _release.forget("Toy")
    assert _release.recall("Toy", "v1") is None


def test_releases_are_written_whole_or_not_at_all(tmp_path):
    target = tmp_path / "toy" / "v1"
    _release.write_release(target, {"index.json": "{}", "sessions/1.json": "[]"})
    assert sorted(p.name for p in target.rglob("*.json")) == ["1.json", "index.json"]
    assert [p.name for p in (tmp_path / "toy").iterdir()] == ["v1"]  # no staging left
    _release.write_file(tmp_path / "toy" / "c.json", "{}")
    assert not list((tmp_path / "toy").glob("*.part"))


def test_a_release_must_match_its_published_checksum():
    import hashlib

    payload = b"release"
    _release.verify_md5(payload, hashlib.md5(payload).hexdigest(), "Toy v1")  # noqa: S324
    with pytest.raises(ConnectorError, match="Toy v1 does not match"):
        _release.verify_md5(payload, "0" * 32, "Toy v1")


def test_keys_come_from_the_user_only(monkeypatch):
    assert _keys.variable("toy") == "SABUESO_TOY_KEY"
    assert _keys.key("toy") is None
    monkeypatch.setenv("SABUESO_TOY_KEY", "env-key")
    assert _keys.key("toy") == "env-key"
    assert _keys.key("toy", "given") == "given"


def test_a_missing_required_key_names_where_to_put_one():
    with pytest.raises(MissingKeyError, match=r"\$SABUESO_TOY_KEY") as info:
        _keys.required("toy", source="Toy")
    assert info.value.code == "SABUESO-E-SOURCE-003"


def test_a_key_is_scrubbed_from_messages():
    assert _keys.scrub("GET ...?api_key=s3cr3t failed", "s3cr3t") == (
        "GET ...?api_key=<key> failed"
    )
    assert _keys.scrub("failed", None) == "failed"


def test_the_ncbi_key_is_sent_but_never_echoed(monkeypatch):
    from urllib.error import HTTPError

    from sabueso.tools.db import clinvar, ncbi_gene, ncbi_taxonomy

    seen = []

    def failing(target, timeout):
        seen.append(target)
        url = target if isinstance(target, str) else target.full_url
        raise HTTPError(url, 500, f"boom at {url}", None, None)

    monkeypatch.setattr(ncbi_gene, "urlopen", failing)
    monkeypatch.setattr(clinvar, "urlopen", failing)
    monkeypatch.setattr(ncbi_taxonomy, "urlopen", failing)
    monkeypatch.setenv("SABUESO_NCBI_KEY", "s3cr3t")
    with pytest.raises(ConnectorError) as gene_error:
        ncbi_gene.OnlineNCBIGeneClient().gene("7167")
    with pytest.raises(ConnectorError) as taxon_error:
        ncbi_taxonomy.OnlineNCBITaxonomyClient().taxa([9606])
    with pytest.raises(ConnectorError) as clinvar_error:
        clinvar.OnlineClinVarClient().variants(["7167"])
    assert "api_key=s3cr3t" in seen[0]
    assert seen[1].get_header("Api-key") == "s3cr3t"
    assert "api_key=s3cr3t" in seen[2].full_url
    for error in (gene_error.value, taxon_error.value, clinvar_error.value):
        assert "s3cr3t" not in str(error)
        assert error.__cause__ is None
