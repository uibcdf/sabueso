"""Byte/graph accounting of genuine SDK227 observations, not saved admission."""

import gzip
import hashlib
import json
import tarfile
from collections import Counter
from pathlib import Path

import pytest

CAPSULE = Path(__file__).with_name("data") / "disease_association_live_sdk227.tar.gz"
ENCODED_SHA256 = "bfc64d581db372319b7216d6a2588bb6dbaa9429d40eed800529a6359da85abf"
DECODED_SHA256 = "0b82a9f4cdc78b9891f98f7cab69c03e9ab344549acd4500337b1e08db645a2b"
DECODED_BYTES = 158453760
PRODUCER = "0e17f8561381c6016ca6ebe77c336b357b0d4203"
CASES = (
    "public-protein",
    "public-molecule",
    "ontology-only",
    "identity-missing_equivalence",
    "identity-misbound_equivalence",
    "identity-conflicting_mapping",
    "identity-foreign_subject",
    "support-missing",
    "support-wrong_subject",
    "medgen-complete",
    "medgen-missing",
    "medgen-misbound",
    "medgen-conflicting",
    "medgen-unfinished",
    "input-revisions",
    "equal-conditions",
    "focal-outgoing",
    "focal-incoming",
    "unknown-channel",
    "placeholder",
    "incoherent-anchor",
)


def _sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class Original:
    """Literal original members; no current Cards or scientific interpretation."""

    def __init__(self, directory, observed):
        self.directory = directory
        self.observed = observed
        self.manifest = json.loads((directory / "manifest.json").read_text())
        self._decoded = {}

    def ref(self, ref):
        assert ref["path"] in self.manifest["files"]
        assert {key: ref[key] for key in ("bytes", "sha256")} == self.manifest["files"][
            ref["path"]
        ]
        if ref["path"] not in self._decoded:
            self._decoded[ref["path"]] = json.loads(
                (self.directory / ref["path"]).read_text()
            )
        return self._decoded[ref["path"]]

    def case(self, name):
        return self.ref(self.manifest["cases"][name])

    def nodes(self, case):
        return {
            row["node"]: {**row, "observation": self.ref(row["observation_ref"])}
            for row in case["views"]
        }

    def accesses(self, case):
        return {
            key: {
                "focal": row["focal"],
                "nonce": row["nonce"],
                **{field: self.ref(ref) for field, ref in row["fields"].items()},
            }
            for key, row in case["accesses"].items()
        }


@pytest.fixture(scope="module")
def original(tmp_path_factory):
    assert _sha(CAPSULE) == ENCODED_SHA256
    decoded, size = hashlib.sha256(), 0
    with gzip.open(CAPSULE, "rb") as stream:
        while chunk := stream.read(1024 * 1024):
            decoded.update(chunk)
            size += len(chunk)
    assert size == DECODED_BYTES and decoded.hexdigest() == DECODED_SHA256
    directory = tmp_path_factory.mktemp("disease-sdk227-original")
    observed = {}
    with tarfile.open(CAPSULE, "r|gz") as archive:
        for member in archive:
            assert member.isfile() and member.name not in observed
            target = directory / member.name
            assert target.resolve().is_relative_to(directory.resolve())
            assert member.name == target.relative_to(directory).as_posix()
            target.parent.mkdir(parents=True, exist_ok=True)
            digest, count = hashlib.sha256(), 0
            with archive.extractfile(member) as source, target.open("xb") as output:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
                    count += len(chunk)
                    output.write(chunk)
            assert count == member.size
            observed[member.name] = {"bytes": count, "sha256": digest.hexdigest()}
    result = Original(directory, observed)
    assert set(observed) == set(result.manifest["files"]) | {"manifest.json"}
    assert {
        key: value for key, value in observed.items() if key != "manifest.json"
    } == result.manifest["files"]
    return result


def test_original_producer_bytes_rights_and_scope_are_fixed(original):
    manifest = original.manifest
    assert manifest["format"] == "disease_association_live_original@1"
    assert manifest["producer_head"] == PRODUCER
    assert manifest["producer_version"] == "0.14.0+227.g0e17f85"
    assert manifest["genuine_live_original"] and manifest["capture_complete"]
    assert manifest["attempts"] == {"network": 0, "source_acquisitions": 0}
    assert set(manifest["cases"]) == set(CASES)
    before = json.loads((original.directory / "source-before.json").read_text())
    after = json.loads((original.directory / "source-after.json").read_text())
    assert before == after and "sabueso/_version.py" in before
    assert "sabueso/core/card_disease_association_access.py" in before
    assert "sabueso/core/card_exploration_disease_association.py" not in before
    assert (original.directory / "fixtures/NOTICE.md").is_file()
    assert (original.directory / "NOTICE.md").is_file()
    assert (original.directory / "LICENSE").is_file()
    for name in CASES:
        control = original.case(name)["synthetic_control"]
        assert (control is None) == (
            name in ("public-protein", "public-molecule", "ontology-only")
        )


