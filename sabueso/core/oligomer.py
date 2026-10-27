"""Source-bound quaternary interpretation, preserving original @1/@2 readers (#165).

Current rules preserve every declaration and interface/family pair. Canonical
positions are compared only after admission; unknown scope is never a negative.
No coordinates, assembly projection or biological relevance are inferred.
"""

import math
import re
from copy import deepcopy

from . import ligand_site_scope as coordinate
from ._oligomer_legacy_v2 import LEGACY_AGREEMENT_RULE
from .errors import ArgumentError
from .relationship_store import make_derivation
from .structures import coverage_class

PARTNER_RULE = "interface_partner_class@2"
AGREEMENT_RULE = "interface_site_agreement@3"
PREVIOUS_AGREEMENT_RULE = "interface_site_agreement@2"
SCOPE_RULE = "interface_coordinate_scope@1"
DECLARATION_RULE = "quaternary_declaration_scope@1"
FAMILY = "features_positional.family_site"
REFERENCE_FIELDS = ("identifiers.uniprot", "sequence.primary", "sequence.length")
INTERFACE_SITE = re.compile(r"\binterface\b", re.IGNORECASE)


def _refs(row):
    values = row.get("source_assertion_ids")
    return (
        list(dict.fromkeys(v for v in values if isinstance(v, str)))
        if isinstance(values, list)
        else []
    )


def declaration_scope(card, row, subject):
    """Bind a retained mapping declaration to its subject and source references."""
    reason = None
    refs = _refs(row)
    if subject is None or row.get("subject_ref") != subject:
        reason = "declaration_subject_not_focal"
    elif not isinstance(row.get("qualifiers"), dict):
        reason = "unrecognized_qualifiers"
    elif not isinstance(row.get("object_ref"), str) or not row["object_ref"]:
        reason = "object_reference_unavailable"
    elif (
        not refs
        or not isinstance(row.get("source_assertion_ids"), list)
        or any(
            not isinstance(ref, str) or not ref for ref in row["source_assertion_ids"]
        )
    ):
        reason = "source_references_unavailable_or_invalid"
    else:
        for ref in refs:
            source = card.source_assertion_store.get(ref)
            raw = source.get("asserted_value") if source else None
            structure_subject = (
                row.get("predicate") == "has_structure"
                and isinstance(raw, dict)
                and raw.get("subject_ref") == subject
                and raw.get("object_ref") == row.get("object_ref")
                and source.get("subject_ref") == row.get("object_ref")
                and isinstance(source.get("source"), dict)
                and source["source"].get("name") == "RCSB PDB"
                and source["source"].get("record_id")
                == str(row.get("object_ref")).removeprefix("pdb:")
            )
            if (
                not source
                or not (source.get("subject_ref") == subject or structure_subject)
                or source.get("field_path") != "relationships." + row["predicate"]
            ):
                reason = "source_support_missing_or_foreign"
                break
            provider = source.get("source")
            if not isinstance(provider, dict) or any(
                not isinstance(provider.get(key), str) or not provider[key]
                for key in ("name", "record_id")
            ):
                reason = "source_identity_unavailable"
                break
            if (
                isinstance(raw, dict)
                and "qualifiers" in raw
                and not coordinate.equal(raw["qualifiers"], row["qualifiers"])
            ):
                reason = "source_qualifier_binding_differs"
                break
            if not isinstance(raw, dict) or raw.get("object_ref") != row["object_ref"]:
                reason = "source_object_reference_differs"
                break
            if row["predicate"] == "has_interface_with" and "partner" in raw:
                partner = raw["partner"]
                if (
                    not isinstance(partner, dict)
                    or "uniprot:" + str(partner.get("accession")) != row["object_ref"]
                ):
                    reason = "interface_native_partner_binding_unavailable"
                    break
                native = partner.get("residues") if isinstance(partner, dict) else None
                if not isinstance(native, list):
                    reason = "interface_native_structure_scope_unavailable"
                    break
                entries = []
                for residue in native:
                    if not isinstance(residue, dict) or not isinstance(
                        residue.get("interactingPDBEntries", []), list
                    ):
                        reason = "interface_native_structure_scope_unavailable"
                        break
                    entries.extend(residue.get("interactingPDBEntries", []))
                if reason is not None:
                    break
                if any(
                    not isinstance(entry, dict)
                    or not isinstance(entry.get("pdbId"), str)
                    or not entry["pdbId"]
                    for entry in entries
                ):
                    reason = "interface_native_structure_scope_unavailable"
                    break
                expected = sorted(
                    {"pdb:" + entry["pdbId"].upper() for entry in entries}
                )
                if not coordinate.equal(expected, row["qualifiers"].get("structures")):
                    reason = "interface_native_structure_references_differ"
                    break
    return {
        "rule": DECLARATION_RULE,
        "status": "comparable" if reason is None else "not_computed",
        "reason": reason,
        "relationship_id": row["id"],
        "source_assertion_ids": refs,
        "basis": "captured_relationship_mapping_and_referenced_source_records",
        "qualifier_lineage": "unrecorded_mapping_lineage_is_not_reconstructed",
    }


