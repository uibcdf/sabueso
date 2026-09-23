"""Every redistributed fixture is covered by temp_data/NOTICE.md (uibcdf/sabueso#24).

The fixtures are frozen public database responses redistributed with the repository. Each
keeps its source's licence, so a new one must not arrive without its source, version and
licence being recorded.
"""

import re
from fnmatch import fnmatch
from pathlib import Path

import pytest

FIXTURES = Path("temp_data")
NOTICE = FIXTURES / "NOTICE.md"
COMPLIANCE = Path("devguide/LICENSING_AND_COMPLIANCE.md")
# Backticked paths and globs of the notice's contents table, e.g. `chembl/*.json`.
LISTED = re.compile(r"`([A-Za-z0-9_./*-]+\.json)`")


def _listed_patterns(notice: str) -> list[str]:
    table = notice[notice.index("## Contents") : notice.index("## Attribution")]
    return LISTED.findall(table)


@pytest.fixture(scope="module")
def notice():
    return NOTICE.read_text(encoding="utf-8")


def test_every_fixture_is_listed(notice):
    patterns = _listed_patterns(notice)
    assert patterns, "the contents table lists no fixture"
    missing = sorted(
        str(path.relative_to(FIXTURES))
        for path in FIXTURES.rglob("*.json")
        if not any(fnmatch(str(path.relative_to(FIXTURES)), p) for p in patterns)
    )
    assert missing == [], f"not covered by {NOTICE}: {missing}"


def test_the_guard_rejects_an_unlisted_fixture(notice):
    patterns = [p for p in _listed_patterns(notice) if not p.startswith("unichem/")]
    assert not any(fnmatch("unichem/SOME-KEY.json", p) for p in patterns)


def test_each_source_in_use_states_a_licence(notice):
    for source in ("UniProt", "RCSB PDB", "STRING", "ChEMBL", "UniChem", "PubChem"):
        assert source in notice
    for licence in ("CC BY 4.0", "CC0 1.0", "CC BY-SA 3.0", "public domain"):
        assert licence in notice


def test_the_share_alike_source_is_called_out(notice):
    # ChEMBL is the only source in use with a share-alike clause.
    assert "share-alike" in notice.lower()
    compliance = COMPLIANCE.read_text(encoding="utf-8")
    assert "CC BY-SA 3.0" in compliance
    assert "temp_data/NOTICE.md" in compliance
