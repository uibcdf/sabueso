"""Rehearse a review proposal on public fixtures; never assert human validation.

Run from the checkout with ``python -m tools.rehearse_public_curation --output DIR``.
All cards and stores produced here are hypothetical acceptance-test artifacts, with
an explicitly simulated curator. The proposal remains a draft outside the stores.
"""

from __future__ import annotations

import argparse
import json
import warnings
from copy import deepcopy
from pathlib import Path

import sabueso
from sabueso._private.smonitor.warnings import CuratedDisagreementWarning
from sabueso.mappings.rcsb_structures import author_position
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "examples/literature_curation/hstim_review.json"
SIMULATED_CURATOR = "acceptance-test simulation; no human validation"


def rehearse(output: Path) -> dict:
    """Apply the hypothetical reviewed values, rebuild and verify historical support."""
    proposal = json.loads(PROPOSAL.read_text(encoding="utf-8"))
    if proposal["status"] != "draft_for_human_review":
        raise ValueError("This rehearsal expects an explicitly unapproved proposal")
    output.mkdir(parents=True, exist_ok=False)
    resolver = EntityResolver(
        FixtureUniProtClient(ROOT / "temp_data"),
        rcsb_client=FixtureRCSBClient(ROOT / "temp_data"),
    )
    placement = proposal["placement"]
    options = {"resolver": resolver, "structures": ["2VOM"]}
    card, _ = sabueso.resolve(proposal["entity"], **options)
    (relationship,) = card.relationships(
        "has_structure", object_ref=placement["structure_ref"]
    )
    qualifiers = relationship["qualifiers"]
    position = placement["uniprot_position"]
    checks = {
        "citation_matches": qualifiers["primary_citation"]["pubmed"]
        == proposal["publication"]["ref"].split(":", 1)[1],
        "author_numbering_matches": author_position(
            qualifiers["author_numbering"][placement["chain"]], position
        )
        == placement["author_position"],
        "reference_residue_matches": card.get("sequence.primary")["value"][position - 1]
        == placement["reference_residue"],
        "mapped_mutation_matches": any(
            mutation["position"] == position
            and mutation["reference"] == placement["reference_residue"]
            and mutation["residue"] == placement["alternate_residue"]
            for mutation in qualifiers["mutations"]
        ),
    }
    if not all(checks.values()):
        raise ValueError(f"The proposal's identity/numbering basis failed: {checks}")
    knowledge = sabueso.KnowledgeStore(output / "hypothetical_knowledge.db")
    baseline_ref = knowledge.save(card)
    original_variants = deepcopy(
        card.get("features_positional.natural_variant")["value"]
    )
    original_claims = len(card.claims()["items"])
    outcomes = []
    with warnings.catch_warnings(record=True) as diagnostics:
        warnings.simplefilter("always", CuratedDisagreementWarning)
        for candidate in proposal["candidates"]:
            outcome = card.add_literature_assertion(
                candidate["field_path"],
                candidate["value"],
                publication=proposal["publication"]["ref"],
                curator=SIMULATED_CURATOR,
                locator=candidate["locator"],
                curated_at=proposal["prepared_by"]["date"],
            )
            outcomes.append({"candidate": candidate["id"], **outcome})
    curations = sabueso.CurationStore(output / "hypothetical_curations.jsonl")
    saved = curations.save(card)
    first_ref = knowledge.save(card)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", CuratedDisagreementWarning)
        rebuilt, _ = sabueso.resolve(proposal["entity"], curations=curations, **options)
    rebuilt_ref = knowledge.save(rebuilt)
    support = []
    for outcome in outcomes:
        sa_id = outcome["source_assertion_id"]
        before = card.source_assertion_store.get(sa_id)
        after = rebuilt.source_assertion_store.get(sa_id)
        if before != after:
            raise AssertionError("A statement changed across rebuilds")
        item_ref = f"{first_ref}#{sa_id}"
        if knowledge.source_assertion(item_ref) != before:
            raise AssertionError("Historical source support changed")
        support.append(
            {
                **outcome,
                "source_assertion_ref": item_ref,
                "compared_with_refs": [
                    f"{baseline_ref}#{other}" for other in outcome["compared_with"]
                ],
            }
        )
    variants = rebuilt.get("features_positional.natural_variant")["value"]
    if not all(item in variants for item in original_variants):
        raise AssertionError("A source's original variant was lost")
    report = {
        "mode": "hypothetical_human_curation_rehearsal",
        "human_validation": None,
        "proposal": str(PROPOSAL.relative_to(ROOT)),
        "publication": proposal["publication"],
        "read_scope": proposal["read_scope"],
        "identity_and_numbering_checks": checks,
        "placement_support_ref": f"{baseline_ref}#{relationship['id']}",
        "baseline_ref": baseline_ref,
        "hypothetical_ref": first_ref,
        "rebuilt_ref": rebuilt_ref,
        "outcomes": support,
        "new_source_assertions": saved["added"],
        "new_free_text_claims": len(rebuilt.claims()["items"]) - original_claims,
        "original_variant": next(
            item
            for item in original_variants
            if item["location"]["sequence"]["start"] == position
        ),
        "conflicts": [
            conflict
            for conflict in rebuilt.quality.get("conflicts") or []
            if conflict.get("type") == "curated_difference"
        ],
        "difference_warnings": sum(
            issubclass(record.category, CuratedDisagreementWarning)
            for record in diagnostics
        ),
        "original_variants_preserved": True,
        "statements_and_historical_support_preserved": True,
        "rebuild": rebuilt.quality["curation_store"],
        "interpretation": "Mechanical differences are not established contradictions; "
        "not_compared claims do not establish scientific novelty.",
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    (output / "README.txt").write_text(
        "HYPOTHETICAL ACCEPTANCE-TEST ARTIFACTS ONLY. No human has validated the proposal.\n"
        "Do not use these simulated curations as a project's accepted knowledge.\n",
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, required=True, help="A new output directory"
    )
    arguments = parser.parse_args()
    report = rehearse(arguments.output)
    print(json.dumps(report, indent=2))
