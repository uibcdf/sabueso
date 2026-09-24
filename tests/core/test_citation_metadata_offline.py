"""Citation metadata (MOLI Zenodo policy). CITATION.cff is the only metadata source for
GitHub and for Zenodo: releases 0.1.0 and 0.1.1, which carried a .zenodo.json, never
finished archiving, while the components archived with CITATION.cff alone did."""

import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _cff():
    return yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))


def test_citation_names_the_authors_with_orcid():
    cff = _cff()
    assert [a["family-names"] for a in cff["authors"]] == [
        "Prada-Gracia",
        "Moreno-Vargas",
    ]
    assert all(a["orcid"].startswith("https://orcid.org/") for a in cff["authors"])


def test_citation_version_is_the_planned_release():
    plan = tomllib.loads(
        (ROOT / "devtools" / "conda-build" / "release_plan.toml").read_text(
            encoding="utf-8"
        )
    )
    assert str(_cff()["version"]) == plan["version"]


def test_there_is_no_second_metadata_file_to_disagree_with():
    # .zenodo.json takes precedence over CITATION.cff on Zenodo; one source avoids drift.
    assert not (ROOT / ".zenodo.json").exists()
