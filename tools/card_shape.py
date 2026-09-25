"""The shape of the cards Sabueso writes, as key paths (card schema policy, #42).

``python tools/card_shape.py --check`` compares the shape of cards built from the
fixtures with ``schemas/card_shape_<CARD_SCHEMA_VERSION>.json``; ``--write`` records it.

A shape is every key path a stored card holds, without values: sections, SourceAssertion
and relationship keys (per predicate), their qualifiers and metadata, and quality records.
Raw source content (``asserted_value``), the quantities seal (PyUnitWizard's format) and
the selection rules (versioned apart) are not part of it.

A schema version is fixed once a release publishes it, and a published version has a
frozen card in ``temp_data/frozen_cards/``. For such a version ``--write`` refuses: a
changed shape needs a new ``CARD_SCHEMA_VERSION``.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import Any, Iterator, List

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "temp_data" / "frozen_cards"
OPAQUE = {"asserted_value", "normalized_value"}


def _paths(node: Any, prefix: str) -> Iterator[str]:
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{prefix}.{key}" if prefix else str(key)
            yield here
            if key not in OPAQUE:
                yield from _paths(value, here)
    elif isinstance(node, list):
        for item in node:
            yield from _paths(item, f"{prefix}[]")


def card_shape(data: dict) -> List[str]:
    """The sorted key paths of a stored card (``Card.to_dict()`` output)."""
    paths = set()
    for key in data:
        paths.add(key)
    paths.update(_paths(data.get("meta") or {}, "meta"))
    paths.update(_paths(data.get("sections") or {}, "sections"))
    paths.update(_paths(data.get("quality") or {}, "quality"))
    for entry in (data.get("entities") or {}).values():  # keys are entity refs
        paths.update(_paths(entry, "entities[]"))
    for assertion in data.get("source_assertion_store") or []:
        paths.update(_paths(assertion, "source_assertion_store[]"))
    for relationship in data.get("relationship_store") or []:
        predicate = relationship.get("predicate")
        paths.update(_paths(relationship, f"relationship_store[{predicate}]"))
    return sorted(paths)


def fixture_cards() -> List[dict]:
    """Cards built from the offline fixtures, covering every kind of stored content."""
    sys.path.insert(0, str(ROOT))
    import sabueso
    from sabueso.resolver import (
        EntityResolver,
        FixtureRCSBClient,
        FixtureUniProtClient,
    )
    from sabueso.tools.db.alphafold import FixtureAlphaFoldClient
    from sabueso.tools.db.chembl import FixtureChEMBLClient
    from sabueso.tools.db.interpro import FixtureInterProClient
    from sabueso.tools.db.pdb_ccd import FixtureCCDClient
    from sabueso.tools.db.pdbe_kb import FixturePDBeKBClient
    from sabueso.tools.db.pubchem import create_compound_card_from_file
    from sabueso.tools.db.stringdb import FixtureStringClient
    from sabueso.tools.db.unichem import FixtureUniChemClient

    data = str(ROOT / "temp_data")
    resolver = EntityResolver(
        FixtureUniProtClient(data), rcsb_client=FixtureRCSBClient(data)
    )
    chembl = FixtureChEMBLClient(data)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        tctim, _ = sabueso.resolve(
            "P52270",
            resolver=resolver,
            profile="structural_baseline@1",
            chembl_client=chembl,
            pdbe_kb_client=FixturePDBeKBClient(data),
            interpro_client=FixtureInterProClient(data),
            predicted_structures=True,
            alphafold_client=FixtureAlphaFoldClient(data),
        )
        hstim, _ = sabueso.resolve(
            "P60174",
            resolver=resolver,
            structures=["1HTI", "1KLG"],
            chembl={},
            chembl_client=chembl,
            string={},
            string_client=FixtureStringClient(data),
        )
        hstim.add_literature_assertion(
            "features_positional.natural_variant",
            {
                "start": 105,
                "substitution": {"original": "E", "alternatives": ["D"]},
                "description": "curated for the shape",
            },
            "pubmed:18562316",
            "shape",
            locator="Title",
            quote="shape",
            eco_code="ECO:0000269",
            curated_at="2026-09-24",
        )
        hstim.add_literature_assertion(
            "properties.physchem.logp", 1.0, "pubmed:1", "shape", method="shape"
        )
        hstim.add_literature_relationship(
            "interacts_with", "uniprot:Q00001", {"method": "shape"}, "pubmed:1", "shape"
        )
        hstim.add_literature_bioactivity(
            {"inchikey": "XBNHRNFODJOFRU-UHFFFAOYSA-N", "records": ["chembl:CHEMBL1"]},
            "IC50",
            "33 uM",
            "pubmed:1",
            "shape",
            "direct",
            assay_description="shape",
        )
        hstim.add_literature_bioactivity(
            {"inchikey": "XBNHRNFODJOFRU-UHFFFAOYSA-N", "records": ["chembl:CHEMBL1"]},
            "Ki",
            "10 uM",
            "pubmed:1",
            "shape",
            "direct",
            upper_value="20 uM",
            uncertainty={
                "kind": "ci",
                "lower": "8 uM",
                "upper": "12 uM",
                "level": 0.95,
                "n": 3,
            },
        )
        hstim.add_literature_bioactivity(
            {"inchikey": "XBNHRNFODJOFRU-UHFFFAOYSA-N", "records": ["chembl:CHEMBL1"]},
            "Kd",
            "12 nM",
            "pubmed:1",
            "shape",
            "direct",
            uncertainty={"kind": "sd", "value": "3 nM"},
        )
        molecule, _ = sabueso.resolve(
            "pdb.ligand:BTS",
            chembl_client=chembl,
            ccd_client=FixtureCCDClient(data),
            unichem_client=FixtureUniChemClient(data),
        )
        compound = create_compound_card_from_file(
            ROOT / "temp_data" / "5978.json", "2026-09-24"
        )
    return [c.to_dict() for c in (tctim, hstim, molecule, compound)]


def current_shape() -> List[str]:
    return sorted({p for card in fixture_cards() for p in card_shape(card)})


def shape_file(version: str) -> Path:
    return ROOT / "schemas" / f"card_shape_{version}.json"


def published(version: str) -> bool:
    return any(FROZEN.glob(f"schema_{version}__*.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="record the shape")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    from sabueso.core.card import CARD_SCHEMA_VERSION

    shape = current_shape()
    path = shape_file(CARD_SCHEMA_VERSION)
    if args.write:
        if published(CARD_SCHEMA_VERSION) and path.exists():
            print(
                f"Card schema {CARD_SCHEMA_VERSION} is published (a frozen card exists): "
                "its shape is fixed. Bump CARD_SCHEMA_VERSION instead (#42)."
            )
            return 1
        path.write_text(
            json.dumps(
                {"schema_version": CARD_SCHEMA_VERSION, "paths": shape}, indent=1
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"wrote {path.relative_to(ROOT)} ({len(shape)} paths)")
        return 0
    stored = json.loads(path.read_text(encoding="utf-8"))["paths"]
    added = sorted(set(shape) - set(stored))
    removed = sorted(set(stored) - set(shape))
    if added or removed:
        print("Card shape changed:", {"added": added, "removed": removed})
        return 1
    print(f"OK: cards match the recorded shape of schema {CARD_SCHEMA_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
