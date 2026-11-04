"""The declared installed-consumer receiving files must run in isolation (#165)."""

import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def test_declared_bioactivity_policy_runs_without_checkout_files():
    root = Path(__file__).resolve().parents[2]
    name = "test_bioactivity_class_v4_offline.py"
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert any("cp " in line and name in line for line in workflow.splitlines())
        assert any(
            "python -m pytest " in line and name in line
            for line in workflow.splitlines()
        )
        assert "data/bioactivity_default_legacy_v1.json.gz" in workflow
    with tempfile.TemporaryDirectory(prefix="sabueso-activity-receiving-") as directory:
        stage = Path(directory)
        shutil.copyfile(root / "tests/core" / name, stage / name)
        (stage / "data").mkdir()
        original = "bioactivity_default_legacy_v1.json.gz"
        shutil.copyfile(root / "tests/core/data" / original, stage / "data" / original)
        env = dict(os.environ, PYTHONPATH=str(stage))
        env.pop("PYTEST_ADDOPTS", None)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--receptor=llm", name],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASS exit=0" in result.stdout


def test_declared_measurement_policy_runs_without_checkout_files():
    root = Path(__file__).resolve().parents[2]
    name = "test_measurement_correspondence_offline.py"
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert any("cp " in line and name in line for line in workflow.splitlines())
        assert any(
            "python -m pytest " in line and name in line
            for line in workflow.splitlines()
        )
    with tempfile.TemporaryDirectory(
        prefix="sabueso-measurement-receiving-"
    ) as directory:
        stage = Path(directory)
        shutil.copyfile(root / "tests/core" / name, stage / name)
        env = dict(os.environ, PYTHONPATH=str(stage))
        env.pop("PYTEST_ADDOPTS", None)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--receptor=llm", name],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASS exit=0" in result.stdout


def test_current_quaternary_packet_case_is_self_contained_in_declared_receiving_scope():
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    names = re.findall(r'cp tests/core/(\S+) "\$client_dir/"', workflow)
    # Tiny receiving inputs only; no second environment, installation or source call.
    with tempfile.TemporaryDirectory(prefix="sabueso-receiving-scope-") as directory:
        stage = Path(directory)
        for name in names:
            shutil.copyfile(root / "tests/core" / name, stage / name)
        code = """
import socket
from pathlib import Path
def forbidden(*a, **k): raise AssertionError('No source requests')
socket.create_connection = forbidden
socket.socket.connect = forbidden
import test_oligomer_explanation_offline as receiving
receiving.test_full_and_index_packets_declare_current_rule_and_preserve_saved_results(Path.cwd())
assert Path(receiving.__file__).resolve().parent == Path.cwd().resolve()
print('PASS isolated declared receiving files, current quaternary packets and original pins')
"""
        env = dict(os.environ, PYTHONPATH=str(stage))
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASS isolated declared receiving files" in result.stdout


def test_declared_nonpolymer_reader_and_original_data_run_outside_checkout():
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    name = "test_card_saved_nonpolymer_assembly_offline.py"
    component = "test_card_saved_component_navigation_offline.py"
    cell_support = "test_cell_serialization_support_offline.py"
    names = re.findall(r'cp tests/core/(\S+) "\$client_dir/"', workflow)
    assert name in names
    assert component in names
    assert cell_support in names
    command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
    arguments = shlex.split(command[1])
    assert name in arguments
    assert component in arguments
    assert cell_support in arguments
    selected_files = [argument for argument in arguments if argument.endswith(".py")]
    assert len(selected_files) == len(set(selected_files))
    originals = re.findall(r'cp tests/core/data/(\S+) "\$client_dir/data/"', workflow)
    assert {
        "assembly_nonpolymer_live_v2.json.gz",
        "card_exploration_quaternary_v1.json.gz",
        "assembly_component_navigation_live_v1.json.gz",
        "card_structure_assembly_saved_v6.json.gz",
        "card_nonpolymer_navigation_saved_v7.json.gz",
    } <= set(originals)
    # Qualify the declared receiving payload, using the shared editable package.
    # Actual installed-package import/receiving qualification belongs to CI.
    with tempfile.TemporaryDirectory(
        prefix="sabueso-nonpolymer-receiving-"
    ) as directory:
        stage = Path(directory)
        shutil.copyfile(root / "tests/core" / name, stage / name)
        shutil.copyfile(root / "tests/core" / component, stage / component)
        shutil.copyfile(root / "tests/core" / cell_support, stage / cell_support)
        (stage / "data").mkdir()
        for original in originals:
            shutil.copyfile(
                root / "tests/core/data" / original, stage / "data" / original
            )
        env = dict(os.environ, PYTHONPATH=str(stage))
        env.pop("PYTEST_ADDOPTS", None)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--receptor=llm",
                "-o",
                "tmp_path_retention_policy=failed",
                f"{name}::test_each_genuine_original_preserves_complete_rows_and_native_keys[1HTI]",
                f"{name}::test_each_genuine_original_preserves_complete_rows_and_native_keys[legacy]",
                f"{component}::test_original_component_destination_reopens_without_current_producers[position]",
                f"{cell_support}::test_owned_support_and_defensive_reference_produce_identical_original_bytes[generic]",
            ],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "4 passed" in result.stdout
        assert not (stage / "temp_data").exists()
