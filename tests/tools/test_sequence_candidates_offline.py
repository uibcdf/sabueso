"""Sequence candidates preserve ambiguity, native references and current checks."""

import copy
import json
from pathlib import Path

import pytest

from sabueso.core.errors import ArgumentError, ConnectorError, RecordNotFoundError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.tools.db.uniparc import FixtureUniParcClient
from sabueso.tools.db.uniprot import FixtureUniProtClient
from sabueso.tools.sequence import find_protein_candidates

CHECKSUM = "A8D44FC2C980A7677A3B54788D0FA323"
SEQUENCE = json.loads(Path("temp_data/P60174.json").read_text())["sequence"]["value"]


class Search:
    def __init__(self, references=None):
        self.calls = []
        self.result = json.loads(
            Path(f"temp_data/uniparc/search__{CHECKSUM}.json").read_text()
        )
        self.result["pages"] = []
        if references is not None:
            self.result["results"][0]["uniProtKBAccessions"] = references

    def records(self, checksum, limit):
        self.calls.append((checksum, limit))
        return copy.deepcopy(self.result)


class Entries:
    def __init__(self):
        self.calls = []
        self.records = {
            accession: json.loads(Path(f"temp_data/{accession}.json").read_text())
            for accession in ["P60174", "P60175"]
        }

    def fetch_entry(self, accession):
        self.calls.append(accession)
        value = self.records[accession]
        if isinstance(value, Exception):
            raise value
        return copy.deepcopy(value), "2026-01-01T00:00:00Z"


def lookup(text=SEQUENCE, **options):
    return find_protein_candidates(
        text,
        uniparc_client=FixtureUniParcClient(),
        uniprot_client=FixtureUniProtClient(),
        **options,
    )


def test_native_identical_sequences_leave_multiple_distinct_candidates():
    report = lookup()
    assert report["rule"] == "exact_sequence_candidates@1"
    assert (
        report["selection"] == "not_performed"
        and report["scope"]["identity"] == "not_resolved"
    )
    assert report["candidate_status"] == "multiple" and report["status"] == "partial"
    assert [c["accession"] for c in report["candidates"]] == [
        "P60175",
        "P60174",
        "V9HWK1",
    ]
    human = next(c for c in report["candidates"] if c["accession"] == "P60174")
    assert [b["native_reference"] for b in human["basis"]] == ["P60174", "P60174.2"]
    assert human["basis"][1]["declared_sequence_revision"] == "2"
    assert any(
        v.get("reason") == "inactive_UniProt_entry" and v["accession"] == "Q6FHP9"
        for v in report["verifications"]
    )
    assert [e["native_reference"] for e in report["excluded"]] == ["P60174-1"]
    assert sum(v["outcome"] == "unavailable" for v in report["verifications"]) == 3
    assert len(report["acquisition_trace"]["records"]) == 8
    assert "card" not in report and "identity_links" not in report


def test_fasta_normalization_keeps_input_and_header_without_taxon_inference():
    archive, entries = Search(["P60174"]), Entries()
    raw = find_protein_candidates(
        SEQUENCE, uniparc_client=archive, uniprot_client=entries
    )
    fasta = find_protein_candidates(
        ">misleading_species taxon=1\n"
        + SEQUENCE.lower()[:100]
        + " \n\t"
        + SEQUENCE.lower()[100:]
        + "*\n",
        uniparc_client=archive,
        uniprot_client=entries,
    )
    assert raw["input"]["sha256"] == fasta["input"]["sha256"]
    assert (
        raw["input"]["normalization"]["raw_input_sha256"]
        != fasta["input"]["normalization"]["raw_input_sha256"]
    )
    assert fasta["input"]["normalization"]["removed_terminal_stop"] is True
    assert fasta["scope"]["taxon_id"] is None and fasta["candidate_status"] == "one"
    assert len(archive.calls) == 2 and entries.calls == ["P60174", "P60174"]


@pytest.mark.parametrize(
    "text",
    [
        "",
        " \n",
        ">",
        ">header\n",
        ">one\nAA\n>two\nAA",
        "AA-",
        "AA*AA",
        "AA**",
        "AAé",
        "AAß",
        "AAſ",
        "AA>header",
        None,
        ["AA"],
    ],
)
def test_invalid_or_multiple_sequences_never_access_sources(text):
    archive = Search()
    entries = Entries()
    with pytest.raises(ArgumentError):
        find_protein_candidates(text, uniparc_client=archive, uniprot_client=entries)
    assert archive.calls == [] and entries.calls == []


