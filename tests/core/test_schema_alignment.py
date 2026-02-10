import subprocess
import sys


def test_schema_alignment():
    result = subprocess.run(
        [sys.executable, "tools/validate_schema.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "OK: FIELD_PATHS and schema are aligned" in result.stdout
