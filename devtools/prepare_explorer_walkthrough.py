"""Prepare public native Cards/Deck for the optional interactive review.

Frozen fixture clients only. This is developer preparation, not application
source selection, a public installation route or a scientific association.
"""

import argparse
import hashlib
import json
import socket
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=Path("temp_data"))
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_directory
    output.mkdir(parents=True, exist_ok=False)

    import sabueso
    from sabueso.core.deck import Deck
    from sabueso.resolver import EntityResolver, FixtureUniProtClient
    from sabueso.tools.card.small_molecule import build_molecule_cards
    from sabueso.tools.db import _http
    from sabueso.tools.db.chembl import FixtureChEMBLClient
    from sabueso.tools.db.clinicaltrials import FixtureClinicalTrialsClient
    from sabueso.tools.db.mondo import FixtureMONDOClient
    from sabueso.tools.db.pdb_ccd import FixtureCCDClient
    from sabueso.tools.db.rcsb import FixtureRCSBClient
    from sabueso.tools.db.unichem import FixtureUniChemClient

    def forbidden(*args, **kwargs):
        raise AssertionError("Walkthrough preparation forbids network acquisition")

    socket.socket.connect = socket.create_connection = _http._urlopen = forbidden
    data = args.fixtures
    chembl, ccd = FixtureChEMBLClient(data), FixtureCCDClient(data)
    protein = sabueso.resolve(
        "P52270",
        resolver=EntityResolver(
            FixtureUniProtClient(data), rcsb_client=FixtureRCSBClient(data)
        ),
        structures=["1SUX"],
        chembl={},
        chembl_client=chembl,
    )[0]
    molecules, unanchored = build_molecule_cards(
        chembl=chembl.molecules(["CHEMBL1161789"]), ccd=ccd.components(["BTS"])
    )
    if unanchored or len(molecules) != 1:
        raise ValueError("The public BTS capture lacks its exact native identity")
    ligand = next(iter(molecules.values()))
    molecule = sabueso.resolve(
        "chembl:CHEMBL110",
        trials={},
        chembl_client=chembl,
        clinicaltrials_client=FixtureClinicalTrialsClient(data),
        ccd_client=ccd,
        unichem_client=FixtureUniChemClient(data),
    )[0]
    disease = sabueso.resolve_disease_card(
        "MONDO:0001444", mondo_client=FixtureMONDOClient(data)
    )[0]
    cards = dict(protein=protein, ligand=ligand, molecule=molecule, disease=disease)
    for name, card in cards.items():
        (output / f"{name}-card.json").write_text(
            json.dumps(card.to_dict(), ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
    deck = Deck(
        [protein, ligand, molecule, disease, protein],
        meta={
            "purpose": "Public retained-knowledge walkthrough",
            "membership": {
                card.id: {
                    "basis": "Explicit demonstration input, not an inferred scientific association"
                }
                for card in cards.values()
            },
            "source_notice": "Existing public fixtures declared in temp_data/NOTICE.md; no new acquisition",
        },
    )
    path = output / "public-mixed-deck.jsonl"
    sabueso.save_deck_jsonl(deck, str(path))

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    manifest = {
        "owner": "uibcdf/sabueso#154/#153",
        "source": "Existing reviewed public fixtures; temp_data/NOTICE.md",
        "members": [card.pinned_ref() for card in deck.cards],
        "cards": {
            name: {
                "pin": card.pinned_ref(),
                "sha256": sha(output / f"{name}-card.json"),
            }
            for name, card in cards.items()
        },
        "deck_sha256": sha(path),
    }
    (output / "inputs.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
