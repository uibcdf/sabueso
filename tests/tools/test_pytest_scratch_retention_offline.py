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


@pytest.mark.parametrize("policy", ["failed", "all"])
def test_original_archives_live_until_module_teardown_and_respect_debug_policy(
    tmp_path, policy
):
    """Use actual frozen readers; never delete failed outputs or compressed inputs."""
    client = tmp_path / "original-readers"
    client.mkdir()
    basetemp = client / "scratch"
    caller = client / "caller-output.txt"
    caller.write_text("caller output", encoding="utf-8")
    factories = [
        ("test_card_saved_literature_offline", "original", "control.archive.name"),
    ]
    if policy == "failed":
        factories += [
            (
                "test_card_molecule_activity_history_offline",
                "original",
                "control.archive.name",
            ),
            (
                "test_card_molecule_activity_history_offline",
                "multifocal_original",
                "control.archive.name",
            ),
            (
                "test_card_molecule_activity_binding_offline",
                "original_graph",
                "control.archive.name",
            ),
            (
                "test_card_molecule_activity_exact_binding_offline",
                "original_tar",
                "control",
            ),
            (
                "test_card_saved_molecule_activity_originals_offline",
                "sdk205_original",
                "control.archive.name",
            ),
            (
                "test_card_saved_molecule_activity_originals_offline",
                "sdk208_original",
                "control.archive.name",
            ),
            (
                "test_card_saved_molecule_activity_offline",
                "retained_writer",
                "control.archive.name",
            ),
        ]
    (client / "conftest.py").write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT / 'tests/core')!r})\n"
        + "\n".join(
            f"from {module} import {factory} as archive_{index}"
            for index, (module, factory, _) in enumerate(factories)
        )
        + "\n",
        encoding="utf-8",
    )
    modules = []
    for index, (_, _, expression) in enumerate(factories):
        before = client / f"test_{index:02d}_consumer.py"
        after = client / f"test_{index:02d}_released.py"
        record = client / f"archive-{index}.txt"
        # The final consumer deliberately fails. Its per-case output must survive,
        # while the reproducible archive's module lifetime still ends normally.
        intentional = index == len(factories) - 1
        before.write_text(
            "from pathlib import Path\n"
            f"def test_reader(archive_{index}, tmp_path):\n"
            f"    control = archive_{index}\n"
            f"    path = Path({expression})\n"
            "    assert path.is_file() and path.stat().st_size > 0\n"
            f"    Path({str(record)!r}).write_text(str(path), encoding='utf-8')\n"
            "    (tmp_path / 'failure-diagnosis.txt').write_text('keep me', encoding='utf-8')\n"
            + (
                "    assert False, 'intentional consumer failure'\n"
                if intentional
                else ""
            ),
            encoding="utf-8",
        )
        after.write_text(
            "from pathlib import Path\n"
            "def test_archive_lifetime():\n"
            f"    path = Path(Path({str(record)!r}).read_text(encoding='utf-8'))\n"
            f"    assert path.exists() is {policy == 'all'!r}\n"
            f"    assert Path({str(caller)!r}).read_text(encoding='utf-8') == 'caller output'\n",
            encoding="utf-8",
        )
        modules += [str(before), str(after)]
    assets = ROOT / "tests/core/data"
    # Reader setup already verifies the complete original digest/member graph.
    # Retain the immutable compressed input identities around actual child teardown.
    import hashlib

    originals = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in assets.glob("*.tar.gz")
    }
    environment = dict(os.environ)
    environment.pop("PYTEST_ADDOPTS", None)
    environment.pop("PYTEST_PLUGINS", None)
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(ROOT / "pyproject.toml"),
            "--basetemp",
            str(basetemp),
            "--receptor=llm",
            "-o",
            f"tmp_path_retention_policy={policy}",
            *modules,
        ],
        cwd=client,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=240,
    )
    output = result.stdout + result.stderr
    (client / "child-output.txt").write_text(output, encoding="utf-8")
    assert result.returncode == 1, output
    assert f"1 failed, {2 * len(factories) - 1} passed" in output, output
    assert list(basetemp.rglob("failure-diagnosis.txt"))
    assert caller.read_text(encoding="utf-8") == "caller output"
    assert all(
        hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in originals.items()
    )
