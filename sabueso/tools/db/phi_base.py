"""PHI-base: phenotypes of pathogen genes, alone or on a host (uibcdf/sabueso#83).

PHI-base curates, from publications, what happens when a pathogen gene is deleted,
disrupted or altered: loss of virulence on a host, a changed pathogen phenotype, a
gene-for-gene interaction. Each gene is keyed by its UniProt accession, so a record
joins a protein card through an identifier the source states.

PHI-base 5 is published as versioned releases on Zenodo (CC BY 4.0), one JSON file of
curation sessions. It has no documented per-gene API, so the online client works on a
release:

- ``OnlinePHIBaseClient`` finds the latest release of PHI-base 5 (or the Zenodo record
  given), downloads it once, checks its MD5 against Zenodo, and splits it per UniProt
  accession. Sabueso writes only where it is told to (``devguide/CACHE_POLICY.md``):
  the split release is kept in memory for the process, unless a cache directory is
  given (``cache_dir=``, or ``$SABUESO_CACHE_DIR``), where it is written once (each
  curation session once, and an index by accession) and read by later sessions.
- ``FixturePHIBaseClient`` reads ``<directory>/phi_base/<ACCESSION>.json``, the same
  format as a cached file: ``{"version", "record", "sessions": [...]}``.

``phenotypes(accession)`` returns ``{"retrieved_at", "version", "record", "sessions"}``:
the curation sessions that name the gene, as PHI-base states them. It raises
``RecordNotFoundError`` when the release has no such gene, and ``ConnectorError`` when
the release cannot be obtained.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.tools.db._record import online, source_record

SOURCE = "PHI-base"
ZENODO_RECORDS = "https://zenodo.org/api/records"
#: The Zenodo concept record of PHI-base 5: every version, the latest first.
CONCEPT_RECORD = "10722192"


#: Releases split in memory, per Zenodo record, for the life of the process.
_MEMORY: Dict[str, Dict[str, Any]] = {}


def cache_root() -> Path | None:
    """The cache directory the user chose (``$SABUESO_CACHE_DIR``), or None: Sabueso
    keeps no files unless told where."""
    value = os.environ.get("SABUESO_CACHE_DIR")
    return Path(value) if value else None


def index_release(data: Dict[str, Any]) -> tuple:
    """``(sessions, index)`` of a PHI-base 5 release: each curation session once, as
    compact JSON text keyed by its id, and the ids of the sessions naming each UniProt
    accession. A session can name many genes, so it is stored once, never per gene."""
    sessions: Dict[str, str] = {}
    index: Dict[str, List[str]] = {}
    for session_id, session in sorted((data.get("curation_sessions") or {}).items()):
        sessions[session_id] = json.dumps({"session": session_id, **session})
        accessions = {
            (gene.get("uniprot_data") or {}).get("uniprot_id")
            for gene in (session.get("genes") or {}).values()
        } - {None}
        for accession in sorted(accessions):
            index.setdefault(accession, []).append(session_id)
    return sessions, index


def split_release(data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """The curation sessions of a release per UniProt accession (fixtures use this)."""
    sessions, index = index_release(data)
    return {
        accession: [json.loads(sessions[sid]) for sid in ids]
        for accession, ids in index.items()
    }


def _get_json(url: str, timeout: float) -> Dict[str, Any]:
    try:
        with urlopen(url, timeout=timeout) as resp:  # nosec - trusted endpoint
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise ConnectorError(f"PHI-base release lookup failed: {exc}") from exc


class OnlinePHIBaseClient:
    def __init__(
        self,
        timeout: float = 300.0,
        cache_dir: str | Path | None = None,
        record: str | None = None,
    ) -> None:
        self.timeout = timeout
        root = Path(cache_dir) if cache_dir else cache_root()
        self.cache_dir = root / "phi-base" if root is not None else None
        self.record = record
        self._release: Dict[str, Any] | None = None

    def release(self) -> Dict[str, Any]:
        """The Zenodo record used: ``{"record", "version", "url", "md5"}``."""
        if self._release is None:
            url = (
                f"{ZENODO_RECORDS}/{self.record}"
                if self.record
                else f"{ZENODO_RECORDS}/{CONCEPT_RECORD}/versions/latest"
            )
            data = _get_json(url, self.timeout)
            files = [f for f in data.get("files") or [] if f["key"].endswith(".zip")]
            if len(files) != 1:
                raise ConnectorError(
                    f"PHI-base record {data.get('id')} does not hold one release file."
                )
            self._release = {
                "record": str(data["id"]),
                "version": str((data.get("metadata") or {}).get("version")),
                "url": files[0]["links"]["self"],
                "md5": files[0]["checksum"].split(":", 1)[-1],
            }
        return self._release

    def _download(self) -> tuple:
        """The release, downloaded, checked against its MD5 and indexed
        (``index_release``)."""
        release = self.release()
        try:
            with urlopen(release["url"], timeout=self.timeout) as resp:  # nosec
                payload = resp.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise ConnectorError(f"PHI-base release download failed: {exc}") from exc
        if hashlib.md5(payload).hexdigest() != release["md5"]:  # nosec - Zenodo's
            raise ConnectorError(
                f"PHI-base release {release['version']} does not match its checksum."
            )
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            (name,) = [
                n
                for n in archive.namelist()
                if n.endswith(".json") and not n.endswith("schema.json")
            ]
            data = json.loads(archive.read(name).decode("utf-8"))
        return index_release(data)

    def _prepared(self) -> Path:
        """The indexed release in the cache directory, written once: each session in
        ``sessions/<id>.json``, the accession index in ``index.json``."""
        release = self.release()
        target = self.cache_dir / release["version"]
        if (target / "release.json").is_file():
            return target
        sessions, index = self._download()
        prepared_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(dir=self.cache_dir))
        try:
            (staging / "sessions").mkdir()
            for session_id, text in sessions.items():
                (staging / "sessions" / f"{session_id}.json").write_text(
                    text, encoding="utf-8"
                )
            (staging / "index.json").write_text(json.dumps(index), encoding="utf-8")
            (staging / "release.json").write_text(
                json.dumps({**release, "retrieved_at": prepared_at}), encoding="utf-8"
            )
            if target.exists():
                shutil.rmtree(target)
            staging.rename(target)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
        return target

    def _in_memory(self, accession: str) -> Dict[str, Any]:
        release = self.release()
        kept = _MEMORY.get(release["record"])
        if kept is None:
            # Sessions as compact text: a fraction of the parsed release's memory.
            sessions, index = self._download()
            kept = {
                "retrieved_at": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                ),
                "sessions": sessions,
                "index": index,
            }
            _MEMORY[release["record"]] = kept
        if accession not in kept["index"]:
            raise RecordNotFoundError(
                f"PHI-base {release['version']} names no gene with UniProt {accession}"
            )
        return {
            "retrieved_at": kept["retrieved_at"],
            "version": release["version"],
            "record": release["record"],
            "sessions": [
                json.loads(kept["sessions"][i]) for i in kept["index"][accession]
            ],
        }

    def phenotypes(self, accession: str) -> Dict[str, Any]:
        if self.cache_dir is None:
            return self._in_memory(accession)
        directory = self._prepared()
        meta = json.loads((directory / "release.json").read_text(encoding="utf-8"))
        index = json.loads((directory / "index.json").read_text(encoding="utf-8"))
        if accession not in index:
            raise RecordNotFoundError(
                f"PHI-base {meta['version']} names no gene with UniProt {accession}"
            )
        return {
            "retrieved_at": meta["retrieved_at"],
            "version": meta["version"],
            "record": meta["record"],
            "sessions": [
                json.loads(
                    (directory / "sessions" / f"{i}.json").read_text(encoding="utf-8")
                )
                for i in index[accession]
            ],
        }


class FixturePHIBaseClient:
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def phenotypes(self, accession: str) -> Dict[str, Any]:
        if accession in self.failing:
            raise ConnectorError(f"PHI-base request for {accession} failed (simulated)")
        path = self.directory / "phi_base" / f"{accession}.json"
        if not path.is_file():
            raise RecordNotFoundError(
                f"PHI-base names no gene with UniProt {accession}"
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        return {"retrieved_at": self.retrieved_at, **data}


# --- Public source access (uibcdf/sabueso#49) -----------------------------------------


@arg_digest()
def get_phenotypes(identifier: str, client: Any = None, skip_digestion: bool = False):
    """PHI-base's curation sessions that name a gene, by its UniProt accession: the
    phenotypes of its mutants, alone or on a host, as curated from publications."""
    response = online(client, OnlinePHIBaseClient).phenotypes(identifier)
    return source_record(
        SOURCE,
        "phenotypes",
        {"uniprot": identifier},
        response.get("retrieved_at"),
        response.get("version"),
        response["sessions"],
    )
