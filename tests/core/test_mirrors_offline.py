"""Local mirrors (#100, phase 2): install a release, check it, read it through the same
client interface, keep it up to date, and work offline."""

import hashlib
import warnings
import zipfile

import pytest

import sabueso
import sabueso.mirrors as mirrors
from sabueso.core.errors import OfflineError, StorageError
from sabueso.tools.db import _http
from sabueso.tools.db.bindingdb_mirror import MirrorBindingDBClient

COLUMNS = [
    "BindingDB Reactant_set_id",
    "Ligand SMILES",
    "Ligand InChI",
    "Ligand InChI Key",
    "BindingDB MonomerID",
    "Ki (nM)",
    "IC50 (nM)",
    "Kd (nM)",
    "EC50 (nM)",
    "Curation/DataSource",
    "Article DOI",
    "PMID",
    "PubChem CID",
    "ChEMBL ID of Ligand",
    "UniProt (SwissProt) Primary ID of Target Chain 1",
    "UniProt (TrEMBL) Primary ID of Target Chain 1",
    "UniProt (SwissProt) Primary ID of Target Chain 2",
]
ROWS = [
    # one measurement of P1, two stated affinities
    [
        "1",
        "CCO",
        "",
        "KEY-A",
        "11",
        " 5",
        " 20",
        "",
        "",
        "ChEMBL",
        "10.1/x",
        "123",
        "702",
        "CHEMBL1",
        "P1",
        "",
        "",
    ],
    # a complex of P1 and P2: one row, both proteins
    [
        "2",
        "CCN",
        "",
        "KEY-B",
        "12",
        "",
        ">100000",
        "",
        "",
        "BindingDB",
        "",
        "",
        "",
        "",
        "P1",
        "",
        "P2",
    ],
    # no affinity stated: not indexed
    [
        "3",
        "CCC",
        "",
        "KEY-C",
        "13",
        "",
        "",
        "",
        "",
        "BindingDB",
        "",
        "",
        "",
        "",
        "P1",
        "",
        "",
    ],
]


@pytest.fixture()
def release_file(tmp_path):
    text = "\t".join(COLUMNS) + "\n" + "".join("\t".join(r) + "\n" for r in ROWS)
    path = tmp_path / "BindingDB_All_202609_tsv.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("BindingDB_All.tsv", text)
    return path, hashlib.md5(path.read_bytes()).hexdigest()


@pytest.fixture()
def installed(tmp_path, release_file):
    path, md5 = release_file
    root = tmp_path / "mirrors"
    info = mirrors.install(
        "bindingdb", "202609", mirror_dir=root, from_file=path, md5=md5
    )
    return root, info


def test_a_release_is_checked_indexed_and_recorded(installed):
    root, info = installed
    assert info["release"] == "202609" and info["records"] == 4
    assert mirrors.status(root)["bindingdb"]["installed"][0]["release"] == "202609"
    # Installing it again does nothing.
    assert mirrors.install("bindingdb", "202609", mirror_dir=root)["records"] == 4


def test_a_wrong_checksum_is_refused(tmp_path, release_file):
    path, _ = release_file
    with pytest.raises(StorageError, match="does not match"):
        mirrors.install(
            "bindingdb",
            "202609",
            mirror_dir=tmp_path / "m",
            from_file=path,
            md5="0" * 32,
        )


def test_the_mirror_answers_as_the_service_and_states_more(installed):
    root, info = installed
    client = MirrorBindingDBClient(info["directory"])
    answer = client.ligands("P1")
    assert (answer["access"], answer["version"]) == ("mirror", "202609")
    records = answer["record"]
    assert [(r["monomerid"], r["affinity_type"], r["affinity"]) for r in records] == [
        (11, "IC50", " 20"),
        (11, "Ki", " 5"),
        (12, "IC50", ">100000"),
    ]
    assert (
        records[0]["chembl_id"] == "CHEMBL1" and records[0]["data_source"] == "ChEMBL"
    )
    # A complex is found through each of its chains; the cutoff and ceiling apply.
    assert len(client.ligands("P2")["record"]) == 1
    assert len(client.ligands("P1", cutoff=50)["record"]) == 2
    assert client.ligands("P1", limit=1)["total_count"] == 3


def test_cards_read_an_installed_mirror_when_asked(installed, monkeypatch):
    root, _ = installed
    from sabueso.resolver import EntityResolver, FixtureUniProtClient
    from sabueso.tools.db.unichem import FixtureUniChemClient

    with mirrors.using(root), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        card, _ = sabueso.resolve(
            "P52270",
            resolver=EntityResolver(FixtureUniProtClient("temp_data")),
            bindingdb={},
            unichem_client=FixtureUniChemClient("temp_data"),
        )
    (record,) = [e for e in card.quality["enrichments"] if e["source"] == "BindingDB"]
    # The synthetic release holds nothing for P52270: not found in release 202609.
    assert (record["status"], record["version"]) == ("not_found", "202609")
    with pytest.raises(StorageError, match="not installed"):
        with mirrors.using(root, releases={"bindingdb": "202601"}):
            from sabueso.tools.db import _mirror

            _mirror.client_for("bindingdb")


def test_offline_never_asks_the_network(installed, monkeypatch):
    root, _ = installed
    asked = []
    monkeypatch.setattr(_http, "_urlopen", lambda *a, **k: asked.append(a))
    with mirrors.using(root, mode="offline"), pytest.raises(OfflineError):
        _http.urlopen("https://example.org/anything")
    assert asked == []


class _Adapter:
    source = "toy"

    def __init__(self, latest):
        self._latest = latest

    def latest(self):
        return self._latest

    def install(self, release, directory, from_file=None, md5=None):
        import json

        directory.mkdir(parents=True)
        info = {"source": "toy", "release": release, "installed_at": "now"}
        (directory / "release.json").write_text(json.dumps(info))
        return info


def test_update_policies(tmp_path, monkeypatch):
    root = tmp_path / "m"
    adapter = _Adapter("2")
    monkeypatch.setitem(mirrors.ADAPTERS, "toy", adapter)
    mirrors.install("toy", "1", mirror_dir=root)
    notice = mirrors.update("toy", "notify", mirror_dir=root)
    assert notice["newer"] and notice["installed"] == ["1"]
    assert [r["release"] for r in sabueso.tools.db._mirror.releases("toy", root)] == [
        "1"
    ]
    mirrors.update("toy", "manual", mirror_dir=root)
    assert [r["release"] for r in sabueso.tools.db._mirror.releases("toy", root)] == [
        "1",
        "2",
    ]
    adapter._latest = "3"
    result = mirrors.update("toy", "auto", keep=2, mirror_dir=root)
    assert result["removed"] == ["1"]
    assert [r["release"] for r in sabueso.tools.db._mirror.releases("toy", root)] == [
        "2",
        "3",
    ]
    with pytest.raises(ValueError):
        mirrors.update("toy", "sometimes", mirror_dir=root)
    with pytest.raises(ValueError):
        mirrors.install("nowhere", mirror_dir=root)


def test_no_directory_no_mirror(monkeypatch):
    monkeypatch.delenv("SABUESO_MIRROR_DIR", raising=False)
    with pytest.raises(StorageError, match="No mirror directory"):
        mirrors.status()
