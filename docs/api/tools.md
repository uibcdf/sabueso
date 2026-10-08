# Tools API

## Development source metadata and annotation access

```{eval-rst}

.. automodule:: sabueso.tools.db.fda_orphan
   :members: get_page, OnlineFDAOrphanClient, FixtureFDAOrphanClient, SnapshotFDAOrphanClient

.. automodule:: sabueso.tools.db.ttd
   :members: get_target_listing, OnlineTTDClient, FixtureTTDClient, SnapshotTTDClient

.. automodule:: sabueso.tools.db.iptmnet
   :members: get_substrate_report, OnlineIPTMnetClient, FixtureIPTMnetClient, SnapshotIPTMnetClient

.. automodule:: sabueso.tools.db.brenda
   :members: get_enzyme_class, OnlineBrendaClient, FixtureBrendaClient, SnapshotBrendaClient

.. automodule:: sabueso.tools.db.pharos
   :members: get_target, OnlinePharosClient, FixturePharosClient, SnapshotPharosClient

.. automodule:: sabueso.tools.db.depmap
   :members: get_model, OnlineDepMapClient, FixtureDepMapClient, SnapshotDepMapClient


.. automodule:: sabueso.tools.db.interactome3d
   :members: get_protein_structures, OnlineInteractome3DClient, FixtureInteractome3DClient, SnapshotInteractome3DClient

.. automodule:: sabueso.tools.db.probis
   :members: get_chain_catalog, OnlineProBiSClient, FixtureProBiSClient, SnapshotProBiSClient

.. automodule:: sabueso.tools.db.pdbtm
   :members: get_topology, OnlinePDBTMClient, FixturePDBTMClient, SnapshotPDBTMClient

.. automodule:: sabueso.tools.db.threedid
   :members: get_motif_interactions, OnlineThreeDIDClient, FixtureThreeDIDClient, SnapshotThreeDIDClient


.. automodule:: sabueso.tools.db.hpo
   :members: get_gene_annotations, OnlineHPOClient, FixtureHPOClient, SnapshotHPOClient

.. automodule:: sabueso.tools.db.merops
   :members: get_assignments, OnlineMEROPSClient, FixtureMEROPSClient, SnapshotMEROPSClient

.. automodule:: sabueso.tools.db.metalpdb
   :members: get_site, OnlineMetalPDBClient, FixtureMetalPDBClient, SnapshotMetalPDBClient

.. automodule:: sabueso.tools.db.ecod
   :members: get_domain, OnlineECODClient, FixtureECODClient, SnapshotECODClient

.. automodule:: sabueso.tools.db.tcdb
   :members: get_assignments, OnlineTCDBClient, FixtureTCDBClient, SnapshotTCDBClient

.. automodule:: sabueso.tools.db.channelsdb
   :members: get_annotations, get_channels, OnlineChannelsDBClient, FixtureChannelsDBClient, SnapshotChannelsDBClient

.. automodule:: sabueso.tools.db.gwas_catalog
   :members: get_associations, OnlineGwasCatalogClient, FixtureGwasCatalogClient, SnapshotGwasCatalogClient

.. automodule:: sabueso.tools.db.monarch
   :members: get_associations, OnlineMonarchClient, FixtureMonarchClient, SnapshotMonarchClient

.. automodule:: sabueso.tools.db.pride
   :members: get_project, OnlinePrideClient, FixturePrideClient, SnapshotPrideClient

.. automodule:: sabueso.tools.db.omnipath
   :members: get_interactions, OnlineOmniPathClient, FixtureOmniPathClient, SnapshotOmniPathClient

.. automodule:: sabueso.tools.db.wikipathways
   :members: get_pathways_by_xref, OnlineWikiPathwaysClient, FixtureWikiPathwaysClient, SnapshotWikiPathwaysClient

.. automodule:: sabueso.tools.db.ema_orphan
   :members: get_designations, OnlineEmaOrphanClient, FixtureEmaOrphanClient, SnapshotEmaOrphanClient

.. automodule:: sabueso.tools.db.civic
   :members: get_molecular_profile_items, OnlineCIViCClient, FixtureCIViCClient, SnapshotCIViCClient

.. automodule:: sabueso.tools.db.drugcentral
   :members: get_target_relations, OnlineDrugCentralClient, FixtureDrugCentralClient, SnapshotDrugCentralClient

.. automodule:: sabueso.tools.db.clingen
   :members: get_gene_validity, OnlineClinGenClient, FixtureClinGenClient, SnapshotClinGenClient

.. automodule:: sabueso.tools.db.hpa
   :members: get_gene_profile, OnlineHpaClient, FixtureHpaClient, SnapshotHpaClient

.. automodule:: sabueso.tools.db.signor
   :members: get_relations, OnlineSignorClient, FixtureSignorClient, SnapshotSignorClient

.. automodule:: sabueso.tools.db.appris
   :members: get_gene_annotations, OnlineApprisClient, FixtureApprisClient, SnapshotApprisClient

.. automodule:: sabueso.tools.db.complex_portal
   :members: get_complex, OnlineComplexPortalClient, FixtureComplexPortalClient, SnapshotComplexPortalClient

.. automodule:: sabueso.tools.db.cath
   :members: get_domain_summary, OnlineCathClient, FixtureCathClient, SnapshotCathClient

.. automodule:: sabueso.tools.db.swissmodel
   :members: get_metadata, OnlineSwissModelClient, FixtureSwissModelClient

.. automodule:: sabueso.tools.db.amypro
   :members: get_entry, OnlineAmyProClient, FixtureAmyProClient

.. automodule:: sabueso.tools.db.intact
   :members: get_interactions, OnlineIntActClient, FixtureIntActClient

.. automodule:: sabueso.tools.db.alphafill
   :members: get_metadata, OnlineAlphaFillClient, FixtureAlphaFillClient, SnapshotAlphaFillClient

.. automodule:: sabueso.tools.db.ligysis
   :members: get_result_page, get_structure_mapping, OnlineLigysisClient, FixtureLigysisClient, SnapshotLigysisClient

.. automodule:: sabueso.tools.db.glygen
   :members: get_protein, OnlineGlyGenClient, FixtureGlyGenClient, SnapshotGlyGenClient

.. automodule:: sabueso.tools.sources
   :members: get_catalog

.. automodule:: sabueso.tools.db.mobidb
   :members: get_annotations, OnlineMobiDBClient, FixtureMobiDBClient

.. automodule:: sabueso.tools.db.sifts
   :members: get_mappings, OnlineSIFTSClient, FixtureSIFTSClient, SnapshotSIFTSClient

.. automodule:: sabueso.tools.db.pdbe_validation
   :members: get_global_percentiles, OnlinePDBeValidationClient, FixturePDBeValidationClient
```

