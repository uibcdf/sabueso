"""Independent disease readers preserve stated identity and expose support gaps."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path("examples/user_journeys/disease_entities.py").resolve()
DATA = Path("temp_data").resolve()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def invoke(action, output, fixtures=DATA):
    command = [sys.executable, str(SCRIPT)]
    if action == "read":
        command = [sys.executable, "-c", """
import runpy, sys
from pathlib import Path
import ackredit, sabueso
from sabueso.core.card import Card
from sabueso.core.deck import Deck
def forbidden(*args, **kwargs):
    raise RuntimeError('A historical reader cannot acquire, derive or generate credit')
ackredit.register_item = ackredit.track_item = forbidden
sabueso.resolve = sabueso.disease_targets = sabueso.disease_drugs = forbidden
Card.diseases = Card.explain_disease = Card.knowledge_state = forbidden
Card.clinical = forbidden
from sabueso.tools.db import clinicaltrials, europepmc
clinicaltrials.get_studies = clinicaltrials.get_study_references = forbidden
clinicaltrials.FixtureClinicalTrialsClient.studies = forbidden
clinicaltrials.FixtureClinicalTrialsClient.study_references = forbidden
europepmc.get_article = europepmc.FixtureEuropePMCClient.article = forbidden
Deck.explain = forbidden
sabueso.__version__ = '999.reader'
script = sys.argv.pop(1)
sys.path.insert(0, str(Path(script).parent))
runpy.run_path(script, run_name='__main__')
""", str(SCRIPT)]  # fmt: skip
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [*command, action, "--output", str(output), "--fixtures",
         str(fixtures if action != "read" else output / "no-fixtures")],
        cwd=output.parent, env=env, capture_output=True, text=True,
        timeout=180, check=False,
    )  # fmt: skip


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    output = tmp_path_factory.mktemp("disease-entities") / "bundle"
    for action in ("produce", "read", "reacquire", "read"):
        result = invoke(action, output)
        assert result.returncode == 0, result.stdout + result.stderr
    return output


def test_saved_disease_identity_membership_grouping_and_partial_credit(bundle):
    original, later = [
        load(bundle / f"{s}.manifest.json") for s in ("original", "later")
    ]
    assert all(original["cards"][r] != later["cards"][r] for r in original["cards"])
    assert all(original["decks"][r] != later["decks"][r] for r in original["decks"])
    report = load(bundle / "original.report.json")
    reader = load(bundle / "original.reader.json")
    assert reader["original_report"] == report and reader["observed_acquisitions"] == 0
    identity = report["resolutions"]["target_disease"]["decision"]["identity"]
    assert (
        identity["rule"] == "mondo_equivalence@1"
        and identity["release"] == "2026-09-01"
    )
    assert identity["equivalent_id"] == "Orphanet:868"
    unresolved = report["resolutions"]["unresolved"]
    assert unresolved["status"] == "not_found"
    assert unresolved["decision"]["rules"] == ["no_stated_equivalence"]
    targets = report["decks_report"]["targets"]
    assert targets["built_count"] == 1
    assert {e["reason"] for e in targets["meta"]["excluded"]} >= {
        "limit",
        "card_not_built",
    }
    basis = targets["explanations"][0]["basis"]
    assert basis["rule"] == "disease_targets@2"
    assert targets["explanations"][0]["support"]["status"] == "recorded"
    assert all(
        e["support"]["status"] == "recorded" for e in targets["excluded_explanations"]
    )
    assert {s["source"] for s in basis["statements"]} == {"Open Targets", "Orphanet"}
    ot = next(s for s in basis["statements"] if s["source"] == "Open Targets")
    assert ot["version"] == "26.09" and ot["score"] == pytest.approx(0.7826557233644024)
    # Source rows, attempted candidates and successfully built cards differ.
    source = next(
        s for s in targets["meta"]["sources"] if s["source"] == "Open Targets"
    )
    assert (
        source["count"] == 20 and source["total_count"] == 252 and source["truncated"]
    )
    drugs = report["decks_report"]["drugs"]
    indications = drugs["explanations"][0]["basis"]["indications"]
    assert drugs["built_count"] == 1 and len(indications) == 2
    assert {i["max_phase_for_ind"] for i in indications} == {"4.0"}
    assert {i["efo_id"] for i in indications} == {"EFO:0008559", "MONDO:0001444"}
    assert (
        report["scope"]["trials"]["limit"] == 1
        and report["scope"]["efficacy"] == "not_assessed"
    )
    group = report["group_explanation"]
    assert group["rule"]["rule"] == "disease_group_explanation@3"
    assert group["grouping_rule"]["rule"] == "disease_grouping@3"
    assert group["group"]["sources"] == [
        "ClinVar",
        "DISEASES",
        "Open Targets",
        "Orphanet",
        "UniProt",
    ]
    assert {u["reason"] for u in report["groups"]["ungrouped"]} >= {
        "no_stated_equivalence",
        "no_id_stated",
        "condition_not_provided",
        "incomplete_identity",
    }
    assert (
        report["gaps"]["membership_source_assertion_pins"]
        == "recorded_by_disease_deck_rules@2"
    )
    observed = load(bundle / "original.observations.json")["acquisitions"]
    assert all(r["network_attempts"] == 0 for r in observed)
    assert {r["source"] for r in observed} == {
        "UniProt",
        "ChEMBL",
        "UniChem",
        "MONDO",
        "Open Targets",
        "Orphanet",
        "DISEASES",
        "ClinVar",
        "MedGen",
        "ClinicalTrials.gov",
        "Europe PMC",
    }
    assert "MONDO" not in report["gaps"]["observation"]
    assert report["gaps"]["observation"] == []
    assert any(
        r["source"] == "MONDO"
        and r["operation"] == "equivalent"
        and r["outcome"] == "empty"
        for r in observed
    )
    assert any(
        r["source"] == "UniProt" and r["outcome"] == "unavailable" for r in observed
    )
    assert any(r["operation"] == "indications_for" for r in observed)
    assert all(r["producer"]["version"] != "999.reader" for r in observed)
    assert load(bundle / "original.references.csl.json")
    assert (bundle / "original.references.bib").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "trace",
        "deck_trace",
        "membership",
        "disease",
        "group",
        "item",
        "coverage",
    ],
)
def test_reader_refuses_changed_or_misbound_support_before_export(
    bundle, tmp_path, defect
):
    output = tmp_path / "copy"
    shutil.copytree(bundle, output)
    manifest_path = output / "original.manifest.json"
    manifest = load(manifest_path)
    if defect == "missing":
        (output / "original.workflow.json").unlink()
    elif defect == "item":
        manifest["assertions"]["target_disease"] = manifest["assertions"][
            "drug_disease"
        ]
    else:
        filename = (
            "original.traces.json"
            if defect in ("trace", "deck_trace")
            else "original.report.json"
        )
        path = output / filename
        value = load(path)
        if defect == "trace":
            value["cards"]["target"]["card_ref"] = manifest["cards"]["target_context"]
        elif defect == "deck_trace":
            value["decks"]["targets"]["input_card_refs"] = [
                manifest["cards"]["drug_disease"]
            ]
        elif defect == "membership":
            value["decks_report"]["targets"]["explanations"][0]["basis"]["statements"][
                0
            ]["score"] = 1.0
        elif defect == "disease":
            value["decks_report"]["targets"]["members"] = [manifest["cards"]["drug"]]
        elif defect == "coverage":
            value["gaps"]["membership_source_assertion_pins"] = "complete"
        else:
            value["group_explanation"]["statements"][0]["input"]["source_assertions"][
                0
            ]["asserted_value"] = {"different": "disease statement"}
        path.write_text(json.dumps(value), encoding="utf-8")
        manifest["files"][filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    references = output / "original.references.csl.json"
    references.unlink()
    result = invoke("read", output)
    assert result.returncode == 2 and "FAIL:" in result.stderr, (
        result.stdout + result.stderr
    )
    assert not references.exists()


def test_completed_stages_cannot_be_overwritten(bundle):
    before = (bundle / "original.manifest.json").read_bytes()
    assert invoke("produce", bundle).returncode == 2
    assert invoke("reacquire", bundle).returncode == 2
    assert (bundle / "original.manifest.json").read_bytes() == before


def test_clinical_source_statements_and_explicit_reference_scope_survive(bundle):
    report = load(bundle / "original.report.json")
    clinical = report["clinical"]
    assert clinical["rule"] == "clinical_registry_review@1"
    assert clinical["efficacy"] == "not_assessed"
    assert clinical["article_text"] == clinical["linked_websites"] == "not_queried"
    assert clinical["card_ref"] == report["cards"]["clinical_drug"]
    assert report["cards"]["drug"] != clinical["card_ref"]
    view = clinical["view"]
    assert len(view["indications"]) == 4 and len(view["not_fetched"]) == 15
    (trial,) = view["trials"]
    assert trial["trial"] == "nct:NCT00123916"
    assert trial["cited_for"] == ["doid:DOID:10113", "mondo:MONDO:0001444"]
    assert trial["enrollment"] == {"count": 2854, "type": "ACTUAL"}
    assert trial["phases"] == ["PHASE3"] and trial["has_results"] is False
    # A false registry results flag does not mean no publications or no effect.
    registry = clinical["registry_references"]["envelope"]
    module = registry["record"]["studies"]["NCT00123916"]["protocolSection"][
        "referencesModule"
    ]
    assert [r["pmid"] for r in module["references"]] == [
        "18585495",
        "26323937",
        "19753491",
    ]
    assert len(module["seeAlsoLinks"]) == 2
    assertions = report["support"]["clinical_drug"]["assertions"]
    relationships = report["support"]["clinical_drug"]["relationships"]
    tested = [rel for rel in relationships if rel["predicate"] == "tested_in"]
    (relationship,) = tested
    by_id = {a["id"]: a for a in assertions}
    assert {
        by_id[i]["source"]["name"] for i in relationship["source_assertion_ids"]
    } == {
        "ChEMBL",
        "ClinicalTrials.gov",
    }
    assert relationship["qualifiers"]["basis"] == "chembl_drug_indication"
    assert all(a["source"]["name"] != "Europe PMC" for a in assertions)


def test_original_clinical_operations_and_collective_authors_remain_distinct(bundle):
    original, later = [
        load(bundle / f"{stage}.observations.json")["acquisitions"]
        for stage in ("original", "later")
    ]
    assert not {r["id"] for r in original} & {r["id"] for r in later}
    registry = [r for r in original if r["source"] == "ClinicalTrials.gov"]
    assert {r["operation"] for r in registry} == {"studies", "study_references"}
    assert all(r["query"] == {"nct_ids": ["NCT00123916"]} for r in registry)
    by_operation = {r["operation"]: r for r in registry}
    assert by_operation["studies"]["source_version"]["value"] == "2026-09-25T09:00:04"
    references = by_operation["study_references"]
    assert references["source_version"]["value"] == "2026-10-05T09:00:05"
    assert (
        references["clinical_context"]["reference_target_access"]
        == "not_queried_by_this_operation"
    )
    assert len(references["clinical_context"]["citation_occurrences"]) == 5
    articles = [r for r in original if r["source"] == "Europe PMC"]
    assert {r["query"]["identifier"] for r in articles} == {
        "pubmed:18585495",
        "pubmed:26323937",
        "pubmed:19753491",
    }
    assert all(
        r["operation"] == "article" and r["network_attempts"] == 0 for r in articles
    )
    assert all(
        r["article_context"]["article_revision"] == "not_stated" for r in articles
    )
    assert "article_number_not_stated" in next(
        r["bibliography_gaps"]
        for r in articles
        if r["query"]["identifier"] == "pubmed:19753491"
    )
    citations = load(bundle / "original.references.csl.json")
    publications = [
        r for r in citations if r["id"].startswith("sabueso:article-publication:")
    ]
    assert sorted(len(r["author"]) for r in publications) == [9, 9, 22]
    assert all(
        {"literal": "BENEFIT Investigators"} in r["author"] for r in publications
    )
    # Registry pointers keep their native citation text rather than borrowing metadata.
    pointers = [
        r
        for r in references["bibliography"]
        if "clinicaltrials-cited-reference:" in r["id"]
    ]
    assert all("authors" not in r and "year" not in r for r in pointers)
    manifest = load(bundle / "original.manifest.json")
    assert all(
        hashlib.sha256((bundle / name).read_bytes()).hexdigest() == digest
        for name, digest in manifest["files"].items()
    )


@pytest.mark.parametrize(
    "defect",
    [
        "card",
        "phase",
        "trial",
        "indication",
        "duplicate_indication",
        "cut",
        "scope",
        "registry_body",
        "registry_trace",
        "article_body",
        "article_trace",
        "article_scope",
        "access_status",
    ],
)
def test_reader_refuses_rehashed_clinical_rebinding_before_export(
    bundle, tmp_path, defect
):
    output = tmp_path / "changed"
    shutil.copytree(bundle, output)
    manifest_path = output / "original.manifest.json"
    manifest = load(manifest_path)
    report_path = output / "original.report.json"
    report = load(report_path)
    clinical = report["clinical"]
    article = clinical["article_metadata"]["pubmed:26323937"]
    if defect == "card":
        clinical["card_ref"] = report["cards"]["drug"]
    elif defect == "phase":
        clinical["view"]["max_phase"] = 3
    elif defect == "trial":
        clinical["view"]["trials"][0]["enrollment"]["count"] = 1
    elif defect == "indication":
        clinical["view"]["indications"][0]["trials"] = ["NCT00123916"]
    elif defect == "duplicate_indication":
        clinical["view"]["indications"][0] = clinical["view"]["indications"][1]
    elif defect == "cut":
        clinical["view"]["not_fetched"] = []
    elif defect == "scope":
        clinical["article_text"] = "read"
    elif defect == "registry_body":
        clinical["registry_references"]["envelope"]["record"]["studies"]["NCT00123916"][
            "protocolSection"
        ]["referencesModule"]["references"][0]["type"] = "DERIVED"
    elif defect == "registry_trace":
        clinical["registry_references"]["envelope"]["acquisition_trace"]["records"][0][
            "query"
        ]["nct_ids"] = ["NCT01162967"]
    elif defect == "article_body":
        article["envelope"]["record"]["articles"][0]["title"] = "Different publication"
    elif defect == "article_trace":
        article["envelope"]["acquisition_trace"] = clinical["article_metadata"][
            "pubmed:18585495"
        ]["envelope"]["acquisition_trace"]
    elif defect == "article_scope":
        del clinical["article_metadata"]["pubmed:19753491"]
    else:
        registry = clinical["registry_references"]
        clinical["registry_references"] = {
            "status": "unavailable",
            "error": "Missing local answer",
            "acquisition_trace": registry["envelope"]["acquisition_trace"],
        }
    report_path.write_text(json.dumps(report), encoding="utf-8")
    manifest["files"][report_path.name] = hashlib.sha256(
        report_path.read_bytes()
    ).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    references = output / "original.references.csl.json"
    references.unlink()
    result = invoke("read", output)
    assert result.returncode == 2 and "FAIL:" in result.stderr, (
        result.stdout + result.stderr
    )
    assert not references.exists()


@pytest.mark.parametrize(
    "case",
    [
        "registry_unavailable",
        "registry_failed",
        "registry_empty",
        "article_unavailable",
        "article_failed",
        "article_empty",
    ],
)
def test_reference_access_gaps_survive_independent_reading(tmp_path, case):
    fixtures = tmp_path / "fixtures"
    shutil.copytree(DATA, fixtures, ignore=shutil.ignore_patterns(".source_snapshots"))
    if case.startswith("registry"):
        path = fixtures / "clinicaltrials/references.json"
        if case.endswith("unavailable"):
            path.unlink()
        elif case.endswith("failed"):
            path.write_text(json.dumps({"studies": []}), encoding="utf-8")
        else:
            path.write_text(
                json.dumps(
                    {
                        "version": "synthetic-complete-negative",
                        "studies": {},
                        "missing": ["NCT00123916"],
                    }
                ),
                encoding="utf-8",
            )
    else:
        path = fixtures / "europepmc/articles/pubmed__26323937.json"
        if case.endswith("unavailable"):
            path.unlink()
        else:
            payload = load(path)
            if case.endswith("empty"):
                payload["hitCount"] = 0
                payload["resultList"]["result"] = []
            else:
                payload["resultList"]["result"] = None
            path.write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "bundle"
    for action in ("produce", "read"):
        result = invoke(action, output, fixtures)
        assert result.returncode == 0, result.stdout + result.stderr
    clinical = load(output / "original.reader.json")["original_report"]["clinical"]
    if case.startswith("registry"):
        registry = clinical["registry_references"]
        if case.endswith("empty"):
            assert registry["status"] == "returned"
            assert registry["envelope"]["record"] == {
                "studies": {},
                "missing": ["NCT00123916"],
            }
            assert (
                registry["envelope"]["acquisition_trace"]["records"][0]["outcome"]
                == "empty"
            )
        else:
            assert registry["status"] == (
                "unavailable" if case.endswith("unavailable") else "failed"
            )
            assert "envelope" not in registry
            assert (
                registry["acquisition_trace"]["records"][0]["outcome"]
                == registry["status"]
            )
    else:
        article = clinical["article_metadata"]["pubmed:26323937"]
        if case.endswith("unavailable"):
            assert article["status"] == "unavailable" and "envelope" not in article
        elif case.endswith("failed"):
            assert article["status"] == "failed" and "envelope" not in article
        else:
            assert article["status"] == "returned"
            assert article["envelope"]["record"]["total_count"] == 0
            assert (
                article["envelope"]["acquisition_trace"]["records"][0]["outcome"]
                == "empty"
            )