@pytest.mark.parametrize("taxon", [True, 0, -1, "9606", 9606.0])
def test_invalid_taxon_fails_before_access(taxon):
    archive = Search()
    with pytest.raises(ArgumentError):
        find_protein_candidates(SEQUENCE, taxon_id=taxon, uniparc_client=archive)
    assert archive.calls == []


def test_exact_taxon_and_entry_limit_do_not_select_by_review_status():
    archive, entries = Search(["P60175", "P60174", "P60174.2", "P60174-1"]), Entries()
    human = find_protein_candidates(
        SEQUENCE, taxon_id=9606, uniparc_client=archive, uniprot_client=entries
    )
    assert [c["accession"] for c in human["candidates"]] == ["P60174"]
    assert human["status"] == "complete" and human["selection"] == "not_performed"
    assert human["verifications"][0]["reason"] == "exact_taxon_differs"
    entries.calls.clear()
    limited = find_protein_candidates(
        SEQUENCE, limit=1, uniparc_client=archive, uniprot_client=entries
    )
    assert limited["status"] == "partial" and limited["candidate_status"] == "one"
    assert limited["scope"]["canonical_references_stated"] == 2
    assert limited["scope"]["canonical_reference_checks_attempted"] == 1
    assert entries.calls == ["P60175"]
    assert limited["verifications"][1]["outcome"] == "not_queried"
    assert limited["excluded"][0]["reason"] == "isoform_sequence_not_queried"


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(primaryAccession="P60175"),
        lambda e: e["sequence"].update(length=True),
        lambda e: e["sequence"].update(length=250),
        lambda e: e["sequence"].update(md5="0" * 32),
        lambda e: e.update(sequence=None),
        lambda e: e.update(organism={"taxonId": True}),
    ],
)
def test_current_entry_integrity_failure_keeps_other_candidate(change):
    archive, entries = Search(["P60174", "P60175"]), Entries()
    change(entries.records["P60174"])
    report = find_protein_candidates(
        SEQUENCE, uniparc_client=archive, uniprot_client=entries
    )
    assert report["status"] == "partial"
    assert [c["accession"] for c in report["candidates"]] == ["P60175"]
    assert report["verifications"][0]["outcome"] == "failed_validation"


@pytest.mark.parametrize("malformed", [[], {"entryAudit": []}, {"entryAudit": "bad"}])
def test_malformed_current_response_is_diagnostic_not_attribute_error(malformed):
    entries = Entries()
    entries.records["P60174"] = malformed
    report = find_protein_candidates(
        SEQUENCE, uniparc_client=Search(["P60174", "P60175"]), uniprot_client=entries
    )
    assert report["status"] == "partial" and report["candidate_status"] == "one"
    assert report["verifications"][0]["error"]["type"] == "ConnectorError"


@pytest.mark.parametrize(
    "error", [ConnectorError("failed"), RecordNotFoundError("absent")]
)
def test_uninstrumented_client_failure_is_not_silently_absent(error):
    entries = Entries()
    entries.records["P60174"] = error
    report = find_protein_candidates(
        SEQUENCE, uniparc_client=Search(["P60174", "P60175"]), uniprot_client=entries
    )
    assert report["status"] == "partial"
    assert report["verifications"][0]["outcome"] == "unobserved_failure"
    assert [c["accession"] for c in report["candidates"]] == ["P60175"]


def test_inactive_entry_and_isoform_only_archive_are_explicit_exclusions():
    entries = Entries()
    entries.records["P60174"]["entryType"] = "Inactive"
    report = find_protein_candidates(
        SEQUENCE,
        uniparc_client=Search(["P60174", "P60174-2.3"]),
        uniprot_client=entries,
    )
    assert (
        report["status"] == "complete"
        and report["candidate_status"] == "none_in_checked_scope"
    )
    assert entries.calls == ["P60174"]
    assert report["verifications"][0]["reason"] == "inactive_UniProt_entry"
    entries.calls.clear()
    report = find_protein_candidates(
        SEQUENCE, uniparc_client=Search(["P60174-2"]), uniprot_client=entries
    )
    assert report["verifications"] == [] and entries.calls == []
    assert report["source_assertions"] and report["excluded"]


def test_no_archive_answer_and_unavailable_archive_are_not_conflated(tmp_path):
    search = Search([])
    search.result.update(total=0, results=[])
    empty = find_protein_candidates(SEQUENCE, uniparc_client=search)
    failed = find_protein_candidates(
        SEQUENCE, uniparc_client=FixtureUniParcClient(tmp_path)
    )
    assert empty["status"] == "complete" and empty["search"]["record"]["total"] == 0
    assert failed["status"] == "failed" and failed["search"] is None
    assert failed["acquisition_trace"]["records"][0]["outcome"] == "unavailable"


