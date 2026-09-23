from sabueso.core.aggregator import build_card_from_mapping


def test_aggregator_uses_resolver_conflict():
    mapping = {
        "fields": {"annotations.domains": "X"},
        "source_assertions": [
            {
                "id": "sa1",
                "field_path": "annotations.domains",
                "asserted_value": "A",
                "source": {"name": "UniProt"},
                "retrieved_at": "2026-02-01",
            },
            {
                "id": "sa2",
                "field_path": "annotations.domains",
                "asserted_value": "B",
                "source": {"name": "PDB"},
                "retrieved_at": "2026-02-02",
            },
        ],
        "field_source_assertions": {"annotations.domains": ["sa1", "sa2"]},
    }
    rules = {"strategy": "most_frequent"}
    card = build_card_from_mapping(mapping, selection_rules=rules, mode="strict")
    val = card.get("annotations.domains")
    assert isinstance(val, dict)
    assert val.get("value") in ("A", "B")
    assert card.quality.get("conflicts")
