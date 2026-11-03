"""The declared installed-consumer receiving files must run in isolation (#165)."""

import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


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
    names = re.findall(r'cp tests/core/(\S+) "\$client_dir/"', workflow)
    assert name in names
    command = re.search(r"python -m pytest (.+)", workflow.replace("\\\n", " "))
    arguments = shlex.split(command[1])
    assert name in arguments
    selected_files = [argument for argument in arguments if argument.endswith(".py")]
    assert len(selected_files) == len(set(selected_files))
    originals = re.findall(r'cp tests/core/data/(\S+) "\$client_dir/data/"', workflow)
    assert {
        "assembly_nonpolymer_live_v2.json.gz",
        "card_exploration_quaternary_v1.json.gz",
    } <= set(originals)
    # Qualify the declared receiving payload, using the shared editable package.
    # Actual installed-package import/receiving qualification belongs to CI.
    with tempfile.TemporaryDirectory(
        prefix="sabueso-nonpolymer-receiving-"
    ) as directory:
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
                f"{name}::test_each_genuine_original_preserves_complete_rows_and_native_keys[1HTI]",
                f"{name}::test_each_genuine_original_preserves_complete_rows_and_native_keys[legacy]",
            ],
            cwd=stage,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "2 passed" in result.stdout
        assert not (stage / "temp_data").exists()
