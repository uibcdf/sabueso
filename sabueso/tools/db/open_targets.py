"""Open Targets Platform: target–disease associations (uibcdf/sabueso#82).

Open Targets scores the association of a human gene (an Ensembl gene, ``ENSG…``) with
diseases (EFO, MONDO… terms), overall and per data type (genetic association, known
drug, literature…). The scores are Open Targets' own computation: Sabueso records them
as its statement, with the data version, and never recomputes or re-ranks them.

``associations(gene, limit)`` returns ``{"retrieved_at", "version", "record": {"target",
"count", "rows"}}``: the target (its symbol and ``proteinIds``, the products Open Targets
lists) and its associated diseases, in Open Targets' own order (overall score), at most
``limit`` of ``count``. It raises ``RecordNotFoundError`` when Open Targets has no such
target, and ``ConnectorError`` when it cannot answer.

``targets(disease, limit)`` is the other direction (#90): a disease's associated
targets, each with its ``proteinIds`` and scores, in Open Targets' order.

``OnlineOpenTargetsClient`` queries the GraphQL API (no key; CC0 1.0).
``FixtureOpenTargetsClient`` reads ``<directory>/open_targets/<ENSG>.json`` and
``<directory>/open_targets/diseases/<MONDO_…>.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.tools.db._http import stamp, urlopen
from sabueso.tools.db._record import online, source_record

SOURCE = "Open Targets"
GRAPHQL = "https://api.platform.opentargets.org/api/v4/graphql"
#: Everything Open Targets states, up to a safety ceiling; a cut is reported.
DEFAULT_LIMIT = 5000
#: The largest page the GraphQL API accepts is 3000 rows.
PAGE_SIZE = 3000
QUERY = """
query($gene: String!, $index: Int!, $size: Int!) {
  target(ensemblId: $gene) {
    id approvedSymbol proteinIds { id source }
    associatedDiseases(page: {index: $index, size: $size}) {
      count rows { score disease { id name } datatypeScores { id score } }
    }
  }
  meta { dataVersion { year month iteration } }
}
"""
#: A disease's associated targets (#82, point 2; #90).
DISEASE_QUERY = """
query($disease: String!, $index: Int!, $size: Int!) {
  disease(efoId: $disease) {
    id name
    associatedTargets(page: {index: $index, size: $size}) {
      count
      rows {
        score datatypeScores { id score }
        target { id approvedSymbol proteinIds { id source } }
      }
    }
  }
  meta { dataVersion { year month iteration } }
}
"""


def disease_id(curie: str) -> str:
    """Open Targets' spelling of a disease id: ``MONDO:0014221`` → ``MONDO_0014221``."""
    return str(curie).replace(":", "_", 1)


def _version(meta: Dict[str, Any]) -> str | None:
    data = (meta or {}).get("dataVersion") or {}
    if not data.get("year"):
        return None
    version = f"{data['year']}.{data['month']}"
    return f"{version}.{data['iteration']}" if data.get("iteration") else version