def test_full_archive_sequence_is_compared_after_checksum_lookup(monkeypatch):
    # Simulate a checksum collision only at the validated source boundary.
    from sabueso.tools import sequence

    archive = Search(["P60174"])
    search_envelope = {
        "source": "UniParc",
        "kind": "checksum_search",
        "query": {"checksum": CHECKSUM},
        "record": {"total": 1, "results": archive.result["results"]},
        "truncated": False,
    }
    from sabueso.mappings.uniparc import map_sequence_records

    assertions = map_sequence_records(search_envelope)
    assertions[0]["asserted_value"]["sequence"]["value"] = "A" * len(SEQUENCE)
    monkeypatch.setattr(sequence, "map_sequence_records", lambda envelope: assertions)
    entries = Entries()
    report = find_protein_candidates(
        SEQUENCE, uniparc_client=archive, uniprot_client=entries
    )
    assert entries.calls == [] and report["candidates"] == []
    assert "full_archive_sequence_differs" in report["excluded"][0]["reason"]


def test_support_snapshots_keep_current_revision_and_are_detached():
    archive, entries = Search(["P60174"]), Entries()
    before = copy.deepcopy(entries.records)
    report = find_protein_candidates(
        SEQUENCE, uniparc_client=archive, uniprot_client=entries
    )
    candidate = report["candidates"][0]
    support = report["source_assertions"][-1]
    assert candidate["current_sequence_assertion_snapshot_id"] == digest(
        canonical_json(support)
    )
    assert support["source"]["version"] == str(
        before["P60174"]["entryAudit"]["entryVersion"]
    )
    assert support["source_metadata"]["sequence"] == before["P60174"]["sequence"]
    support["source_metadata"]["sequence"]["value"] = "A"
    assert entries.records == before
    assert (
        report["verifications"][0]["record"]["record"]["sequence"]["value"] == SEQUENCE
    )


def test_historical_reference_is_rechecked_against_current_full_sequence():
    entries = Entries()
    entries.records["P60174"]["sequence"].update(value="A" * len(SEQUENCE))
    entries.records["P60174"]["sequence"].pop("md5", None)
    report = find_protein_candidates(
        SEQUENCE, uniparc_client=Search(["P60174.2", "P60175"]), uniprot_client=entries
    )
    assert report["status"] == "complete"
    assert [c["accession"] for c in report["candidates"]] == ["P60175"]
    assert report["verifications"][0]["reason"] == "current_UniProt_sequence_differs"
    assert report["verifications"][0]["basis"][0]["native_reference"] == "P60174.2"


def test_later_search_page_failure_retains_valid_candidates_and_trace(monkeypatch):
    import io
    from email.message import Message

    from sabueso.tools.db import uniparc

    class Response(io.BytesIO):
        headers = Message()

    Response.headers["X-Total-Results"] = "2"
    Response.headers["X-UniProt-Release"] = "test-release"
    Response.headers["Link"] = '<https://evil.example/search>; rel="next"'
    payload = {"results": Search(["P60174"]).result["results"]}
    monkeypatch.setattr(
        uniparc, "urlopen", lambda *a, **k: Response(json.dumps(payload).encode())
    )
    report = find_protein_candidates(SEQUENCE, uniprot_client=Entries())
    assert report["status"] == "partial" and report["candidate_status"] == "one"
    assert report["search"]["truncated"] is True
    assert report["search"]["record"]["total"] == 2
    assert report["search_error"]["type"] == "ConnectorError"
    assert report["acquisition_trace"]["records"][0]["outcome"] == "partial"


def test_native_online_not_found_excludes_reference_without_partial_failure(
    monkeypatch,
):
    from email.message import Message
    from urllib.error import HTTPError

    from sabueso.tools.db import _http

    def absent(*args, **kwargs):
        raise HTTPError(
            "https://rest.uniprot.org/uniprotkb/P60174.json",
            404,
            "not found",
            Message(),
            None,
        )

    monkeypatch.setattr(_http, "_urlopen", absent)
    report = find_protein_candidates(SEQUENCE, uniparc_client=Search(["P60174"]))
    assert report["status"] == "complete" and report["candidates"] == []
    assert report["verifications"][0]["outcome"] == "not_found"
