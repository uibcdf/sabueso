"""The declared installed-consumer receiving files must run in isolation (#165)."""

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def test_declared_molecule_literal_topics_run_with_only_their_public_inputs():
    root = Path(__file__).resolve().parents[2]
    name = "test_card_molecule_literal_topics_offline.py"
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert (
            sum("cp " in line and name in line for line in workflow.splitlines()) == 1
        )
        command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
        assert shlex.split(command[1]).count(name) == 1
    outside_parent = None if sys.platform == "win32" else "/tmp"
    with tempfile.TemporaryDirectory(
        prefix="sabueso-molecule-literal-topics-", dir=outside_parent
    ) as directory:
        stage = Path(directory).resolve()
        assert not stage.is_relative_to(root)
        shutil.copyfile(root / "tests/core" / name, stage / name)
        for relative in (
            "chembl/molecules.json",
            "pdb_ccd_charge/pdb_ccd/SO4.json",
            "pubchem/3717450.json",
        ):
            destination = stage / "temp_data" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / "temp_data" / relative, destination)
        env = dict(os.environ, PYTHONPATH=str(stage), TMPDIR=str(stage))
        env.pop("PYTEST_ADDOPTS", None)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                name,
                "-m",
                "not online",
                "--receptor=llm",
                "--receptor-events=events.jsonl",
            ],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        raw = (stage / "events.jsonl").read_bytes().splitlines(keepends=True)
        finish = json.loads(raw[-1])
        assert finish["complete"] and finish["exitstatus"] == 0
        assert finish["counts"]["passed"] == finish["counts"]["collected"] == 17
        assert finish["counts"]["warnings"] == finish["counts"]["skipped"] == 0
        assert finish["integrity"]["records"] == len(raw) - 1
        assert (
            finish["integrity"]["digest"]
            == hashlib.sha256(b"".join(raw[:-1])).hexdigest()
        )


def test_installed_chemical_receiving_provisions_older_python_zstd():
    root = Path(__file__).resolve().parents[2]
    for workflow_path, job, environment, python_key in (
        (".github/workflows/ci.yml", "ackredit-pilot", "test", "python-version"),
        (
            ".github/workflows/test_staged_conda_package.yaml",
            "install",
            "candidate",
            "python",
        ),
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        section = re.search(
            rf"(?ms)^  {re.escape(job)}:\n(.*?)(?=^  [a-zA-Z0-9_-]+:\n|\Z)",
            workflow,
        )
        assert section is not None
        steps = re.split(r"(?m)^      - ", section[1])
        backend = [step for step in steps if "backports.zstd=1.8.0" in step]
        assert len(backend) == 1
        assert f"if: matrix.{python_key} != '3.14'" in backend[0]
        assert (
            f"micromamba install --yes -n {environment} -c uibcdf -c conda-forge "
            f'"python=${{{{ matrix.{python_key} }}}}" backports.zstd=1.8.0'
        ) in backend[0]
        assert section[1].index(backend[0]) < section[1].index("python -m pytest")
        clean_verification = (
            'python "$checker" installed'
            if job == "install"
            else "Verify installed imports outside both checkouts"
        )
        assert section[1].index(clean_verification) < section[1].index(backend[0])
        assert "test_card_saved_chemical_offline.py" in section[1]


def test_declared_saved_chemical_runs_with_only_original_live_capsule():
    root = Path(__file__).resolve().parents[2]
    name = "test_card_saved_chemical_offline.py"
    original = "chemical_live_v1.json.gz"
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert (
            sum("cp " in line and name in line for line in workflow.splitlines()) == 1
        )
        command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
        assert shlex.split(command[1]).count(name) == 1
        assert f"data/{original}" in workflow
    with tempfile.TemporaryDirectory(
        prefix="sabueso-chemical-exploration-"
    ) as directory:
        stage = Path(directory)
        shutil.copyfile(root / "tests/core" / name, stage / name)
        (stage / "data").mkdir()
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
        assert "38 passed" in result.stdout and "PASS exit=0" in result.stdout


def test_declared_chemical_exploration_runs_with_only_original_public_capsule():
    root = Path(__file__).resolve().parents[2]
    name = "test_card_chemical_exploration_offline.py"
    original = "chemical_native_sdk192.json.gz"
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert (
            sum("cp " in line and name in line for line in workflow.splitlines()) == 1
        )
        command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
        assert shlex.split(command[1]).count(name) == 1
        assert f"data/{original}" in workflow
    with tempfile.TemporaryDirectory(
        prefix="sabueso-chemical-exploration-"
    ) as directory:
        stage = Path(directory)
        shutil.copyfile(root / "tests/core" / name, stage / name)
        (stage / "data").mkdir()
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
        assert "27 passed" in result.stdout and "PASS exit=0" in result.stdout


def test_declared_chemical_classification_runs_with_only_its_public_input():
    root = Path(__file__).resolve().parents[2]
    name = "test_chemical_classification_offline.py"
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert (
            sum("cp " in line and name in line for line in workflow.splitlines()) == 1
        )
        command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
        assert shlex.split(command[1]).count(name) == 1
    with tempfile.TemporaryDirectory(
        prefix="sabueso-chemical-classification-"
    ) as directory:
        stage = Path(directory)
        shutil.copyfile(root / "tests/core" / name, stage / name)
        (stage / "temp_data/chebi").mkdir(parents=True)
        shutil.copyfile(
            root / "temp_data/chebi/compounds.json",
            stage / "temp_data/chebi/compounds.json",
        )
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
        assert "30 passed" in result.stdout and "PASS exit=0" in result.stdout


def test_declared_retained_filter_runs_without_checkout_files():
    root = Path(__file__).resolve().parents[2]
    name = "test_card_retained_filter_offline.py"
    original = "display_filter_noop_sdk187.json.gz"
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert (
            sum("cp " in line and name in line for line in workflow.splitlines()) == 1
        )
        command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
        assert shlex.split(command[1]).count(name) == 1
        assert f"data/{original}" in workflow
    with tempfile.TemporaryDirectory(prefix="sabueso-retained-filter-") as directory:
        stage = Path(directory)
        shutil.copyfile(root / "tests/core" / name, stage / name)
        (stage / "data").mkdir()
        shutil.copyfile(root / "tests/core/data" / original, stage / "data" / original)
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
                name,
            ],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=420,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "35 passed" in result.stdout and "PASS exit=0" in result.stdout
        assert not (stage / "temp_data").exists()


