"""Prepare one public, source-mapped input cohort for both standalone hosts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def forbidden(*args, **kwargs):
    raise RuntimeError(
        "Standalone input preparation requires frozen public inputs only"
    )


def prepare(output):
    if output.exists():
        raise ValueError(
            "Choose a new output directory; original probe inputs are immutable"
        )
    path = ROOT / "examples/user_journeys/structural_context.py"
    spec = importlib.util.spec_from_file_location("public_structural_context", path)
    example = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(example)
    import molsysmt as msm

    import sabueso
    from sabueso.core.card import Card

    output.mkdir(parents=True)
    with (
        patch("socket.create_connection", forbidden),
        patch("socket.socket.connect", forbidden),
        patch("socket.socket.connect_ex", forbidden),
    ):
        example.produce(ROOT / "temp_data", output / "source")
        source = output / "source"
        card = Card.from_json(str(source / "card.json"))
        manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
        original = sabueso.read_exploration(
            source / "exploration.json.gz",
            expected_digest=manifest["receipt"]["bundle_digest"],
        )
        coordinates = (
            ROOT / "temp_data/rcsb_structural_context/coordinates/1tcd.bcif.gz"
        )
        container = msm.convert(
            str(coordinates), to_form="mmcif.PdbxContainers.DataContainer"
        )
        admitted = example._correspondence(card, container, original.native_payload)
        molsys = msm.convert(container, to_form="molsysmt.MolSys")
        atoms = example._unique(example._records(container, "atom_site"), "id")
        atom_ids = msm.get(molsys, element="atom", atom_id=True)
        chain_ids = msm.get(molsys, element="chain", chain_id=True)
        native_chains = msm.get(molsys, element="atom", chain_index=True)
        names = msm.get(molsys, element="atom", atom_name=True)
        mapping = []
        for index, atom_id in enumerate(atom_ids):
            row = atoms[str(atom_id)]
            if (
                chain_ids[native_chains[index]] != row["label_asym_id"]
                or names[index] != row["label_atom_id"]
            ):
                raise ValueError(
                    "Loaded native atom order contradicts the admitted source"
                )
            polymer = row["label_asym_id"] in {"A", "B"}
            mapping.append(
                {
                    "atom_index": index,
                    "source_atom_id": str(atom_id),
                    "source_asym_id": row["label_asym_id"],
                    "source_entity_id": str(row["label_entity_id"]),
                    "source_label_seq_id": row["label_seq_id"],
                    "source_auth_seq_id": row["auth_seq_id"],
                    "source_atom_name": row["label_atom_id"],
                    "uniprot_position": int(row["label_seq_id"]) + 2
                    if polymer
                    else None,
                    "basis": (
                        "public_tctim_coordinate_correspondence@1; explicit 1..249 -> 3..251 source alignment"
                        if polymer
                        else "coordinate entity only; no protein identity assigned"
                    ),
                }
            )
        write_json(
            output / "correspondence.json", {"admission": admitted, "atoms": mapping}
        )
        shutil.copyfile(coordinates, output / "1tcd.bcif.gz")
        shutil.copyfile(ROOT / "temp_data/NOTICE.md", output / "SOURCE_NOTICE.md")
    protected = [p for p in output.rglob("*") if p.is_file()]
    write_json(
        output / "inputs.json",
        {
            "format": "sabueso.standalone_probe_inputs@1",
            "card_ref": card.pinned_ref(),
            "scope": "Public TcTIM/1TCD only; existing correspondence criterion, no new geometry or identity rule",
            "files": {str(p.relative_to(output)): sha256(p) for p in sorted(protected)},
            "atom_count": len(mapping),
        },
    )
    print(
        f"Prepared one immutable public input cohort: {len(mapping)} source-mapped atoms"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.output.resolve())


if __name__ == "__main__":
    main()
