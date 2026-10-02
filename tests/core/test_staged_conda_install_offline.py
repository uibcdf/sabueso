"""Exercise immutable producer provenance and installed-package checks."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "devtools" / "conda-build" / "verify_staged_install.py"
WORKFLOW = ROOT / ".github" / "workflows" / "test_staged_conda_package.yaml"
SHA = "a" * 40
DIGEST = "b" * 64
VERSION = "0.1.0"
RUN_ID = 12345

spec = importlib.util.spec_from_file_location("sabueso_staged_install", SCRIPT)
assert spec and spec.loader
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def _receipts(tmp_path: Path) -> dict:
    run = {
        "id": RUN_ID,
        "event": "workflow_dispatch",
        "conclusion": "success",
        "head_sha": SHA,
        "path": verifier.PRODUCER_WORKFLOW,
        "run_attempt": 1,
    }
    route = {
        "schema": "sabueso.conda-route@1",
        "candidate_sha": SHA,
        "version": VERSION,
        "route": "staged",
        "gates": [{"workflow": ".github/workflows/ci.yml", "run_id": 42}],
    }
    producer = {
        "schema": "gh-run-receptor.events@1",
        "subject": {
            "repository": "uibcdf/sabueso",
            "head_sha": SHA,
            "run_id": RUN_ID,
            "run_attempt": 1,
            "job_key": "conda_deployment_with_new_tag",
        },
        "events": [
            {
                "kind": "conda.package",
                "artifact": f"sabueso-{VERSION}-py_0.tar.bz2",
                "platform": "noarch",
                "build": "success",
                "upload": "success",
                "sha256": DIGEST,
            }
        ],
    }
    (tmp_path / "sabueso-conda-route.json").write_text(
        json.dumps(route), encoding="utf-8"
    )
    (tmp_path / "gh-run-receptor-events.json").write_text(
        json.dumps(producer), encoding="utf-8"
    )
    return run


def test_exact_staging_receipts_yield_package_digest(tmp_path):
    run = _receipts(tmp_path)
    assert verifier.verify_receipts(run, tmp_path, SHA, VERSION, 0, RUN_ID) == DIGEST


def test_staged_matrix_uses_candidate_verifier_and_supported_lanes():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert workflow.count("ref: ${{ inputs.candidate_sha }}") == 2
    assert workflow.count('test "$(git rev-parse HEAD)" = "$CANDIDATE_SHA"') == 2
    assert "os: [ubuntu-latest, macos-26, windows-latest]" in workflow
    assert 'test "$(uname -m)" = arm64' in workflow
    assert 'python: ["3.11", "3.12", "3.13", "3.14"]' in workflow
    assert "uibcdf/label/staging::sabueso=" in workflow
    assert "uibcdf::smonitor=0.17.0=py_0" in workflow
    assert "uibcdf::depdigest=0.11.0=py_2" in workflow
    assert "uibcdf::pyunitwizard=0.27.0=py_0" in workflow
    assert "uibcdf::argdigest=0.13.0=py_1" in workflow
    assert "pip install" not in workflow


@pytest.mark.parametrize(
    ("surface", "field", "bad_value"),
    [
        ("run", "head_sha", "c" * 40),
        ("run", "conclusion", "failure"),
        ("route", "route", "direct"),
        ("route", "version", "0.0.9"),
        ("producer", "sha256", "not-a-digest"),
        ("producer", "upload", "failure"),
        ("producer", "artifact", f"sabueso-{VERSION}-py_1.tar.bz2"),
    ],
)
def test_wrong_or_failed_receipt_is_rejected(tmp_path, surface, field, bad_value):
    run = _receipts(tmp_path)
    if surface == "run":
        run[field] = bad_value
    else:
        filename = (
            "sabueso-conda-route.json"
            if surface == "route"
            else "gh-run-receptor-events.json"
        )
        path = tmp_path / filename
        receipt = json.loads(path.read_text(encoding="utf-8"))
        if surface == "producer":
            receipt["events"][0][field] = bad_value
        else:
            receipt[field] = bad_value
        path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError):
        verifier.verify_receipts(run, tmp_path, SHA, VERSION, 0, RUN_ID)


def _installed_records(tmp_path: Path) -> None:
    meta = tmp_path / "conda-meta"
    meta.mkdir()
    records = [
        (
            "sabueso",
            VERSION,
            "py_0",
            verifier.STAGING_CHANNEL,
            DIGEST,
        ),
    ] + [
        # The verifier's own list, so that moving a pin is one edit, not three.
        (name, version, build, verifier.PUBLIC_CHANNEL, f"{i:x}" * 64)
        for i, (name, version, build) in enumerate(verifier.PUBLIC_DEPENDENCIES, 10)
    ]
    for name, version, build, channel, sha256 in records:
        filename = f"{name}-{version}-{build}.tar.bz2"
        record = {
            "name": name,
            "version": version,
            "build": build,
            "subdir": "noarch",
            "sha256": sha256,
            "url": f"{channel}/{filename}",
        }
        (meta / f"{name}-{version}-{build}.json").write_text(
            json.dumps(record), encoding="utf-8"
        )


def test_installed_gate_accepts_exact_stage_and_public_dependencies(
    tmp_path, monkeypatch
):
    _installed_records(tmp_path)
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    monkeypatch.setattr(verifier.importlib.metadata, "version", lambda _: VERSION)
    monkeypatch.setitem(
        sys.modules,
        "sabueso",
        SimpleNamespace(
            __version__=VERSION, __file__=tmp_path / "sabueso" / "__init__.py"
        ),
    )
    monkeypatch.setattr(verifier, "api_smoke", lambda: True)
    verifier.verify_installed(
        tmp_path,
        DIGEST,
        VERSION,
        0,
        f"{sys.version_info.major}.{sys.version_info.minor}",
    )


@pytest.mark.parametrize(
    ("record", "field", "bad_value"),
    [
        ("sabueso", "sha256", "0" * 64),
        (
            "sabueso",
            "url",
            f"{verifier.PUBLIC_CHANNEL}/sabueso-{VERSION}-py_0.tar.bz2",
        ),
        (
            "smonitor",
            "url",
            f"{verifier.STAGING_CHANNEL}/smonitor-0.17.0-py_0.tar.bz2",
        ),
        (
            "depdigest",
            "url",
            f"{verifier.STAGING_CHANNEL}/depdigest-0.11.0-py_2.tar.bz2",
        ),
    ],
)
def test_installed_gate_rejects_wrong_digest_or_channel(
    tmp_path, monkeypatch, record, field, bad_value
):
    _installed_records(tmp_path)
    path = next((tmp_path / "conda-meta").glob(f"{record}-*.json"))
    data = json.loads(path.read_text(encoding="utf-8"))
    data[field] = bad_value
    path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    with pytest.raises(ValueError):
        verifier.verify_installed(
            tmp_path,
            DIGEST,
            VERSION,
            0,
            f"{sys.version_info.major}.{sys.version_info.minor}",
        )


def test_the_api_smoke_really_exercises_the_quantities_seal():
    # Runs against the source checkout here; in the staged gate, against the installed file.
    assert verifier.api_smoke() is True


# --- the exact artifact (uibcdf/sabueso#77) ---------------------------------------------


def _artifact(tmp_path, version=VERSION, embedded=None, drop=None, metadata=None):
    """A conda-like .tar.bz2 with the members the archive check reads."""
    import hashlib
    import io
    import tarfile

    members = {
        "info/index.json": json.dumps({"name": "sabueso", "version": version}),
        "site-packages/sabueso/_version.py": f'__version__ = "{embedded or version}"\n',
        f"site-packages/sabueso-{version}.dist-info/METADATA": (
            f"Metadata-Version: 2.1\nName: sabueso\nVersion: {metadata or version}\n"
        ),
        **{resource: "{}" for resource in verifier.REQUIRED_RESOURCES},
    }
    members.pop(drop, None)
    path = tmp_path / f"sabueso-{version}-py_0.tar.bz2"
    with tarfile.open(path, "w:bz2") as archive:
        for name, text in members.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_the_artifact_check_accepts_the_exact_candidate(tmp_path):
    path, digest = _artifact(tmp_path)
    verifier.verify_archive(path, digest, VERSION)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"embedded": "0.0.0+unknown"}, "Embedded _version.py is stale"),
        ({"metadata": "0.3.1"}, "Distribution metadata version is stale"),
        (
            {"drop": "site-packages/sabueso/resolver/selection_rules.json"},
            "lacks site-packages/sabueso/resolver/selection_rules.json",
        ),
    ],
)
def test_the_artifact_check_rejects_a_stale_version_or_a_missing_resource(
    tmp_path, kwargs, message
):
    path, digest = _artifact(tmp_path, **kwargs)
    with pytest.raises(ValueError, match=message):
        verifier.verify_archive(path, digest, VERSION)


def test_the_artifact_check_rejects_another_digest_or_version(tmp_path):
    path, digest = _artifact(tmp_path)
    with pytest.raises(ValueError, match="digest mismatch"):
        verifier.verify_archive(path, "0" * 64, VERSION)
    with pytest.raises(ValueError, match="index version is stale"):
        verifier.verify_archive(path, digest, "9.9.9")


def test_the_required_resources_are_the_shipped_package_data():
    # Adding a package data file must add it to the artifact check.
    shipped = sorted(
        f"site-packages/{p.relative_to(ROOT).as_posix()}"
        for p in (ROOT / "sabueso" / "resolver").glob("*.json")
    )
    assert sorted(verifier.REQUIRED_RESOURCES) == shipped
