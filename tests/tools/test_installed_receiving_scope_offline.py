"""The declared installed-consumer receiving files must run in isolation (#165)."""

import os
import re
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
