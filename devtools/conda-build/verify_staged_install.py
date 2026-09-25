"""Verify an immutable staged Conda candidate and its clean installation."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import sys
from pathlib import Path

PACKAGE = "sabueso"
PUBLIC_DEPENDENCIES = (
    ("smonitor", "0.16.0", "py_1"),
    ("pyunitwizard", "0.27.0", "py_0"),
    ("argdigest", "0.13.0", "py_1"),
    ("depdigest", "0.11.0", "py_2"),
)
STAGING_CHANNEL = "https://conda.anaconda.org/uibcdf/label/staging/noarch"
PUBLIC_CHANNEL = "https://conda.anaconda.org/uibcdf/noarch"
PRODUCER_WORKFLOW = ".github/workflows/build_and_upload_conda_packages.yaml"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_identity(sha: str, version: str, build_number: int, run_id: int) -> None:
    _require(bool(re.fullmatch(r"[0-9a-f]{40}", sha)), "Invalid candidate SHA")
    _require(
        bool(re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version)),
        "Invalid candidate version",
    )
    _require(build_number >= 0, "Invalid build number")
    _require(run_id > 0, "Invalid staging run ID")


def verify_receipts(
    run: dict,
    evidence_dir: Path,
    sha: str,
    version: str,
    build_number: int,
    run_id: int,
) -> str:
    """Return the package digest only if the run and both receipts agree."""
    validate_identity(sha, version, build_number, run_id)
    _require(run.get("id") == run_id, "Staging run ID mismatch")
    _require(run.get("event") == "workflow_dispatch", "Not a staging dispatch")
    _require(run.get("conclusion") == "success", "Staging run did not succeed")
    _require(run.get("head_sha") == sha, "Staging run built a different commit")
    _require(run.get("path") == PRODUCER_WORKFLOW, "Unexpected producer workflow")
    attempt = run.get("run_attempt")
    _require(isinstance(attempt, int) and attempt > 0, "Invalid run attempt")

    routes = list(evidence_dir.rglob("sabueso-conda-route.json"))
    producers = list(evidence_dir.rglob("gh-run-receptor-events.json"))
    _require(len(routes) == 1 and len(producers) == 1, "Expected exactly two receipts")
    route = _read_json(routes[0])
    producer = _read_json(producers[0])
    _require(route.get("schema") == "sabueso.conda-route@1", "Unexpected route schema")
    _require(route.get("candidate_sha") == sha, "Route commit mismatch")
    _require(route.get("version") == version, "Route version mismatch")
    _require(route.get("route") == "staged", "Not a staged release route")
    _require(route.get("gates"), "No CI gate recorded")
    _require(
        producer.get("schema") == "gh-run-receptor.events@1", "Unexpected event schema"
    )
    subject = producer.get("subject", {})
    _require(subject.get("repository") == "uibcdf/sabueso", "Wrong producer repository")
    _require(subject.get("head_sha") == sha, "Producer commit mismatch")
    _require(subject.get("run_id") == run_id, "Producer run mismatch")
    _require(subject.get("run_attempt") == attempt, "Producer attempt mismatch")
    _require(
        subject.get("job_key") == "conda_deployment_with_new_tag", "Wrong producer job"
    )
    events = producer.get("events", [])
    _require(len(events) == 1, "Expected exactly one package event")
    event = events[0]
    filename = f"{PACKAGE}-{version}-py_{build_number}.tar.bz2"
    _require(event.get("kind") == "conda.package", "Wrong artifact kind")
    _require(event.get("artifact") == filename, "Wrong artifact filename")
    _require(event.get("platform") == "noarch", "Wrong artifact platform")
    _require(event.get("build") == "success", "Build failed")
    _require(event.get("upload") == "success", "Upload failed")
    digest = event.get("sha256")
    _require(
        isinstance(digest, str) and bool(re.fullmatch(r"[0-9a-f]{64}", digest)),
        "Invalid digest",
    )
    return digest


def verify_installed(
    prefix: Path, sha256: str, version: str, build_number: int, python_version: str
) -> None:
    """Check the installed bytes, source channels, interpreter, import, and API."""
    _require(bool(re.fullmatch(r"[0-9a-f]{64}", sha256)), "Invalid expected digest")
    _require(
        f"{sys.version_info.major}.{sys.version_info.minor}" == python_version,
        "Wrong Python",
    )
    _require(prefix.resolve() == Path(sys.prefix).resolve(), "Wrong environment prefix")
    build = f"py_{build_number}"
    package_record = _read_json(
        prefix / "conda-meta" / f"{PACKAGE}-{version}-{build}.json"
    )
    _require(package_record.get("name") == PACKAGE, "Wrong package record")
    _require(
        package_record.get("version") == version, "Wrong installed package version"
    )
    _require(package_record.get("build") == build, "Wrong installed package build")
    _require(package_record.get("subdir") == "noarch", "Package not noarch")
    _require(
        package_record.get("sha256") == sha256, "Installed package digest mismatch"
    )
    _require(
        package_record.get("url")
        == f"{STAGING_CHANNEL}/{PACKAGE}-{version}-{build}.tar.bz2",
        "Wrong package URL",
    )
    for dependency, dependency_version, dependency_build in PUBLIC_DEPENDENCIES:
        dependency_record = _read_json(
            prefix
            / "conda-meta"
            / f"{dependency}-{dependency_version}-{dependency_build}.json"
        )
        _require(dependency_record.get("name") == dependency, "Wrong dependency record")
        _require(
            dependency_record.get("version") == dependency_version,
            "Wrong dependency version",
        )
        _require(
            dependency_record.get("build") == dependency_build,
            "Wrong dependency build",
        )
        _require(
            dependency_record.get("url")
            == f"{PUBLIC_CHANNEL}/{dependency}-{dependency_version}-{dependency_build}.tar.bz2",
            "Dependency not from public channel",
        )

    _require(
        importlib.metadata.version(PACKAGE) == version, "Distribution version mismatch"
    )
    import sabueso

    _require(sabueso.__version__ == version, "Imported module version mismatch")
    _require(
        Path(sabueso.__file__).resolve().is_relative_to(prefix.resolve()),
        "Imported the source checkout instead of the installed package",
    )
    _require(api_smoke(), "Installed API smoke failed")


def api_smoke() -> bool:
    """A card is built from a mapping, which reads the packaged selection rules (#35),
    and its quantity survives its own seal: to_dict() writes the PyUnitWizard
    QuantityRecordBundle and from_dict() verifies it (#32)."""
    import pyunitwizard as puw

    from sabueso.core.aggregator import build_card_from_mapping
    from sabueso.core.card import Card
    from sabueso.core.source_assertion_store import make_source_assertion

    field = "properties.physchem.tpsa"
    assertion = make_source_assertion(field, 63.6, "PubChem", "5978", "2026-09-24")
    mapping = {
        "fields": {field: 63.6},
        "source_assertions": [assertion],
        "field_source_assertions": {field: [assertion["id"]]},
        "relationships": [],
    }
    card = build_card_from_mapping(
        mapping,
        meta={"entity_type": "small_molecule"},
        card_id="sabueso:small_molecule:smoke",
    )
    again = Card.from_dict(card.to_dict())
    if puw.get_value(again.quantity(field), to_unit="angstrom**2") != 63.6:
        return False
    # Packaged data added in 0.2.0: the enrichment profiles (#45).
    from sabueso.resolver.loader import load_enrichment_profiles

    if "structural_baseline@1" not in load_enrichment_profiles():
        return False
    # The glossary of entities is written and read back (#52).
    if "smoke" not in str(again.to_dict().get("entities")):
        return False
    # Added in 0.3.0: the knowledge store round trip on the installed package, with its
    # pinned reference (#7, #27), and the knowledge-state view (#56).
    import tempfile

    import sabueso

    with tempfile.TemporaryDirectory() as tmp:
        store = sabueso.KnowledgeStore(Path(tmp) / "knowledge.db")
        ref = store.save(again, note="smoke")
        if ref != again.pinned_ref() or store.load(ref).to_dict() != again.to_dict():
            return False
        del store  # every connection is closed per call; Windows can remove the file
    if not isinstance(again.knowledge_state().get("rows"), list):
        return False
    # pandas is optional: without it, the DepDigest check answers (#46).
    import importlib.util

    if importlib.util.find_spec("pandas") is None:
        import sabueso
        from sabueso.core.errors import LibraryNotFoundError

        try:
            sabueso.to_dataframe([])
        except LibraryNotFoundError:
            pass
        else:
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    receipts = subparsers.add_parser("receipts")
    receipts.add_argument("--run", type=Path, required=True)
    receipts.add_argument("--evidence-dir", type=Path, required=True)
    receipts.add_argument("--sha", required=True)
    receipts.add_argument("--version", required=True)
    receipts.add_argument("--build-number", type=int, required=True)
    receipts.add_argument("--run-id", type=int, required=True)
    installed = subparsers.add_parser("installed")
    installed.add_argument("--prefix", type=Path, required=True)
    installed.add_argument("--sha256", required=True)
    installed.add_argument("--version", required=True)
    installed.add_argument("--build-number", type=int, required=True)
    installed.add_argument("--python-version", required=True)
    args = parser.parse_args()
    if args.mode == "receipts":
        digest = verify_receipts(
            _read_json(args.run),
            args.evidence_dir,
            args.sha,
            args.version,
            args.build_number,
            args.run_id,
        )
        print(digest)
    else:
        verify_installed(
            args.prefix,
            args.sha256,
            args.version,
            args.build_number,
            args.python_version,
        )
        print("PASS: exact staged package, public dependency, import, and API")


if __name__ == "__main__":
    main()
