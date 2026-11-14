"""Prepare declared public disease-association inputs for optional Qt receiving.

This is a developer fixture workflow, not a public acquisition/installation mode.
"""

import argparse
import hashlib
import json
import socket
from pathlib import Path


def cards(fixtures):
    import sabueso
    from sabueso.resolver import EntityResolver, FixtureUniProtClient
    from sabueso.tools.db.chembl import FixtureChEMBLClient
    from sabueso.tools.db.clinvar import FixtureClinVarClient
    from sabueso.tools.db.diseases import FixtureDISEASESClient
    from sabueso.tools.db.mondo import FixtureMONDOClient
    from sabueso.tools.db.open_targets import FixtureOpenTargetsClient
    from sabueso.tools.db.orphadata import FixtureOrphadataClient
    from sabueso.tools.db.pdb_ccd import FixtureCCDClient

    mondo = FixtureMONDOClient(fixtures)
    disease = sabueso.resolve_disease_card("MONDO:0014221", mondo_client=mondo)[0]
    chagas = sabueso.resolve_disease_card("MONDO:0001444", mondo_client=mondo)[0]
    protein = sabueso.resolve(
        "P60174",
        profile="identity@1",
        resolver=EntityResolver(FixtureUniProtClient(fixtures)),
        diseases={},
        diseases_client=FixtureDISEASESClient(fixtures),
        open_targets={"limit": 3},
        open_targets_client=FixtureOpenTargetsClient(fixtures),
        orphadata=True,
        orphadata_client=FixtureOrphadataClient(fixtures),
        clinvar={"limit": 5},
        clinvar_client=FixtureClinVarClient(fixtures),
    )[0]
    molecule = sabueso.resolve(
        "chembl:CHEMBL110",
        profile="identity@1",
        unichem=False,
        indications=True,
        chembl_client=FixtureChEMBLClient(fixtures),
        ccd_client=FixtureCCDClient(fixtures),
    )[0]
    return dict(disease=disease, chagas=chagas, protein=protein, molecule=molecule)


def synthetic_phenotype_control():
    """Fictitious identifiers, explicitly synthetic source; no scientific claim."""
    from sabueso.core.card import Card
    from sabueso.core.relationship_store import make_relationship
    from sabueso.core.source_assertion_store import make_source_assertion

    disease = "mondo:MONDO:9999999"
    card = Card(
        meta={"card_id": "sabueso:disease:" + disease, "entity_type": "disease"}
    )
    source = make_source_assertion(
        "relationships.associated_with",
        {
            "phenotype_ref": "hpo:HP:9999999",
            "scope": "Explicit synthetic presentation control",
        },
        "Synthetic phenotype control",
        "not-a-scientific-source",
        "synthetic",
        subject_ref=disease,
    )
    card.source_assertion_store.add(source)
    card.relationship_store.add(
        make_relationship(
            disease,
            "associated_with",
            "hpo:HP:9999999",
            qualifiers={"source": "Synthetic phenotype control"},
            source_assertion_ids=[source["id"]],
        )
    )
    return card


def source_decks(fixtures, inputs):
    import sabueso
    from sabueso.resolver import EntityResolver, FixtureUniProtClient
    from sabueso.tools.db.chembl import FixtureChEMBLClient
    from sabueso.tools.db.open_targets import FixtureOpenTargetsClient
    from sabueso.tools.db.orphadata import FixtureOrphadataClient
    from sabueso.tools.db.pdb_ccd import FixtureCCDClient
    from sabueso.tools.db.unichem import FixtureUniChemClient

    targets = sabueso.disease_targets(
        inputs["disease"],
        limit=2,
        resolver=EntityResolver(FixtureUniProtClient(fixtures)),
        open_targets_client=FixtureOpenTargetsClient(fixtures),
        orphadata_client=FixtureOrphadataClient(fixtures),
    )
    drugs = sabueso.disease_drugs(
        inputs["chagas"],
        limit=2,
        chembl_client=FixtureChEMBLClient(fixtures),
        ccd_client=FixtureCCDClient(fixtures),
        unichem_client=FixtureUniChemClient(fixtures),
    )
    return dict(targets=targets, drugs=drugs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=Path("temp_data"))
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    import sabueso
    from sabueso.core.deck import Deck
    from sabueso.tools.db import _http

    def forbidden(*args, **kwargs):
        raise AssertionError("Public disease preparation forbids network access")

    _http._urlopen = socket.create_connection = socket.socket.connect = forbidden
    output = args.output_directory
    output.mkdir(exist_ok=False)
    inputs = cards(args.fixtures)
    for name, card in inputs.items():
        (output / (name + "-card.json")).write_text(
            json.dumps(card.to_dict(), ensure_ascii=False, separators=(",", ":"))
        )
    deck = Deck(
        [
            inputs["disease"],
            inputs["protein"],
            inputs["molecule"],
            inputs["chagas"],
            inputs["disease"],
        ],
        meta={
            "purpose": "Public retained disease/protein/indication exploration",
            "membership": {
                card.id: {
                    "basis": "Explicit demonstration input, not an inferred scientific association"
                }
                for card in inputs.values()
            },
        },
    )
    sabueso.save_deck_jsonl(deck, str(output / "public-disease-deck.jsonl"))
    for name, produced in source_decks(args.fixtures, inputs).items():
        sabueso.save_deck_jsonl(produced, str(output / (name + "-deck.jsonl")))
    control = synthetic_phenotype_control()
    (output / "synthetic-phenotype-control.json").write_text(
        json.dumps(control.to_dict(), ensure_ascii=False, separators=(",", ":"))
    )
    manifest = {
        "owner": "uibcdf/sabueso#154/#153",
        "scope": "Existing public frozen responses in temp_data/NOTICE.md; no new acquisition or new scientific fixture. synthetic-phenotype-control.json is separately labelled, with fictitious identifiers and a synthetic source; no scientific claim.",
        "files": {
            p.name: {
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "bytes": p.stat().st_size,
            }
            for p in output.iterdir()
        },
        "deck_members": [c.pinned_ref() for c in deck.cards],
    }
    (output / "inputs.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
