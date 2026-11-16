"""A missing/foreign development workspace must never run the active environment."""

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "devtools/explorer_workspace.py"


def test_missing_owned_workspace_cannot_fall_back_to_active_python():
    (ROOT / "build").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT / "build") as directory:
        result = subprocess.run(
            [
                sys.executable,
                str(LAUNCHER),
                "--workspace",
                directory,
                "run",
                "--",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    assert result.returncode == 2
    assert "Workspace is absent" in result.stderr


def test_foreign_workspace_python_is_not_executed(tmp_path):
    executable = tmp_path / "env/bin/python"
    executable.parent.mkdir(parents=True)
    marker = tmp_path / "unexpected-execution"
    executable.write_text(
        f"#!{sys.executable}\nfrom pathlib import Path\nPath({str(marker)!r}).touch()\n"
    )
    executable.chmod(0o700)
    result = subprocess.run(
        [sys.executable, str(LAUNCHER), "--workspace", str(tmp_path), "check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "component-owned workspace" in result.stderr
    assert not marker.exists()
