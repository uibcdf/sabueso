import subprocess
import sys
from pathlib import Path

import pytest

from sabueso.core.card import CARD_SCHEMA_VERSION

VALIDATOR = Path(__file__).resolve().parents[2] / "tools/validate_schema.py"


def test_schema_alignment():
    result = subprocess.run(
        [sys.executable, "tools/validate_schema.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "OK: FIELD_PATHS and schema are aligned" in result.stdout


@pytest.mark.parametrize(
    "schema,fields,status,diagnostics",
    [
        (
            "card_base:\n  names:\n    label: {value: str}\n",
            ["names.label"],
            0,
            ["OK: FIELD_PATHS and schema are aligned"],
        ),
        (
            "card_base:\n  names:\n    label: {value: str}\n",
            ["names.label", "names.absent"],
            1,
            ["Missing in schema:", "- names.absent"],
        ),
        (
            "card_base:\n  names:\n    label: {value: str}\n",
            [],
            1,
            ["Missing in FIELD_PATHS:", "- names.label"],
        ),
        (
            "card_base:\n  names:\n    label: {value: str}\n",
            ["names.absent"],
            1,
            ["Missing in schema:", "Missing in FIELD_PATHS:"],
        ),
        (
            "card_base:\n  clinical: '*'\n",
            ["clinical.indications", "clinical.studies.status"],
            0,
            ["OK: FIELD_PATHS and schema are aligned"],
        ),
        (
            "card_base:\n  clinical: '*'\n",
            ["clinically_unrelated.status"],
            1,
            ["Missing in schema:", "- clinically_unrelated.status"],
        ),
    ],
    ids=[
        "aligned",
        "missing-schema-field",
        "missing-guide-field",
        "both",
        "wildcard",
        "wildcard-boundary",
    ],
)
def test_validator_exit_status_matches_reported_alignment(
    tmp_path, schema, fields, status, diagnostics
):
    """A real CLI consumer must be able to refuse an inconsistent checkout."""
    guide = tmp_path / "devguide"
    schemas = tmp_path / "schemas"
    guide.mkdir()
    schemas.mkdir()
    (guide / "FIELD_PATHS.md").write_text(
        "\n".join(f"- `{field}`" for field in fields) + "\n", encoding="utf-8"
    )
    (schemas / f"card_schema_{CARD_SCHEMA_VERSION}.yaml").write_text(
        schema, encoding="utf-8"
    )
    result = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == status, result.stdout + result.stderr
    assert all(message in result.stdout for message in diagnostics)
    assert ("OK: FIELD_PATHS and schema are aligned" in result.stdout) == (status == 0)