def interface_scope(card, canonical, row):
    """Validate all mapped and original interface coordinate inputs."""
    scope = {
        "rule": SCOPE_RULE,
        "status": "not_computed",
        "reason": None,
        "relationship_id": row["id"],
        "sequence_ref": canonical["sequence_ref"],
        "positions": None,
        "source_assertion_ids": _refs(row),
        "sequence_revision_agreement": "not_established",
    }

    def stop(reason):
        return {**scope, "reason": reason}

    if canonical["status"] != "comparable":
        return stop(canonical["reason"])
    declared = declaration_scope(card, row, canonical["sequence_ref"])
    if declared["status"] != "comparable":
        return stop(declared["reason"])
    q = row["qualifiers"]
    conflicts = row.get("qualifier_conflicts")
    if conflicts is not None and not isinstance(conflicts, dict):
        return stop("unrecognized_qualifier_conflicts")
    if any(
        (conflicts or {}).get(key)
        for key in (
            "numbering",
            "indexing",
            "sequence_ref",
            "sequence_id",
            "residues",
            "sequence_version",
        )
    ):
        return stop("conflicting_interface_coordinates")
    if q.get("numbering") != "uniprot" or q.get("indexing", "1-based") != "1-based":
        return stop("interface_numbering_not_comparable")
    subject = canonical["sequence_ref"]
    if any(
        key in q and q[key] not in (subject, "UniProt:" + subject.split(":", 1)[1])
        for key in ("sequence_ref", "sequence_id")
    ):
        return stop("interface_axis_not_canonical")
    if any(key in q for key in ("location", "fragments")):
        return stop("interface_coordinate_shape_unsupported")
    residues = q.get("residues")
    if not isinstance(residues, list) or any(
        not isinstance(r, dict)
        or set(r)
        - {"start", "end", "start_modifier", "end_modifier", "residue", "observed_in"}
        for r in residues
    ):
        return stop("interface_positions_unstated_or_invalid")
    spans = [
        {k: r[k] for k in ("start", "end", "start_modifier", "end_modifier") if k in r}
        for r in residues
    ]
    positions = coordinate._spans(spans, canonical["length"])
    if positions is None:
        return stop("interface_positions_unstated_or_invalid")
    if "sequence_version" in q:
        version = q["sequence_version"]
        if type(version) is not int or version < 1:
            return stop("interface_sequence_version_invalid")
        if canonical["sequence_versions"] and canonical["sequence_versions"] != [
            version
        ]:
            return stop("interface_sequence_version_differs")
        if (
            canonical["sequence_versions"] == [version]
            and not canonical["unstated_sequence_version_ids"]
        ):
            scope["sequence_revision_agreement"] = "matching_stated_versions"
    for ref in scope["source_assertion_ids"]:
        source = card.source_assertion_store.get(ref)
        raw = source.get("asserted_value")
        if (
            isinstance(raw, dict)
            and raw.get("object_ref") == row["object_ref"]
            and coordinate.equal(raw.get("qualifiers"), q)
        ):
            continue
        provider = source["source"]
        if (
            provider["name"] != "PDBe-KB"
            or provider["record_id"] != subject.split(":", 1)[1]
            or not isinstance(raw, dict)
            or raw.get("object_ref") != row["object_ref"]
        ):
            return stop("interface_native_binding_unavailable")
        partner = raw.get("partner")
        if (
            not isinstance(partner, dict)
            or "uniprot:" + str(partner.get("accession")) != row["object_ref"]
        ):
            return stop("interface_native_partner_binding_unavailable")
        native = partner.get("residues")
        if (
            not isinstance(native, list)
            or not native
            or any(
                not isinstance(r, dict)
                or not isinstance(r.get("indexType"), str)
                or r["indexType"].upper() != "UNIPROT"
                or type(r.get("startIndex")) is not int
                or type(r.get("endIndex")) is not int
                for r in native
            )
        ):
            return stop("interface_native_endpoints_not_stated_exactly")
        expected = [{"start": r["startIndex"], "end": r["endIndex"]} for r in native]
        if coordinate._spans(expected, canonical["length"]) != positions:
            return stop("interface_native_positions_differ")
    return {**scope, "status": "comparable", "positions": positions}


