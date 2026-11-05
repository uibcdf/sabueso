"""Run an offline public geometry control and refuse an unqualified Card join.

Requires the shared editable MolSysMT PR #566 source. Run from any directory:
    python check_molsysmt_structural_control_20261105.py --output NEW_DIRECTORY

This is an engineering experiment, not a public modeling API or a new Card rule.
The calculated contacts never become SourceAssertions or source-reported contacts.
"""

import argparse
import hashlib
import importlib.metadata as metadata
import json
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


def forbidden(*args, **kwargs):
    raise AssertionError("No provider requests in the public structural control")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def records(container, category):
    item = container.getObj(category)
    return [dict(zip(item.getAttributeList(), row, strict=True)) for row in item]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    output = arguments.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    socket.socket.connect = forbidden
    socket.create_connection = forbidden

    import molsysmt as msm
    import numpy as np

    import sabueso
    from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

    puw = msm.pyunitwizard
    root = Path(__file__).resolve().parents[2]
    provider = Path(msm.__file__).resolve().parents[1]
    provider_sha = subprocess.check_output(
        ["git", "-C", str(provider), "rev-parse", "HEAD"], text=True
    ).strip()
    assert provider_sha == "3635c90acc9ca2453479f5dcdf1b361f84c5bf4f"
    assert msm.__version__ == metadata.version("molsysmt")
    assert sabueso.__version__ == metadata.version("sabueso")
    installed = json.loads(
        metadata.distribution("molsysmt").read_text("direct_url.json") or "{}"
    )
    assert installed.get("dir_info", {}).get("editable")
    assert Path(unquote(urlparse(installed["url"]).path)).resolve() == provider
    coordinates_file = Path(msm.systems["TcTIM"]["1tcd.bcif.gz"])
    original_hash = hashlib.sha256(coordinates_file.read_bytes()).hexdigest()
    container = msm.convert(
        str(coordinates_file), to_form="mmcif.PdbxContainers.DataContainer"
    )
    assert records(container, "entry") == [{"id": "1TCD"}]
    revision = records(container, "pdbx_audit_revision_history")[-1]
    generators = records(container, "pdbx_struct_assembly_gen")
    assert generators == [
        {"assembly_id": "1", "oper_expression": "1", "asym_id_list": "A,B,C,D"}
    ]
    source_operator = next(
        row for row in records(container, "pdbx_struct_oper_list") if row["id"] == "1"
    )
    rotation = np.array(
        [
            [float(source_operator[f"matrix[{i}][{j}]"]) for j in range(1, 4)]
            for i in range(1, 4)
        ]
    )
    translation = puw.get_value(
        puw.quantity(
            [float(source_operator[f"vector[{i}]"]) for i in range(1, 4)], "angstrom"
        ),
        to_unit="nm",
    )
    atoms_by_id = {str(row["id"]): row for row in records(container, "atom_site")}
    assert len(atoms_by_id) == len(records(container, "atom_site"))
    assert {str(row["pdbx_PDB_model_num"]) for row in atoms_by_id.values()} == {"1"}
    assert {str(row["label_alt_id"]) for row in atoms_by_id.values()} <= {".", "?"}

    with puw.context(standard_units=["angstrom", "ns", "kcal/mol", "K"]):
        molsys = msm.convert(container, to_form="molsysmt.MolSys")
        chain_ids = msm.get(molsys, element="chain", chain_id=True)
        assert chain_ids == ["A", "B", "C", "D"]
        assert {row["id"] for row in records(container, "struct_asym")} == set(
            chain_ids
        )
        native_ids = msm.get(molsys, element="atom", atom_id=True)
        native_chains = np.asarray(msm.get(molsys, element="atom", chain_index=True))
        names = np.asarray(msm.get(molsys, element="atom", atom_name=True))
        original = puw.get_value(msm.get(molsys, coordinates=True), to_unit="nm")
        expected = puw.get_value(
            puw.quantity(
                np.array(
                    [
                        [
                            float(atoms_by_id[str(key)][f"Cartn_{axis}"])
                            for axis in "xyz"
                        ]
                        for key in native_ids
                    ]
                )[None],
                "angstrom",
            ),
            to_unit="nm",
        )
        np.testing.assert_allclose(original, expected, rtol=0, atol=1e-12)
        for index, key in enumerate(native_ids):
            assert (
                atoms_by_id[str(key)]["label_asym_id"]
                == chain_ids[native_chains[index]]
            )
        operation = msm.get(molsys, bioassembly=True)["1"]
        np.testing.assert_array_equal(operation["chain_indices"], [0, 1, 2, 3])
        np.testing.assert_array_equal(operation["rotations"], rotation[None])
        np.testing.assert_allclose(
            puw.get_value(operation["translations"][0], to_unit="nm"),
            translation,
            rtol=0,
            atol=1e-14,
        )
        assembled = msm.build.make_bioassembly(
            molsys, bioassembly="1", structure_indices=[0]
        )
        built = puw.get_value(msm.get(assembled, coordinates=True), to_unit="nm")
        np.testing.assert_allclose(
            built, original @ rotation.T + translation, rtol=0, atol=1e-12
        )
        assert msm.get(assembled, element="atom", atom_id=True) == native_ids
        assert msm.get(assembled, element="chain", chain_name=True) == msm.get(
            molsys, element="chain", chain_name=True
        )

        # Explicit source atom IDs + operation position establish this control's map.
        correspondence = [
            {
                "generated_atom_index": i,
                "source_atom_id": str(key),
                "source_asym_id": atoms_by_id[str(key)]["label_asym_id"],
                "assembly_id": "1",
                "generator_position": 0,
                "operation_position": 0,
                "source_operator_ids": ["1"],
                "source_structure_index": 0,
                "source_model_id": "1",
            }
            for i, key in enumerate(native_ids)
        ]
        endpoints_a = np.flatnonzero((native_chains == 0) & (names == "CA"))
        endpoints_b = np.flatnonzero((native_chains == 1) & (names == "CA"))
        assert len(endpoints_a) and len(endpoints_b)
        cutoff = puw.quantity(10.0, "angstrom")
        contacts = msm.structure.get_contacts(
            assembled,
            selection=endpoints_a.tolist(),
            selection_2=endpoints_b.tolist(),
            structure_indices=[0],
            structure_indices_2=[0],
            threshold=cutoff,
            pbc=False,
            cell_list=False,
            use_gpu=False,
            parallel=False,
            num_threads=1,
        )
        distance_squared = np.sum(
            (built[:, endpoints_a, None] - built[:, None, endpoints_b]) ** 2, axis=-1
        )
        np.testing.assert_array_equal(contacts, distance_squared <= 1.0)
        assert contacts.shape == (1, len(endpoints_a), len(endpoints_b))

    fixture = root / "temp_data/rcsb/1TCD.json"
    source_entry = json.loads(fixture.read_text())
    assert (
        not {"revision_date", "revision_id", "major_revision", "minor_revision"}
        & source_entry["rcsb_accession_info"].keys()
    )
    assert all(
        "pdbx_struct_assembly_gen" not in row for row in source_entry["assemblies"]
    )
    card, _ = sabueso.resolve(
        "P52270",
        resolver=EntityResolver(
            FixtureUniProtClient(root / "temp_data"),
            rcsb_client=FixtureRCSBClient(root / "temp_data/rcsb"),
        ),
        structures=["1TCD"],
    )
    before = card.to_dict()
    explorer = card.explore()
    options = {"structure_ref": "pdb:1TCD"}
    human = explorer.answer("assembly_generation", options=options)
    agent = explorer.access.select("assembly_generation", options=options)
    assert human.result_ref == agent.result_ref
    assert human.native_payload["physical_membership"] == "not_computed"
    saved = human.save(output / "knowledge.json")
    restored = sabueso.read_exploration(
        output / "knowledge.json", expected_digest=saved["bundle_digest"]
    )
    assert restored.native_payload == human.native_payload
    reader = r"""
import hashlib, json, socket, sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a, **k):
    raise AssertionError("No Card reconstruction, molecular calculation, provider or fixture access")
socket.socket.connect = forbidden
socket.create_connection = forbidden
Card.__init__ = forbidden
Card.from_dict = forbidden
def audit(event, args):
    if event == "open" and isinstance(args[0], str) and "temp_data" in args[0].split("/"):
        forbidden()
sys.addaudithook(audit)
restored = sabueso.read_exploration(sys.argv[1], expected_digest=sys.argv[2])
assert hashlib.sha256(json.dumps(restored.native_payload, sort_keys=True).encode()).hexdigest() == sys.argv[3]
assert restored.result_ref == restored.explorer.access.select("assembly_generation", options={"structure_ref": "pdb:1TCD"}).result_ref
assert "molsysmt" not in sys.modules
print("PASS independent saved knowledge reading without geometry or source access")
"""
    fresh = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            reader,
            str(output / "knowledge.json"),
            saved["bundle_digest"],
            digest(human.native_payload),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    (output / "fresh-reader.log").write_text(fresh.stdout)
    assert card.to_dict() == before
    assert hashlib.sha256(coordinates_file.read_bytes()).hexdigest() == original_hash
    (output / "atom-correspondence.json").write_text(
        json.dumps(correspondence, indent=2) + "\n"
    )
    receipt = {
        "owner": "uibcdf/sabueso#173/#148; provider uibcdf/molsysmt#563/PR566",
        "review_trigger": "provider receiving and admitted structural input contract before B3 closeout",
        "kind": "public single-source modeling control plus unqualified cross-source join refusal",
        "provider_sha": provider_sha,
        "provider_sdk": msm.__version__,
        "sabueso_sdk": sabueso.__version__,
        "coordinate_file": "molsysmt/data/bcif_gz/1tcd.bcif.gz",
        "coordinate_sha256": original_hash,
        "coordinate_revision": revision,
        "entry": "1TCD",
        "generator_rows": generators,
        "atomic_input": {
            "structure_index": 0,
            "model_id": "1",
            "alternate_location": "none present",
        },
        "generated_atom_count": built.shape[1],
        "atom_correspondence_sha256": digest(correspondence),
        "analytical_coordinates_match": True,
        "non_default_unit_policy": "angstrom",
        "contact_method": {
            "provider": "molsysmt.structure.get_contacts",
            "endpoint_semantics": "atomic C-alpha positions on source chains A and B; no group reduction or center",
            "threshold": {"value": 1.0, "unit": "nm"},
            "inclusive": True,
            "pbc": False,
            "structure_indices": [0],
            "dense_shape": list(contacts.shape),
            "true_count": int(contacts.sum()),
            "independent_squared_distance_formula_matches": True,
        },
        "knowledge_fixture": "temp_data/rcsb/1TCD.json",
        "knowledge_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        "human_agent_same_result": True,
        "saved_knowledge_same_payload": True,
        "fresh_saved_reader_without_geometry_card_or_sources": True,
        "card_unchanged": True,
        "cross_source_correspondence": "not_admitted",
        "refusal_reasons": [
            "The retained RCSB fixture has no structure revision identity.",
            "The retained RCSB fixture has no generator or numeric transform inputs.",
            "Shared entry/assembly/native labels alone cannot qualify an operation-level join.",
        ],
        "source_assertions_created_from_calculations": 0,
        "calculated_contacts_joined_to_card": 0,
        "molecular_provider_queries": 0,
        "private_pilot_inputs": 0,
        "scope": "One deposited public assembly, one model and atomic C-alpha contact criterion. No unique-copy inference, ligand-contact join, general bridge, shared protocol, researcher acceptance or B3/release completion.",
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: receipt[key]
                for key in [
                    "provider_sdk",
                    "generated_atom_count",
                    "contact_method",
                    "cross_source_correspondence",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
