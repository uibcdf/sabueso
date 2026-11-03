"""Exercise scratch lifetime in repository and copied-consumer pytest routes."""

import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def _installed_retention_arguments():
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    steps = workflow["jobs"]["ackredit-pilot"]["steps"]
    commands = [step.get("run", "") for step in steps]
    (command,) = [run for run in commands if "python -m pytest test_attribution" in run]
    (line,) = [
        line
        for line in command.replace("\\\n", " ").splitlines()
        if "python -m pytest test_attribution" in line
    ]
    tokens = shlex.split(line)
    settings = [
        tokens[index + 1] for index, token in enumerate(tokens) if token == "-o"
    ]
    (retention,) = [
        setting
        for setting in settings
        if setting.startswith("tmp_path_retention_policy=")
    ]
    return ["-o", retention]


@pytest.mark.parametrize("route", ["repository", "installed", "debug_all"])
def test_pytest_releases_only_completed_successful_case_scratch(tmp_path, route):
    client = tmp_path / "client"
    client.mkdir()
    caller = client / "caller-output.txt"
    caller.write_text("owned by the caller", encoding="utf-8")
    if route == "installed":
        config = client / "pytest.ini"
        config.write_text("[pytest]\n", encoding="utf-8")
        arguments = _installed_retention_arguments()
    else:
        config = ROOT / "pyproject.toml"
        arguments = (
            ["-o", "tmp_path_retention_policy=all"] if route == "debug_all" else []
        )
    # The manifest is outside the child's basetemp, as are caller-owned outputs.
    # Tiny payloads prove lifetime without exhausting a host to reproduce the CI failure.
    (client / "test_lifetime.py").write_text(
        """
import os
from pathlib import Path
import pytest

CLIENT = Path(__file__).resolve().parent

@pytest.fixture(scope="module")
def shared(tmp_path_factory):
    path = tmp_path_factory.mktemp("shared") / "shared.txt"
    path.write_text("shared", encoding="utf-8")
    (CLIENT / "shared-path").write_text(str(path), encoding="utf-8")
    return path

def test_01_success(tmp_path, shared):
    (tmp_path / "payload").write_text("successful scratch", encoding="utf-8")
    (CLIENT / "passed-path").write_text(str(tmp_path), encoding="utf-8")
    assert shared.read_text(encoding="utf-8") == "shared"

def test_02_failure(tmp_path, shared):
    (tmp_path / "payload").write_text("failure diagnosis", encoding="utf-8")
    (CLIENT / "failed-path").write_text(str(tmp_path), encoding="utf-8")
    assert False, "intentional failure to verify retention"

def test_03_shared_still_live(shared):
    assert shared.read_text(encoding="utf-8") == "shared"

def test_04_completed_case_retention(shared):
    passed = Path((CLIENT / "passed-path").read_text(encoding="utf-8"))
    failed = Path((CLIENT / "failed-path").read_text(encoding="utf-8"))
    assert passed.exists() == (os.environ["SCRATCH_EXPECT_ALL"] == "1")
    assert (failed / "payload").read_text(encoding="utf-8") == "failure diagnosis"
    assert shared.read_text(encoding="utf-8") == "shared"
    assert (CLIENT / "caller-output.txt").read_text(encoding="utf-8") == "owned by the caller"
""",
        encoding="utf-8",
    )
    basetemp = tmp_path / "child-scratch"
    environment = dict(os.environ, SCRATCH_EXPECT_ALL=str(int(route == "debug_all")))
    # The child exercises a single pytest process, even under a distributed parent.
    environment.pop("PYTEST_ADDOPTS", None)
    environment.pop("PYTEST_PLUGINS", None)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(config),
            "--basetemp",
            str(basetemp),
            "--receptor=llm",
            *arguments,
            str(client / "test_lifetime.py"),
        ],
        cwd=client,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=90,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    assert "1 failed, 3 passed" in output, output
    passed = Path((client / "passed-path").read_text(encoding="utf-8"))
    failed = Path((client / "failed-path").read_text(encoding="utf-8"))
    shared = Path((client / "shared-path").read_text(encoding="utf-8"))
    assert passed.is_relative_to(basetemp)
    assert failed.is_relative_to(basetemp)
    assert shared.is_relative_to(basetemp)
    assert passed.exists() == (route == "debug_all")
    assert (failed / "payload").read_text(encoding="utf-8") == "failure diagnosis"
    assert shared.read_text(encoding="utf-8") == "shared"
    assert caller.read_text(encoding="utf-8") == "owned by the caller"
