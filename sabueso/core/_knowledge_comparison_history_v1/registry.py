"""Frozen SDK243 source declarations, evaluated once without acquisition."""

from copy import deepcopy

PROTEIN_AREAS = [
    ("relationships.functionally_associated_with", "STRING", {"source": "STRING"}),
    (
        "relationships.has_ligand_site",
        "PDBe-KB",
        {"data": "ligand_sites", "source": "PDBe-KB"},
    ),
    (
        "relationships.has_interface_with",
        "PDBe-KB",
        {"data": "interface_residues", "source": "PDBe-KB"},
    ),
    (
        "relationships.has_predicted_structure",
        "AlphaFold DB",
        {"source": "AlphaFold DB"},
    ),
    ("annotations.taxonomy", "NCBI Taxonomy", {"source": "NCBI Taxonomy"}),
    ("features_positional.family_site", "InterPro", {"source": "InterPro"}),
    ("annotations.pathogen_phenotypes", "PHI-base", {"source": "PHI-base"}),
    ("relationships.associated_with", "DISEASES", {"source": "DISEASES"}),
    ("relationships.associated_with", "Open Targets", {"source": "Open Targets"}),
    ("relationships.associated_with", "Orphanet", {"source": "Orphanet"}),
    ("relationships.participates_in", "Reactome", {"source": "Reactome"}),
    ("annotations.population_variants", "gnomAD", {"data": None, "source": "gnomAD"}),
    (
        "annotations.exon_usage_by_tissue",
        "gnomAD",
        {"data": "pext", "source": "gnomAD"},
    ),
    (
        "annotations.isoform_coding_exons",
        "gnomAD",
        {"data": "pext", "source": "gnomAD"},
    ),
    ("annotations.tissue_terms", "GTEx", {"source": "GTEx"}),
    ("annotations.clinical_variants", "ClinVar", {"source": "ClinVar"}),
    ("annotations.interface_mutations", "SKEMPI", {"source": "SKEMPI"}),
    ("annotations.antibody_complexes", "SAbDab", {"source": "SAbDab"}),
    ("relationships.ortholog_of", "OMA", {"source": "OMA"}),
    ("identifiers.uniref", "UniProt", {"data": "uniref", "source": "UniProt"}),
    (
        "relationships.clustered_with",
        "UniProt",
        {"data": "uniref", "source": "UniProt"},
    ),
    ("annotations.kinase_classification", "KLIFS", {"source": "KLIFS"}),
    ("annotations.kinase_structures", "KLIFS", {"source": "KLIFS"}),
    ("annotations.kinase_pocket", "KLIFS", {"source": "KLIFS"}),
    ("annotations.gpcr_classification", "GPCRdb", {"source": "GPCRdb"}),
    ("annotations.gpcr_segments", "GPCRdb", {"source": "GPCRdb"}),
    ("annotations.gpcr_residues", "GPCRdb", {"source": "GPCRdb"}),
    ("annotations.gpcr_structures", "GPCRdb", {"source": "GPCRdb"}),
    ("relationships.mentioned_in", "Europe PMC", {"source": "Europe PMC"}),
    (
        "relationships.structure_mentioned_in",
        "Europe PMC",
        {
            "data": "located_accession_annotations",
            "mapping": "located_accession_mapping@2",
            "source": "Europe PMC",
        },
    ),
    ("relationships.same_as (MedGen)", "MedGen", {"source": "MedGen"}),
    ("relationships.same_as (MONDO)", "MONDO", {"source": "MONDO"}),
    ("relationships.subclass_of (MONDO)", "MONDO", {"source": "MONDO"}),
]
COUNTS = {
    ("relationships.mentioned_in", "Europe PMC"): "uniprot_mention_count",
    ("relationships.structure_mentioned_in", "Europe PMC"): "structure_mention_count",
}
NOT_QUERIED_DETAILS = {
    (
        "relationships.structure_mentioned_in",
        "Europe PMC",
    ): "Located PDB mention context requires "
    "explicit article_ids; bibliographic "
    "search does not query article "
    "annotations."
}
STATED_FIELDS = frozenset(
    (
        "annotations.activity_regulation",
        "annotations.alternative_products",
        "annotations.catalytic_activity",
        "annotations.disease",
        "annotations.domain_notes",
        "annotations.function",
        "annotations.isoforms",
        "annotations.lineage",
        "annotations.miscellaneous",
        "annotations.organism",
        "annotations.pathway",
        "annotations.polymorphism",
        "annotations.ptm",
        "annotations.similarity",
        "annotations.source_cautions",
        "annotations.subcellular_location",
        "annotations.subunit",
        "annotations.taxon_id",
        "annotations.tissue_specificity",
        "features_positional.active_site",
        "features_positional.alternative_sequence",
        "features_positional.binding_site",
        "features_positional.chain",
        "features_positional.disulfide_bond",
        "features_positional.domains",
        "features_positional.glycosylation",
        "features_positional.lipidation",
        "features_positional.modified_residue",
        "features_positional.motif",
        "features_positional.mutagenesis",
        "features_positional.natural_variant",
        "features_positional.region",
        "features_positional.secondary_structure",
        "features_positional.sequence_conflict",
        "features_positional.topological_domain",
        "features_positional.transmembrane",
        "identifiers.ensembl_transcripts",
        "identifiers.gene_loci",
        "identifiers.uniprot",
        "names.abbreviations",
        "names.canonical_name",
        "names.gene_names",
        "names.synonyms",
        "sequence.checksums",
        "sequence.length",
        "sequence.molecular_weight",
        "sequence.primary",
    )
)
STATED_PREDICATES = frozenset(
    (
        "annotated_with",
        "classified_in",
        "described_in",
        "has_structure",
        "interacts_with",
    )
)


def knowledge_areas(entity_type="protein"):
    return deepcopy(PROTEIN_AREAS) if entity_type == "protein" else []


def count_by_area():
    return deepcopy(COUNTS)


def not_queried_details_by_area():
    return deepcopy(NOT_QUERIED_DETAILS)
