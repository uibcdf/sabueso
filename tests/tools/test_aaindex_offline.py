"""AAindex native order, literal values, missing data and observed fixture access."""

import copy
import io

import pytest

from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.core.terms import USES, verdict
from sabueso.mappings.aaindex import map_index, parse_index
from sabueso.tools.db.aaindex import (
    FixtureAAindexClient,
    OnlineAAindexClient,
    get_index,
)

SAMPLE = """H TEST000001
D Synthetic index for a parser regression
R PMID:1
A Example, A.
T Synthetic test record
J No external response is represented by this fixture
I    A/L R/K N/M D/F C/P Q/S E/T G/W H/Y I/V
    1 2 3 4 5 6 7 8 9 10
    11 12 13 14 15 16 17 18 19 NA
//
"""


def fixture(tmp_path, text=SAMPLE):
    directory = tmp_path / "aaindex"
    directory.mkdir()
    (directory / "aaindex1").write_text(text, encoding="utf-8")
    return FixtureAAindexClient(tmp_path)


def test_paired_order_missing_values_and_literals():
    record = parse_index(SAMPLE, "TEST000001")
    assert record["values"]["A"] == 1 and record["values"]["L"] == 11
    assert record["values"]["V"] is None and record["native_values"]["V"] == "NA"
    assert record["references"] == ["PMID:1"]
    assert record["unit_basis"] == "not_stated_in_structured_record"


def test_public_download_does_not_establish_permission():
    for use in USES:
        report = verdict("AAindex", use)
        assert report["verdict"] == "unknown"
        assert report["reason"] == "licence_not_stated"


@pytest.mark.parametrize(
    "text",
    [
        "<html>error</html>",
        SAMPLE.replace("19 NA", "19"),
        SAMPLE.replace("19 NA", "19 nan"),
        SAMPLE + SAMPLE,
        SAMPLE.rstrip()[:-2],
    ],
)
def test_malformed_truncated_and_duplicate_documents_fail(text):
    with pytest.raises(ConnectorError):
        parse_index(text, "TEST000001")


def test_malformed_unmatched_record_does_not_establish_absence_or_presence():
    broken = SAMPLE.replace("TEST000001", "TEST000003").replace("19 NA", "19")
    for identifier in ("TEST000001", "TEST000002"):
        with pytest.raises(ConnectorError):
            parse_index(SAMPLE + broken, identifier)


def test_online_transport_uses_native_document_and_refuses_bad_ids(monkeypatch):
    from sabueso.tools.db import aaindex

    calls = []

    def download(url, timeout):
        calls.append((url, timeout))
        return io.BytesIO(SAMPLE.encode())

    monkeypatch.setattr(aaindex, "urlopen", download)
    envelope = get_index("TEST000001", client=OnlineAAindexClient(timeout=3))
    assert envelope["record"]["native_values"]["V"] == "NA"
    assert calls == [(aaindex.URL, 3)]
    with pytest.raises(ConnectorError):
        get_index("not-an-index", client=OnlineAAindexClient())
    assert calls == [(aaindex.URL, 3)]


def test_missing_index_and_fixture_have_different_observed_outcomes(tmp_path):
    with pytest.raises(RecordNotFoundError) as missing:
        get_index("TEST000002", client=fixture(tmp_path))
    assert missing.value.acquisition_trace["records"][0]["outcome"] == "not_found"
    with pytest.raises(ConnectorError) as unavailable:
        get_index("TEST000001", client=FixtureAAindexClient(tmp_path / "absent"))
    assert unavailable.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


def test_assertions_and_acquisition_retain_scope_and_references(tmp_path):
    envelope = get_index("TEST000001", client=fixture(tmp_path))
    (operation,) = envelope["acquisition_trace"]["records"]
    assert (
        operation["network_attempts"] == 0
        and operation["source_version"]["value"] is None
    )
    assert (
        operation["native_references"] == ["PMID:1"]
        and operation["document_identity"]["hash"]
    )
    assert (
        "native_index_publication_metadata_not_fetched"
        in operation["bibliography_gaps"]
    )
    original = copy.deepcopy(envelope)
    assertions = map_index(envelope)
    assert len(assertions) == 20
    assert (
        next(a for a in assertions if a["subject_ref"] == "amino_acid:V")[
            "asserted_value"
        ]["native_value"]
        == "NA"
    )
    assert envelope == original
