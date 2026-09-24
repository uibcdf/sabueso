"""Citation metadata stay in agreement (MOLI Zenodo policy: shared metadata must agree
before publication). CITATION.cff is the GitHub-facing record; .zenodo.json feeds the
Zenodo archive of each release."""

import json
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _cff():
    return yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))


def _zenodo():
    return json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))


def test_citation_and_zenodo_metadata_agree():
    cff, zenodo = _cff(), _zenodo()
    assert [f"{a['family-names']}, {a['given-names']}" for a in cff["authors"]] == [
        c["name"] for c in zenodo["creators"]
    ]
    assert [a["orcid"].rsplit("/", 1)[1] for a in cff["authors"]] == [
        c["orcid"] for c in zenodo["creators"]
    ]
    assert (cff["title"], str(cff["version"]), cff["license"]) == (
        zenodo["title"],
        zenodo["version"],
        zenodo["license"],
    )
    assert cff["keywords"] == zenodo["keywords"]
    assert " ".join(cff["abstract"].split()) == zenodo["description"]


def test_citation_version_is_the_planned_release():
    plan = tomllib.loads(
        (ROOT / "devtools" / "conda-build" / "release_plan.toml").read_text(
            encoding="utf-8"
        )
    )
    assert str(_cff()["version"]) == _zenodo()["version"] == plan["version"]