def test_declared_region_orientation_runs_without_checkout_files():
    root = Path(__file__).resolve().parents[2]
    name = "test_card_region_orientation_offline.py"
    original = "assembly_nonpolymer_live_v2.json.gz"
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert (
            sum("cp " in line and name in line for line in workflow.splitlines()) == 1
        )
        command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
        assert shlex.split(command[1]).count(name) == 1
        assert f"data/{original}" in workflow
    with tempfile.TemporaryDirectory(prefix="sabueso-region-orientation-") as directory:
        stage = Path(directory)
        shutil.copyfile(root / "tests/core" / name, stage / name)
        (stage / "data").mkdir()
        shutil.copyfile(root / "tests/core/data" / original, stage / "data" / original)
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
                name,
            ],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "14 passed" in result.stdout and "PASS exit=0" in result.stdout
        assert not (stage / "temp_data").exists()


def test_declared_shared_values_run_without_checkout_files():
    root = Path(__file__).resolve().parents[2]
    name = "test_exploration_shared_values_offline.py"
    original = "shared_values_v12_writer_replay.json.gz"
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert (
            sum("cp " in line and name in line for line in workflow.splitlines()) == 1
        )
        command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
        assert shlex.split(command[1]).count(name) == 1
        assert (
            sum(
                "cp " in line and f"data/{original}" in line
                for line in workflow.splitlines()
            )
            == 1
        )
    outside_parent = None if sys.platform == "win32" else "/tmp"
    with tempfile.TemporaryDirectory(
        prefix="sabueso-shared-values-receiving-", dir=outside_parent
    ) as directory:
        stage = Path(directory).resolve()
        assert not stage.is_relative_to(root)
        shutil.copyfile(root / "tests/core" / name, stage / name)
        (stage / "data").mkdir()
        shutil.copyfile(root / "tests/core/data" / original, stage / "data" / original)
        env = dict(
            os.environ,
            PYTHONPATH=str(stage),
            TMPDIR=str(stage),
            PYTHONIOENCODING="utf-8",
        )
        env.pop("PYTEST_ADDOPTS", None)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--receptor=llm",
                "-o",
                "tmp_path_retention_policy=failed",
                "--basetemp",
                str(stage / "pytest-scratch"),
                name,
            ],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "96 passed" in result.stdout and "PASS exit=0" in result.stdout
        assert not (stage / "temp_data").exists()