@pytest.mark.parametrize("name", CASES)
def test_original_actual_view_access_origin_and_machine_graph(original, name):
    case = original.case(name)
    nodes, accesses = original.nodes(case), original.accesses(case)
    assert len(nodes) == len(case["views"])
    assert set(case["named_views"].values()) <= nodes.keys()
    assert case["root_access_node"] in accesses
    for row in nodes.values():
        view = row["observation"]
        assert (
            row["access_node"] in accesses and row["selection_access_node"] in accesses
        )
        assert (
            accesses[row["access_node"]]["focal"]
            == accesses[row["selection_access_node"]]["focal"]
            == view["focal"]
        )
        assert view["focal"] in accesses[row["access_node"]]["captures"]
        for origin in ("origin_node", "explorer_origin_node"):
            assert row[origin] is None or row[origin] in nodes
        if row["origin_node"] is not None:
            assert (
                view["back_view_ref"]
                == nodes[row["origin_node"]]["observation"]["view_ref"]
            )
        displayed = Counter(
            json.dumps(item["payload_location"], sort_keys=True)
            for item in view["items"]
        )
        underlying = Counter(
            json.dumps(entry["location"], sort_keys=True)
            for entry in view["selection"]["entries"]
        )
        assert displayed <= underlying
        if view["record_panel"] == "associations" and view["display_request"] is None:
            assert displayed == underlying
        for item in view["items"]:
            original.ref(item["support_ref"])
            for cell in item["cells"].values():
                original.ref(cell["support_ref"])
        original.ref(view["native_payload_ref"])
    for access in accesses.values():
        for capture in access["captures"].values():
            original.ref(capture["data_ref"])
        for ref in access["objects"].values():
            original.ref(ref)
    for query in case["queries"]:
        count = 0
        for index, ref in enumerate(query["pages"]):
            page = original.ref(ref)
            assert page["selection_ref"] == query["selection_ref"]
            assert page["page"]["blocked"] is None
            assert (page["page"]["next_cursor"] is None) == (
                index == len(query["pages"]) - 1
            )
            count += len(page["items"])
        assert count == query["count"]
    root = nodes[case["named_views"]["root"]]["observation"]
    native, oracles = (
        original.ref(root["native_payload_ref"]),
        original.ref(case["native_oracles"]),
    )
    assert len(native["input_occurrences"]) == len(oracles)
    for context in native["contexts"]:
        assert any(
            context["native_payload"] == item["native_payload"]
            and context["knowledge_state"] == item["knowledge_state"]
            for item in oracles
        )


def test_original_public_sources_and_distinct_uncertainty_controls(original):
    def root(name):
        case = original.case(name)
        nodes = original.nodes(case)
        view = nodes[case["named_views"]["root"]]["observation"]
        return view, original.ref(view["native_payload_ref"])

    def statements(view):
        return [row for row in view["items"] if row["kind"] != "association_context"]

    protein, _ = root("public-protein")
    assert {row["cells"]["source"]["value"] for row in statements(protein)} >= {
        "UniProt",
        "DISEASES",
        "Open Targets",
        "Orphanet",
        "ClinVar",
    }
    molecule, native = root("public-molecule")
    assert statements(molecule)
    assert all(
        row["kind"] == "indication_statement"
        and row["cells"]["object_ref"]["value"] == "mondo:MONDO:0001444"
        for row in statements(molecule)
    )
    assert any(
        row["original_item"]["object_ref"] == "efo:EFO:0008559"
        for row in native["exclusions"]
    )
    ontology, _ = root("ontology-only")
    assert ontology["outcome"]["status"] == "missing_prerequisite"
    assert not statements(ontology)
    for state in ("missing", "misbound", "conflicting", "unfinished"):
        view, native = root("medgen-" + state)
        assert not statements(view)
        assert any(
            row["reason"]
            == (
                "conflicting_identity"
                if state == "conflicting"
                else "incomplete_identity"
            )
            for row in native["exclusions"]
        )
    view, _ = root("medgen-complete")
    assert (
        statements(view)[0]["cells"]["identity_basis"]["value"]
        == "medgen_mondo_equivalence"
    )
    for name in ("support-missing", "support-wrong_subject"):
        view, _ = root(name)
        assert view["outcome"]["status"] == "partial"
        assert statements(view)[0]["cells"]["support_state"]["value"] == "partial"
    view, _ = root("unknown-channel")
    cell = statements(view)[0]["cells"]["channel"]
    assert cell["value"] is None and cell["state"] == "unrecognized_shape"
    view, native = root("input-revisions")
    assert len(statements(view)) == 2 and len(native["contexts"]) == 3
    assert len(native["input_occurrences"]) == 4
    assert native["input_occurrences"][1] == native["input_occurrences"][2]
    view, _ = root("equal-conditions")
    assert len(statements(view)) == 2
    assert len({row["item_ref"] for row in statements(view)}) == 2
    assert not statements(root("placeholder")[0])
    assert not statements(root("incoherent-anchor")[0])
