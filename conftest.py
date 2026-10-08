"""Keep unshared native-input qualification explicit in the repository test route."""

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
DELIVERY = json.loads(
    (ROOT / "devguide/sources/fixture_delivery.json").read_text(encoding="utf-8")
)
LOCAL_MODULES = set(DELIVERY["local_qualification_tests"])


def pytest_addoption(parser):
    parser.addoption(
        "--local-source-inputs",
        action="store_true",
        default=False,
        help="Include native-response qualification requiring reviewed local-only originals.",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "local_source_inputs: qualification requiring unshared native originals",
    )


def pytest_sessionstart(session):
    if not session.config.getoption("--local-source-inputs"):
        return
    errors = []
    for row in DELIVERY["files"]:
        if row["delivery"] != "local_only":
            continue
        path = ROOT / row["path"]
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            errors.append(row["path"] + ": original path is not contained")
        elif not path.is_file():
            errors.append(row["path"] + ": original is missing")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            errors.append(row["path"] + ": original digest differs")
    if errors:
        raise pytest.UsageError(
            "Local-source-input qualification requires reviewed originals:\n"
            + "\n".join(errors)
        )


def pytest_ignore_collect(collection_path, config):
    if config.getoption("--local-source-inputs"):
        return None
    try:
        name = collection_path.relative_to(ROOT).as_posix()
    except ValueError:
        return None
    return True if name in LOCAL_MODULES else None


def pytest_collection_modifyitems(config, items):
    for item in items:
        if (
            item.path.is_relative_to(ROOT)
            and item.path.relative_to(ROOT).as_posix() in LOCAL_MODULES
        ):
            item.add_marker(pytest.mark.local_source_inputs)
        if item.get_closest_marker("local_source_inputs") and not config.getoption(
            "--local-source-inputs"
        ):
            item.add_marker(
                pytest.mark.skip(
                    reason="Native original remains local-only; use --local-source-inputs."
                )
            )


def pytest_report_header(config):
    if config.getoption("--local-source-inputs"):
        return "Fixture scope: repository inputs + verified local-only originals."
    return f"Fixture scope: repository inputs; {len(LOCAL_MODULES)} local qualification modules require --local-source-inputs."
