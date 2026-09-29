"""PDBe-KB: ligand sites (``has_ligand_site``) and interface residues
(``has_interface_with``), two enrichers of one service."""

from __future__ import annotations

from sabueso.enrichers import Enricher


class _PDBeKB(Enricher):
    source = "PDBe-KB"
    registry_id = "pdbe_kb"
    client_option = "pdbe_kb_client"
    stage = "after_chembl"
    not_found_detail = False
    data: str

    @property
    def match(self):
        return {"source": self.source, "data": self.data}

    def client(self):
        from sabueso.tools.db.pdbe_kb import OnlinePDBeKBClient

        return OnlinePDBeKBClient()

    def record(self, context, options):
        return {"source": self.source, "data": self.data, "identifier": context.anchor}

    def map(self, context, request, response, options):
        mapped = self._map(response, response.get("retrieved_at", ""))
        return mapped, {"status": "added", "count": len(mapped["relationships"])}


class LigandSites(_PDBeKB):
    option = "ligand_sites"
    data = "ligand_sites"
    areas = ("relationships.has_ligand_site",)

    def fetch(self, client, request, options):
        return client.ligand_sites(request.identifier)

    def _map(self, response, retrieved_at):
        from sabueso.mappings.pdbe_kb import map_ligand_sites

        return map_ligand_sites(response, retrieved_at)


class Interfaces(_PDBeKB):
    option = "interfaces"
    data = "interface_residues"
    areas = ("relationships.has_interface_with",)

    def fetch(self, client, request, options):
        return client.interface_residues(request.identifier)

    def _map(self, response, retrieved_at):
        from sabueso.mappings.pdbe_kb import map_interfaces

        return map_interfaces(response, retrieved_at)


LIGAND_SITES = LigandSites()
INTERFACES = Interfaces()
