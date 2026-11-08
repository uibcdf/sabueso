"""Source-stated disease associations in explicit captured input scope."""

from copy import deepcopy
from dataclasses import dataclass

from .card_access import _Entry, _handle
from .card_disease_association_selection_v1 import (
    COLUMNS,
    DEFAULT_FIELDS,
    FORMAT,
    item_ref,
)
from .errors import ArgumentError
from .relationship_store import make_derivation
from .snapshot import canonical_json
from .source_assertion_store import assertion_value

TOPIC = "associations"
ADAPTER = "disease_association_exploration@1"
RULE = "disease_association_context@1"
SUPPORT_FORMAT = "disease_association_support@1"
SCOPE = (
    "Original disease association, indication and variant-condition occurrences "
    "in explicitly captured Cards. Exact identifiers and source-stated equivalences "
    "only; no name, synonym, related-xref or hierarchy identity joins, acquisition, "
    "score ranking, causality, target validity or efficacy inference."
)


def descriptor():
    return {
        "key": TOPIC,
        "label": "Retained molecular and clinical associations",
        "description": SCOPE,
        "adapter": ADAPTER,
        "scientific_adapter": True,
        "operations": ["select", "explain", "read", "page"],
        "columns": {key: {"type": "string|null"} for key in COLUMNS},
        "default_fields": list(DEFAULT_FIELDS),
        "options": {},
        "projection": True,
        "machine_filter": True,
        "machine_order": True,
        "machine_membership": True,
        "selection_policy": FORMAT,
        "mandatory_interpretation": [
            "rule",
            "scope",
            "row_grain",
            "identity_basis",
            "support_state",
            "direction_scope",
        ],
        "source_support": {"format": SUPPORT_FORMAT},
        "save": False,
        "save_reason": "Independent original disease association saved reading is not implemented.",
    }


def options_for_associations(options):
    if options is not None and (not isinstance(options, dict) or options):
        raise ArgumentError(
            "associations has no scientific options; supply related Cards explicitly."
        )
    return {}


def _norm(value):
    from sabueso.tools.db.mondo import normalize

    return normalize(value) if isinstance(value, str) else None


def _anchor(capture):
    identifier = capture.data["meta"].get("card_id")
    return (
        identifier.split(":", 2)[2]
        if isinstance(identifier, str) and identifier.startswith("sabueso:")
        else None
    )


def _location(access, capture, store=None, key=None, *, path=None):
    owner = access._captures[capture]
    segments = []
    if store is not None:
        segments = [{"type": "Key", "value": store}, {"type": "Record", "value": key}]
    elif path is not None:
        segments = [
            {"type": "Key", "value": part} for part in ("sections", *path.split("."))
        ]
    return {
        "format": "card_access_location@1",
        "kind": "card",
        "card_ref": owner.pin,
        "snapshot_id": owner.snapshot,
        "segments": segments,
    }


def _field(access, capture, path):
    node = access._captures[capture].data.get("sections", {})
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def _sources(access, capture, ids, subject, field, role, *, source=None, accepts=None):
    stored = {
        row["id"]: row
        for row in access._captures[capture].data["source_assertion_store"]
    }
    result = []
    for identifier in ids:
        record = stored.get(identifier)
        valid = bool(
            record is not None
            and record.get("subject_ref") == subject
            and record.get("field_path") == field
            and (source is None or record.get("source", {}).get("name") == source)
            and (accepts is None or accepts(assertion_value(record)))
        )
        result.append(
            {
                "id": identifier,
                "capture": capture,
                "role": role,
                "state": "present"
                if valid
                else "not_retained"
                if record is None
                else "role_mismatch",
                "expected_subject_ref": subject,
                "expected_field_path": field,
                "expected_source": source,
                "location": _location(
                    access, capture, "source_assertion_store", identifier
                )
                if record is not None
                else None,
            }
        )
    return result


def _valid(records):
    return bool(records) and all(row["state"] == "present" for row in records)


