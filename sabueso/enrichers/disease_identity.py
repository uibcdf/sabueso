"""MONDO: which of a protein's disease ids are the same disease (``same_as``, #90), and
which of the terms they reach MONDO places under another (``subclass_of``,
``mondo_hierarchy@1``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher, Request, RequestPrerequisiteMissing


class DiseaseIdentity(Enricher):
    option = "disease_identity"
    source = "MONDO"
    registry_id = "mondo"
    areas = ("relationships.same_as (MONDO)", "relationships.subclass_of (MONDO)")
    client_option = "mondo_client"
    #: Last: it reads the diseases every other source put on the card.
    stage = "after_bioactivity"

    def client(self):
        from sabueso.tools.db.mondo import OnlineMONDOClient

        return OnlineMONDOClient()

    def requests(self, context, options):
        from sabueso.core.diseases import CLINVAR_PLACEHOLDERS, disease_statements

        fields, relationships = {}, []
        for mapping in context.mappings:
            fields.update(mapping.get("fields") or {})
            relationships.extend(mapping.get("relationships") or [])
        statements = disease_statements(fields.get, relationships)
        if not statements:
            raise RequestPrerequisiteMissing("the card names no disease")
        # MONDO names MedGen records by UID: concept ids are asked through the UIDs
        # MedGen states for them (the medgen enrichment), not directly.
        uid_of = {
            r["subject_ref"]: r["object_ref"]
            for r in relationships
            if r.get("predicate") == "same_as"
            and (r.get("qualifiers") or {}).get("source") == "MedGen"
        }
        uids = set(uid_of.values())
        curies = sorted(
            {
                c
                for s in statements
                for c in s["curies"]
                if not c.startswith("MEDGEN:C") and c not in CLINVAR_PLACEHOLDERS
            }
            | uids
        )
        if not curies:
            raise RequestPrerequisiteMissing(
                "the card names no queryable disease id; MONDO needs a mapped "
                "identifier or a MedGen UID"
            )
        unmapped = sorted({r for s in statements for r in s["unmapped"]})
        # The ids each statement names together: MONDO's hierarchy is asked only
        # between the terms one statement reaches (mondo_hierarchy@1).
        together = sorted(
            {
                tuple(sorted({uid_of.get(c, c) for c in s["curies"]}))
                for s in statements
                if len(s["curies"]) > 1
            }
        )
        return [
            Request(
                context.anchor,
                {"source": self.source, "identifier": context.anchor},
                {"curies": curies, "unmapped": unmapped, "together": together},
            )
        ]

    def fetch(self, client, request, options):
        from sabueso.core.errors import RecordNotFoundError

        answers = {}
        for curie in request.args["curies"]:
            if curie.startswith("MONDO:"):
                term = client.term(curie)
                record = term["record"]
                answers[curie] = {
                    "version": term.get("version"),
                    "retrieved_at": term.get("retrieved_at"),
                    "mondo": None if record.get("obsolete") else curie,
                    "obsolete": bool(record.get("obsolete")),
                }
                continue
            answer = client.equivalent(curie)
            if answer.get("mondo"):
                record = client.term(answer["mondo"])["record"]
                answer["name"] = record.get("name")
            answers[curie] = answer
        chains, seen = [], set()
        for ids in request.args.get("together") or []:
            reached = sorted(
                {
                    answers[c]["mondo"]
                    for c in ids
                    if (answers.get(c) or {}).get("mondo")
                }
            )
            for chain in _hierarchy(client, reached, RecordNotFoundError):
                key = (chain[0]["term"], chain[-1]["parent"])
                if key not in seen:
                    seen.add(key)
                    chains.append(chain)
        return {"answers": answers, "hierarchy": chains}

    def map(self, context, request, response, options):
        from sabueso.mappings.mondo import map_equivalences, map_hierarchy

        hierarchy = response["hierarchy"]
        response = response["answers"]
        mapped = map_equivalences(response, context.anchor)
        ranks = map_hierarchy(hierarchy)
        mapped["source_assertions"] += ranks["source_assertions"]
        mapped["relationships"] += ranks["relationships"]
        ungrouped = [
            {
                "curie": c,
                "reason": "obsolete_term"
                if a.get("obsolete")
                else "no_stated_equivalence",
            }
            for c, a in sorted(response.items())
            if not a.get("mondo")
        ]
        versions = sorted({a.get("version") for a in response.values()} - {None})
        return mapped, {
            "status": "added" if mapped["relationships"] else "not_found",
            "version": "; ".join(versions) or None,
            "count": len(mapped["relationships"]),
            "subclass_of": len(ranks["relationships"]),
            "ids": len(response),
            "ungrouped": ungrouped
            + [
                {"curie": r, "reason": "namespace_not_mapped"}
                for r in request.args["unmapped"]
            ],
        }


def _hierarchy(client, terms, not_found):
    """For each pair of ``terms`` where MONDO places one under the other, the chain of
    ``is_a`` statements between them (``[{"term", "parent", "version",
    "retrieved_at"}, ...]``), from the more specific term up (``mondo_hierarchy@1``).

    ``terms`` are those one statement reaches: the card does not carry MONDO's whole
    hierarchy above its diseases.
    """
    records: dict = {}

    def term(mondo_id):
        if mondo_id not in records:
            try:
                records[mondo_id] = client.term(mondo_id)
            except not_found:
                records[mondo_id] = None
        return records[mondo_id]

    wanted = set(terms)
    chains = []
    for start in terms:
        # Breadth first: the shortest chain of stated is_a steps to each ancestor.
        paths = {start: []}
        queue = [start]
        while queue:
            node = queue.pop(0)
            answer = term(node)
            if answer is None:
                continue
            for parent in answer["record"].get("parents") or []:
                if parent in paths:
                    continue
                step = {
                    "term": node,
                    "parent": parent,
                    "version": answer.get("version"),
                    "retrieved_at": answer.get("retrieved_at"),
                }
                paths[parent] = paths[node] + [step]
                queue.append(parent)
        chains += [
            paths[ancestor] for ancestor in sorted(wanted & set(paths) - {start})
        ]
    return chains


ENRICHER = DiseaseIdentity()
