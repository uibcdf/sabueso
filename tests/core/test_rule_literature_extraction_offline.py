"""Named rules extract literal source text without human curation or inference."""

import json

import ackredit
import pytest

import sabueso
from sabueso._private.smonitor.warnings import AttributionTrackingWarning
from sabueso.core import attribution as adapter
from sabueso.core.errors import ArgumentError
from sabueso.core.snapshot import digest
from sabueso.resolver import EntityResolver, FixtureUniProtClient


@pytest.fixture(autouse=True)
def independent_workflow():
    with ackredit.session("literal extraction test"):
        yield


def extract(text, **kwargs):
    return sabueso.extract_literature_mentions(
        text, "P60174", "pubmed:40832834", "Synthetic test fragment", **kwargs
    )


def test_unicode_offsets_each_occurrence_tool_version_and_saved_citations():
    text = "α UniProt:P60174; UniProtKB:P60174 and https://www.uniprot.org/uniprotkb/P60174/entry."
    result = extract(text)
    assertions = result["source_assertions"]
    assert len(assertions) == 3
    assert len({a["id"] for a in assertions}) == 3
    for assertion in assertions:
        value = assertion["asserted_value"]
        assert text[value["start"] : value["end"]] == value["text"]
        assert value["input_sha256"] == digest(text)
        assert assertion["source"] == {
            "name": "Literature",
            "type": "literature",
            "record_id": "pubmed:40832834",
        }
        assert assertion["subject_ref"] == "uniprot:P60174"
        acquisition = assertion["acquisition"]
        assert acquisition["method"] == "rule_extraction"
        assert acquisition["tool"] == "sabueso.literal_uniprot_mention"
        assert acquisition["version"] == "1" and "validated_by" not in acquisition
    (relationship,) = result["relationships"]
    assert relationship["source_assertion_ids"] == [a["id"] for a in assertions]
    trace = result["extraction_trace"]
    assert trace["rule"] == "literal_uniprot_mention@1"
    assert trace["provider"]["status"] == "available"
    assert trace["terms"]["state"] == "unknown"
    assert trace["bibliography_gaps"]
    before = ackredit.get_attribution().to_dict()
    saved = json.loads(json.dumps(result))
    original = ackredit.Attribution.from_dict(
        saved["extraction_trace"]["provider"]["attribution"]
    )
    assert "https://pubmed.ncbi.nlm.nih.gov/40832834/" in original.report(
        format="csl-json"
    )
    assert ackredit.get_attribution().to_dict() == before


@pytest.mark.parametrize(
    "text",
    [
        "P60174 is mentioned",
        "TIM and triosephosphate isomerase",
        "UniProt:P601740",
        "UniProt:P60174-2",
        "UniProt:P60174/other",
        "UniProt:Q9C401",
        "uniprot:p60174",
        "https://evil.org/uniprotkb/P60174",
        "https://evil.org/UniProt:P60174",
        "xUniProt:P60174",
        "https://www.uniprot.org/uniprotkb/P60174/entryX",
    ],
)
def test_names_bare_ids_isoforms_wrong_namespaces_and_longer_tokens_are_not_findings(
    text,
):
    result = extract(text)
    assert result["source_assertions"] == result["relationships"] == []
    assert result["extraction_trace"]["outcome"] == "empty"
    assert (
        result["extraction_trace"]["configuration"]["scope"] == "supplied_text_fragment"
    )


def test_same_statement_ids_reuse_input_while_different_fragments_keep_distinct_support():
    first = extract("UniProt:P60174")
    second = extract("UniProt:P60174")
    different = extract("UniProt:P60174 ")
    assert first["source_assertions"][0]["id"] == second["source_assertions"][0]["id"]
    assert (
        first["source_assertions"][0]["id"] != different["source_assertions"][0]["id"]
    )
    assert first["relationships"][0]["id"] == different["relationships"][0]["id"]


def test_original_extraction_can_be_read_without_becoming_human_curation(tmp_path):
    result = extract("UniProt:P60174")
    card, _ = sabueso.resolve(
        "P60174", resolver=EntityResolver(FixtureUniProtClient("temp_data"))
    )
    # Existing generic stores can inspect the already negotiated statement shape.
    for assertion in result["source_assertions"]:
        card.source_assertion_store.add(assertion)
    assert card.acquisition()["extractions"][0]["method"] == "rule_extraction"
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    assert store.save(card)["total"] == 0
    assert store.records() == []


@pytest.mark.parametrize(
    "change",
    [
        {"text": ""},
        {"identifier": "TIM"},
        {"identifier": "P60174-2"},
        {"publication": "PMC123"},
        {"locator": None},
    ],
)
def test_invalid_public_inputs_are_refused(change):
    arguments = {
        "text": "UniProt:P60174",
        "identifier": "P60174",
        "publication": "pubmed:40832834",
        "locator": "Synthetic test fragment",
        **change,
    }
    with pytest.raises(ArgumentError):
        sabueso.extract_literature_mentions(**arguments)


def test_provider_failure_retains_scientific_extraction_and_explicit_gap(monkeypatch):
    def unavailable():
        raise RuntimeError("synthetic provider failure")

    monkeypatch.setattr(adapter, "_load_backend", unavailable)
    with pytest.warns(AttributionTrackingWarning):
        result = extract("UniProt:P60174")
    assert len(result["source_assertions"]) == 1
    assert result["extraction_trace"]["provider"]["status"] == "failed"
    assert result["extraction_trace"]["provider"]["attribution"] is None