def _member_sources(access, capture, node, subject, field, source, member):
    stored = {
        r["id"]: r for r in access._captures[capture].data["source_assertion_store"]
    }
    selected = node.get("source_assertion_ids", [])
    # Other valid native members do not support this particular occurrence.
    # Missing or misbound selected IDs remain explicit uncertainties.
    ids = [
        identifier
        for identifier in selected
        if identifier not in stored
        or canonical_json(assertion_value(stored[identifier])) == canonical_json(member)
        or stored[identifier].get("subject_ref") != subject
        or stored[identifier].get("field_path") != field
        or stored[identifier].get("source", {}).get("name") != source
    ]
    return _sources(
        access,
        capture,
        ids or selected,
        subject,
        field,
        "association_statement",
        source=source,
        accepts=lambda value: canonical_json(value) == canonical_json(member),
    )


def _identity(access):
    claims, invalid = {}, []
    for key, captured in sorted(access._captures.items()):
        anchor = _norm(_anchor(captured))
        if captured.data["meta"].get("entity_type") == "disease" and anchor:
            claims.setdefault(anchor, []).append(
                {
                    "term": anchor,
                    "capture": key,
                    "basis": "exact_card_anchor",
                    "source_assertions": [],
                }
            )
            node = _field(access, key, "identifiers.equivalent_ids")
            refs = node.get("value") if isinstance(node, dict) else None
            for ref in refs if isinstance(refs, list) else []:
                curie = _norm(ref)
                support = _sources(
                    access,
                    key,
                    node.get("source_assertion_ids", []),
                    _anchor(captured),
                    "identifiers.equivalent_ids",
                    "disease_equivalence",
                    source="MONDO",
                    accepts=lambda value, curie=curie: (
                        isinstance(value, list) and curie in [_norm(v) for v in value]
                    ),
                )
                record = {
                    "term": anchor,
                    "capture": key,
                    "identifier": ref,
                    "basis": "source_stated_equivalence",
                    "source_assertions": support,
                }
                if curie and _valid(support):
                    claims.setdefault(curie, []).append(record)
                else:
                    invalid.append(record)
        # A supported conflicting MONDO mapping in another input is consequential,
        # even when that input is a protein rather than a second disease Card.
        for rel in captured.data["relationship_store"]:
            if (
                rel.get("predicate") != "same_as"
                or (rel.get("qualifiers") or {}).get("source") != "MONDO"
            ):
                continue
            curie, term = _norm(rel["subject_ref"]), _norm(rel["object_ref"])
            support = _sources(
                access,
                key,
                rel.get("source_assertion_ids", []),
                rel["subject_ref"],
                "relationships.same_as",
                "disease_equivalence",
                source="MONDO",
                accepts=lambda value, curie=curie, term=term: (
                    isinstance(value, dict)
                    and _norm(value.get("equivalent_id")) == curie
                    and _norm(value.get("mondo")) == term
                ),
            )
            record = {
                "term": term,
                "capture": key,
                "basis": "source_stated_equivalence",
                "relationship_location": _location(
                    access, key, "relationship_store", rel["id"]
                ),
                "source_assertions": support,
            }
            if (
                curie
                and term
                and not rel.get("qualifier_conflicts")
                and _valid(support)
            ):
                claims.setdefault(curie, []).append(record)
            else:
                invalid.append(record)
    # Only the established MedGen concept/UID/MONDO contract may add a second
    # hop. Freeze direct claims here so newly derived paths cannot form a closure.
    direct, incomplete = deepcopy(claims), {}
    for key, capture in sorted(access._captures.items()):
        for rel in capture.data["relationship_store"]:
            if (
                rel["predicate"] != "same_as"
                or (rel.get("qualifiers") or {}).get("source") != "MedGen"
            ):
                continue
            curie, uid = _norm(rel["subject_ref"]), _norm(rel["object_ref"])
            support = _sources(
                access,
                key,
                rel.get("source_assertion_ids", []),
                rel["subject_ref"],
                "relationships.same_as",
                "medgen_identity",
                source="MedGen",
                accepts=lambda value, curie=curie, uid=uid: (
                    isinstance(value, dict)
                    and _norm("MEDGEN:" + str(value.get("concept_id"))) == curie
                    and _norm("MEDGEN:" + str(value.get("uid"))) == uid
                ),
            )
            location = _location(access, key, "relationship_store", rel["id"])
            path = {
                "capture": key,
                "basis": "medgen_mondo_equivalence",
                "via": uid,
                "relationship_location": location,
                "source_assertions": support,
            }
            targets = direct.get(uid, []) if uid and uid.startswith("MEDGEN:") else []
            if (
                not curie
                or not curie.startswith("MEDGEN:")
                or not _valid(support)
                or rel.get("qualifier_conflicts")
                or not targets
            ):
                incomplete.setdefault(curie or rel["subject_ref"], []).append(
                    {**path, "reason": "incomplete_or_unverified_medgen_path"}
                )
                continue
            for target in targets:
                claims.setdefault(curie, []).append(
                    {
                        **path,
                        "term": target["term"],
                        "source_assertions": [
                            *support,
                            *deepcopy(target["source_assertions"]),
                        ],
                        "terminal_identity": deepcopy(target),
                        "rules": ["medgen_concept@1", "mondo_equivalence@1"],
                    }
                )
    focal = _norm(_anchor(access._focal))
    primary = _field(access, access._focal_key, "identifiers.mondo")
    coherent = bool(
        focal
        and focal.startswith("MONDO:")
        and (
            primary is None
            or isinstance(primary, dict)
            and (primary.get("value") is None or _norm(primary["value"]) == focal)
        )
    )
    return {
        "focal": focal,
        "coherent": coherent,
        "claims": claims,
        "unverified_claims": invalid,
        "incomplete_identifiers": incomplete,
        "scope": "Exact focal anchor, supported MONDO equivalences and the explicit MedGen concept/UID/MONDO contract; no name, hierarchy or general transitive closure.",
    }