def test_declared_range_alias_reader_and_originals_run_without_checkout_files():
    root = Path(__file__).resolve().parents[2]
    name = "test_alphafold_range_aliases_offline.py"
    originals = (
        "model_range_alias_navigation_original_v1.json.gz",
        "model_range_alias_modern_only_legacy_v1.json.gz",
        "model_range_alias_disagreeing_legacy_v1.json.gz",
    )
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert (
            sum("cp " in line and name in line for line in workflow.splitlines()) == 1
        )
        command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
        assert shlex.split(command[1]).count(name) == 1
        for original in originals:
            assert (
                sum(
                    "cp " in line and "data/" + original in line
                    for line in workflow.splitlines()
                )
                == 1
            )
    with tempfile.TemporaryDirectory(prefix="sabueso-range-receiving-") as directory:
        stage = Path(directory)
        shutil.copyfile(root / "tests/core" / name, stage / name)
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
                name,
            ],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=180,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASS exit=0" in result.stdout
        assert not (stage / "temp_data").exists()


def test_declared_fragment_navigation_runs_without_checkout_files():
    root = Path(__file__).resolve().parents[2]
    name = "test_card_model_fragments_offline.py"
    originals = (
        "model_fragment_navigation_original_v1.json.gz",
        "assembly_nonpolymer_live_v2.json.gz",
    )
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert any("cp " in line and name in line for line in workflow.splitlines())
        command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
        assert name in shlex.split(command[1])
        for original in originals:
            assert f"data/{original}" in workflow
    # Receiving-payload qualification in the shared editable environment;
    # installed-artifact import/behavior qualification remains with hosted CI.
    with tempfile.TemporaryDirectory(prefix="sabueso-fragment-receiving-") as directory:
        stage = Path(directory)
        shutil.copyfile(root / "tests/core" / name, stage / name)
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
                name,
            ],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=240,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "41 passed" in result.stdout
        assert not (stage / "temp_data").exists()


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


def test_declared_target_scope_runs_without_checkout_files():
    root = Path(__file__).resolve().parents[2]
    name = "test_bioactivity_target_scope_offline.py"
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
    with tempfile.TemporaryDirectory(prefix="sabueso-target-receiving-") as directory:
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


def test_declared_saved_bioactivity_runs_with_only_original_public_projection():
    """One outer case receives 29 overlapping child cases, not 29 extra cases."""
    root = Path(__file__).resolve().parents[2]
    name = "test_card_saved_bioactivity_offline.py"
    original = "bioactivity_live_v1.json.gz"
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert (
            sum("cp " in line and name in line for line in workflow.splitlines()) == 1
        )
        command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
        assert shlex.split(command[1]).count(name) == 1
        assert (
            sum(
                "cp " in line and f"data/{original}" in line
                for line in workflow.splitlines()
            )
            == 1
        )
    outside_parent = None if sys.platform == "win32" else "/tmp"
    with tempfile.TemporaryDirectory(
        prefix="sabueso-saved-bioactivity-", dir=outside_parent
    ) as directory:
        stage = Path(directory)
        assert not stage.resolve().is_relative_to(root.resolve())
        shutil.copyfile(root / "tests/core" / name, stage / name)
        (stage / "data").mkdir()
        shutil.copyfile(root / "tests/core/data" / original, stage / "data" / original)
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
                name,
            ],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            # Receive the complete retained workload, including the independent
            # child's read/resave; the measured full save alone exceeds 300 s.
            timeout=1800,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "29 passed" in result.stdout and "PASS exit=0" in result.stdout
        assert not (stage / "temp_data").exists()


