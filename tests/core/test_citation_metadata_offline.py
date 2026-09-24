"""Citation metadata, as the sibling components ship it (MOLI Zenodo policy; the profile
MolSysSuite members follow, see uibcdf/moli#14): CITATION.cff is the single source for
GitHub and for Zenodo. There is no .zenodo.json, which would silently override it."""

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
    assert not (ROOT / ".zenodo.json").exists()
