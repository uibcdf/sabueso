"""ProteinCards built from resolved entities (uibcdf/sabueso#6, step 4c).

``resolve_protein_card`` resolves a query with the EntityResolver and builds the card of
the resolved protein entity:

- only SourceAssertions about the entity (its anchor record and ``same_as`` records) feed
  card fields (``entity_subjects`` guard);
- identity links (``same_as``, ``superseded_by``, ``isoform_of``, derived
  ``possibly_same_as``) are kept as relationships;
- experimental structures are relationships shown through ``Card.structures()``,
  optionally enriched with RCSB polymer-entity data;
- STRING functional associations, ChEMBL bioactivities and PDBe-KB ligand sites can be
  added on request; every enrichment outcome is recorded in ``quality.enrichments``;
- the resolution trace (policy, alternatives, decision) is kept in
  ``quality.entity_resolution``.

``ambiguity_deck`` turns unresolved candidates, or non-preferred alternatives, into a Deck
of light candidate cards built only from what the source already reported.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from smonitor import signal

from sabueso._private.argdigest import arg_digest
from sabueso._private.smonitor.outcomes import report_outcomes
from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.core.merge import merge_mapping_results
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.chembl import map_bioactivities
from sabueso.mappings.rcsb_structures import map_structure_entities
from sabueso.mappings.uniprot import map_protein
from sabueso.resolver.entity_resolver import (
    EntityQuery,
    EntityResolution,
    EntityResolver,
)

UNIPROT_PREFIX = "sabueso:protein:uniprot:"


@signal(tags=["api", "protein"])
@arg_digest()
def resolve_protein_card(
    query: EntityQuery | str,
    resolver: EntityResolver | None = None,
    structures: Iterable[str] | str = (),
    string: Dict[str, Any] | None = None,
    string_client: Any | None = None,
    chembl: Dict[str, Any] | None = None,
    chembl_client: Any | None = None,
    ligand_sites: bool = False,
    interfaces: bool = False,
    pdbe_kb_client: Any | None = None,
    family_sites: bool = False,
    interpro_client: Any | None = None,
    predicted_structures: bool = False,
    alphafold_client: Any | None = None,
    taxonomy: bool = False,
    taxonomy_client: Any | None = None,
    bindingdb: Dict[str, Any] | None = None,
    bindingdb_client: Any | None = None,
    unichem_client: Any | None = None,
    pubchem_bioassay: bool | Dict[str, Any] = False,
    pubchem_bioassay_client: Any | None = None,
    ncbi_gene: bool = False,
    ncbi_gene_client: Any | None = None,
    phi_base: bool = False,
    phi_base_client: Any | None = None,
    diseases: Dict[str, Any] | None = None,
    diseases_client: Any | None = None,
    open_targets: Dict[str, Any] | None = None,
    open_targets_client: Any | None = None,
    orphadata: bool = False,
    orphadata_client: Any | None = None,
    reactome: bool = False,
    reactome_client: Any | None = None,
    clinvar: Dict[str, Any] | None = None,
    clinvar_client: Any | None = None,
    gnomad: Dict[str, Any] | None = None,
    gnomad_client: Any | None = None,
    skempi: bool = False,
    skempi_client: Any | None = None,
    medgen: bool = False,
    medgen_client: Any | None = None,
    disease_identity: bool = False,
    mondo_client: Any | None = None,
    europepmc: Dict[str, Any] | None = None,
    europepmc_client: Any | None = None,
    terms: str | None = None,
    skip_digestion: bool = False,
) -> Tuple[Card | None, EntityResolution]:
    """Resolve ``query`` and build the ProteinCard of the resolved entity.

    ``structures`` lists PDB ids to enrich with RCSB polymer-entity data, or ``"all"``
    for every PDB cross-reference of the entry. ``string`` (e.g. ``{}`` or
    ``{"required_score": 900, "limit": 20}``; default score 700, every partner up to
    5000) adds STRING functional associations for the entry's organism. ``chembl`` (e.g. ``{}`` or ``{"limit": 1000}``) adds the ChEMBL
    bioactivities of the targets the entry cross-references (``Card.bioactivities()``).
    ``ligand_sites`` adds the residues each ligand contacts in the protein's structures,
    from PDBe-KB (``Card.ligand_sites()``). ``interfaces`` adds the residues PDBe-KB
    reports at the protein's interfaces with other chains, per partner
    (``Card.oligomer()``). ``family_sites`` adds the site residues that
    InterPro member databases place on the protein's sequence
    (``features_positional.family_site``). ``predicted_structures`` adds the AlphaFold
    DB models of the entry as ``has_predicted_structure`` relationships, apart from
    experimental structures (``Card.predicted_structures()``). ``taxonomy`` adds the
    organism's rank and ranked ancestors from NCBI Taxonomy (``annotations.taxonomy``),
    which makes relations between organisms exact. ``bindingdb`` (e.g. ``{}``) adds the
    affinities BindingDB holds for the entry, with each monomer anchored at its InChIKey
    through UniChem; measurements several sources state are grouped, never counted
    twice (``sabueso.core.measurements``). ``pubchem_bioassay`` adds PubChem's results
    for the entry; results copied from ChEMBL or BindingDB are grouped with their
    originals, and a ChEMBL assay named by a copy but missing from the card is fetched
    from ChEMBL (#68).
    Every enrichment outcome (added, not_found, error) is recorded in
    ``quality.enrichments``. Returns ``(card, resolution)``; ``card`` is None when the
    query did not resolve to a protein entity.

    ``ncbi_gene`` lets the resolution's identity audit ask NCBI Gene about two
    candidates that state their gene in different databases: NCBI Gene lists the UniProt
    entries of a gene's products (#69).

    ``phi_base`` adds the phenotypes PHI-base curates for mutants of the gene, alone or
    on a host (``annotations.pathogen_phenotypes``). The first use downloads a PHI-base
    release into the local cache (``sabueso.tools.db.phi_base``).

    ``diseases`` (e.g. ``{}``, or ``{"channels": ["knowledge", "experiments",
    "textmining"]}``) adds DISEASES's gene–disease associations as ``associated_with``
    relationships, one per disease and channel, through the Ensembl proteins the entry
    cross-references. The default channels are curated knowledge and experiments; text
    mining links names, not molecules, and is added only when asked for. DISEASES covers
    human genes only.

    ``open_targets`` (e.g. ``{}`` or ``{"limit": 50}``; default all, up to 5000, in
    Open Targets' own order) adds Open Targets' target–disease associations, with its scores as
    stated, through the Ensembl gene the entry cross-references, when Open Targets also
    lists the entry among that gene's products. Human genes only.

    ``orphadata`` adds the rare disorders Orphanet associates with the gene, through the
    UniProt accession Orphanet states for it, with Orphanet's association type and
    status. Human genes only.

    ``reactome`` adds the Reactome pathways and reactions the entry takes part in
    (``participates_in``), with each pathway's ancestors and whether Reactome inferred
    the event from orthology.

    ``clinvar`` (e.g. ``{}`` or ``{"limit": 100}``; default all, up to 5000 per gene)
    adds ClinVar's variants of the gene, found by the NCBI Gene id the entry cross-references, with
    their classification as ClinVar states it (``annotations.clinical_variants``). A
    variant is placed in UniProt numbering only when its transcript is one UniProt states
    for the canonical isoform and its residue matches. Human genes only.

    ``gnomad`` (e.g. ``{}`` or ``{"limit": 200}``; default all, up to 5000) adds
    gnomAD's variants of the gene with a protein change, and their exome and genome frequencies
    (``annotations.population_variants``), placed in UniProt numbering by the same rule
    through an Ensembl transcript UniProt states for the canonical isoform. Human genes
    only.

    ``skempi`` adds SKEMPI 2.0's measured binding changes of mutations at the
    interfaces of complexes of this protein (``annotations.interface_mutations``), for
    the PDB entries whose chains UniProt states are this protein. A mutation is placed
    in UniProt numbering only through the author numbering RCSB states for that chain,
    so ask for the ``structures`` too, and only when its residue matches.

    ``disease_identity`` asks MONDO which of the disease ids the other sources put on
    the card are the same disease (``same_as`` to ``mondo:<term>``, only where MONDO
    states it), so that ``Card.diseases()`` can group them. It reads the diseases of
    ``diseases``, ``open_targets``, ``orphadata``, ``clinvar`` and UniProt, so ask for
    those in the same call. ``medgen`` asks MedGen which record each MedGen concept id
    naming a condition is, so that a condition ClinVar names only by a MedGen concept id
    reaches MONDO through MedGen's statement and MONDO's (``medgen_concept@1``).

    ``europepmc`` (e.g. ``{}`` or ``{"limit": 100}``; default all, up to 5000, newest
    first) adds the publications whose text states the UniProt accession, as Europe PMC
    found them by text mining (``mentioned_in``, #92). Only a stated accession counts:
    a protein named in a paper is never matched to the entry by its name.

    ``terms`` (``"commercial"`` or ``"non_commercial"``) builds the card only from
    sources whose stated terms allow that use (#94): the others are not queried, their
    records say why (``not_queried``), and ``quality["terms_profile"]`` keeps the
    profile. Sources with unknown terms (e.g. PubChem BioAssay's depositors) are
    excluded too.
    """
    if ncbi_gene:
        import copy

        from sabueso.tools.db.ncbi_gene import OnlineNCBIGeneClient

        resolver = copy.copy(resolver) if resolver is not None else EntityResolver()
        resolver.ncbi_gene = (
            ncbi_gene_client or resolver.ncbi_gene or OnlineNCBIGeneClient()
        )
    resolver = resolver or EntityResolver()
    resolution = resolver.resolve(query)
    entity_ref = resolution.entity_ref or ""
    if resolution.status != "resolved" or not entity_ref.startswith(UNIPROT_PREFIX):
        return None, resolution

    anchor = entity_ref[len(UNIPROT_PREFIX) :]
    entry, retrieved_at = resolver.uniprot.fetch_entry(anchor)
    protein_mapping = map_protein(entry, retrieved_at)
    mappings: List[Dict[str, Any]] = [protein_mapping]

    if structures == "all":
        structures = [
            rel["object_ref"].split(":", 1)[1]
            for rel in protein_mapping["relationships"]
            if rel["predicate"] == "has_structure"
        ]
    length = (entry.get("sequence") or {}).get("length")
    sequence = (entry.get("sequence") or {}).get("value")
    enrichments: List[Dict[str, Any]] = []
    profile = None
    if terms is not None:
        from sabueso.core.terms import TermsProfile

        profile = TermsProfile(terms)

    def admitted(source: str) -> bool:
        """Whether the terms profile admits a source; if not, the record says why."""
        if profile is None or profile.admits(source):
            return True
        enrichments.append(
            {
                "source": source,
                "identifier": anchor,
                "status": "not_queried",
                "detail": profile.detail(source),
            }
        )
        return False

    if structures and not admitted("RCSB PDB"):
        structures = []
    if chembl is not None and not admitted("ChEMBL"):
        chembl = None
    if bindingdb is not None and not (admitted("BindingDB") and admitted("UniChem")):
        bindingdb = None
    # ``True``, or options (``{}``, ``{"limit": n}``), asks PubChem BioAssay: None
    # when it is not asked.
    pubchem_options = (
        dict(pubchem_bioassay)
        if isinstance(pubchem_bioassay, dict)
        else ({} if pubchem_bioassay else None)
    )
    if pubchem_options is not None and not admitted("PubChem BioAssay"):
        pubchem_options = None
    for pdb_id in structures:
        record = {"source": "RCSB PDB", "structure": pdb_id}
        try:
            rcsb_entry, rcsb_retrieved_at = resolver.rcsb.fetch_structure(pdb_id)
        except RecordNotFoundError:
            enrichments.append({**record, "status": "not_found"})
            continue
        except ConnectorError as exc:
            enrichments.append({**record, "status": "error", "detail": str(exc)})
            continue
        mapped = map_structure_entities(
            rcsb_entry,
            rcsb_retrieved_at,
            subjects={anchor},
            reference_lengths={anchor: length} if length else None,
            reference_sequences={anchor: sequence} if sequence else None,
        )
        mappings.append(mapped)
        partial = rcsb_entry.get("_partial")
        enrichments.append(
            {
                **record,
                "status": "partial" if partial else "added",
                "count": len(mapped["relationships"]),
                **(
                    {
                        "missing": partial.get("missing"),
                        "detail": partial.get("reason"),
                    }
                    if partial
                    else {}
                ),
            }
        )

    # Declared enrichers (#86), run in stages among the bespoke enrichments so that
    # records keep their order.
    from sabueso.enrichers import Context, run_stage

    requested = {
        "string": (string, string_client),
        "ligand_sites": (ligand_sites, pdbe_kb_client),
        "interfaces": (interfaces, pdbe_kb_client),
        "predicted_structures": (predicted_structures, alphafold_client),
        "taxonomy": (taxonomy, taxonomy_client),
        "family_sites": (family_sites, interpro_client),
        "phi_base": (phi_base, phi_base_client),
        "diseases": (diseases, diseases_client),
        "open_targets": (open_targets, open_targets_client),
        "orphadata": (orphadata, orphadata_client),
        "reactome": (reactome, reactome_client),
        "gnomad": (gnomad, gnomad_client),
        "clinvar": (clinvar, clinvar_client),
        "skempi": (skempi, skempi_client),
        "medgen": (medgen, medgen_client),
        "disease_identity": (disease_identity, mondo_client),
        "europepmc": (europepmc, europepmc_client),
    }
    if profile is not None:
        from sabueso.enrichers import ENRICHERS

        for enricher in ENRICHERS:
            options, client = requested.get(enricher.option, (None, None))
            if enricher.requested(options) and not admitted(enricher.source):
                requested[enricher.option] = (None, client)
    context = Context(anchor, entry, mappings)
    run_stage("after_structures", context, requested, mappings, enrichments)

    if chembl is not None:
        from sabueso.tools.db.chembl import OnlineChEMBLClient

        client = chembl_client or OnlineChEMBLClient()
        targets = [
            x["id"]
            for x in entry.get("uniProtKBCrossReferences", [])
            if x.get("database") == "ChEMBL"
        ]
        if not targets:
            enrichments.append(
                {
                    "source": "ChEMBL",
                    "status": "not_found",
                    "detail": "no ChEMBL cross-reference in the UniProt entry",
                }
            )
        for target in targets:
            record = {"source": "ChEMBL", "target": target, **chembl}
            try:
                response = client.bioactivities(target, **chembl)
            except RecordNotFoundError:
                enrichments.append({**record, "status": "not_found"})
                continue
            except ConnectorError as exc:
                enrichments.append({**record, "status": "error", "detail": str(exc)})
                continue
            mapped = map_bioactivities(
                response, anchor, response.get("retrieved_at", "")
            )
            mappings.append(mapped)
            enrichments.append(
                {
                    **record,
                    "status": "added",
                    "version": response.get("version"),
                    "count": len(mapped["relationships"]),
                    "total_count": response.get("total_count"),
                    "truncated": response.get("truncated"),
                }
            )

    run_stage("after_chembl", context, requested, mappings, enrichments)

    identities: List[tuple] = []
    if bindingdb is not None:
        from sabueso.mappings.bindingdb import map_affinities, molecule_identity
        from sabueso.tools.db.bindingdb import OnlineBindingDBClient
        from sabueso.tools.db.unichem import BINDINGDB_SOURCE, OnlineUniChemClient

        client = bindingdb_client or OnlineBindingDBClient()
        record = {"source": "BindingDB", "identifier": anchor, **bindingdb}
        try:
            response = client.ligands(anchor, **bindingdb)
        except RecordNotFoundError:
            enrichments.append({**record, "status": "not_found"})
        except ConnectorError as exc:
            enrichments.append({**record, "status": "error", "detail": str(exc)})
        else:
            from sabueso.tools.db._http import gather

            unichem = unichem_client or OnlineUniChemClient()
            resolved: Dict[str, Any] = {}
            unanchored, errors = [], []
            # One UniChem lookup per monomer, a few at once and politely paced (#98).
            monomers = sorted({str(r.get("monomerid")) for r in response["record"]})
            for monomer, found in gather(
                lambda m: unichem.compound_by_source(BINDINGDB_SOURCE, m),
                monomers,
                # The online client states its pace; saved answers need none.
                workers=getattr(unichem, "workers", 1),
                per_second=getattr(unichem, "per_second", None),
                expected=(RecordNotFoundError, ConnectorError),
            ):
                if isinstance(found, RecordNotFoundError):
                    resolved[monomer] = None
                    unanchored.append(f"bindingdb:{monomer}")
                elif isinstance(found, ConnectorError):
                    resolved[monomer] = None
                    errors.append(f"bindingdb:{monomer}")
                else:
                    resolved[monomer] = molecule_identity(found["compound"], monomer)
            mapped = map_affinities(
                response, anchor, response.get("retrieved_at", ""), resolved
            )
            mappings.append(mapped)
            identities += [
                (i["anchor"], i["records"]) for i in resolved.values() if i is not None
            ]
            enrichments.append(
                {
                    **record,
                    "status": "added",
                    "count": len(mapped["relationships"]),
                    # Records BindingDB returned, and the rule that chose which to
                    # keep (#88, #98).
                    "total_count": response.get("total_count"),
                    "truncated": (response.get("total_count") or 0)
                    > len(response["record"]),
                    "record_order": response.get("record_order"),
                    "anchored": sum(1 for i in resolved.values() if i is not None),
                    "unanchored": unanchored,
                    **({"unichem_errors": errors} if errors else {}),
                }
            )

    if pubchem_options is not None:
        from sabueso.mappings.chembl import map_bioactivities as map_chembl
        from sabueso.mappings.pubchem_bioassay import map_assays
        from sabueso.tools.db.chembl import OnlineChEMBLClient
        from sabueso.tools.db.pubchem_bioassay import DEFAULT_LIMIT as PUBCHEM_LIMIT
        from sabueso.tools.db.pubchem_bioassay import OnlinePubChemBioAssayClient

        client = pubchem_bioassay_client or OnlinePubChemBioAssayClient()
        record = {"source": "PubChem BioAssay", "identifier": anchor, **pubchem_options}
        try:
            response = client.assays(
                anchor, pubchem_options.get("limit", PUBCHEM_LIMIT)
            )
        except RecordNotFoundError:
            enrichments.append({**record, "status": "not_found"})
        except ConnectorError as exc:
            enrichments.append({**record, "status": "error", "detail": str(exc)})
        else:
            mapped = map_assays(response, anchor, response.get("retrieved_at", ""))
            excluded_by_profile = 0
            if profile is not None:
                # Each result keeps its depositor's terms (#94): keep those the profile
                # admits, and count the others.
                kept, dropped = [], set()
                for rel in mapped["relationships"]:
                    depositor = ((rel.get("qualifiers") or {}).get("assay") or {}).get(
                        "depositor"
                    )
                    if profile.admits_record("PubChem BioAssay", depositor):
                        kept.append(rel)
                    else:
                        dropped.update(rel.get("source_assertion_ids") or [])
                excluded_by_profile = len(mapped["relationships"]) - len(kept)
                mapped = {
                    **mapped,
                    "relationships": kept,
                    "source_assertions": [
                        sa
                        for sa in mapped["source_assertions"]
                        if sa["id"] not in dropped
                    ],
                }
            mappings.append(mapped)
            depositors: Dict[str, int] = {}
            for s_ in response["record"].get("summaries") or []:
                depositors[s_.get("SourceName")] = (
                    depositors.get(s_.get("SourceName"), 0) + 1
                )
            copies = [
                r
                for r in mapped["relationships"]
                if (r.get("qualifiers") or {}).get("copy_of")
            ]
            enrichments.append(
                {
                    **record,
                    "status": "added",
                    "assays": len(response["record"].get("aids") or []),
                    "count": len(mapped["relationships"]),
                    # Rows of the protein PubChem states, and the rule that chose
                    # which to keep (#88, #98).
                    "total_count": response["record"].get("total_rows"),
                    "truncated": response["record"].get("total_rows", 0)
                    > response["record"].get("rows", 0),
                    "row_order": response["record"].get("row_order"),
                    "copies": len(copies),
                    "depositors": dict(sorted(depositors.items())),
                    **(
                        {"excluded_by_terms_profile": excluded_by_profile}
                        if excluded_by_profile
                        else {}
                    ),
                }
            )
            # Copies are pointers: ChEMBL assays they name that the card lacks. An assay
            # on the card is complete only if the target query was not truncated.
            chembl_rels = [
                rel
                for m in mappings
                for rel in m["relationships"]
                if rel["predicate"] == "has_bioactivity"
                and not (rel.get("qualifiers") or {}).get("source")
            ]
            present = {
                (rel.get("qualifiers") or {}).get("activity_id") for rel in chembl_rels
            }
            truncated = any(
                e.get("source") == "ChEMBL" and e.get("truncated") for e in enrichments
            )
            on_card = (
                set()
                if truncated
                else {
                    (rel.get("qualifiers") or {}).get("assay", {}).get("id")
                    for rel in chembl_rels
                }
            )
            named = sorted(
                {
                    r["qualifiers"]["copy_of"]["assay"]
                    for r in copies
                    if r["qualifiers"]["copy_of"].get("source") == "ChEMBL"
                    and r["qualifiers"]["copy_of"].get("assay")
                }
                - on_card
            )
            if named:
                pointer = {
                    "source": "ChEMBL",
                    "data": "assays named by PubChem copies",
                    "assays": named,
                }
                try:
                    followed = (chembl_client or OnlineChEMBLClient()).assay_activities(
                        named
                    )
                except ConnectorError as exc:
                    enrichments.append(
                        {**pointer, "status": "error", "detail": str(exc)}
                    )
                else:
                    followed = {
                        **followed,
                        "activities": [
                            a
                            for a in followed.get("activities") or []
                            if a.get("activity_id") not in present
                        ],
                    }
                    extra = map_chembl(
                        followed, anchor, followed.get("retrieved_at", "")
                    )
                    targets = sorted(
                        {
                            (rel.get("qualifiers") or {}).get("target")
                            for rel in extra["relationships"]
                        }
                        - {None}
                    )
                    for rel in extra["relationships"]:
                        rel["qualifiers"]["retrieved_via"] = "PubChem BioAssay copy"
                    mappings.append(extra)
                    enrichments.append(
                        {
                            **pointer,
                            "status": "added"
                            if extra["relationships"]
                            else "not_found",
                            "version": followed.get("version"),
                            "count": len(extra["relationships"]),
                            "targets": targets,
                        }
                    )

    if bindingdb is not None or pubchem_options is not None:
        # ChEMBL's molecules anchored at the InChIKey ChEMBL states for them, so that the
        # same molecule is recognised across sources (#66, #68).
        from sabueso.tools.db.chembl import OnlineChEMBLClient

        chembl_ids = {
            ref.split(":", 1)[1]
            for m in mappings
            for rel in m["relationships"]
            if rel["predicate"] == "has_bioactivity"
            and not (rel.get("qualifiers") or {}).get("source")
            for ref in (
                rel["object_ref"],
                (rel.get("qualifiers") or {}).get("parent_molecule"),
            )
            if ref and ref.startswith("chembl:")
        }
        if chembl_ids:
            try:
                found = (chembl_client or OnlineChEMBLClient()).molecules(chembl_ids)
            except ConnectorError:
                found = {"molecules": {}}
            for chembl_id, molecule in sorted((found.get("molecules") or {}).items()):
                key = ((molecule or {}).get("molecule_structures") or {}).get(
                    "standard_inchi_key"
                )
                if key:
                    identities.append((f"inchikey:{key}", [f"chembl:{chembl_id}"]))
        # PubChem compounds, at the InChIKey PubChem states (in the mapping).
        for m in mappings:
            for rel in m["relationships"]:
                q = rel.get("qualifiers") or {}
                if q.get("source") == "PubChem BioAssay" and q.get("molecule_ref"):
                    identities.append((q["molecule_ref"], [rel["object_ref"]]))

    run_stage("after_bioactivity", context, requested, mappings, enrichments)

    mappings.append(
        {
            "fields": {},
            "source_assertions": list(resolution.source_assertions),
            "field_source_assertions": {},
            "relationships": list(resolution.identity_links),
        }
    )
    subjects = {f"uniprot:{anchor}"} | {
        link["subject_ref"]
        for link in resolution.identity_links
        if link["predicate"] == "same_as" and link["object_ref"] == f"uniprot:{anchor}"
    }
    card = build_card_from_mapping(
        merge_mapping_results(mappings),
        meta={"entity_type": "protein"},
        card_id=entity_ref,
        entity_subjects=subjects,
    )
    for anchor_ref, records in identities:
        # Stated by UniChem, which links the BindingDB monomer to the anchor (#66).
        card.register_identity(anchor_ref, records, "small_molecule", {"by": "UniChem"})
    if enrichments:
        card.quality["enrichments"] = enrichments
        report_outcomes(enrichments, subject=entity_ref)
    if profile is not None:
        card.quality["terms_profile"] = profile.record()
    card.quality["entity_resolution"] = {
        "status": resolution.status,
        "entity_ref": resolution.entity_ref,
        "qualifiers": resolution.qualifiers,
        "policy": resolution.policy,
        "alternatives": resolution.alternatives,
        "decision": resolution.decision,
    }
    return card, resolution


def _candidate_card(
    candidate: Dict[str, Any], resolution: EntityResolution, retrieved_at: str
) -> Card:
    basis = candidate["basis"]
    accession = basis["accession"]
    mapping: Dict[str, Any] = {
        "fields": {},
        "source_assertions": [],
        "field_source_assertions": {},
    }
    for fp, value in (
        ("identifiers.uniprot", accession),
        ("annotations.organism", basis.get("organism_name")),
        ("sequence.length", basis.get("length")),
    ):
        if value is None:
            continue
        assertion = make_source_assertion(fp, value, "UniProt", accession, retrieved_at)
        mapping["fields"][fp] = value
        mapping["source_assertions"].append(assertion)
        mapping["field_source_assertions"][fp] = [assertion["id"]]
    card = build_card_from_mapping(
        mapping,
        meta={"entity_type": "protein"},
        card_id=candidate["entity_ref"],
        entity_subjects={f"uniprot:{accession}"},
    )
    card.quality["entity_resolution"] = {
        "status": "candidate",
        "basis": basis,
        "query": resolution.decision.get("query"),
        "rules": resolution.decision.get("rules"),
    }
    return card


@arg_digest()
def ambiguity_deck(resolution: EntityResolution, skip_digestion: bool = False) -> Deck:
    """Deck of candidate cards: the candidates of an ambiguous resolution, or the
    non-preferred alternatives of a resolved one. Nothing is fetched again."""
    items = resolution.candidates if resolution.status == "ambiguous" else []
    items = items or resolution.alternatives
    retrieved = next(
        (
            s["retrieved_at"]
            for s in resolution.decision.get("sources", [])
            if s.get("retrieved_at")
        ),
        "",
    )
    cards = [_candidate_card(c, resolution, retrieved) for c in items]
    role = "candidate" if resolution.status == "ambiguous" else "alternative"
    return Deck(
        cards,
        meta={
            "kind": "entity_ambiguity"
            if resolution.status == "ambiguous"
            else "entity_alternatives",
            "status": resolution.status,
            "entity_ref": resolution.entity_ref,
            "policy": resolution.policy,
            "decision": resolution.decision,
            # Why each card is here (#58): the query it answered, and its role.
            "membership": {
                card.id: {"role": role, "query": resolution.decision.get("query")}
                for card in cards
            },
        },
    )