## Development EPPIC and PDB-REDO context

```{eval-rst}
.. automodule:: sabueso.tools.db.eppic
   :members: get_annotations, get_interface_residues, OnlineEPPICClient, FixtureEPPICClient

.. automodule:: sabueso.tools.db.pdb_redo
   :members: get_entry, get_versions, OnlinePDBRedoClient, FixturePDBRedoClient
```

## `sabueso.tools.db.alphamissense`

```{eval-rst}
.. automodule:: sabueso.tools.db.alphamissense
   :members: get_annotations, OnlineAlphaMissenseClient, FixtureAlphaMissenseClient
```

## `sabueso.tools.sequence`

```{eval-rst}
.. automodule:: sabueso.tools.sequence
   :members: find_protein_candidates
```

## `sabueso.tools.db.uniparc`

```{eval-rst}
.. automodule:: sabueso.tools.db.uniparc
   :members: get_records, OnlineUniParcClient, FixtureUniParcClient
```

## `sabueso.tools.resolve`

```{eval-rst}
.. automodule:: sabueso.tools.resolve
   :members:
   :undoc-members:
```

## `sabueso.tools.card.protein`

```{eval-rst}
.. automodule:: sabueso.tools.card.protein
   :members:
   :undoc-members:
```

## `sabueso.tools.card.small_molecule`

```{eval-rst}
.. automodule:: sabueso.tools.card.small_molecule
   :members:
   :undoc-members:
```

## Card and Deck storage

