"""Bounded, reproducible extraction from identified supplied text fragments (#92)."""

from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime, timezone

from sabueso._private.argdigest import arg_digest
from sabueso._private.argdigest._shared import refuse
from sabueso.core import attribution as adapter
from sabueso.core.relationship_store import make_relationship
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_acquisition, make_source_assertion

RULE = "literal_uniprot_mention@1"
_ACCESSION = re.compile(
    r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})"
)


@arg_digest()
def extract_literature_mentions(
    text: str,
    identifier: str,
    publication: str,
    locator: str,
    skip_digestion: bool = False,
) -> dict:
    """Find explicitly namespaced UniProt mentions in an identified text fragment.

    ``identifier`` is a canonical UniProt accession. ``publication`` is a PubMed
    or DOI reference; ``locator`` identifies the supplied fragment. Matches require
    ``UniProt:<accession>``, ``UniProtKB:<accession>`` or an official UniProt URL.
    Names, bare accessions, isoform suffixes and longer tokens are not matches.

    Returns detached SourceAssertions, supported mention relationships and original
    execution attribution. It does not mutate a card, curate a claim, fetch text
    or establish a biological finding. Offsets count Python Unicode characters,
    starting at zero with an exclusive end, in the exact supplied text.
    """
    if not _ACCESSION.fullmatch(identifier):
        raise refuse(
            "identifier",
            identifier,
            "sabueso.extract_literature_mentions",
            "expected a canonical UniProt accession",
        )
    if not locator:
        raise refuse(
            "locator",
            locator,
            "sabueso.extract_literature_mentions",
            "expected the location of the supplied text",
        )
    from sabueso.core.attribution_bibliography import software

    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    accession = re.escape(identifier)
    # Prefix alternatives name the namespace; no sequence/name matching occurs.
    pattern = re.compile(
        rf"(?<![\w:/.-])(?:UniProt(?:KB)?:{accession}|https?://www\.uniprot\.org/(?:uniprotkb|uniprot)/{accession}(?:/entry)?)(?![\w/-])"
    )
    input_hash = digest(text)
    configuration = {
        "identifier": identifier,
        "namespaces": ["UniProt", "UniProtKB", "official_uniprot_url"],
        "case_sensitive": True,
        "offset_basis": "unicode_characters_zero_based_end_exclusive",
        "scope": "supplied_text_fragment",
    }
    acquisition = make_acquisition(
        "rule_extraction",
        tool="sabueso.literal_uniprot_mention",
        version="1",
        configuration=configuration,
    )
    assertions, locations = [], []
    for match in pattern.finditer(text):
        value = {
            "text": match.group(),
            "start": match.start(),
            "end": match.end(),
            "locator": locator,
            "input_sha256": input_hash,
        }
        assertion = make_source_assertion(
            "relationships.mentioned_in",
            value,
            "Literature",
            publication,
            started,
            source_type="literature",
            subject_ref=f"uniprot:{identifier}",
            acquisition=deepcopy(acquisition),
        )
        assertions.append(assertion)
        locations.append({**value, "source_assertion_id": assertion["id"]})
    relationships = (
        [
            make_relationship(
                f"uniprot:{identifier}",
                "mentioned_in",
                publication,
                qualifiers={
                    "source": "Literature",
                    "mention": "uniprot_accession",
                    "article": {"publication_ref": publication},
                    "locations": locations,
                },
                source_assertion_ids=[a["id"] for a in assertions],
            )
        ]
        if assertions
        else []
    )
    trace = {
        "format": "sabueso.literature_extraction@1",
        "rule": RULE,
        "producer": software(),
        "publication_ref": publication,
        "locator": locator,
        "input_sha256": input_hash,
        "configuration": configuration,
        "started_at": started,
        "outcome": "received" if assertions else "empty",
        "count": len(assertions),
        "terms": {"state": "unknown", "scope": "supplied_text_fragment"},
        "bibliography_gaps": ["supplied_publication_metadata_not_declared"],
    }
    trace["provider"] = _credit(trace)
    adapter._observe_literature(trace)
    return {
        "source_assertions": assertions,
        "relationships": relationships,
        "extraction_trace": trace,
    }


def _credit(trace):
    backend = None
    try:
        backend = adapter._load_backend()
        context = {k: deepcopy(v) for k, v in trace.items() if k != "producer"}
        resource = "sabueso:literature-extraction:" + digest(
            canonical_json(
                {
                    key: trace[key]
                    for key in (
                        "rule",
                        "publication_ref",
                        "locator",
                        "input_sha256",
                        "configuration",
                    )
                }
            )
        )
        publication = trace["publication_ref"]
        citation = {
            "id": "sabueso:literature-publication:" + digest(publication),
            "type": "article",
        }
        if publication.startswith("doi:"):
            citation["doi"] = publication[4:]
            citation["url"] = "https://doi.org/" + publication[4:]
        else:
            citation["url"] = "https://pubmed.ncbi.nlm.nih.gov/" + publication[7:] + "/"
        with backend.capture(
            "sabueso.extract_literature_mentions", context=context
        ) as capture:
            with backend.scope("sabueso.extract_literature_mentions"):
                backend.register_item(**trace["producer"])
                backend.register_item(**citation)
                backend.register_item(
                    id=resource, type="dataset", title="Supplied literature fragment"
                )
                backend.track_item(
                    trace["producer"]["id"],
                    roles=["executed_software"],
                    context=context,
                )
                backend.track_item(
                    citation["id"],
                    roles=["source_publication"],
                    context=context,
                )
                backend.track_item(
                    resource, roles=["extraction_input"], context=context
                )
        return {
            "status": "available",
            "version": backend.__version__,
            "attribution": capture.attribution.to_dict(),
        }
    except Exception as error:
        reason = f"{type(error).__name__}: {error}"
        adapter._warning("literature extraction", reason)
        return {
            "status": "failed",
            "version": getattr(backend, "__version__", None),
            "reason": reason,
            "attribution": None,
        }