def _match(refs, identity):
    from .diseases import CLINVAR_PLACEHOLDERS

    if any(_norm(ref) in CLINVAR_PLACEHOLDERS for ref in refs):
        return {
            "state": "condition_not_provided",
            "basis": None,
            "original_refs": deepcopy(refs),
            "reached_terms": [],
            "paths": [],
            "unmapped_refs": deepcopy(refs),
        }
    terms, paths, unresolved = set(), [], []
    for ref in refs:
        blocked = identity["incomplete_identifiers"].get(_norm(ref), [])
        if blocked:
            unresolved.extend(deepcopy(blocked))
            continue
        for path in identity["claims"].get(_norm(ref), []):
            terms.add(path["term"])
            paths.append({"original_ref": ref, **deepcopy(path)})
    matched = identity["coherent"] and terms == {identity["focal"]}
    return {
        "state": "matched"
        if matched
        else "conflicting_identity"
        if len(terms) > 1
        else "incomplete_identity"
        if unresolved
        else "not_matched",
        "basis": "exact_identifier"
        if matched and any(_norm(ref) == identity["focal"] for ref in refs)
        else "medgen_mondo_equivalence"
        if matched
        and any(path["basis"] == "medgen_mondo_equivalence" for path in paths)
        else "source_stated_equivalence"
        if matched
        else None,
        "original_refs": deepcopy(refs),
        "reached_terms": sorted(terms),
        "paths": paths,
        "unresolved_identity_paths": unresolved,
        "unmapped_refs": [
            ref for ref in refs if not identity["claims"].get(_norm(ref))
        ],
    }