def test_declared_live_literature_runs_with_only_required_public_fixtures():
    """One outer case receives 45 repeated LIVE/native cases outside the checkout."""
    from pytest_receptor import read_artifact

    root = Path(__file__).resolve().parents[2]
    modules = (
        "test_card_literature_exploration_offline.py",
        "test_literature_summary_values_offline.py",
    )
    # Exact paths used by the fixture clients; MED:1 deliberately remains absent.
    fixtures = (
        "NOTICE.md",
        "P52270.json",
        "P60174.json",
        "chembl/CHEMBL5834.json",
        "chembl/molecules.json",
        "europepmc/P60174.json",
        "europepmc/annotations/PMC_PMC12400196.json",
        "europepmc/annotations/MED_18562316.json",
        "mondo/mondo.obo",
    )
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
        assert command is not None
        selection = shlex.split(command[1])
        for name in modules:
            assert (
                sum("cp " in line and name in line for line in workflow.splitlines())
                == 1
            )
            assert selection.count(name) == 1
    outside_parent = None if sys.platform == "win32" else "/tmp"
    with tempfile.TemporaryDirectory(
        prefix="sabueso-live-literature-", dir=outside_parent
    ) as directory:
        stage = Path(directory)
        assert not stage.resolve().is_relative_to(root.resolve())
        for name in modules:
            shutil.copyfile(root / "tests/core" / name, stage / name)
        for name in fixtures:
            destination = stage / "temp_data" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / "temp_data" / name, destination)
        assert {
            path.relative_to(stage).as_posix()
            for path in stage.rglob("*")
            if path.is_file()
        } == {*modules, *("temp_data/" + name for name in fixtures)}
        env = dict(os.environ, PYTHONPATH=str(stage), PYTHONDONTWRITEBYTECODE="1")
        env.pop("PYTEST_ADDOPTS", None)
        env.pop("PYTEST_PLUGINS", None)
        events = stage / "events.jsonl"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--receptor=llm",
                f"--receptor-events={events}",
                "-m",
                "not online",
                "-o",
                "tmp_path_retention_policy=failed",
                *modules,
            ],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=600,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "45 passed" in result.stdout and "PASS exit=0" in result.stdout
        artifact = read_artifact(events)
        assert artifact.complete and artifact.integrity_valid and artifact.final
        final = artifact.final.data
        assert final["complete"] and final["exitstatus"] == 0
        assert final["counts"]["collected"] == final["counts"]["executed"] == 45
        assert final["counts"]["passed"] == 45
        assert not any(
            final["counts"][key]
            for key in (
                "failed",
                "errors",
                "skipped",
                "not_executed",
                "xfailed",
                "xpassed",
            )
        )


def test_declared_molecule_activity_runs_with_only_required_public_inputs():
    """Receive the complete LIVE cohort outside the checkout, with exact inputs."""
    from pytest_receptor import read_artifact

    root = Path(__file__).resolve().parents[2]
    name = "test_card_molecule_activity_exploration_offline.py"
    original = "bioactivity_saved_original17_sdk202.json.gz"
    fixtures = (
        "NOTICE.md",
        "P52270.json",
        "chembl/CHEMBL5834.json",
        "chembl/molecules.json",
        "pdb_ccd/BTS.json",
        "rcsb/1SUX.json",
    )
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert (
            sum("cp " in line and name in line for line in workflow.splitlines()) == 1
        )
        command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
        assert command is not None and shlex.split(command[1]).count(name) == 1
        assert (
            sum(
                "cp " in line and f"data/{original}" in line
                for line in workflow.splitlines()
            )
            == 1
        )
    outside_parent = None if sys.platform == "win32" else "/tmp"
    with tempfile.TemporaryDirectory(
        prefix="sabueso-molecule-activity-", dir=outside_parent
    ) as directory:
        stage = Path(directory)
        assert not stage.resolve().is_relative_to(root.resolve())
        shutil.copyfile(root / "tests/core" / name, stage / name)
        (stage / "data").mkdir()
        shutil.copyfile(root / "tests/core/data" / original, stage / "data" / original)
        for fixture in fixtures:
            destination = stage / "temp_data" / fixture
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / "temp_data" / fixture, destination)
        assert {
            path.relative_to(stage).as_posix()
            for path in stage.rglob("*")
            if path.is_file()
        } == {
            name,
            "data/" + original,
            *("temp_data/" + fixture for fixture in fixtures),
        }
        env = dict(os.environ, PYTHONPATH=str(stage), PYTHONDONTWRITEBYTECODE="1")
        env.pop("PYTEST_ADDOPTS", None)
        env.pop("PYTEST_PLUGINS", None)
        events = stage / "events.jsonl"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--receptor=llm",
                f"--receptor-events={events}",
                "-m",
                "not online",
                "-o",
                "tmp_path_retention_policy=failed",
                name,
            ],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=600,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        artifact = read_artifact(events)
        assert artifact.complete and artifact.integrity_valid and artifact.final
        final = artifact.final.data
        assert final["complete"] and final["exitstatus"] == 0
        assert (
            final["counts"]["collected"]
            == final["counts"]["executed"]
            == final["counts"]["passed"]
            == 71
        )
        assert not any(
            final["counts"][key]
            for key in (
                "failed",
                "errors",
                "skipped",
                "not_executed",
                "reruns",
                "xfailed",
                "xpassed",
            )
        )


