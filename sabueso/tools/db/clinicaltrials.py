"""ClinicalTrials.gov: registered clinical studies, by NCT id (uibcdf/sabueso#81).

A study names its interventions only as text ("Benznidazole", a brand name, a code), so
it is never matched to a molecule by name. Sabueso asks only for the NCT ids another
source states for a molecule: ChEMBL's drug indications cite them.

``studies(nct_ids)`` returns ``{"retrieved_at", "version", "record": {nct_id: study},
"missing": [...]}``. ``study`` keeps the fields Sabueso maps (``FIELDS``) as the API v2
states them, and ``version`` is the API's data timestamp. An id ClinicalTrials.gov does
not hold is listed in ``missing``, and a failed request raises ``ConnectorError``.
``OnlineClinicalTrialsClient`` queries the API v2 in batches; the fixture client reads
``<directory>/clinicaltrials/studies.json``.

Terms: works of the US government, not under copyright in the US; NLM asks that the
source be acknowledged ("Source: National Library of Medicine").
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError
from sabueso.tools.db._http import stamp, urlopen
from sabueso.tools.db._record import online, source_record

SOURCE = "ClinicalTrials.gov"
API = "https://clinicaltrials.gov/api/v2"
BATCH = 50
#: The parts of a study Sabueso keeps: identity, status and dates, design (type, phases,
#: enrolment), conditions, interventions, lead sponsor, and whether results are posted.
FIELDS = (
    "protocolSection.identificationModule.nctId",
    "protocolSection.identificationModule.briefTitle",
    "protocolSection.statusModule.overallStatus",
    "protocolSection.statusModule.startDateStruct",
    "protocolSection.statusModule.completionDateStruct",
    "protocolSection.statusModule.lastUpdatePostDateStruct",
    "protocolSection.designModule.studyType",
    "protocolSection.designModule.phases",
    "protocolSection.designModule.enrollmentInfo",
    "protocolSection.conditionsModule.conditions",
    "protocolSection.armsInterventionsModule.interventions",
    "protocolSection.sponsorCollaboratorsModule.leadSponsor",
    "hasResults",
)


def _get(path: str, params: Dict[str, Any], timeout: float) -> Any:
    url = f"{API}/{path}" + ("?" + urlencode(params) if params else "")
    try:
        with urlopen(url, timeout=timeout) as resp:  # nosec - trusted endpoint
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise ConnectorError(f"ClinicalTrials.gov {path} failed: {exc}") from exc


def _nct(study: Dict[str, Any]) -> str | None:
    return ((study.get("protocolSection") or {}).get("identificationModule") or {}).get(
        "nctId"
    )


class OnlineClinicalTrialsClient:
    def __init__(self, timeout: float = 60.0) -> None:
        self.timeout = timeout

    def studies(self, nct_ids: Iterable[str]) -> Dict[str, Any]:
        ids = sorted({i.strip().upper() for i in nct_ids if i and i.strip()})
        retrieval = stamp(SOURCE)
        version = _get("version", {}, self.timeout).get("dataTimestamp")
        found: Dict[str, Any] = {}
        for i in range(0, len(ids), BATCH):
            chunk = ids[i : i + BATCH]
            page = _get(
                "studies",
                {
                    "filter.ids": ",".join(chunk),
                    "fields": ",".join(FIELDS),
                    "pageSize": len(chunk),
                    "format": "json",
                },
                self.timeout,
            )
            for study in page.get("studies") or []:
                if _nct(study):
                    found[_nct(study)] = study
        return {
            "retrieved_at": retrieval.value,
            "version": version,
            "record": {i: found[i] for i in ids if i in found},
            "missing": [i for i in ids if i not in found],
        }


class FixtureClinicalTrialsClient:
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def studies(self, nct_ids: Iterable[str]) -> Dict[str, Any]:
        ids: List[str] = sorted({i.strip().upper() for i in nct_ids if i and i.strip()})
        if self.failing & set(ids):
            raise ConnectorError(
                f"ClinicalTrials.gov request for {ids} failed (simulated)"
            )
        path = self.directory / "clinicaltrials" / "studies.json"
        saved = (
            json.loads(path.read_text(encoding="utf-8"))
            if path.is_file()
            else {"version": None, "studies": {}}
        )
        return {
            "retrieved_at": self.retrieved_at,
            "version": saved.get("version"),
            "record": {i: saved["studies"][i] for i in ids if i in saved["studies"]},
            "missing": [i for i in ids if i not in saved["studies"]],
        }


# --- Public source access (uibcdf/sabueso#49) -----------------------------------------


@arg_digest()
def get_studies(identifiers: Any, client: Any = None, skip_digestion: bool = False):
    """ClinicalTrials.gov studies by NCT id; ``missing`` lists ids it does not hold."""
    response = online(client, OnlineClinicalTrialsClient).studies(identifiers)
    return source_record(
        SOURCE,
        "studies",
        {"nct_ids": list(identifiers)},
        response.get("retrieved_at"),
        response.get("version"),
        {"studies": response["record"], "missing": response["missing"]},
    )