def _own_refs(access, key):
    capture = access._captures[key]
    anchor = _anchor(capture)
    refs = {anchor} if anchor else set()
    support = []
    if capture.data["meta"].get("entity_type") == "small_molecule":
        for rel in capture.data["relationship_store"]:
            if (
                rel["predicate"] != "same_as"
                or rel["object_ref"] != anchor
                or rel.get("qualifier_conflicts")
            ):
                continue
            records = _sources(
                access,
                key,
                rel.get("source_assertion_ids", []),
                rel["subject_ref"],
                "relationships.same_as",
                "molecule_identity",
                accepts=lambda value: (
                    isinstance(value, dict) and value.get("object_ref") == anchor
                ),
            )
            if _valid(records):
                # Conflicting supplied anchors never become one molecule.
                others = {
                    r["object_ref"]
                    for c in access._captures.values()
                    for r in c.data["relationship_store"]
                    if r["predicate"] == "same_as"
                    and r["subject_ref"] == rel["subject_ref"]
                }
                if others == {anchor}:
                    refs.add(rel["subject_ref"])
                    support.extend(records)
    return refs, support


def _endpoints_match(refs, identity):
    endpoints = [_match([ref], identity) for ref in refs]
    matched = [match for match in endpoints if match["state"] == "matched"]
    if not matched:
        return {
            "state": "conflicting_identity"
            if any(m["state"] == "conflicting_identity" for m in endpoints)
            else "not_matched",
            "basis": None,
            "paths": [],
            "endpoint_bindings": endpoints,
        }
    return {
        "state": "matched",
        "basis": matched[0]["basis"],
        "paths": [p for m in matched for p in m["paths"]],
        "endpoint_bindings": endpoints,
        "matching_endpoints": [
            index
            for index, match in enumerate(endpoints)
            if match["state"] == "matched"
        ],
        "scope": "Separate subject/object endpoints, never equivalent identifiers of one entity.",
    }


def _occurrences(access, key):
    from .diseases import disease_statements

    capture = access._captures[key]
    nature = capture.data["meta"].get("entity_type")
    anchor = _anchor(capture)
    for rel in capture.data["relationship_store"]:
        if rel["predicate"] not in ("associated_with", "investigated_for"):
            continue
        q = rel.get("qualifiers") or {}
        location = _location(access, key, "relationship_store", rel["id"])
        yield {
            "kind": "association_statement"
            if rel["predicate"] == "associated_with"
            else "indication_statement",
            "subject_ref": rel["subject_ref"],
            "predicate": rel["predicate"],
            "object_ref": rel["object_ref"],
            "refs": [rel["subject_ref"], rel["object_ref"]]
            if nature == "disease"
            else [rel["object_ref"]],
            "source": q.get("source")
            or ("ChEMBL" if rel["predicate"] == "investigated_for" else None),
            "channel": q.get("channel"),
            "item": deepcopy(rel),
            "location": location,
            "support": _sources(
                access,
                key,
                rel.get("source_assertion_ids", []),
                rel["subject_ref"],
                "relationships." + rel["predicate"],
                "association_statement",
                source=q.get("source")
                or ("ChEMBL" if rel["predicate"] == "investigated_for" else None),
            ),
            "conflicts": deepcopy(rel.get("qualifier_conflicts") or []),
            "relationship_location": location,
        }
    if nature != "protein":
        return
    for path, source, kind in (
        ("annotations.disease", "UniProt", "uniprot_disease_xref"),
        ("annotations.clinical_variants", "ClinVar", "variant_condition"),
    ):
        node = _field(access, key, path)
        values = node.get("value") if isinstance(node, dict) else None
        for index, member in enumerate(values if isinstance(values, list) else []):
            if not isinstance(member, dict):
                continue
            for ordinal, statement in enumerate(
                disease_statements(lambda p: [member] if p == path else None, [])
            ):
                location = _location(access, key, path=path)
                location["segments"] += [
                    {"type": "Key", "value": "value"},
                    {"type": "Index", "value": index},
                ]
                if kind == "variant_condition":
                    location["segments"] += [
                        {"type": "Key", "value": "conditions"},
                        {"type": "Index", "value": statement["condition"]},
                    ]
                yield {
                    "kind": kind,
                    "subject_ref": anchor,
                    "predicate": "disease_annotation"
                    if source == "UniProt"
                    else "variant_condition",
                    "object_ref": statement["refs"][0]
                    if len(statement["refs"]) == 1
                    else None,
                    "refs": statement["refs"],
                    "source": source,
                    "channel": None,
                    "item": access._resolve(location)[0],
                    "location": location,
                    "native_statement": statement,
                    "ordinal": ordinal,
                    "support": _member_sources(
                        access, key, node, anchor, path, source, member
                    ),
                    "conflicts": [],
                }