### `sabueso.tools.card.notebook`

```{eval-rst}
.. automodule:: sabueso.tools.card.notebook
   :members: write_notebook
```

### `sabueso.tools.card.storage`

```{eval-rst}
.. automodule:: sabueso.tools.card.storage
   :members:
   :undoc-members:
```

### `sabueso.tools.deck.storage`

```{eval-rst}
.. automodule:: sabueso.tools.deck.storage
   :members:
   :undoc-members:
```

## Source access (`sabueso.tools.db`)

### `sabueso.tools.source_snapshot`

`load_source_snapshot` reads structured JSON/JSONL/NDJSON/CSV/TSV or literal UTF-8
HTML/TXT, optionally gzip-compressed. Literal content retains BOM and line endings
without parsing or script execution. The receipt hashes original file bytes and
separates declared source metadata from observed access. Source clients still
validate native identity and completeness before mapping.

```{eval-rst}
.. automodule:: sabueso.tools.source_snapshot
   :members: load_source_snapshot
```

### `sabueso.tools.db.disprot`

```{eval-rst}
.. automodule:: sabueso.tools.db.disprot
   :members: get_records, OnlineDisProtClient, FixtureDisProtClient, SnapshotDisProtClient
```

### `sabueso.tools.db.aaindex`

```{eval-rst}
.. automodule:: sabueso.tools.db.aaindex
   :members: get_index, OnlineAAindexClient, FixtureAAindexClient
```

### `sabueso.tools.db.europepmc`

```{eval-rst}
.. automodule:: sabueso.tools.db.europepmc
   :members:
```

### `sabueso.tools.db.uniprot`

```{eval-rst}
.. automodule:: sabueso.tools.db.uniprot
   :members:
   :undoc-members:
```

### `sabueso.tools.db.rcsb`

```{eval-rst}
.. automodule:: sabueso.tools.db.rcsb
   :members:
   :undoc-members:
```

### `sabueso.tools.db.pdb_ccd`

```{eval-rst}
.. automodule:: sabueso.tools.db.pdb_ccd
   :members:
   :undoc-members:
```

### `sabueso.tools.db.pdbe_kb`

```{eval-rst}
.. automodule:: sabueso.tools.db.pdbe_kb
   :members:
   :undoc-members:
```

### `sabueso.tools.db.interpro`

```{eval-rst}
.. automodule:: sabueso.tools.db.interpro
   :members:
   :undoc-members:
```

### `sabueso.tools.db.alphafold`

```{eval-rst}
.. automodule:: sabueso.tools.db.alphafold
   :members:
   :undoc-members:
```

### `sabueso.tools.db.chembl`

```{eval-rst}
.. automodule:: sabueso.tools.db.chembl
   :members:
   :undoc-members:
```

### `sabueso.tools.db.bindingdb`

```{eval-rst}
.. automodule:: sabueso.tools.db.bindingdb
   :members:
   :undoc-members:
```

### `sabueso.tools.db.pubchem`

```{eval-rst}
.. automodule:: sabueso.tools.db.pubchem
   :members:
   :undoc-members:
```

### `sabueso.tools.db.pubchem_bioassay`

```{eval-rst}
.. automodule:: sabueso.tools.db.pubchem_bioassay
   :members:
   :undoc-members:
```

### `sabueso.tools.db.unichem`

```{eval-rst}
.. automodule:: sabueso.tools.db.unichem
   :members:
   :undoc-members:
```

### `sabueso.tools.db.stringdb`

```{eval-rst}
.. automodule:: sabueso.tools.db.stringdb
   :members:
   :undoc-members:
```

### `sabueso.tools.db.ncbi_taxonomy`

```{eval-rst}
.. automodule:: sabueso.tools.db.ncbi_taxonomy
   :members:
   :undoc-members:
```

### `sabueso.tools.db.ncbi_gene`

```{eval-rst}
.. automodule:: sabueso.tools.db.ncbi_gene
   :members:
   :undoc-members:
```

### `sabueso.tools.db.pdb`

```{eval-rst}
.. automodule:: sabueso.tools.db.pdb
   :members:
   :undoc-members:
```
