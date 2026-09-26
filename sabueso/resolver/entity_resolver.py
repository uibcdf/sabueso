"""EntityResolver: which molecular entity is an identifier or query talking about?

MVP implementation of the contract in ``devguide/archive/entity_resolver.md``
(uibcdf/sabueso#6). It covers UniProtKB accessions (active primary, merged and demerged
inactive, isoform) and protein name + organism searches resolved by an explicit,
recorded preference policy, and PDB entry identifiers (``pdb:<id>``), which resolve to a
structure record plus the protein entities its polymer entities map to.

Principles: never choose silently, keep "not found", "unsupported" and "error" apart,
record every decision, and never create identity from identical sequences across
organisms.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sabueso._private.argdigest import arg_digest
from sabueso.core.card import make_card_id
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.core.relationship_store import (
    Relationship,
    make_relationship,
)
from sabueso.core.source_assertion_store import SourceAssertion, make_source_assertion
from sabueso.tools.db.rcsb import OnlineRCSBClient
from sabueso.tools.db.uniprot import OnlineUniProtClient

# UniProtKB accession format, optionally followed by an isoform suffix (e.g. P60174-3).
UNIPROT_ACCESSION = re.compile(
    r"^(?P<accession>[OPQ][0-9][A-Z0-9]{3}[0-9]"
    r"|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})(?:-(?P<isoform>[0-9]+))?$"
)

STATUSES = ("resolved", "ambiguous", "not_found", "unsupported", "error")

# Named, versioned preference policies. A policy may pick one candidate among several
# matches; the others are always kept as alternatives. None disables preferences.
POLICIES = ("prefer_reviewed@1",)
DEFAULT_POLICY = "prefer_reviewed@1"


@dataclass
class EntityQuery:
    identifier: Optional[str] = None
    name: Optional[str] = None
    organism: Optional[int | str] = None
    include_subtaxa: bool = False  # e.g. strains below the queried species
    entity_type: Optional[str] = None


@dataclass
class EntityResolution:
    status: str
    entity_ref: Optional[str] = None
    qualifiers: Dict[str, Any] = field(default_factory=dict)
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    policy: Optional[str] = None
    identity_links: List[Relationship] = field(default_factory=list)
    source_assertions: List[SourceAssertion] = field(default_factory=list)
    related: List[Dict[str, Any]] = field(
        default_factory=list
    )  # e.g. proteins in a PDB entry
    decision: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def protein_ref(accession: str) -> str:
    return make_card_id("protein", f"uniprot:{accession}")


def uniprot_basis(entry: Dict[str, Any]) -> Dict[str, Any]:
    """What a candidate is, as reported by its UniProt record."""
    return {
        "accession": entry.get("primaryAccession"),
        "reviewed": str(entry.get("entryType", "")).startswith("UniProtKB reviewed"),
        "organism": entry.get("organism", {}).get("taxonId"),
        "organism_name": entry.get("organism", {}).get("scientificName"),
        "length": entry.get("sequence", {}).get("length"),
        "md5": entry.get("sequence", {}).get("md5"),
    }


def _organism_matches(entry: Dict[str, Any], organism: int | str | None) -> bool:
    if organism is None:
        return True
    info = entry.get("organism", {})
    if isinstance(organism, int) or str(organism).isdigit():
        return info.get("taxonId") == int(organism)
    return str(info.get("scientificName", "")).lower() == str(organism).lower()


def sequence_identity_link(
    entry_a: Dict[str, Any], entry_b: Dict[str, Any]
) -> Optional[Relationship]:
    """Derived ``possibly_same_as`` between two UniProt entries, or None.

    Rule ``protein_identity_audit@1`` (``sabueso.core.identity_audit``, #55): a shared
    gene locus, or an identical or near-identical sequence within related organisms,
    raises the flag; distinct loci of one genome never do (paralogs). Entries of
    unrelated organisms (e.g. human P60174 and chimpanzee P60175) are never linked, and
    no link merges entities.
    """
    from sabueso.core.identity_audit import (
        basis_of_entry,
        compare,
        pairs_to_relationships,
    )

    found = compare(basis_of_entry(entry_a), basis_of_entry(entry_b))
    links = pairs_to_relationships([found] if found else [])
    return links[0] if links else None


def identity_audit(
    results: List[Dict[str, Any]],
    gene_client: Any = None,
    decision: Dict[str, Any] | None = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """Findings among the candidates of a search (``protein_identity_audit@1``), and
    the basis of each candidate by reference.

    With ``gene_client`` (NCBI Gene), a pair whose loci could not be compared (#69) is
    compared again with the products NCBI Gene lists for each entry's NCBI gene. Each
    request is recorded in ``decision["sources"]``.
    """
    from sabueso.core.identity_audit import audit, basis_of_entry, compare

    bases = {b["ref"]: b for b in (basis_of_entry(e) for e in results)}
    findings = audit(bases.values())
    if gene_client is None:
        return findings, bases
    fetched: Dict[str, Any] = {}
    for i, finding in enumerate(findings):
        if (finding.get("basis") or {}).get("gene_loci") != "not_comparable":
            continue
        for ref in finding["refs"]:
            basis = bases[ref]
            for database, gene_id in basis["gene_loci"]:
                if database != "NCBI Gene":
                    continue
                if gene_id not in fetched:
                    fetched[gene_id] = _gene_products(gene_client, gene_id, decision)
                if fetched[gene_id] is not None:
                    basis.setdefault("gene_products", {})[(database, gene_id)] = (
                        fetched[gene_id]
                    )
        again = compare(*(bases[ref] for ref in finding["refs"]))
        if again:
            findings[i] = again
    return findings, bases


def _gene_products(
    client: Any, gene_id: str, decision: Dict[str, Any] | None
) -> Dict[str, Any] | None:
    from sabueso.mappings.ncbi_gene import products

    record: Dict[str, Any] = {"name": "NCBI Gene", "record": gene_id}
    try:
        gene, retrieved_at = client.gene(gene_id)
    except RecordNotFoundError:
        record["outcome"] = "not_found"
        gene, retrieved_at = None, None
    except ConnectorError as exc:
        record["outcome"] = f"error: {exc}"
        gene, retrieved_at = None, None
    else:
        record["retrieved_at"] = retrieved_at
    if decision is not None:
        decision["sources"].append(record)
    if gene is None:
        return None
    return {"products": products(gene), "retrieved_at": retrieved_at}


class EntityResolver:
    @arg_digest()
    def __init__(
        self,
        uniprot_client: Any | None = None,
        policy: str | None = DEFAULT_POLICY,
        rcsb_client: Any | None = None,
        ncbi_gene_client: Any | None = None,
        skip_digestion: bool = False,
    ) -> None:
        self.uniprot = uniprot_client or OnlineUniProtClient()
        self.rcsb = rcsb_client or OnlineRCSBClient()
        self.policy = policy
        # Consulted only when two candidates state loci that cannot be compared (#69).
        self.ncbi_gene = ncbi_gene_client

    def resolve(self, query: EntityQuery | str) -> EntityResolution:
        if isinstance(query, str):
            query = EntityQuery(identifier=query)
        from sabueso import __version__

        decision: Dict[str, Any] = {
            "query": asdict(query),
            "rules": [],
            "sources": [],
            "sabueso_version": __version__,
        }
        if query.identifier:
            namespace, _, value = query.identifier.rpartition(":")
            if namespace in ("", "uniprot"):
                match = UNIPROT_ACCESSION.match(value)
                if match:
                    return self._resolve_uniprot(
                        match["accession"], match["isoform"], query, decision
                    )
                decision["rules"].append("invalid_identifier_format")
                return EntityResolution("unsupported", decision=decision)
            if namespace == "pdb" and re.fullmatch(r"[0-9][A-Za-z0-9]{3}", value):
                return self._resolve_pdb(value.upper(), decision)
            decision["rules"].append(f"unsupported_namespace:{namespace}")
            return EntityResolution("unsupported", decision=decision)
        if query.name:
            if query.organism is None:
                # Too broad to resolve responsibly (e.g. ~30k UniProt matches for a TIM name).
                decision["rules"].append("name_without_organism")
                return EntityResolution("unsupported", decision=decision)
            return self._resolve_name(query, decision)
        decision["rules"].append("unsupported_query")
        return EntityResolution("unsupported", decision=decision)

    # PDB entry ----------------------------------------------------------------------

    def _resolve_pdb(self, pdb_id: str, decision: Dict[str, Any]) -> EntityResolution:
        try:
            entry, retrieved_at = self.rcsb.fetch_structure(pdb_id)
        except RecordNotFoundError:
            decision["sources"].append(
                {"name": "RCSB PDB", "record": pdb_id, "outcome": "not_found"}
            )
            decision["rules"].append("record_not_found")
            return EntityResolution("not_found", decision=decision)
        except ConnectorError as exc:
            decision["sources"].append(
                {"name": "RCSB PDB", "record": pdb_id, "outcome": f"error: {exc}"}
            )
            decision["rules"].append("source_error")
            return EntityResolution("error", decision=decision)
        decision["sources"].append(
            {"name": "RCSB PDB", "record": pdb_id, "retrieved_at": retrieved_at}
        )
        decision["rules"].append("pdb_entry")
        related: Dict[str, List[str]] = {}
        for pe in entry.get("polymer_entities") or []:
            ids = pe.get("rcsb_polymer_entity_container_identifiers") or {}
            for acc in ids.get("uniprot_ids") or []:
                related.setdefault(acc, []).append(str(ids.get("entity_id")))
        return EntityResolution(
            "resolved",
            entity_ref=f"pdb:{pdb_id}",
            qualifiers={"record_type": "structure"},
            related=[
                {
                    "entity_ref": protein_ref(acc),
                    "predicate": "has_structure",
                    "polymer_entities": entities,
                }
                for acc, entities in sorted(related.items())
            ],
            decision=decision,
        )

    # Name + organism ----------------------------------------------------------------

    def _resolve_name(
        self, query: EntityQuery, decision: Dict[str, Any]
    ) -> EntityResolution:
        try:
            found = self.uniprot.search(
                query.name, query.organism, query.include_subtaxa
            )
        except ConnectorError as exc:
            decision["sources"].append(
                {"name": "UniProt search", "outcome": f"error: {exc}"}
            )
            decision["rules"].append("source_error")
            return EntityResolution("error", decision=decision)
        results = found.get("results", [])
        decision["sources"].append(
            {
                "name": "UniProt search",
                "query": found.get("query"),
                "total": found.get("total"),
                "release": found.get("release"),
                "retrieved_at": found.get("retrieved_at"),
            }
        )
        candidates = [
            {
                "entity_ref": protein_ref(e["primaryAccession"]),
                "basis": uniprot_basis(e),
            }
            for e in results
        ]
        if not results:
            decision["rules"].append("name_organism_no_match")
            return EntityResolution("not_found", decision=decision)
        if (found.get("total") or len(results)) > len(results):
            # Never resolve from a partial list of matches.
            decision["rules"].append("search_truncated")
            return EntityResolution(
                "ambiguous", candidates=candidates, decision=decision
            )
        bases: Dict[str, Dict[str, Any]] = {}
        if len(results) > 1:
            # Redundant entries, strain variants and paralogs among the candidates,
            # each with its basis; nothing is merged (#55).
            decision["identity_audit"], bases = identity_audit(
                results, self.ncbi_gene, decision
            )
        if len(results) == 1:
            decision["rules"].append("name_organism_single_match")
            return EntityResolution(
                "resolved", entity_ref=candidates[0]["entity_ref"], decision=decision
            )
        return self._apply_preference(results, candidates, decision, bases)

    def _apply_preference(
        self,
        results: List[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
        decision: Dict[str, Any],
        bases: Dict[str, Dict[str, Any]] | None = None,
    ) -> EntityResolution:
        decision["policy"] = self.policy
        if self.policy is None:
            decision["rules"].append("no_preference_policy")
            return EntityResolution(
                "ambiguous", candidates=candidates, decision=decision
            )
        preferred = [i for i, c in enumerate(candidates) if c["basis"]["reviewed"]]
        if len(preferred) != 1:
            decision["rules"].append(f"preference_inconclusive:{self.policy}")
            return EntityResolution(
                "ambiguous", candidates=candidates, decision=decision
            )
        chosen = preferred[0]
        decision["rules"].append(f"preference:{self.policy}")
        resolution = EntityResolution(
            "resolved",
            entity_ref=candidates[chosen]["entity_ref"],
            alternatives=[c for i, c in enumerate(candidates) if i != chosen],
            policy=self.policy,
            decision=decision,
        )
        # Make identical-sequence alternatives in the same organism explicit (derived).
        from sabueso.core.identity_audit import compare, pairs_to_relationships

        mine = f"uniprot:{results[chosen]['primaryAccession']}"
        for i, entry in enumerate(results):
            if i == chosen:
                continue
            other = f"uniprot:{entry['primaryAccession']}"
            if bases and mine in bases and other in bases:
                # The bases the audit used, gene products included (#69).
                found = compare(bases[mine], bases[other])
                links = pairs_to_relationships([found] if found else [])
                link = links[0] if links else None
            else:
                link = sequence_identity_link(results[chosen], entry)
            if link:
                resolution.identity_links.append(link)
        return resolution

    # UniProt ------------------------------------------------------------------------

    def _fetch(self, accession: str, decision: Dict[str, Any]) -> Dict[str, Any]:
        try:
            entry, retrieved_at = self.uniprot.fetch_entry(accession)
        except RecordNotFoundError:
            decision["sources"].append(
                {"name": "UniProt", "record": accession, "outcome": "not_found"}
            )
            raise
        except ConnectorError as exc:
            decision["sources"].append(
                {"name": "UniProt", "record": accession, "outcome": f"error: {exc}"}
            )
            raise
        decision["sources"].append(
            {"name": "UniProt", "record": accession, "retrieved_at": retrieved_at}
        )
        return entry

    def _resolve_uniprot(
        self,
        accession: str,
        isoform: Optional[str],
        query: EntityQuery,
        decision: Dict[str, Any],
    ) -> EntityResolution:
        try:
            entry = self._fetch(accession, decision)
            if entry.get("entryType") == "Inactive":
                return self._resolve_inactive(accession, entry, query, decision)
            if not _organism_matches(entry, query.organism):
                decision["rules"].append("organism_mismatch")
                return EntityResolution("not_found", decision=decision)
            primary = entry["primaryAccession"]
            resolution = EntityResolution(
                "resolved", entity_ref=protein_ref(primary), decision=decision
            )
            if primary != accession:
                # The REST API answered a secondary accession with the active entry.
                decision["rules"].append("secondary_accession_redirected")
                self._link(resolution, accession, "same_as", primary, entry, {})
            else:
                decision["rules"].append("active_primary_accession")
            if isoform:
                return self._apply_isoform(resolution, primary, isoform, entry)
            return resolution
        except RecordNotFoundError:
            decision["rules"].append("record_not_found")
            return EntityResolution("not_found", decision=decision)
        except ConnectorError:
            decision["rules"].append("source_error")
            return EntityResolution("error", decision=decision)

    def _resolve_inactive(
        self,
        accession: str,
        entry: Dict[str, Any],
        query: EntityQuery,
        decision: Dict[str, Any],
    ) -> EntityResolution:
        reason = entry.get("inactiveReason", {}) or {}
        kind = reason.get("inactiveReasonType")
        targets = reason.get("mergeDemergeTo", []) or []
        if not targets:
            decision["rules"].append(f"inactive_without_successor:{kind}")
            return EntityResolution("not_found", decision=decision)

        target_entries = [self._fetch(t, decision) for t in targets]
        candidates = [
            {
                "entity_ref": protein_ref(t["primaryAccession"]),
                "basis": uniprot_basis(t),
            }
            for t in target_entries
        ]
        predicate = (
            "same_as" if kind == "MERGED" and len(targets) == 1 else "superseded_by"
        )

        matching = [
            (t, c)
            for t, c in zip(target_entries, candidates)
            if _organism_matches(t, query.organism)
        ]
        if len(targets) == 1 and matching:
            decision["rules"].append(f"inactive_{kind.lower()}_single_successor")
        elif query.organism is not None and len(matching) == 1:
            decision["rules"].append(f"inactive_{kind.lower()}_filtered_by_organism")
        elif not matching:
            decision["rules"].append("organism_mismatch")
            return EntityResolution(
                "not_found", candidates=candidates, decision=decision
            )
        else:
            decision["rules"].append(f"inactive_{kind.lower()}_ambiguous")
            return EntityResolution(
                "ambiguous", candidates=candidates, decision=decision
            )

        chosen_entry, chosen = matching[0]
        resolution = EntityResolution(
            "resolved",
            entity_ref=chosen["entity_ref"],
            alternatives=[c for c in candidates if c is not chosen],
            decision=decision,
        )
        self._link(
            resolution,
            accession,
            predicate,
            chosen_entry["primaryAccession"],
            entry,
            {"inactive_reason": kind},
        )
        return resolution

    def _apply_isoform(
        self,
        resolution: EntityResolution,
        canonical: str,
        isoform: str,
        entry: Dict[str, Any],
    ) -> EntityResolution:
        isoform_acc = f"{canonical}-{isoform}"
        listed = {}
        for comment in entry.get("comments", []) or []:
            if comment.get("commentType") != "ALTERNATIVE PRODUCTS":
                continue
            for item in comment.get("isoforms", []) or []:
                for iso_id in item.get("isoformIds", []) or []:
                    listed[iso_id] = item
        if isoform_acc not in listed:
            resolution.decision["rules"].append("isoform_not_listed")
            return EntityResolution("not_found", decision=resolution.decision)
        item = listed[isoform_acc]
        resolution.qualifiers["isoform"] = isoform_acc
        resolution.decision["rules"].append("isoform_accession")
        self._link(
            resolution,
            isoform_acc,
            "isoform_of",
            canonical,
            entry,
            {
                "isoform": isoform_acc,
                "isoform_name": (item.get("name") or {}).get("value"),
                "sequence_status": item.get("isoformSequenceStatus"),
            },
        )
        return resolution

    def _link(
        self,
        resolution: EntityResolution,
        subject_accession: str,
        predicate: str,
        object_accession: str,
        stating_entry: Dict[str, Any],
        qualifiers: Dict[str, Any],
    ) -> None:
        """Identity link asserted by the UniProt record that states it."""
        record = stating_entry.get("primaryAccession") or subject_accession
        retrieved_at = next(
            (
                s.get("retrieved_at", "")
                for s in resolution.decision["sources"]
                if s.get("record") == record
            ),
            "",
        )
        assertion = make_source_assertion(
            f"relationships.{predicate}",
            {
                "subject_ref": f"uniprot:{subject_accession}",
                "object_ref": f"uniprot:{object_accession}",
                **qualifiers,
            },
            "UniProt",
            record,
            retrieved_at,
        )
        resolution.source_assertions.append(assertion)
        resolution.identity_links.append(
            make_relationship(
                f"uniprot:{subject_accession}",
                predicate,
                f"uniprot:{object_accession}",
                qualifiers=qualifiers,
                source_assertion_ids=[assertion["id"]],
            )
        )