@dataclass(frozen=True)
class AssociationResult:
    result_ref: str
    wire: dict
    entries: tuple
    options: dict

    @property
    def native(self):
        return self.wire["native_payload"]

    @property
    def explanations(self):
        return self.wire["explanations"]

    def location(self, *keys):
        return {
            "format": "card_access_location@1",
            "kind": "result",
            "result_ref": self.result_ref,
            "segments": [{"type": "Key", "value": key} for key in keys],
        }

    def value(self, key, column):
        return self.wire["rows"][key][column]

    def cell_state(self, key, column):
        if column in self.wire["rows"][key].get("unrecognized_fields", {}):
            return "unrecognized_shape"
        return (
            "present"
            if self.value(key, column) is not None
            else "not_applicable"
            if self.value(key, "kind") == "association_context"
            else "unknown"
        )

    def cell_reason(self, key, column):
        state = self.cell_state(key, column)
        return (
            None
            if state == "present"
            else "The retained value has an unrecognized scalar shape; inspect the complete original item."
            if state == "unrecognized_shape"
            else "Not a source statement column for this context row."
            if state == "not_applicable"
            else "The original occurrence does not state a scalar value for this column; inspect the complete item."
        )

    def frame(self, access, selection, entry):
        row, support = self.wire["rows"][entry.key], self.wire["support"][entry.key]
        interpretation = access._location(
            self.location("rows", entry.key, "interpretation")
        )
        return {
            "adapter": ADAPTER,
            "item_ref": item_ref(self, entry),
            "kind": row["kind"],
            "label": row["label"],
            "subject_ref": row["subject_ref"],
            "location": access._location(entry.location),
            "payload_location": access._location(
                self.location("rows", entry.key, "item")
            ),
            "state": row["state"],
            "support_location": access._location(self.location("support", entry.key)),
            "support": {
                "format": SUPPORT_FORMAT,
                "ref": entry.key,
                "basis": support["basis"],
                "source_assertions": deepcopy(support["source_assertions"]),
            },
            "interpretation": deepcopy(row["interpretation"]),
            "interpretation_location": interpretation,
            "cells": {
                column: {
                    "value": deepcopy(self.value(entry.key, column)),
                    "state": self.cell_state(entry.key, column),
                    "reason": self.cell_reason(entry.key, column),
                    "field": {"adapter": ADAPTER, "column": column},
                    "support_basis": support["basis"],
                    "support_ref": entry.key,
                    "value_included": True,
                    "value_location": access._location(
                        self.location("rows", entry.key, column)
                    ),
                    "interpretation_location": interpretation,
                }
                for column in selection._fields
            },
            "value_included": True,
            "inspection_required": False,
        }


