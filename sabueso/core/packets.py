"""Knowledge packets: one declared question, one pinned, cited answer (uibcdf/sabueso#71).

A **KnowledgeQuery** is a structured question, not natural language: a subject protein,
an optional comparator, the aspects asked for, and constraints. A **KnowledgePacket** is
the composed answer. It is a composition over cards, not a new kind of knowledge:

- ``entities``: the pinned card states it was composed from (never copies);
- ``facts``: per aspect, the output of Sabueso's views, each with its named rule;
- ``conflicts``: where sources disagree, as the cards record it;
- ``unknowns``: per source, what is not stated, not queried, unavailable or partial,
  for the areas of the aspects asked (``knowledge_state@2``);
- ``provenance``: the sources, their releases and retrieval dates.

**Deterministic.** Composition is a pure function of the query and the card states. It
never calls an LLM, never ranks, never summarizes, and holds the aspects the query
declares, nothing else. The same query and the same card states give the same packet.

**Two ids.** ``snapshot_id`` is the exact state, retrieval times included: the citable
pin, ``sabueso:packet:<name>@sha256:…``. ``content_id`` leaves out retrieval times and
the Sabueso version that built the cards, so two assemblies of unchanged knowledge have
the same ``content_id`` even when the sources were read again (``same_knowledge``).

What each aspect asks the sources for, and which knowledge areas it covers, is fixed by
the mapping ``packet_aspects@1``. It never changes once published: a change is a new
version.

The shared contract (query and packet shapes, references, the boundary with MOLI's
Context Assembly) is proposed in uibcdf/moli#22; this is Sabueso's prototype of it.
"""

from __future__ import annotations

import copy
import json
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from sabueso._private.argdigest import arg_digest

from .errors import StorageError
from .snapshot import canonical_json, digest, parse_ref, pinned_ref, snapshot_content

QUERY_FORMAT = "knowledge_query@1"
PACKET_FORMAT = "knowledge_packet@1"
ASPECT_MAPPING = "packet_aspects@1"
PACKET_PREFIX = "sabueso:packet:"

#: Keys left out of a content-equivalence id: when the sources were read, and which
#: Sabueso version built the card. Neither is knowledge.
NOT_KNOWLEDGE = ("retrieved_at", "sabueso_version")

#: Identity fields a packet shows (the full sequence stays on the card).
IDENTITY_FIELDS = (
    "identifiers.uniprot",
    "identifiers.gene_loci",
    "names.canonical_name",
    "names.gene_names",
    "annotations.organism",
    "annotations.taxon_id",
    "annotations.lineage",
    "annotations.taxonomy",
    "sequence.length",
    "sequence.checksums",
)

#: ``packet_aspects@1``: per aspect, the knowledge areas (field paths and relationships,
#: as ``knowledge_state`` names them) whose facts, conflicts and unknowns it reports,
#: matched by prefix; and the options of the bespoke sources it needs. The options of
#: declared enrichers are derived (``aspect_options``): an aspect asks every enricher
#: that answers one of its areas, so a packet never reports as "not queried" what its
#: own aspects could have asked (#86).
ASPECTS: Dict[str, Dict[str, Any]] = {
    "identity": {
        "bespoke_options": {},
        "areas": (
            "identifiers.",
            "names.",
            "annotations.organism",
            "annotations.taxon_id",
            "annotations.lineage",
            "annotations.taxonomy",
            "sequence.",
        ),
    },
    "structures": {
        "bespoke_options": {"structures": "all"},
        "areas": (
            "relationships.has_structure",
            "relationships.has_predicted_structure",
        ),
    },
    "oligomer": {
        "bespoke_options": {"structures": "all"},
        "areas": (
            "annotations.subunit",
            "relationships.has_interface_with",
            "features_positional.family_site",
        ),
    },
    "ligand_sites": {
        "bespoke_options": {},
        "areas": (
            "relationships.has_ligand_site",
            "features_positional.binding_site",
            "features_positional.active_site",
            "features_positional.family_site",
        ),
    },
    "bioactivities": {
        "bespoke_options": {},  # from the bioactivity_sources constraint
        "areas": ("relationships.has_bioactivity",),
    },
    "sequence_features": {
        "bespoke_options": {},
        "areas": (
            "features_positional.",
            "annotations.isoforms",
            "annotations.alternative_products",
            "annotations.population_variants",
        ),
    },
    "literature": {
        "bespoke_options": {},
        "areas": ("relationships.described_in", "literature."),
    },
    "disease_association": {
        "bespoke_options": {},
        "areas": (
            "relationships.associated_with",
            "annotations.disease",
            "annotations.clinical_variants",
        ),
    },
    "biological_context": {
        "bespoke_options": {},
        "areas": (
            "relationships.participates_in",
            "annotations.pathogen_phenotypes",
            "annotations.stage_expression",
            "annotations.essentiality",
            "annotations.accessibility",
            "annotations.metabolic_role",
            "annotations.subcellular_location",
            "annotations.tissue_specificity",
            "annotations.pathway",
        ),
    },
}


