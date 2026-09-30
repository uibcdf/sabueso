"""MONDO: one disease across terminologies, through the equivalences it states (#90).

MONDO (Monarch Initiative, CC BY 4.0) integrates disease terminologies: DOID, Orphanet,
OMIM, NCIT, MeSH, EFO, ICD, MedGen and others. For each of its terms it states which
external ids are the same disease: an xref marked ``source="MONDO:equivalentTo"``.
Other xrefs are related terms, not the same disease. Sabueso joins a disease id to a
MONDO term only through a stated equivalence.

It is published as dated releases on GitHub (``v2026-09-01``), with the SHA-256 of each
file. ``OnlineMONDOClient`` downloads ``mondo.obo`` (about 53 MB) once per process,
checks it, and indexes it (``tools.db._release``). ``FixtureMONDOClient`` reads
``<directory>/mondo/mondo.obo``, a subset of the same file.

- ``term(mondo_id)`` returns ``{"retrieved_at", "version", "record": term}``, or raises
  ``RecordNotFoundError``.
- ``equivalent(curie)`` returns ``{"retrieved_at", "version", "mondo": id | None}``:
  the MONDO term MONDO states is the same disease, if any.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.error import HTTPError, URLError

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.tools.db import _release
from sabueso.tools.db._http import request, stamp, urlopen
from sabueso.tools.db._record import online, source_record

SOURCE = "MONDO"
LATEST = "https://api.github.com/repos/monarch-initiative/mondo/releases/latest"
EQUIVALENT = "MONDO:equivalentTo"
XREF = re.compile(r"^xref: (\S+)(?: \{(.*)\})?")
SYNONYM = re.compile(r'^synonym: "((?:[^"\\]|\\.)*)" (\w+)')
DEFINITION = re.compile(r'^def: "((?:[^"\\]|\\.)*)" \[(.*)\]')
#: Namespaces as users and sources write them → MONDO's spelling.
NAMESPACES = {
    "mondo": "MONDO",
    "doid": "DOID",
    "omim": "OMIM",
    "omimps": "OMIMPS",
    "orphanet": "Orphanet",
    "orpha": "Orphanet",
    "ordo": "Orphanet",
    "mesh": "MESH",
    "efo": "EFO",
    "ncit": "NCIT",
    "medgen": "MEDGEN",
    "umls": "UMLS",
    "icd10cm": "ICD10CM",
    "icd10who": "ICD10WHO",
    "icd9": "ICD9",
    "sctid": "SCTID",
    "snomedct": "SCTID",
    "icd11.foundation": "icd11.foundation",
    "oncotree": "ONCOTREE",
    "decipher": "DECIPHER",
}


def normalize(curie: str) -> str | None:
    """MONDO's spelling of a disease id, from the forms users and sources write:
    ``doid:9352``, ``DOID:9352``, ``doid:DOID:9352``, ``efo:EFO:0001360``,
    ``EFO_0001360``, ``ORPHA:586``. None when the namespace is not one MONDO maps."""
    text = str(curie).strip()
    if ":" not in text and "_" in text:
        text = text.replace("_", ":", 1)
    namespace, _, local = text.partition(":")
    if ":" in local and local.split(":", 1)[0].lower() == namespace.lower():
        local = local.split(":", 1)[1]
    elif ":" in local and local.split(":", 1)[0].lower() in NAMESPACES:
        namespace, _, local = local.partition(":")
    prefix = NAMESPACES.get(namespace.lower())
    if prefix is None or not local:
        return None
    return f"{prefix}:{local}"


def _unescape(text: str) -> str:
    return text.replace('\\"', '"').replace("\\\\", "\\")


def parse_release(text: str) -> Tuple[str | None, Dict[str, Any], Dict[str, str]]:
    """``(version, terms, equivalents)`` of a MONDO OBO file: each term as stated, and
    each external id MONDO states is equivalent, to its MONDO term."""
    version = None
    terms: Dict[str, Dict[str, Any]] = {}
    equivalents: Dict[str, str] = {}
    stanza, term = None, None
    for line in text.splitlines():
        if line.startswith("data-version:") and version is None:
            version = line.split(":", 1)[1].strip().replace("releases/", "")
        if line.startswith("["):
            stanza, term = line.strip(), None
            continue
        if stanza != "[Term]":
            continue
        if line.startswith("id: MONDO:"):
            term = {
                "id": line[4:].strip(),
                "synonyms": [],
                "xrefs": [],
                "parents": [],
                "subsets": [],
                "replaced_by": [],
                "consider": [],
            }
            terms[term["id"]] = term
        elif term is None:
            continue
        elif line.startswith("name: "):
            term["name"] = line[6:].strip()
        elif line.startswith("def: "):
            match = DEFINITION.match(line)
            if match:
                refs = [r.strip() for r in match.group(2).split(",") if r.strip()]
                term["definition"] = {
                    "text": _unescape(match.group(1)),
                    "references": refs,
                }
        elif line.startswith("synonym: "):
            match = SYNONYM.match(line)
            if match:
                term["synonyms"].append(
                    {"name": _unescape(match.group(1)), "scope": match.group(2).lower()}
                )
        elif line.startswith("xref: "):
            match = XREF.match(line)
            if match:
                sources = re.findall(r'source="([^"]*)"', match.group(2) or "")
                equivalent = EQUIVALENT in sources
                term["xrefs"].append({"id": match.group(1), "equivalent": equivalent})
                if equivalent:
                    equivalents[match.group(1)] = term["id"]
        elif line.startswith("is_a: MONDO:"):
            term["parents"].append(line[6:].split(" ", 1)[0])
        elif line.startswith("subset: "):
            term["subsets"].append(line[8:].split(" ", 1)[0])
        elif line.startswith("is_obsolete: true"):
            term["obsolete"] = True
        elif line.startswith("replaced_by: "):
            term["replaced_by"].append(line[13:].strip())
        elif line.startswith("consider: "):
            term["consider"].append(line[10:].strip())
    return version, terms, equivalents


def _answer(index: tuple, retrieved_at: str) -> Dict[str, Any]:
    version, _, _ = index
    return {"retrieved_at": retrieved_at, "version": version}


class _Index:
    """Lookups shared by the online and fixture clients."""

    def _index(self) -> tuple:
        raise NotImplementedError

    def _retrieved_at(self) -> str:
        raise NotImplementedError

    def term(self, mondo_id: str) -> Dict[str, Any]:
        index = self._index()
        key = normalize(mondo_id)
        record = index[1].get(key or "")
        if record is None:
            raise RecordNotFoundError(
                f"MONDO {index[0]} has no term {mondo_id}", version=index[0]
            )
        return {**_answer(index, self._retrieved_at()), "record": record}

    def equivalent(self, curie: str) -> Dict[str, Any]:
        index = self._index()
        key = normalize(curie)
        return {
            **_answer(index, self._retrieved_at()),
            "query": key,
            "mondo": index[2].get(key or ""),
        }


class OnlineMONDOClient(_Index):
    def __init__(self, timeout: float = 300.0, release: str | None = None) -> None:
        self.timeout = timeout
        self.release = release
        self._when = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _retrieved_at(self) -> str:
        return self._when

    def _asset(self) -> Dict[str, str]:
        stamp(SOURCE)  # what an archive keeps of this lookup is MONDO's
        url = (
            LATEST
            if self.release is None
            else f"{LATEST.rsplit('/', 1)[0]}/tags/{self.release}"
        )
        try:
            with urlopen(request(url), timeout=60) as resp:  # nosec - trusted
                data = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            raise ConnectorError(f"MONDO release lookup failed: {exc}") from exc
        assets = [a for a in data.get("assets") or [] if a.get("name") == "mondo.obo"]
        if len(assets) != 1:
            raise ConnectorError(f"MONDO {data.get('tag_name')} has no mondo.obo")
        return {
            "tag": data.get("tag_name"),
            "url": assets[0]["browser_download_url"],
            "sha256": str(assets[0].get("digest") or "").replace("sha256:", ""),
        }

    def _download(self, asset: Dict[str, str]) -> tuple:
        stamp(SOURCE)
        try:
            with urlopen(request(asset["url"]), timeout=self.timeout) as resp:  # nosec
                payload = resp.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise ConnectorError(f"MONDO download failed: {exc}") from exc
        if asset["sha256"]:
            _release.verify_sha256(payload, asset["sha256"], f"MONDO {asset['tag']}")
        return parse_release(payload.decode("utf-8"))

    def _index(self) -> tuple:
        if not hasattr(self, "_asset_info"):
            self._asset_info = self._asset()
        asset = self._asset_info
        return _release.remembered(SOURCE, asset["tag"], lambda: self._download(asset))


class FixtureMONDOClient(_Index):
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.path = Path(directory) / "mondo" / "mondo.obo"
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def _retrieved_at(self) -> str:
        return self.retrieved_at

    def _index(self) -> tuple:
        return parse_release(self.path.read_text(encoding="utf-8"))

    def term(self, mondo_id: str) -> Dict[str, Any]:
        if mondo_id in self.failing:
            raise ConnectorError(f"MONDO request for {mondo_id} failed (simulated)")
        return super().term(mondo_id)

    def equivalent(self, curie: str) -> Dict[str, Any]:
        if curie in self.failing:
            raise ConnectorError(f"MONDO request for {curie} failed (simulated)")
        return super().equivalent(curie)


# --- Public source access (uibcdf/sabueso#49) -----------------------------------------


@arg_digest()
def get_term(identifier: str, client: Any = None, skip_digestion: bool = False):
    """A MONDO term as stated: name, definition, synonyms, xrefs (each marked
    equivalent or not), parents, subsets, and obsolescence."""
    response = online(client, OnlineMONDOClient).term(identifier)
    return source_record(
        SOURCE,
        "term",
        {"mondo": identifier},
        response.get("retrieved_at"),
        response.get("version"),
        response["record"],
    )