def materialize(access, options=None):
    options_for_associations(options)
    if access.mode != "live":
        raise ArgumentError(
            "Independent original disease association saved reading is not implemented."
        )
    if access.profile != "disease":
        raise ArgumentError("associations requires a disease Card.")
    cache = (ADAPTER, access._focal_key)
    if cache in access._scientific_cache:
        return access._scientific_cache[cache]
    from .card_scientific_access import _CapturedCard
    from .diseases import _card_statements

    identity, contexts, excluded, rows, supports = _identity(access), [], [], {}, {}
    matched_count = 0
    for position, (key, capture) in enumerate(sorted(access._captures.items())):
        nature = capture.data["meta"].get("entity_type", "generic")
        if nature not in ("disease", "protein", "small_molecule"):
            excluded.append(
                {
                    "capture": key,
                    "reason": "unsupported_context_nature",
                    "location": _location(access, key),
                }
            )
            continue
        card = _CapturedCard(capture)
        native = (
            _card_statements(card)
            if nature == "protein"
            else card.clinical()
            if nature == "small_molecule"
            else None
        )
        records = list(_occurrences(access, key))
        knowledge = card.knowledge_state()
        context = {
            "capture": key,
            "card_ref": capture.pin,
            "nature": nature,
            "native_payload": deepcopy(native),
            "knowledge_state": deepcopy(knowledge),
            "stored_occurrences": len(records),
            "matched_occurrences": 0,
        }
        contexts.append(context)
        refs, actor_support = _own_refs(access, key)
        for index, record in enumerate(records):
            match = (
                _endpoints_match(record["refs"], identity)
                if nature == "disease"
                else _match(record["refs"], identity)
            )
            reason = (
                "foreign_or_unverified_subject"
                if nature != "disease" and record["subject_ref"] not in refs
                else match["state"]
                if match["state"] != "matched"
                else None
            )
            if reason is not None:
                excluded.append(
                    {
                        "capture": key,
                        "reason": reason,
                        "original_location": record["location"],
                        "original_item": deepcopy(record["item"]),
                        "identity": match,
                    }
                )
                continue
            row_key = f"statement:{position}:{index}"
            source_records = [
                *record["support"],
                *actor_support,
                *(
                    r
                    for path in match["paths"]
                    if path["term"] == identity["focal"]
                    for r in path["source_assertions"]
                ),
            ]
            verified = (
                _valid(record["support"])
                and not record["conflicts"]
                and not match.get("unresolved_identity_paths")
            )
            support = {
                "format": SUPPORT_FORMAT,
                "basis": "retained_role_bound_source_membership"
                if verified
                else "support_membership_unverified",
                "state": "retained" if verified else "partial",
                "source_assertions": deepcopy(source_records),
                "original_location": record["location"],
                "context_capture": key,
                "relationship_locations": [record["relationship_location"]]
                if "relationship_location" in record
                else [],
                "identity": match,
                "qualifier_conflicts": record["conflicts"],
            }
            row = {
                **dict.fromkeys(COLUMNS),
                "label": f"{record['source'] or 'Source not stated'} · {record['predicate']} · {record['subject_ref']}",
                "kind": record["kind"],
                "context_card_ref": capture.pin,
                "context_nature": nature,
                "subject_ref": record["subject_ref"],
                "predicate": record["predicate"],
                "object_ref": record["object_ref"],
                "disease_ref": identity["focal"],
                "source": record["source"],
                "channel": record["channel"],
                "identity_basis": match["basis"],
                "support_state": support["state"],
                "state": support["state"],
                "item": deepcopy(record["item"]),
                "native_statement": deepcopy(record.get("native_statement")),
                "interpretation": {
                    "rule": RULE,
                    "scope": SCOPE,
                    "row_grain": record["kind"],
                    "identity_basis": match,
                    "support_state": support["state"],
                    "direction_scope": "Original subject/predicate/object or source annotation occurrence; no reverse causality or efficacy is inferred.",
                },
            }
            unrecognized = {
                name: deepcopy(row[name])
                for name in COLUMNS
                if row[name] is not None and not isinstance(row[name], str)
            }
            if unrecognized:
                row["unrecognized_fields"] = unrecognized
                row["interpretation"]["unrecognized_fields"] = deepcopy(unrecognized)
                for name in unrecognized:
                    row[name] = None
            rows[row_key], supports[row_key] = row, support
            context["matched_occurrences"] += 1
            matched_count += 1
        context_key = f"context:{position}"
        rows[context_key] = {
            **dict.fromkeys(COLUMNS),
            "label": f"Captured {nature} context · {capture.pin or capture.snapshot}",
            "kind": "association_context",
            "context_card_ref": capture.pin,
            "context_nature": nature,
            "disease_ref": identity["focal"],
            "state": "retained",
            "support_state": "context_only",
            "item": deepcopy(context),
            "interpretation": {
                "rule": RULE,
                "scope": SCOPE,
                "row_grain": "association_context",
                "identity_basis": "Not an association statement.",
                "support_state": "context_only",
                "direction_scope": "Native source/query context only; zero matches is not global absence.",
            },
        }
        supports[context_key] = {
            "format": SUPPORT_FORMAT,
            "basis": "captured_native_context",
            "state": "context_only",
            "source_assertions": [],
            "context_capture": key,
            "original_location": _location(access, key),
            "relationship_locations": [],
        }
    rule = make_derivation(RULE, sorted(access._captures), parameters={})
    native = {
        "rule": rule,
        "identity": identity,
        "focal_term": {
            "name_field": deepcopy(
                _field(access, access._focal_key, "names.canonical_name")
            ),
            "name_location": _location(
                access, access._focal_key, path="names.canonical_name"
            ),
            "term_status_field": deepcopy(
                _field(access, access._focal_key, "annotations.term_status")
            ),
        },
        "contexts": contexts,
        "matched_occurrences": matched_count,
        "exclusions": excluded,
        "scope": SCOPE,
        "input_occurrences": list(access._inputs),
    }
    has_molecular = any(c["nature"] in ("protein", "small_molecule") for c in contexts)
    partial = any(s["state"] == "partial" for s in supports.values()) or any(
        e["reason"] in ("conflicting_identity", "incomplete_identity") for e in excluded
    )
    status = (
        "missing_prerequisite"
        if not identity["coherent"] or not has_molecular and not matched_count
        else "partial"
        if partial
        else "ok"
        if matched_count
        else "empty"
    )
    coverage = {
        "rule": rule,
        "scope": "Only explicitly captured input occurrences, source statements and original request states; no global completeness.",
        "contexts": [
            {
                "capture": c["capture"],
                "knowledge_state": c["knowledge_state"],
                "stored_occurrences": c["stored_occurrences"],
                "matched_occurrences": c["matched_occurrences"],
            }
            for c in contexts
        ],
    }
    ref = _handle(
        "XR_",
        {
            "format": "disease_association_result@1",
            "focal": access._focal_key,
            "native": native,
            "rows": rows,
            "support": supports,
        },
    )
    wire = {
        "context": {
            **access.context,
            "adapter": ADAPTER,
            "options": {},
            "rule": RULE,
            "disease_card_ref": access._focal.pin,
            "used_captures": sorted(access._captures),
        },
        "native_payload": native,
        "rows": rows,
        "support": supports,
        "coverage": coverage,
        "scope": SCOPE,
        "schema": descriptor(),
        "outcome": {
            "status": status,
            "reason": "Source support, identity and request limits remain explicit; supplied scope never establishes global absence.",
        },
        "explanations": {
            k: {
                "item": deepcopy(r["item"]),
                "support": deepcopy(supports[k]),
                "interpretation": deepcopy(r["interpretation"]),
            }
            for k, r in rows.items()
        },
        "exclusions": excluded,
    }
    shell = AssociationResult(ref, wire, (), {})
    result = AssociationResult(
        ref,
        wire,
        tuple(
            _Entry(shell.location("rows", key), key, row) for key, row in rows.items()
        ),
        {},
    )
    access._objects[ref] = wire
    access._scientific_cache[cache] = result
    for entry in result.entries:
        access._scientific_items[item_ref(result, entry)] = (result, entry.key)
    return result


def defer_frame(frame):
    deferred = {
        key: deepcopy(value)
        for key, value in frame.items()
        if key not in ("interpretation", "support", "cells")
    }
    deferred.update(
        cells={
            key: {k: deepcopy(v) for k, v in value.items() if k != "value"}
            | {"value_included": False}
            for key, value in frame["cells"].items()
        },
        value_included=False,
        inspection_required=True,
        detail="referenced",
        reason="Original association values, source roles and identity context are deferred together; inspect the referenced item.",
    )
    deferred["value_location"] = deepcopy(frame["location"])
    return deferred