def test_declared_saved_literature_runs_with_only_genuine_public_capsule():
    """One outer case receives the complete overlapping saved-literature cohort."""
    from pytest_receptor import read_artifact

    root = Path(__file__).resolve().parents[2]
    name = "test_card_saved_literature_offline.py"
    originals = ("literature_live_sdk202.tar.gz", "README.md")
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert (
            sum("cp " in line and name in line for line in workflow.splitlines()) == 1
        )
        command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
        assert command is not None
        assert shlex.split(command[1]).count(name) == 1
        for original in originals:
            assert (
                sum(
                    "cp " in line and f"data/{original}" in line
                    for line in workflow.splitlines()
                )
                == 1
            )
    outside_parent = None if sys.platform == "win32" else "/tmp"
    with tempfile.TemporaryDirectory(
        prefix="sabueso-saved-literature-", dir=outside_parent
    ) as directory:
        stage = Path(directory)
        assert not stage.resolve().is_relative_to(root.resolve())
        shutil.copyfile(root / "tests/core" / name, stage / name)
        (stage / "data").mkdir()
        for original in originals:
            shutil.copyfile(
                root / "tests/core/data" / original, stage / "data" / original
            )
        # The unchanged full original carries its Card inputs and public NOTICE.
        # A current source fixture or a LIVE fixture factory would hide a missing
        # installed receiving dependency, so neither is copied into this client.
        assert {
            path.relative_to(stage).as_posix()
            for path in stage.rglob("*")
            if path.is_file()
        } == {name, *("data/" + original for original in originals)}
        env = dict(os.environ, PYTHONPATH=str(stage), PYTHONDONTWRITEBYTECODE="1")
        env.pop("PYTEST_ADDOPTS", None)
        env.pop("PYTEST_PLUGINS", None)
        events = stage / "events.jsonl"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--receptor=llm",
                f"--receptor-events={events}",
                "-m",
                "not online",
                "-o",
                "tmp_path_retention_policy=failed",
                name,
            ],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=1800,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASS exit=0" in result.stdout
        artifact = read_artifact(events)
        assert artifact.complete and artifact.integrity_valid and artifact.final
        final = artifact.final.data
        assert final["complete"] and final["exitstatus"] == 0
        counts = final["counts"]
        assert counts["collected"] == counts["executed"] == counts["passed"] == 48
        assert not any(
            counts[key]
            for key in (
                "failed",
                "errors",
                "skipped",
                "not_executed",
                "xfailed",
                "xpassed",
            )
        )
        assert not (stage / "temp_data").exists()


