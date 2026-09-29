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
from sabueso.mappings.interpro import map_family_sites
from sabueso.mappings.pdbe_kb import map_interfaces, map_ligand_sites
from sabueso.mappings.rcsb_structures import map_structure_entities
from sabueso.mappings.stringdb import map_string_partners
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
    pubchem_bioassay: bool = False,
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
    skip_digestion: bool = False,
) -> Tuple[Card | None, EntityResolution]:
    """Resolve ``query`` and build the ProteinCard of the resolved entity.

    ``structures`` lists PDB ids to enrich with RCSB polymer-entity data, or ``"all"``
    for every PDB cross-reference of the entry. ``string`` (e.g. ``{}`` or
    ``{"required_score": 900, "limit": 20}``) adds STRING functional associations for the
    entry's organism. ``chembl`` (e.g. ``{}`` or ``{"limit": 1000}``) adds the ChEMBL
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

    ``open_targets`` (e.g. ``{}`` or ``{"limit": 50}``; default 100, in Open Targets'
    own order) adds Open Targets' target–disease associations, with its scores as
    stated, through the Ensembl gene the entry cross-references, when Open Targets also
    lists the entry among that gene's products. Human genes only.

    ``orphadata`` adds the rare disorders Orphanet associates with the gene, through the
    UniProt accession Orphanet states for it, with Orphanet's association type and
    status. Human genes only.

    ``reactome`` adds the Reactome pathways and reactions the entry takes part in
    (``participates_in``), with each pathway's ancestors and whether Reactome inferred
    the event from orthology.

    ``clinvar`` (e.g. ``{}`` or ``{"limit": 100}``; default 500 per gene) adds ClinVar's
    variants of the gene, found by the NCBI Gene id the entry cross-references, with
    their classification as ClinVar states it (``annotations.clinical_variants``). A
    variant is placed in UniProt numbering only when its transcript is one UniProt states
    for the canonical isoform and its residue matches. Human genes only.

    ``gnomad`` (e.g. ``{}`` or ``{"limit": 200}``; default 1000) adds gnomAD's variants of
    the gene with a protein change, and their exome and genome frequencies
    (``annotations.population_variants``), placed in UniProt numbering by the same rule
    through an Ensembl transcript UniProt states for the canonical isoform. Human genes
    only.
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

    if string is not None:
        from sabueso.tools.db.stringdb import OnlineStringClient

        client = string_client or OnlineStringClient()
        species = (entry.get("organism") or {}).get("taxonId")
        record = {
            "source": "STRING",
            "identifier": anchor,
            "species": species,
            **string,
        }
        try:
            response = client.partners(anchor, species, **string)
        except RecordNotFoundError:
            enrichments.append({**record, "status": "not_found"})
        except ConnectorError as exc:
            enrichments.append({**record, "status": "error", "detail": str(exc)})
        else:
            mapped = map_string_partners(
                response, anchor, response.get("retrieved_at", "")
            )
            mappings.append(mapped)
            enrichments.append(
                {
                    **record,
                    "required_score": response.get("query", {}).get("required_score"),
                    "limit": response.get("query", {}).get("limit"),
                    "status": "added",
                    "version": response.get("version"),
                    "count": len(mapped["relationships"]),
                }
            )

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

    if ligand_sites:
        from sabueso.tools.db.pdbe_kb import OnlinePDBeKBClient

        client = pdbe_kb_client or OnlinePDBeKBClient()
        record = {"source": "PDBe-KB", "data": "ligand_sites", "identifier": anchor}
        try:
            response = client.ligand_sites(anchor)
        except RecordNotFoundError:
            enrichments.append({**record, "status": "not_found"})
        except ConnectorError as exc:
            enrichments.append({**record, "status": "error", "detail": str(exc)})
        else:
            mapped = map_ligand_sites(response, response.get("retrieved_at", ""))
            mappings.append(mapped)
            enrichments.append(
                {**record, "status": "added", "count": len(mapped["relationships"])}
            )

    if interfaces:
        from sabueso.tools.db.pdbe_kb import OnlinePDBeKBClient

        client = pdbe_kb_client or OnlinePDBeKBClient()
        record = {
            "source": "PDBe-KB",
            "data": "interface_residues",
            "identifier": anchor,
        }
        try:
            response = client.interface_residues(anchor)
        except RecordNotFoundError:
            enrichments.append({**record, "status": "not_found"})
        except ConnectorError as exc:
            enrichments.append({**record, "status": "error", "detail": str(exc)})
        else:
            mapped = map_interfaces(response, response.get("retrieved_at", ""))
            mappings.append(mapped)
            enrichments.append(
                {**record, "status": "added", "count": len(mapped["relationships"])}
            )

    if predicted_structures:
        from sabueso.mappings.alphafold import map_predictions
        from sabueso.tools.db.alphafold import OnlineAlphaFoldClient

        client = alphafold_client or OnlineAlphaFoldClient()
        record = {"source": "AlphaFold DB", "identifier": anchor}
        try:
            response = client.prediction(anchor)
        except RecordNotFoundError:
            enrichments.append({**record, "status": "not_found"})
        except ConnectorError as exc:
            enrichments.append({**record, "status": "error", "detail": str(exc)})
        else:
            mapped = map_predictions(
                response,
                anchor,
                response.get("retrieved_at", ""),
                sequence_md5=(entry.get("sequence") or {}).get("md5"),
            )
            mappings.append(mapped)
            versions = sorted(
                {r["qualifiers"]["model_version"] for r in mapped["relationships"]}
                - {None}
            )
            enrichments.append(
                {
                    **record,
                    "status": "added",
                    "version": "; ".join(f"v{v}" for v in versions) or None,
                    "count": len(mapped["relationships"]),
                }
            )

    if taxonomy:
        from sabueso.mappings.ncbi_taxonomy import map_taxonomy
        from sabueso.tools.db.ncbi_taxonomy import OnlineNCBITaxonomyClient

        client = taxonomy_client or OnlineNCBITaxonomyClient()
        tax_id = (entry.get("organism") or {}).get("taxonId")
        record = {"source": "NCBI Taxonomy", "identifier": tax_id}
        try:
            organism = client.taxa([tax_id]) if tax_id is not None else {"record": []}
            if not organism["record"]:
                enrichments.append({**record, "status": "not_found"})
            else:
                taxon = organism["record"][0]
                lineage = client.taxa(taxon.get("lineage") or [])
                mapped = map_taxonomy(
                    taxon,
                    lineage["record"],
                    anchor,
                    organism.get("retrieved_at", ""),
                )
                mappings.append(mapped)
                enrichments.append(
                    {
                        **record,
                        "status": "added",
                        "count": len(taxon.get("lineage") or []),
                        **(
                            {"missing": lineage["missing"]}
                            if lineage.get("missing")
                            else {}
                        ),
                    }
                )
        except ConnectorError as exc:
            enrichments.append({**record, "status": "error", "detail": str(exc)})

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
            unichem = unichem_client or OnlineUniChemClient()
            resolved: Dict[str, Any] = {}
            unanchored, errors = [], []
            for monomer in sorted(
                {str(r.get("monomerid")) for r in response["record"]}
            ):
                try:
                    found = unichem.compound_by_source(BINDINGDB_SOURCE, monomer)
                    resolved[monomer] = molecule_identity(found["compound"], monomer)
                except RecordNotFoundError:
                    resolved[monomer] = None
                    unanchored.append(f"bindingdb:{monomer}")
                except ConnectorError:
                    resolved[monomer] = None
                    errors.append(f"bindingdb:{monomer}")
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
                    "anchored": sum(1 for i in resolved.values() if i is not None),
                    "unanchored": unanchored,
                    **({"unichem_errors": errors} if errors else {}),
                }
            )

    if pubchem_bioassay:
        from sabueso.mappings.chembl import map_bioactivities as map_chembl
        from sabueso.mappings.pubchem_bioassay import map_assays
        from sabueso.tools.db.chembl import OnlineChEMBLClient
        from sabueso.tools.db.pubchem_bioassay import OnlinePubChemBioAssayClient

        client = pubchem_bioassay_client or OnlinePubChemBioAssayClient()
        record = {"source": "PubChem BioAssay", "identifier": anchor}
        try:
            response = client.assays(anchor)
        except RecordNotFoundError:
            enrichments.append({**record, "status": "not_found"})
        except ConnectorError as exc:
            enrichments.append({**record, "status": "error", "detail": str(exc)})
        else:
            mapped = map_assays(response, anchor, response.get("retrieved_at", ""))
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
                    "copies": len(copies),
                    "depositors": dict(sorted(depositors.items())),
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

    if bindingdb is not None or pubchem_bioassay:
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

    if family_sites:
        from sabueso.tools.db.interpro import OnlineInterProClient

        client = interpro_client or OnlineInterProClient()
        record = {"source": "InterPro", "identifier": anchor}
        try:
            response = client.site_residues(anchor)
        except RecordNotFoundError as exc:
            enrichments.append({**record, "status": "not_found", "detail": str(exc)})
        except ConnectorError as exc:
            enrichments.append({**record, "status": "error", "detail": str(exc)})
        else:
            mapped = map_family_sites(response, response.get("retrieved_at", ""))
            mappings.append(mapped)
            enrichments.append(
                {
                    **record,
                    "status": "added",
                    "version": response.get("version"),
                    "count": len(mapped["source_assertions"]),
                }
            )

    if phi_base:
        from sabueso.mappings.phi_base import map_phenotypes
        from sabueso.tools.db.phi_base import OnlinePHIBaseClient

        client = phi_base_client or OnlinePHIBaseClient()
        record = {"source": "PHI-base", "identifier": anchor}
        try:
            response = client.phenotypes(anchor)
        except RecordNotFoundError as exc:
            enrichments.append({**record, "status": "not_found", "detail": str(exc)})
        except ConnectorError as exc:
            enrichments.append({**record, "status": "error", "detail": str(exc)})
        else:
            mapped = map_phenotypes(
                response["sessions"],
                anchor,
                response.get("retrieved_at", ""),
                response.get("version"),
            )
            mappings.append(mapped)
            enrichments.append(
                {
                    **record,
                    "status": "added",
                    "version": response.get("version"),
                    "count": len(mapped["source_assertions"]),
                }
            )

    if diseases is not None:
        from sabueso.mappings.diseases import map_associations
        from sabueso.tools.db.diseases import OnlineDISEASESClient

        channels = tuple(diseases.get("channels") or ("knowledge", "experiments"))
        record = {"source": "DISEASES", "identifier": anchor, "channels": channels}
        isoform_of = {
            prop["value"].split(".")[0]: xref.get("isoformId")
            for xref in entry.get("uniProtKBCrossReferences") or []
            if xref.get("database") == "Ensembl"
            for prop in xref.get("properties") or []
            if prop.get("key") == "ProteinId" and prop.get("value")
        }
        taxon = (entry.get("organism") or {}).get("taxonId")
        if taxon != 9606:
            enrichments.append(
                {
                    **record,
                    "status": "not_applicable",
                    "detail": "DISEASES covers Homo sapiens genes only",
                }
            )
        elif not isoform_of:
            enrichments.append(
                {
                    **record,
                    "status": "not_found",
                    "detail": "the entry cross-references no Ensembl protein",
                }
            )
        else:
            client = diseases_client or OnlineDISEASESClient()
            try:
                response = client.associations(sorted(isoform_of), channels)
            except ConnectorError as exc:
                enrichments.append({**record, "status": "error", "detail": str(exc)})
            else:
                mapped = map_associations(
                    response["record"],
                    anchor,
                    isoform_of,
                    response.get("retrieved_at", ""),
                    response.get("version") or {},
                )
                mappings.append({"fields": {}, "field_source_assertions": {}, **mapped})
                enrichments.append(
                    {
                        **record,
                        "status": "added" if mapped["relationships"] else "not_found",
                        "version": "; ".join(
                            f"{c} {v}"
                            for c, v in sorted((response.get("version") or {}).items())
                            if v
                        )
                        or None,
                        "count": len(mapped["relationships"]),
                    }
                )

    if open_targets is not None:
        from sabueso.mappings.open_targets import lists_protein
        from sabueso.mappings.open_targets import (
            map_associations as map_open_targets,
        )
        from sabueso.tools.db.open_targets import (
            DEFAULT_LIMIT,
            OnlineOpenTargetsClient,
        )

        genes = sorted(
            {
                prop["value"].split(".")[0]
                for xref in entry.get("uniProtKBCrossReferences") or []
                if xref.get("database") == "Ensembl"
                for prop in xref.get("properties") or []
                if prop.get("key") == "GeneId" and prop.get("value")
            }
        )
        limit = open_targets.get("limit", DEFAULT_LIMIT)
        taxon = (entry.get("organism") or {}).get("taxonId")
        if taxon != 9606:
            enrichments.append(
                {
                    "source": "Open Targets",
                    "identifier": anchor,
                    "status": "not_applicable",
                    "detail": "Open Targets covers Homo sapiens genes only",
                }
            )
        elif not genes:
            enrichments.append(
                {
                    "source": "Open Targets",
                    "identifier": anchor,
                    "status": "not_found",
                    "detail": "the entry cross-references no Ensembl gene",
                }
            )
        client = open_targets_client or OnlineOpenTargetsClient()
        for gene in genes if taxon == 9606 else []:
            record = {"source": "Open Targets", "identifier": gene}
            try:
                response = client.associations(gene, limit)
            except RecordNotFoundError as exc:
                enrichments.append(
                    {**record, "status": "not_found", "detail": str(exc)}
                )
                continue
            except ConnectorError as exc:
                enrichments.append({**record, "status": "error", "detail": str(exc)})
                continue
            target = response["record"]["target"]
            if not lists_protein(target, anchor):
                enrichments.append(
                    {
                        **record,
                        "status": "not_found",
                        "detail": f"Open Targets does not list {anchor} among "
                        f"{gene}'s products",
                    }
                )
                continue
            mapped = map_open_targets(
                response["record"],
                anchor,
                response.get("retrieved_at", ""),
                response.get("version"),
            )
            mappings.append({"fields": {}, "field_source_assertions": {}, **mapped})
            count = response["record"].get("count") or 0
            enrichments.append(
                {
                    **record,
                    "status": "added" if mapped["relationships"] else "not_found",
                    "version": response.get("version"),
                    "count": len(mapped["relationships"]),
                    "truncated": count > len(response["record"]["rows"]),
                    "total_count": count,
                }
            )

    if orphadata:
        from sabueso.mappings.orphadata import map_associations as map_orphadata
        from sabueso.tools.db.orphadata import OnlineOrphadataClient

        record = {"source": "Orphanet", "identifier": anchor}
        if (entry.get("organism") or {}).get("taxonId") != 9606:
            enrichments.append(
                {
                    **record,
                    "status": "not_applicable",
                    "detail": "Orphanet covers Homo sapiens genes only",
                }
            )
        else:
            client = orphadata_client or OnlineOrphadataClient()
            try:
                response = client.associations(anchor)
            except RecordNotFoundError as exc:
                enrichments.append(
                    {**record, "status": "not_found", "detail": str(exc)}
                )
            except ConnectorError as exc:
                enrichments.append({**record, "status": "error", "detail": str(exc)})
            else:
                mapped = map_orphadata(
                    response["record"],
                    anchor,
                    response.get("retrieved_at", ""),
                    response.get("version"),
                )
                mappings.append({"fields": {}, "field_source_assertions": {}, **mapped})
                enrichments.append(
                    {
                        **record,
                        "status": "added",
                        "version": response.get("version"),
                        "count": len(mapped["relationships"]),
                    }
                )

    if reactome:
        from sabueso.mappings.reactome import map_pathways
        from sabueso.tools.db.reactome import OnlineReactomeClient

        record = {"source": "Reactome", "identifier": anchor}
        try:
            response = (reactome_client or OnlineReactomeClient()).pathways(anchor)
        except RecordNotFoundError as exc:
            enrichments.append({**record, "status": "not_found", "detail": str(exc)})
        except ConnectorError as exc:
            enrichments.append({**record, "status": "error", "detail": str(exc)})
        else:
            mapped = map_pathways(
                response["record"],
                anchor,
                response.get("retrieved_at", ""),
                response.get("version"),
            )
            mappings.append({"fields": {}, "field_source_assertions": {}, **mapped})
            enrichments.append(
                {
                    **record,
                    "status": "added",
                    "version": response.get("version"),
                    "count": len(mapped["relationships"]),
                }
            )

    if gnomad is not None or clinvar is not None:
        from sabueso.mappings._hgvs import transcript_context

        # Transcripts, isoforms and their position maps, as the entry states them.
        context = transcript_context(entry)
    if gnomad is not None:
        from sabueso.mappings.gnomad import map_variants as map_gnomad
        from sabueso.tools.db.gnomad import OnlineGnomADClient

        xrefs = entry.get("uniProtKBCrossReferences") or []
        ensembl = [x for x in xrefs if x.get("database") == "Ensembl"]
        genes = sorted(
            {
                p["value"].split(".")[0]
                for x in ensembl
                for p in x.get("properties") or []
                if p.get("key") == "GeneId" and p.get("value")
            }
        )
        limit = gnomad.get("limit", 1000)
        if (entry.get("organism") or {}).get("taxonId") != 9606:
            enrichments.append(
                {
                    "source": "gnomAD",
                    "identifier": anchor,
                    "status": "not_applicable",
                    "detail": "gnomAD covers human variants only",
                }
            )
        elif not genes:
            enrichments.append(
                {
                    "source": "gnomAD",
                    "identifier": anchor,
                    "status": "not_found",
                    "detail": "the entry cross-references no Ensembl gene",
                }
            )
        for gene in (
            genes if (entry.get("organism") or {}).get("taxonId") == 9606 else []
        ):
            record = {"source": "gnomAD", "identifier": gene}
            try:
                response = (gnomad_client or OnlineGnomADClient()).variants(gene)
            except RecordNotFoundError as exc:
                enrichments.append(
                    {**record, "status": "not_found", "detail": str(exc)}
                )
                continue
            except ConnectorError as exc:
                enrichments.append({**record, "status": "error", "detail": str(exc)})
                continue
            variants = response["record"]["variants"]
            coding = [v for v in variants if v.get("hgvsp")]
            mapped = map_gnomad(
                coding[:limit],
                anchor,
                context,
                response.get("retrieved_at", ""),
                response.get("version"),
            )
            mappings.append(mapped)
            enrichments.append(
                {
                    **record,
                    "status": "added" if coding else "not_found",
                    "version": response.get("version"),
                    "count": len(mapped["source_assertions"]),
                    "without_protein_change": len(variants) - len(coding),
                    "truncated": len(coding) > limit,
                    "total_count": len(coding),
                }
            )

    if clinvar is not None:
        from sabueso.mappings.clinvar import map_variants
        from sabueso.tools.db.clinvar import DEFAULT_LIMIT as CLINVAR_LIMIT
        from sabueso.tools.db.clinvar import OnlineClinVarClient

        xrefs = entry.get("uniProtKBCrossReferences") or []
        genes = sorted({x["id"] for x in xrefs if x.get("database") == "GeneID"})
        record = {"source": "ClinVar", "identifier": anchor, "genes": genes}
        if (entry.get("organism") or {}).get("taxonId") != 9606:
            enrichments.append(
                {
                    **record,
                    "status": "not_applicable",
                    "detail": "ClinVar covers human variants only",
                }
            )
        elif not genes:
            enrichments.append(
                {
                    **record,
                    "status": "not_found",
                    "detail": "the entry cross-references no NCBI Gene id",
                }
            )
        else:
            client = clinvar_client or OnlineClinVarClient()
            try:
                response = client.variants(genes, clinvar.get("limit", CLINVAR_LIMIT))
            except ConnectorError as exc:
                enrichments.append({**record, "status": "error", "detail": str(exc)})
            else:
                mapped = map_variants(
                    response["record"],
                    anchor,
                    context,
                    response.get("retrieved_at", ""),
                    response.get("version"),
                )
                mappings.append(mapped)
                enrichments.append(
                    {
                        **record,
                        "status": "added" if response["record"] else "not_found",
                        "version": response.get("version"),
                        "count": len(response["record"]),
                        "truncated": response.get("truncated", False),
                        "total_count": response.get("total_count"),
                    }
                )

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
