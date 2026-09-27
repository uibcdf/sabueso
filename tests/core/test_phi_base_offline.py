"""PHI-base: phenotypes of pathogen mutants, keyed by UniProt (#83).

Fixtures: the PHI-base 5.6 curation sessions naming Q4D3W2 (T. cruzi dihydroorotate
dehydrogenase), H2DQH1 (T. cruzi) and Q4QGX0 (L. major), and the UniProt entry Q4D3W2.
"""

import hashlib
import io
import json
import zipfile

import pytest

import sabueso
from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.mappings.phi_base import map_phenotypes
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import phi_base
from sabueso.tools.db.phi_base import FixturePHIBaseClient, OnlinePHIBaseClient

FIELD = "annotations.pathogen_phenotypes"


def _items(accession):
    response = FixturePHIBaseClient("temp_data").phenotypes(accession)
    mapped = map_phenotypes(response["sessions"], accession, "fixture", "5.6")
    return mapped, mapped["fields"].get(FIELD, [])


def test_a_knockout_phenotype_is_kept_with_its_genotype_and_publication():
    mapped, (item,) = _items("Q4D3W2")
    assert item["high_level_terms"] == ["Lethal"]
    assert item["phenotype"] == "PHIPO:0000513"
    assert item["genotype"] == [
        {"gene": "Q4D3W2", "allele": "DHODΔ", "allele_type": "deletion"}
    ]
    assert item["pathogen"] == {
        "taxon_id": 5693,
        "name": "Trypanosoma cruzi",
        "strain": "Tulahuen",
    }
    assert item["publication"] == "pubmed:15696374"
    (assertion,) = mapped["source_assertions"]
    assert assertion["source"] == {
        "type": "database",
        "name": "PHI-base",
        "record_id": "PHI:2575",
        "version": "5.6",
    }
    assert assertion["subject_ref"] == "uniprot:Q4D3W2"


def test_a_phenotype_on_a_host_names_the_host_and_the_disease():
    _, items = _items("Q4QGX0")
    on_host = [i for i in items if i.get("host")]
    assert on_host
    assert on_host[0]["host"]["name"] == "Mus musculus"
    assert on_host[0]["extensions"][0]["label"] == "reduced virulence"
    assert all(d.startswith("PHIDO:") for i in on_host for d in i.get("diseases", []))


def _session(genotype_genes):
    """A synthetic session: one pathogen phenotype for a genotype of the given genes."""
    genes = {
        f"Pathogen {a}": {"uniprot_data": {"uniprot_id": a}} for a in genotype_genes
    }
    alleles = {
        f"{a}:s-1": {
            "gene": f"Pathogen {a}",
            "name": f"{a}Δ",
            "allele_type": "deletion",
        }
        for a in genotype_genes
    }
    return {
        "session": "s",
        "genes": genes,
        "alleles": alleles,
        "genotypes": {"g-1": {"loci": [[{"id": k}] for k in alleles]}},
        "annotations": [
            {"type": "pathogen_phenotype", "term": "PHIPO:1", "genotype": "g-1"},
            {"type": "biological_process", "term": "GO:1", "genotype": "g-1"},
        ],
    }


def test_a_double_mutant_is_never_read_as_a_single_one():
    (item,) = map_phenotypes([_session(["P1", "P2"])], "P1", "t", "5.6")["fields"][
        FIELD
    ]
    assert [a["gene"] for a in item["genotype"]] == ["P1", "P2"]
    # A gene outside the genotype gets nothing; GO annotations are not phenotypes.
    assert map_phenotypes([_session(["P2"])], "P1", "t", "5.6")["fields"] == {}


def test_a_session_naming_several_genes_is_indexed_once():
    sessions, index = phi_base.index_release(
        {"curation_sessions": {"s": _session(["P1", "P2"])}}
    )
    assert list(sessions) == ["s"]
    assert index == {"P1": ["s"], "P2": ["s"]}


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(FixtureUniProtClient("temp_data"))


def _states(card):
    return {
        (r["area"], r["source"]): r
        for r in card.knowledge_state()["rows"]
        if r["area"] == FIELD
    }


def test_resolve_adds_phenotypes_and_says_what_is_not_stated(resolver):
    client = FixturePHIBaseClient("temp_data")
    card, _ = sabueso.resolve(
        "Q4D3W2", resolver=resolver, phi_base=True, phi_base_client=client
    )
    assert len(card.get(FIELD)["value"]) == 1
    assert _states(card)[(FIELD, "PHI-base")]["state"] == "known"
    # TcTIM is not in PHI-base: not stated, never evidence of anything.
    tim, _ = sabueso.resolve(
        "P52270", resolver=resolver, phi_base=True, phi_base_client=client
    )
    assert tim.get(FIELD) is None
    assert _states(tim)[(FIELD, "PHI-base")]["state"] == "not_stated"
    asked_not, _ = sabueso.resolve("P52270", resolver=resolver)
    assert _states(asked_not)[(FIELD, "PHI-base")]["state"] == "not_queried"


def test_a_failed_release_is_unavailable(resolver):
    failing = FixturePHIBaseClient("temp_data", failing={"Q4D3W2"})
    with pytest.warns(EnrichmentFailedWarning):
        card, _ = sabueso.resolve(
            "Q4D3W2", resolver=resolver, phi_base=True, phi_base_client=failing
        )
    assert _states(card)[(FIELD, "PHI-base")]["state"] == "unavailable"


# --- the online client, on a synthetic release ------------------------------------------


def _release_zip():
    data = {"curation_sessions": {"s": _session(["P1", "P2"])}, "schema_version": 1}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("phi-base_vX/phi-base.schema.json", "{}")
        archive.writestr("phi-base_vX/phi-base_vX.json", json.dumps(data))
    return buffer.getvalue()


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


@pytest.fixture()
def release(monkeypatch):
    payload = _release_zip()
    monkeypatch.setattr(phi_base, "urlopen", lambda url, timeout: _Response(payload))
    monkeypatch.setattr(phi_base, "_MEMORY", {})
    info = {
        "record": "1",
        "version": "X",
        "url": "https://example.org/r.zip",
        "md5": hashlib.md5(payload).hexdigest(),  # noqa: S324 - Zenodo's checksum
    }
    monkeypatch.setattr(OnlinePHIBaseClient, "release", lambda self: info)
    return info


def test_the_release_is_cached_only_where_told(tmp_path, monkeypatch, release):
    monkeypatch.delenv("SABUESO_CACHE_DIR", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    in_memory = OnlinePHIBaseClient()
    assert in_memory.cache_dir is None
    assert in_memory.phenotypes("P1")["sessions"][0]["session"] == "s"
    assert not (tmp_path / "home").exists()  # nothing written without a directory
    on_disk = OnlinePHIBaseClient(cache_dir=tmp_path / "cache")
    assert on_disk.phenotypes("P2")["version"] == "X"
    written = tmp_path / "cache" / "phi-base" / "X"
    assert sorted(p.name for p in written.iterdir()) == [
        "index.json",
        "release.json",
        "sessions",
    ]
    assert [p.name for p in (written / "sessions").iterdir()] == ["s.json"]
    with pytest.raises(RecordNotFoundError):
        on_disk.phenotypes("P3")


def test_a_release_that_does_not_match_its_checksum_is_refused(tmp_path, release):
    release["md5"] = "0" * 32
    with pytest.raises(ConnectorError, match="checksum"):
        OnlinePHIBaseClient(cache_dir=tmp_path).phenotypes("P1")
    assert not (tmp_path / "phi-base" / "X").exists()