def test_declared_bioactivity_literature_v2_runs_with_only_genuine_public_capsule():
    """One outer case receives SDK202 and historical-v1 overlapping children."""
    from pytest_receptor import read_artifact

    root = Path(__file__).resolve().parents[2]
    name = "test_bioactivity_literature_v2_offline.py"
    originals = (
        "bioactivity_literature_scalars_sdk202.tar.gz",
        "bioactivity_saved_original17_sdk202.json.gz",
        "README.md",
    )
    for workflow_path in (
        ".github/workflows/ci.yml",
        ".github/workflows/test_staged_conda_package.yaml",
    ):
        workflow = (root / workflow_path).read_text(encoding="utf-8")
        assert (
            sum("cp " in line and name in line for line in workflow.splitlines()) == 1
        )
        command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
        assert command is not None
        assert shlex.split(command[1]).count(name) == 1
        for original in originals:
            assert (
                sum(
                    "cp " in line and f"data/{original}" in line
                    for line in workflow.splitlines()
                )
                == 1
            )
    outside_parent = None if sys.platform == "win32" else "/tmp"
    with tempfile.TemporaryDirectory(
        prefix="sabueso-bioactivity-literature-v2-", dir=outside_parent
    ) as directory:
        stage = Path(directory)
        assert not stage.resolve().is_relative_to(root.resolve())
        shutil.copyfile(root / "tests/core" / name, stage / name)
        (stage / "data").mkdir()
        for original in originals:
            shutil.copyfile(
                root / "tests/core/data" / original, stage / "data" / original
            )
        # The scalar original carries its Card inputs and public NOTICE; the
        # separate retained @17 output binds historical v1 reading and resaving.
        # A current source fixture or a LIVE fixture factory would hide a missing
        # installed receiving dependency, so neither is copied into this client.
        assert {
            path.relative_to(stage).as_posix()
            for path in stage.rglob("*")
            if path.is_file()
        } == {name, *("data/" + original for original in originals)}
        env = dict(os.environ, PYTHONPATH=str(stage), PYTHONDONTWRITEBYTECODE="1")
        env.pop("PYTEST_ADDOPTS", None)
        env.pop("PYTEST_PLUGINS", None)
        events = stage / "events.jsonl"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--receptor=llm",
                f"--receptor-events={events}",
                "-m",
                "not online",
                "-o",
                "tmp_path_retention_policy=failed",
                name,
            ],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=600,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASS exit=0" in result.stdout
        artifact = read_artifact(events)
        assert artifact.complete and artifact.integrity_valid and artifact.final
        final = artifact.final.data
        assert final["complete"] and final["exitstatus"] == 0
        counts = final["counts"]
        assert counts["collected"] == counts["executed"] == counts["passed"] == 22
        assert not any(
            counts[key]
            for key in (
                "failed",
                "errors",
                "skipped",
                "not_executed",
                "xfailed",
                "xpassed",
            )
        )
        assert not (stage / "temp_data").exists()


def test_installed_molecule_files_deliver_the_complete_original_payload():
    root = Path(__file__).resolve().parents[2]
    modules = (
        "test_card_saved_molecule_activity_offline.py",
        "test_card_saved_molecule_activity_originals_offline.py",
        "test_card_molecule_activity_exact_binding_offline.py",
        "test_card_saved_molecule_activity_exact_offline.py",
    )
    helpers = (
        "test_card_molecule_activity_binding_offline.py",
        "test_card_molecule_activity_history_offline.py",
    )
    capsules = (
        "molecule_activity_live_sdk205.tar.gz",
        "molecule_activity_multifocal_live_sdk208.tar.gz",
        "molecule_activity_quantity_live_sdk211.tar.gz",
        "molecule_activity_saved_legacy_sdk216.tar.gz",
        "molecule_activity_root_exact_live_sdk218.tar.gz",
    )
    for path, job in (
        (".github/workflows/ci.yml", "ackredit-pilot"),
        (".github/workflows/test_staged_conda_package.yaml", "install"),
    ):
        workflow = (root / path).read_text(encoding="utf-8")
        section = re.search(
            rf"(?ms)^  {re.escape(job)}:\n(.*?)(?=^  [a-zA-Z0-9_-]+:\n|\Z)",
            workflow,
        )[1]
        lines = section.splitlines()
        for name in (*modules, *helpers, *capsules):
            assert sum("cp " in line and name in line for line in lines) == 1
        command = re.search(r"python -m pytest (.+)", section.replace("\\\n", " "))
        selected = shlex.split(command[1])
        assert all(selected.count(name) == 1 for name in modules)
        assert all(name not in selected for name in helpers)
        # Both installed routes retain every original selected case. CI uses
        # bounded outer workers; staging remains a separate installed-matrix gate.
        assert "--collect-only" not in selected and "-k" not in selected
        assert "timeout-minutes: 240" in section
        effective_environment = section + workflow.partition("\njobs:\n")[0]
        for variable in (
            "OPENMM_CPU_THREADS",
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
            "NUMBA_NUM_THREADS",
        ):
            assert f'{variable}: "1"' in effective_environment
        if path == ".github/workflows/ci.yml":
            assert (
                '"$GITHUB_WORKSPACE/devtools/run_ci_pytest.py" --workers 3' in section
            )
            assert "Retain bounded pytest resource report" in section
        assert "tests/core/data/README.md" in section
        assert "temp_data" in section
