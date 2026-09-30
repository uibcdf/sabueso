"""RCSB entries in batches (#98): many entries per GraphQL request, each answer or
failure its own, and an entry an error touched asked again alone."""

from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.tools.db import rcsb


class _Client(rcsb.OnlineRCSBClient):
    """The online client with GraphQL answered from a script."""

    def __init__(self, answers):
        super().__init__()
        self.answers, self.batches, self.alone = list(answers), [], []

    def _post(self, query, pdb_id, variables=None):
        self.batches.append((variables or {}).get("ids"))
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    def fetch_structure(self, pdb_id):
        self.alone.append(pdb_id)
        if pdb_id == "GONE":
            raise RecordNotFoundError("RCSB has no entry GONE")
        return {"rcsb_id": pdb_id, "_partial": {"missing": ["x"]}}, "alone"


def _entry(pdb_id):
    return {"rcsb_id": pdb_id}


def test_one_request_for_many_entries_and_a_missing_one_is_not_found():
    client = _Client([{"data": {"entries": [_entry("1ABC"), _entry("2DEF")]}}])
    out = client.fetch_structures(["1abc", "2def", "3GHI"])
    assert client.batches == [["1ABC", "2DEF", "3GHI"]]
    assert out["1ABC"][0] == {"rcsb_id": "1ABC"}
    assert isinstance(out["3GHI"], RecordNotFoundError)
    assert client.alone == []


def test_an_entry_an_error_touched_is_asked_alone():
    answer = {
        "data": {"entries": [_entry("1ABC"), _entry("2DEF")]},
        "errors": [{"path": ["entries", 1, "polymer_entities", 0], "message": "x"}],
    }
    client = _Client([answer])
    out = client.fetch_structures(["1ABC", "2DEF"])
    assert client.alone == ["2DEF"]
    assert out["2DEF"][0]["_partial"]  # the fallback of #74
    assert out["1ABC"][1] != "alone"


def test_a_failed_batch_is_asked_entry_by_entry():
    client = _Client([ConnectorError("HTTP 502")])
    out = client.fetch_structures(["1ABC", "GONE"])
    assert client.alone == ["1ABC", "GONE"]
    assert isinstance(out["GONE"], RecordNotFoundError)


def test_a_null_entry_leaves_the_unanswered_ones_to_be_asked_alone():
    client = _Client([{"data": {"entries": [_entry("1ABC"), None]}}])
    out = client.fetch_structures(["1ABC", "2DEF"])
    assert client.alone == ["2DEF"]
    assert set(out) == {"1ABC", "2DEF"}


def test_batches_of_twenty_five():
    ids = [f"{i:04d}" for i in range(30)]
    client = _Client(
        [
            {"data": {"entries": [_entry(p) for p in ids[:25]]}},
            {"data": {"entries": [_entry(p) for p in ids[25:]]}},
        ]
    )
    client.fetch_structures(ids)
    assert [len(b) for b in client.batches] == [25, 5]


def test_a_client_without_batches_is_asked_one_entry_at_a_time():
    from sabueso.tools.db.rcsb import FixtureRCSBClient, fetch_many

    out = fetch_many(FixtureRCSBClient("temp_data"), ["1sux", "NONE"])
    assert out["1SUX"][0]["rcsb_id"] == "1SUX"
    assert isinstance(out["NONE"], RecordNotFoundError)
