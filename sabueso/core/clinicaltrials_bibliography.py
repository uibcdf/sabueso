"""Native registry records and declared references, never citation-string parsed."""

from copy import deepcopy
from urllib.parse import urlsplit

from .snapshot import canonical_json, digest


def _url(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def citations(entries, *, references_requested):
    items, registry_ids, occurrences, gaps = {}, set(), [], []
    for entry in entries:
        if entry["outcome"] != "received":
            continue
        native = entry["study"]["protocolSection"]
        location = {
            key: deepcopy(entry[key])
            for key in ("page_index", "record_index", "nct_id", "response_identity")
        }
        identifier = "sabueso:clinicaltrials-registry-record:" + digest(
            canonical_json(entry["study"])
        )
        item = {
            "id": identifier,
            "type": "dataset",
            "url": "https://clinicaltrials.gov/study/" + entry["nct_id"],
        }
        title = native["identificationModule"].get("briefTitle")
        if isinstance(title, str) and title:
            item["title"] = title
        items[identifier] = item
        registry_ids.add(identifier)
        gaps.append(
            {
                "citation_id": identifier,
                "reason": "registry_citation_metadata_not_stated",
                "fields": [
                    key for key in ("title", "authors", "year") if key not in item
                ],
            }
        )
        if "referencesModule" not in native:
            gaps.append(
                {
                    **location,
                    "reason": "registry_references_not_stated"
                    if references_requested
                    else "registry_references_not_requested",
                }
            )
            continue
        module = native["referencesModule"]
        if not isinstance(module, dict):
            gaps.append({**location, "reason": "registry_references_module_malformed"})
            continue

        def pointer(reference, relation, position, *, parent_position=None):
            occurrence = {
                **location,
                "relation": relation,
                "reference_position": position,
                "native_reference": deepcopy(reference),
            }
            if parent_position is not None:
                occurrence["parent_reference_position"] = parent_position
            if not isinstance(reference, dict):
                gaps.append({**occurrence, "reason": "registry_reference_malformed"})
                return
            citation_id = "sabueso:clinicaltrials-cited-reference:" + digest(
                canonical_json({"relation": relation, "reference": reference})
            )
            citation = {
                "id": citation_id,
                "type": "article"
                if relation in {"references", "retractions"}
                else "dataset"
                if relation == "availIpds"
                else "web",
                "note": "Reference declared by ClinicalTrials.gov; target not consulted by this operation. Native reference: "
                + canonical_json(reference),
            }
            pmid = reference.get("pmid")
            if isinstance(pmid, str) and pmid.isdecimal() and int(pmid) > 0:
                citation["url"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            elif pmid is not None:
                gaps.append(
                    {**occurrence, "reason": "registry_reference_pmid_unusable"}
                )
            if relation in {"seeAlsoLinks", "availIpds"}:
                if _url(reference.get("url")):
                    citation["url"] = reference["url"]
                else:
                    gaps.append(
                        {**occurrence, "reason": "registry_reference_url_unusable"}
                    )
                if isinstance(reference.get("label"), str) and reference["label"]:
                    citation["title"] = reference["label"]
            text = reference.get("citation")
            if "url" not in citation and not (isinstance(text, str) and text):
                gaps.append(
                    {**occurrence, "reason": "registry_reference_pointer_unusable"}
                )
                return
            if citation_id not in items:
                items[citation_id] = citation
                gaps.append(
                    {
                        "citation_id": citation_id,
                        "reason": "registry_reference_structured_metadata_not_projected",
                        "fields": [
                            key
                            for key in ("title", "authors", "year")
                            if key not in citation
                        ],
                    }
                )
            occurrences.append({**occurrence, "citation_id": citation_id})

        for relation in ("references", "seeAlsoLinks", "availIpds"):
            values = module.get(relation, [])
            if not isinstance(values, list):
                gaps.append(
                    {
                        **location,
                        "relation": relation,
                        "reason": "registry_reference_list_malformed",
                    }
                )
                continue
            for position, reference in enumerate(values):
                pointer(reference, relation, position)
                if (
                    relation == "references"
                    and isinstance(reference, dict)
                    and "retractions" in reference
                ):
                    retractions = reference["retractions"]
                    if not isinstance(retractions, list):
                        gaps.append(
                            {
                                **location,
                                "reference_position": position,
                                "reason": "registry_retractions_malformed",
                            }
                        )
                        continue
                    for index, retraction in enumerate(retractions):
                        pointer(
                            retraction, "retractions", index, parent_position=position
                        )
    if references_requested:
        gaps.append("registry_reference_targets_not_queried")
    return list(items.values()), registry_ids, occurrences, gaps