def _structure_basis(card, row, subject, partner):
    declared = declaration_scope(card, row, subject)
    q = row.get("qualifiers") or {}
    reason = declared["reason"]
    basis = "undetermined"
    conflicts = row.get("qualifier_conflicts")
    if reason is None:
        if (
            conflicts is not None
            and not isinstance(conflicts, dict)
            or (conflicts or {}).get("chimeric_with")
        ):
            reason = "conflicting_or_unrecognized_structure_context"
        elif (
            "chimeric_with" not in q
            or not isinstance(q["chimeric_with"], list)
            or any(not isinstance(v, str) for v in q["chimeric_with"])
        ):
            reason = "entity_mapping_not_retrieved_or_invalid"
        elif partner in q["chimeric_with"]:
            basis = "chimera_with_partner"
        elif (conflicts or {}).get("coverage"):
            reason = "conflicting_structure_coverage"
        else:
            coverage = q.get("coverage")
            if (
                type(coverage) not in (int, float)
                or not math.isfinite(coverage)
                or not 0 <= coverage <= 1
            ):
                reason = "structure_coverage_unavailable_or_invalid"
            else:
                basis = (
                    "protein_as_fragment"
                    if coverage_class(coverage) == "fragment_or_peptide"
                    else "complex_with_partner"
                )
    return {
        "relationship_id": row["id"],
        "basis": basis,
        "reason": reason,
        "scope": declared,
        "qualifiers": deepcopy(q),
        "qualifier_conflicts": deepcopy(conflicts),
    }


def _partner_class(card, row, subject, canonical, structures):
    declared = declaration_scope(card, row, subject)
    result = {
        "rule": PARTNER_RULE,
        "status": "not_computed",
        "reason": None,
        "basis": {},
        "declaration_scope": declared,
        "identity_basis": "source_declared_references_only",
        "class": "undetermined",
    }
    if canonical["status"] != "comparable":
        return {**result, "reason": canonical["reason"]}
    if declared["status"] != "comparable":
        return {**result, "reason": declared["reason"]}
    partner = row["object_ref"]
    if not partner.startswith("uniprot:") or not partner.split(":", 1)[1]:
        return {**result, "reason": "partner_protein_reference_unavailable"}
    q = row["qualifiers"]
    refs = q.get("structures")
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
        refs = []
    for ref in dict.fromkeys(refs):
        declarations = [
            s
            for s in structures
            if s["object_ref"] == ref and s["subject_ref"] == subject
        ]
        records = [
            _structure_basis(card, s, subject, partner.split(":", 1)[1])
            for s in declarations
        ]
        if not records:
            records = [
                {
                    "relationship_id": None,
                    "basis": "undetermined",
                    "reason": "structure_not_on_card",
                }
            ]
        result["basis"][ref] = records
    if partner == subject:
        return {
            **result,
            "status": "computed",
            "class": "homomeric",
            "identity_basis": "source_declared_self_interface",
        }
    conflicts = row.get("qualifier_conflicts")
    if (
        conflicts is not None
        and not isinstance(conflicts, dict)
        or (conflicts or {}).get("structures")
    ):
        return {**result, "reason": "conflicting_or_unrecognized_interface_structures"}
    bases = []
    for records in result["basis"].values():
        kinds = {r["basis"] for r in records}
        bases.append(next(iter(kinds)) if len(kinds) == 1 else "undetermined")
    if "complex_with_partner" in bases:
        return {
            **result,
            "status": "partial" if "undetermined" in bases else "computed",
            "class": "heteromeric",
        }
    if not bases or "undetermined" in bases:
        return {**result, "reason": "structure_context_unavailable_or_conflicting"}
    kinds = set(bases)
    value = (
        "chimera"
        if kinds == {"chimera_with_partner"}
        else "fragment_complex"
        if kinds == {"protein_as_fragment"}
        else "chimera_or_fragment"
    )
    return {**result, "status": "computed", "class": value}