def aspect_options(aspect: str) -> Dict[str, Any]:
    """The resolve options an aspect needs: its bespoke sources', and every declared
    enricher answering one of its areas (``packet_aspects@1``)."""
    from sabueso.enrichers import ENRICHERS

    options = dict(ASPECTS[aspect]["bespoke_options"])
    for enricher in ENRICHERS:
        if enricher.entity_type == "protein" and any(
            _in_areas(area, [aspect]) for area in enricher.areas
        ):
            options[enricher.option] = enricher.default_request
    return options


#: Bioactivity sources a query may name, and the resolve option each needs.
BIOACTIVITY_SOURCES = {
    "ChEMBL": ("chembl", {}),
    "BindingDB": ("bindingdb", {}),
    "PubChem BioAssay": ("pubchem_bioassay", True),
}
#: Constraints and their defaults (``knowledge_query@1``).
CONSTRAINTS = {"bioactivity_sources": ("ChEMBL",)}

UNKNOWN_STATES = ("not_stated", "not_queried", "unavailable", "partial")


class KnowledgeQuery:
    """A declared question about a protein, optionally beside a comparator.

    ``subject`` and ``comparator`` are UniProt accessions (``P60174`` or
    ``uniprot:P60174``). ``aspects`` are names of ``packet_aspects@1`` (default: all
    of them). ``constraints``: ``bioactivity_sources``, among ChEMBL, BindingDB and
    PubChem BioAssay (default ChEMBL). Anything else is refused, never ignored.
    """

    @arg_digest()
    def __init__(
        self,
        subject: str,
        comparator: str | None = None,
        aspects: Iterable[str] | None = None,
        constraints: Mapping[str, Any] | None = None,
        skip_digestion: bool = False,
    ) -> None:
        self.subject = subject
        self.comparator = comparator
        self.aspects = tuple(sorted(aspects)) if aspects else tuple(sorted(ASPECTS))
        merged = dict(CONSTRAINTS)
        merged.update(constraints or {})
        self.constraints = {
            "bioactivity_sources": tuple(sorted(merged["bioactivity_sources"]))
        }
        if subject == comparator:
            raise ValueError("A subject is not its own comparator.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": QUERY_FORMAT,
            "subject": self.subject,
            "comparator": self.comparator,
            "aspects": list(self.aspects),
            "constraints": {k: list(v) for k, v in self.constraints.items()},
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "KnowledgeQuery":
        if data.get("format") != QUERY_FORMAT:
            raise ValueError(
                f"Not a {QUERY_FORMAT} query: format {data.get('format')!r}."
            )
        return cls(
            data["subject"],
            data.get("comparator"),
            data.get("aspects"),
            data.get("constraints"),
        )

    def options(self) -> Dict[str, Any]:
        """The resolve options the aspects need (``packet_aspects@1``)."""
        options: Dict[str, Any] = {}
        for aspect in self.aspects:
            options.update(aspect_options(aspect))
        if "bioactivities" in self.aspects:
            for source in self.constraints["bioactivity_sources"]:
                option, value = BIOACTIVITY_SOURCES[source]
                options[option] = value
        return options

    def __eq__(self, other: object) -> bool:
        return isinstance(other, KnowledgeQuery) and self.to_dict() == other.to_dict()

    def __repr__(self) -> str:
        if not hasattr(self, "constraints"):  # refused while being built
            return "KnowledgeQuery(<not built>)"
        return f"KnowledgeQuery({self.to_dict()!r})"


def as_stated(data: Any) -> Any:
    """View output as JSON: a quantity becomes its node ``{value, unit}`` (the unit is
    never dropped), tuples become lists and sets sorted lists. Anything else that JSON
    cannot state is refused."""
    import pyunitwizard as puw

    from .quantities import canonical_unit, quantity_node

    if isinstance(data, dict):
        return {str(k): as_stated(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [as_stated(v) for v in data]
    if isinstance(data, (set, frozenset)):
        return sorted((as_stated(v) for v in data), key=canonical_json)
    if data is None or isinstance(data, (str, bool, int, float)):
        return data
    if puw.is_quantity(data):
        # Its own unit, named: the value is read in that unit, never in a session's.
        unit = canonical_unit(str(puw.get_unit(data)))
        value = puw.get_value(data, to_unit=unit)
        value = value.item() if hasattr(value, "item") else value
        return quantity_node(value, unit)
    raise TypeError(f"A packet cannot state {type(data).__name__}: {data!r}")


def without_retrieval(data: Any) -> Any:
    """A copy without the keys that are not knowledge (``NOT_KNOWLEDGE``)."""
    if isinstance(data, dict):
        return {
            k: without_retrieval(v) for k, v in data.items() if k not in NOT_KNOWLEDGE
        }
    if isinstance(data, list):
        return [without_retrieval(v) for v in data]
    return data


def card_content_id(card: Any) -> str:
    """The content-equivalence id of a card: its snapshot content without retrieval
    times and without the Sabueso version that built it."""
    content = without_retrieval(snapshot_content(card.to_dict()))
    for key in ("source_assertion_store", "relationship_store"):
        content[key] = sorted(content.get(key) or [], key=canonical_json)
    return digest(canonical_json(content))


def _in_areas(area: str, aspects: Iterable[str]) -> bool:
    return any(
        area.startswith(prefix) for a in aspects for prefix in ASPECTS[a]["areas"]
    )


def _fields(card: Any, paths: Iterable[str]) -> Dict[str, Any]:
    out = {}
    for path in paths:
        node = card.get(path)
        if node is not None:
            out[path] = node
    return out


def _positional(card: Any) -> Dict[str, Any]:
    paths = [p for p in card.list_fields() if p.startswith("features_positional.")]
    paths = {p.split(".")[0] + "." + p.split(".")[1] for p in paths}
    return _fields(
        card,
        sorted(paths)
        + [
            "annotations.isoforms",
            "annotations.alternative_products",
            "annotations.population_variants",
        ],
    )


def _facts(aspect: str, card: Any) -> Dict[str, Any]:
    if aspect == "identity":
        decision = (card.quality.get("entity_resolution") or {}).get("decision") or {}
        return {
            "card_id": card.id,
            "fields": _fields(card, IDENTITY_FIELDS),
            "resolution": {k: decision.get(k) for k in ("rules", "sources", "route")},
        }
    if aspect == "structures":
        return {
            "experimental": card.structures(),
            "predicted": card.predicted_structures(),
        }
    if aspect == "oligomer":
        return card.oligomer()
    if aspect == "ligand_sites":
        return card.ligand_sites()
    if aspect == "bioactivities":
        return card.bioactivities()
    if aspect == "sequence_features":
        return _positional(card)
    if aspect == "literature":
        return {"publications": card.literature(), "claims": card.claims()}
    if aspect == "disease_association":
        return {
            "uniprot": _fields(card, ["annotations.disease"]),
            "clinical_variants": _fields(card, ["annotations.clinical_variants"]),
            "associations": [
                {k: r[k] for k in ("object_ref", "qualifiers", "source_assertion_ids")}
                for r in sorted(
                    card.relationships(predicate="associated_with"),
                    key=lambda r: (r["object_ref"], r["qualifiers"].get("channel", "")),
                )
            ],
        }
    if aspect == "biological_context":
        return {
            **_fields(card, ASPECTS["biological_context"]["areas"][1:]),
            "pathways": [
                {k: r[k] for k in ("object_ref", "qualifiers", "source_assertion_ids")}
                for r in sorted(
                    card.relationships(predicate="participates_in"),
                    key=lambda r: r["object_ref"],
                )
            ],
        }
    raise KeyError(aspect)


def _together(aspect: str, subject: Any, comparator: Any) -> Dict[str, Any] | None:
    """What an aspect says of the two proteins side by side."""
    from .deck import Deck

    if aspect == "identity":
        return {"identity_audit": Deck([subject, comparator]).identity_audit()}
    if aspect == "structures":
        return {"inventory": Deck([subject, comparator]).structure_inventory()}
    return None


def _unknowns(card: Any, aspects: Iterable[str]) -> Dict[str, Any]:
    state = card.knowledge_state()
    return {
        "rows": [
            r
            for r in state["rows"]
            if r["state"] in UNKNOWN_STATES and _in_areas(r["area"], aspects)
        ],
        "rule": state["rule"],
    }


def _conflicts(card: Any, aspects: Iterable[str]) -> List[Dict[str, Any]]:
    return [
        c
        for c in card.quality.get("conflicts") or []
        if _in_areas(str(c.get("field") or ""), aspects)
    ]


def _provenance(card: Any) -> Dict[str, Any]:
    sources: Dict[str, Dict[str, Any]] = {}
    for sa in card.source_assertion_store.to_list():
        source = sa.get("source") or {}
        entry = sources.setdefault(
            source.get("name") or "unknown",
            {"releases": set(), "retrieved": set(), "assertions": 0},
        )
        entry["assertions"] += 1
        if source.get("version") is not None:
            entry["releases"].add(str(source["version"]))
        if sa.get("retrieved_at"):
            entry["retrieved"].add(str(sa["retrieved_at"]))
    enrichments: Dict[str, Dict[str, int]] = {}
    for record in card.quality.get("enrichments") or []:
        name = record.get("source") or "unknown"
        if record.get("data"):
            name += f" {record['data']}"
        by_status = enrichments.setdefault(name, {})
        status = str(record.get("status"))
        by_status[status] = by_status.get(status, 0) + 1
    return {
        "sources": {
            name: {
                "releases": sorted(e["releases"]),
                "assertions": e["assertions"],
                "retrieved_at": sorted(e["retrieved"])[:1] + sorted(e["retrieved"])[-1:]
                if e["retrieved"]
                else [],
            }
            for name, e in sorted(sources.items())
        },
        "enrichments": enrichments,
    }


class KnowledgePacket:
    """A composed, pinned answer to a KnowledgeQuery. Build it with
    ``compose_packet`` or ``sabueso.knowledge_packet``; read ``facts``, ``unknowns``,
    ``conflicts``, ``entities`` and ``provenance``."""

    def __init__(self, data: Dict[str, Any], ref: str | None = None) -> None:
        if data.get("format") != PACKET_FORMAT:
            raise StorageError(
                f"Not a {PACKET_FORMAT} packet: format {data.get('format')!r}."
            )
        self._data = data
        self.ref = ref

    query = property(lambda self: KnowledgeQuery.from_dict(self._data["query"]))
    entities = property(lambda self: self._data["entities"])
    facts = property(lambda self: self._data["facts"])
    conflicts = property(lambda self: self._data["conflicts"])
    unknowns = property(lambda self: self._data["unknowns"])
    provenance = property(lambda self: self._data["provenance"])

    def to_dict(self) -> Dict[str, Any]:
        return copy.deepcopy(self._data)

    def snapshot_id(self) -> str:
        """The exact state, retrieval times included: what a pin names."""
        return digest(canonical_json(self._data))

    def content_id(self) -> str:
        """The knowledge, without retrieval times or the building Sabueso version."""
        content = without_retrieval(self._data)
        for entity in content["entities"].values():
            entity.pop("ref", None)
        return digest(canonical_json(content))

    def same_knowledge(self, other: "KnowledgePacket") -> bool:
        """Whether two packets hold the same knowledge, however often it was read."""
        return self.content_id() == other.content_id()

    def cite(self, role: str, item_id: str) -> str:
        """The pinned reference of a SourceAssertion or relationship of an entity,
        e.g. ``cite("subject", "SA_…")``."""
        card_id, sid, _ = parse_ref(self.entities[role]["ref"])
        return pinned_ref(card_id, sid, item_id)

    def __repr__(self) -> str:
        roles = ", ".join(f"{r}={e['card_id']}" for r, e in self.entities.items())
        return f"KnowledgePacket({roles}; aspects={list(self.facts)})"


def compose_packet(
    knowledge_query: KnowledgeQuery, subject: Any, comparator: Any = None
) -> KnowledgePacket:
    """Compose the packet of a query from card states; pure and deterministic.

    The cards are used as they are: an aspect whose sources they were not built with
    shows as ``not_queried`` in ``unknowns``, never as absent knowledge.
    """
    roles: List[Tuple[str, Any]] = [("subject", subject)]
    if comparator is not None:
        roles.append(("comparator", comparator))
    elif knowledge_query.comparator is not None:
        raise ValueError("The query names a comparator; give its card.")
    for role, card in roles:
        wanted = getattr(knowledge_query, role)
        anchor = (card.get("identifiers.uniprot") or {}).get("value")
        if wanted.split(":", 1)[1] != anchor:
            raise ValueError(
                f"The {role} card is {card.id}, but the query asks about {wanted}."
            )
    aspects = knowledge_query.aspects
    facts: Dict[str, Any] = {}
    for aspect in aspects:
        facts[aspect] = {role: _facts(aspect, card) for role, card in roles}
        if comparator is not None:
            together = _together(aspect, subject, comparator)
            if together is not None:
                facts[aspect]["together"] = together
    data = {
        "format": PACKET_FORMAT,
        "aspect_mapping": ASPECT_MAPPING,
        "query": knowledge_query.to_dict(),
        "entities": {
            role: {
                "card_id": card.id,
                "ref": card.pinned_ref(),
                "content_id": card_content_id(card),
            }
            for role, card in roles
        },
        "facts": facts,
        "conflicts": {role: _conflicts(card, aspects) for role, card in roles},
        "unknowns": {role: _unknowns(card, aspects) for role, card in roles},
        "provenance": {role: _provenance(card) for role, card in roles},
    }
    # The packet is what its canonical JSON states, so a stored packet reads back
    # identical, with every quantity as a node.
    return KnowledgePacket(json.loads(canonical_json(as_stated(data))))
