"""Card schema versioning policy (uibcdf/sabueso#42).

A stored card states its schema; this Sabueso reads its own schema line, reads newer
versions of that line with a warning and keeps what it does not know, and refuses other
lines until a migration exists (#51). Cards written by published releases are kept
frozen and must stay readable.
"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from sabueso._private.smonitor.warnings import NewerCardSchemaWarning
from sabueso.core.card import CARD_SCHEMA_VERSION, Card
from sabueso.core.errors import StorageError
from sabueso.core.schema_version import parse

FROZEN = sorted(Path("temp_data/frozen_cards").glob("schema_*__*.json"))


def _frozen(name="schema_0.3.0__P52270.json"):
    return json.loads(Path("temp_data/frozen_cards", name).read_text(encoding="utf-8"))


def _resealed(data):
    from sabueso.core.quantities import seal

    data = copy.deepcopy(data)
    data.pop("quantities", None)
    data["quantities"] = seal(data)
    return data


@pytest.mark.parametrize("path", FROZEN, ids=[p.name for p in FROZEN])
def test_cards_of_published_releases_stay_readable(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    card = Card.from_dict(data)
    assert card.meta["schema_version"] == path.name.split("__")[0][len("schema_") :]
    assert card.structures()["items"]  # views work on it
    assert card.quantity("sequence.molecular_weight") is not None


def test_the_release_0_1_1_card_keeps_what_it_stated():
    card = Card.from_dict(_frozen())
    assert card.id == "sabueso:protein:uniprot:P52270"
    assert card.meta["schema_version"] == "0.3.0"
    # Reading does not upgrade it silently: saved again, it states its own schema.
    assert card.to_dict()["meta"]["schema_version"] == "0.3.0"


def test_a_card_from_a_newer_sabueso_is_read_with_a_warning_and_kept_whole():
    data = _frozen()
    major, minor, patch = parse(CARD_SCHEMA_VERSION)
    data["meta"]["schema_version"] = f"{major}.{minor}.{patch + 7}"
    data["sections"]["future_section"] = {"value": "x", "source_assertion_ids": []}
    data["future_top_level"] = {"kept": True}
    with pytest.warns(NewerCardSchemaWarning, match="newer"):
        card = Card.from_dict(_resealed(data))
    again = card.to_dict()
    assert again["future_top_level"] == {"kept": True}
    assert again["sections"]["future_section"]["value"] == "x"


@pytest.mark.parametrize("version", ["0.2.0", "0.4.0", "1.0.0"])
def test_another_schema_line_is_refused_until_a_migration_exists(version):
    data = _frozen()
    data["meta"]["schema_version"] = version
    with pytest.raises(StorageError, match="#51"):
        Card.from_dict(data)


@pytest.mark.parametrize("version", [None, "0.3", "v0.3.0", 3])
def test_a_missing_or_invalid_version_is_refused(version):
    data = _frozen()
    if version is None:
        del data["meta"]["schema_version"]
    else:
        data["meta"]["schema_version"] = version
    with pytest.raises(StorageError):
        Card.from_dict(data)


def test_every_new_card_states_the_current_schema():
    assert Card().meta["schema_version"] == CARD_SCHEMA_VERSION
    assert Card().to_dict()["meta"]["schema_version"] == CARD_SCHEMA_VERSION


def test_every_schema_version_in_use_has_its_schema_file():
    versions = {CARD_SCHEMA_VERSION} | {
        p.name.split("__")[0][len("schema_") :] for p in FROZEN
    }
    for version in versions:
        assert Path(f"schemas/card_schema_{version}.yaml").is_file(), version


def test_cards_match_the_recorded_shape_of_the_current_schema():
    spec = importlib.util.spec_from_file_location("card_shape", "tools/card_shape.py")
    card_shape = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(card_shape)
    stored = json.loads(card_shape.shape_file(CARD_SCHEMA_VERSION).read_text())["paths"]
    current = card_shape.current_shape()
    added = sorted(set(current) - set(stored))
    removed = sorted(set(stored) - set(current))
    assert (added, removed) == ([], []), (
        "The shape of stored cards changed. If card schema "
        f"{CARD_SCHEMA_VERSION} is published (it has a frozen card), bump "
        "CARD_SCHEMA_VERSION and add its schema file; otherwise run "
        "`python tools/card_shape.py --write` (devguide/SCHEMA.md, #42)."
    )