def oligomer_derivations(agreement_rule=AGREEMENT_RULE):
    if agreement_rule in (LEGACY_AGREEMENT_RULE, PREVIOUS_AGREEMENT_RULE):
        from ._oligomer_legacy_v2 import oligomer_derivations as legacy

        return legacy(agreement_rule)
    if agreement_rule != AGREEMENT_RULE:
        raise ArgumentError("Unsupported interface agreement rule.")
    return [
        make_derivation(
            PARTNER_RULE,
            parameters={
                "basis": "all source-bound structure declarations",
                "missing_or_conflicting": "uncomputed",
                "identity": "exact source-declared references",
            },
        ),
        make_derivation(
            AGREEMENT_RULE,
            parameters={
                "pairs": "every focal self-interface and source family-interface annotation",
                "coordinate_scope": SCOPE_RULE,
                "revision_agreement": "only when explicitly stated",
            },
        ),
        make_derivation(SCOPE_RULE),
        make_derivation(DECLARATION_RULE),
    ]


def oligomer_view(card, agreement_rule=AGREEMENT_RULE):
    if agreement_rule in (LEGACY_AGREEMENT_RULE, PREVIOUS_AGREEMENT_RULE):
        from ._oligomer_legacy_v2 import oligomer_view as legacy

        return legacy(card, agreement_rule)
    rules = oligomer_derivations(agreement_rule)
    canonical = coordinate.reference(card)
    subject = canonical["sequence_ref"]
    structures = card.relationships("has_structure")
    assemblies, without, excluded = [], [], []
    for row in structures:
        if subject is None or row["subject_ref"] != subject:
            excluded.append(
                {"relationship_id": row["id"], "reason": "structure_subject_not_focal"}
            )
            continue
        q = row.get("qualifiers")
        stated = q.get("assemblies") if isinstance(q, dict) else None
        assemblies.append(
            {
                "structure_ref": row["object_ref"],
                "relationship_id": row["id"],
                "assemblies": deepcopy(stated),
                "scope": declaration_scope(card, row, subject),
                "qualifier_conflicts": deepcopy(row.get("qualifier_conflicts")),
                "declaration_state": "not_stated"
                if stated is None
                else "stated_empty"
                if stated == []
                else "stated"
                if isinstance(stated, list)
                else "unrecognized_shape",
            }
        )
        if stated is None:
            without.append(row["object_ref"])
    interfaces = []
    for row in card.relationships("has_interface_with"):
        q = row.get("qualifiers") if isinstance(row.get("qualifiers"), dict) else {}
        classification = _partner_class(card, row, subject, canonical, structures)
        scope = interface_scope(card, canonical, row)
        interfaces.append(
            {
                "partner_ref": row["object_ref"],
                "partner_name": q.get("partner_name"),
                "partner_type": q.get("partner_type"),
                "class": classification["class"],
                "basis": classification["basis"],
                "classification": classification,
                "positions": scope["positions"],
                "coordinate_scope": scope,
                "structures": deepcopy(q.get("structures")),
                "relationship_id": row["id"],
                "source_assertion_ids": _refs(row),
                "sources": sorted(
                    {
                        source["source"]["name"]
                        for ref in _refs(row)
                        if (source := card.source_assertion_store.get(ref))
                        and isinstance(source.get("source"), dict)
                        and isinstance(source["source"].get("name"), str)
                    }
                ),
                "qualifier_conflicts": deepcopy(row.get("qualifier_conflicts")),
            }
        )
    family = []
    node = card.get(FAMILY)
    values = node.get("value") if isinstance(node, dict) else None
    if isinstance(values, list):
        for index, value in enumerate(values):
            if (
                not isinstance(value, dict)
                or not isinstance(value.get("description"), str)
                or not INTERFACE_SITE.search(value["description"])
            ):
                continue
            sources, problems = coordinate.matching(card, node, FAMILY, value, subject)
            scope = coordinate.annotation(
                card, canonical, "family_site", FAMILY, index, value, sources, problems
            )
            family.append(
                {
                    "kind": "family_site",
                    "description": value["description"],
                    "signature": deepcopy(value.get("signature")),
                    "positions": scope["positions"],
                    "scope": scope,
                    "index": index,
                    "value": deepcopy(value),
                    "source_assertion_ids": [s["id"] for s in sources],
                }
            )
    agreement = []
    for interface in interfaces:
        row = card.relationship_store.get(interface["relationship_id"])
        if (
            subject is None
            or row["subject_ref"] != subject
            or interface["partner_ref"] != subject
        ):
            continue
        for site in family:
            left, right = interface["coordinate_scope"], site["scope"]
            comparable = left["status"] == right["status"] == "comparable"
            a, b = set(left["positions"] or []), set(right["positions"] or [])
            agreement.append(
                {
                    "rule": AGREEMENT_RULE,
                    "interface_relationship_id": interface["relationship_id"],
                    "relationship_id": interface["relationship_id"],
                    "family_site_index": site["index"],
                    "family_site": site["description"],
                    "signature": deepcopy(site["signature"]),
                    "both": sorted(a & b) if comparable else None,
                    "family_only": sorted(b - a) if comparable else None,
                    "observed_only": sorted(a - b) if comparable else None,
                    "comparison": {
                        "rule": SCOPE_RULE,
                        "status": "comparable" if comparable else "not_computed",
                        "reasons": [
                            s["reason"] for s in (left, right) if s.get("reason")
                        ],
                        "interface_scope": deepcopy(left),
                        "family_scope": deepcopy(right),
                    },
                    "source_assertion_ids": sorted(
                        set(interface["source_assertion_ids"])
                        | set(site["source_assertion_ids"])
                        | set(canonical["inputs"])
                    ),
                }
            )
    subunit = []
    node = card.get("annotations.subunit")
    if isinstance(node, dict) and isinstance(node.get("value"), list):
        for index, value in enumerate(node["value"]):
            sources, problems = coordinate.matching(
                card, node, "annotations.subunit", value, subject
            )
            subunit.append(
                {
                    "text": deepcopy(value),
                    "index": index,
                    "source_assertion_ids": [s["id"] for s in sources],
                    "support_problems": problems,
                    "support_state": "retained"
                    if sources and not problems
                    else "unconfirmed",
                }
            )
    computed = sum(row["comparison"]["status"] == "comparable" for row in agreement)
    reasons = []
    if canonical["status"] != "comparable":
        reasons.append(canonical["reason"])
    if not agreement:
        reasons.append("no_focal_self_interface_family_pairs")
    if agreement and not computed:
        reasons.append("no_comparable_interface_sites_on_card")
    return {
        "subunit": subunit,
        "assemblies": assemblies,
        "without_assembly_data": without,
        "excluded_structure_relationships": excluded,
        "interfaces": interfaces,
        "family_interface_sites": family,
        "agreement": agreement,
        "agreement_state": {
            "status": "computed"
            if agreement and computed == len(agreement)
            else "partial"
            if computed
            else "not_computed",
            "computed_pair_count": computed,
            "pair_count": len(agreement),
            "reasons": reasons,
        },
        "canonical_reference": canonical,
        "rules": rules,
        "scope": "Source-bound reference labels and all original declarations; aggregate interfaces are not physical assembly occurrences. No assembly projection, geometry, affinity or biological relevance is inferred. Unknown coordinate scope is not a negative comparison.",
    }