class OnlineOpenTargetsClient:
    def __init__(self, timeout: float = 60.0) -> None:
        self.timeout = timeout

    def _post(self, variables: Dict[str, Any], query: str = QUERY) -> Dict[str, Any]:
        body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
        request = Request(
            GRAPHQL, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urlopen(request, timeout=self.timeout, expect_json=True) as resp:  # nosec - trusted
                data = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            raise ConnectorError(f"Open Targets request failed: {exc}") from exc
        if data.get("errors"):
            raise ConnectorError(f"Open Targets answered with errors: {data['errors']}")
        return data.get("data") or {}

    def associations(self, gene: str, limit: int = DEFAULT_LIMIT) -> Dict[str, Any]:
        retrieval = stamp(SOURCE)
        rows, index, count, target, version = [], 0, None, None, None
        while count is None or len(rows) < min(limit, count):
            data = self._post(
                {"gene": gene, "index": index, "size": min(PAGE_SIZE, limit)}
            )
            target = data.get("target")
            version = _version(data.get("meta"))
            if target is None:
                raise RecordNotFoundError(
                    f"Open Targets has no target {gene}", version=version
                )
            page = target.get("associatedDiseases") or {}
            count = page.get("count") or 0
            batch = page.get("rows") or []
            if not batch:
                break
            rows.extend(batch)
            index += 1
        return {
            "retrieved_at": retrieval.value,
            "version": version,
            "record": {
                "target": {
                    k: target[k] for k in ("id", "approvedSymbol", "proteinIds")
                },
                "count": count,
                "rows": rows[:limit],
            },
        }

    def targets(self, disease: str, limit: int = DEFAULT_LIMIT) -> Dict[str, Any]:
        """A disease's associated targets, in Open Targets' order (overall score), at
        most ``limit`` of ``count``: ``{"retrieved_at", "version", "record":
        {"disease", "count", "rows"}}``. ``disease`` is a MONDO, EFO… id."""
        retrieval = stamp(SOURCE)
        rows, index, count, found, version = [], 0, None, None, None
        while count is None or len(rows) < min(limit, count):
            data = self._post(
                {
                    "disease": disease_id(disease),
                    "index": index,
                    "size": min(PAGE_SIZE, limit),
                },
                DISEASE_QUERY,
            )
            found = data.get("disease")
            version = _version(data.get("meta"))
            if found is None:
                raise RecordNotFoundError(
                    f"Open Targets has no disease {disease}", version=version
                )
            page = found.get("associatedTargets") or {}
            count = page.get("count") or 0
            batch = page.get("rows") or []
            if not batch:
                break
            rows.extend(batch)
            index += 1
        return {
            "retrieved_at": retrieval.value,
            "version": version,
            "record": {
                "disease": {k: found[k] for k in ("id", "name")},
                "count": count,
                "rows": rows[:limit],
            },
        }


class FixtureOpenTargetsClient:
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def associations(self, gene: str, limit: int = DEFAULT_LIMIT) -> Dict[str, Any]:
        if gene in self.failing:
            raise ConnectorError(f"Open Targets request for {gene} failed (simulated)")
        path = self.directory / "open_targets" / f"{gene}.json"
        if not path.is_file():
            raise RecordNotFoundError(f"Open Targets has no target {gene}")
        saved = json.loads(path.read_text(encoding="utf-8"))
        return {
            "retrieved_at": self.retrieved_at,
            "version": saved.get("version"),
            "record": {**saved["record"], "rows": saved["record"]["rows"][:limit]},
        }

    def targets(self, disease: str, limit: int = DEFAULT_LIMIT) -> Dict[str, Any]:
        """Reads ``<directory>/open_targets/diseases/<MONDO_…>.json``."""
        key = disease_id(disease)
        if disease in self.failing or key in self.failing:
            raise ConnectorError(
                f"Open Targets request for {disease} failed (simulated)"
            )
        path = self.directory / "open_targets" / "diseases" / f"{key}.json"
        if not path.is_file():
            raise RecordNotFoundError(f"Open Targets has no disease {disease}")
        saved = json.loads(path.read_text(encoding="utf-8"))
        return {
            "retrieved_at": self.retrieved_at,
            "version": saved.get("version"),
            "record": {**saved["record"], "rows": saved["record"]["rows"][:limit]},
        }


# --- Public source access (uibcdf/sabueso#49) -----------------------------------------


@arg_digest()
def get_associations(
    identifier: str,
    limit: int = DEFAULT_LIMIT,
    client: Any = None,
    skip_digestion: bool = False,
):
    """Open Targets' target record (an Ensembl gene id) and its associated diseases, in
    Open Targets' order, at most ``limit``."""
    response = online(client, OnlineOpenTargetsClient).associations(identifier, limit)
    return source_record(
        SOURCE,
        "associations",
        {"ensembl_gene": identifier, "limit": limit},
        response.get("retrieved_at"),
        response.get("version"),
        response["record"],
    )
