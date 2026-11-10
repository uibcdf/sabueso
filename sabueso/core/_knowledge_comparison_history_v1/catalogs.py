"""Literal SDK243 catalogs, frozen before independent saved reading."""

from copy import deepcopy

from .._protein_context_history_v1.catalogs import NATURE_TOPICS as _NATURE_TOPICS
from .._protein_context_history_v1.catalogs import QUESTIONS as _QUESTIONS
from .._protein_context_history_v1.catalogs import TOPICS as _TOPICS

NATURE_TOPICS = deepcopy(_NATURE_TOPICS)
QUESTIONS = deepcopy(_QUESTIONS)
TOPICS = deepcopy(_TOPICS)
NATURE_TOPICS["protein"] = (
    "function",
    "bioactivities",
    "structures",
    "sequence",
    "annotated_regions",
    "predicted_structures",
    "sites",
    "ligand_site_comparisons",
    "ligand_instances",
    "quaternary_structure",
    "quaternary_interpretation",
    "assembly_generation",
    "variants",
    "sequence_changes",
    "comparative_context",
    "associations",
)
QUESTIONS["protein"] = {
    "function": {
        "label": "What do the sources state this protein does?",
        "topic": "function",
        "required_options": [],
        "scope": "Retained function and catalytic annotations, with original support.",
    },
    "region_coverage": {
        "label": "What do retained structures tell us about this region?",
        "topic": "structures",
        "required_options": ["sequence_ref", "region"],
        "scope": "Explicit canonical UniProt positions; sequence "
        "coverage alone does not establish coordinate "
        "completeness.",
    },
    "measured_molecules": {
        "label": "Which molecules have retained measurements, "
        "and what supports each result?",
        "topic": "bioactivities",
        "required_options": [],
        "scope": "Original molecule, measurement-group, "
        "activity-record and assay/citation context "
        "with units and support; concentration bands "
        "do not establish mechanism or efficacy.",
    },
    "assembly_generation": {
        "label": "Which components and operations are "
        "declared for each retained assembly?",
        "topic": "assembly_generation",
        "required_options": [],
        "scope": "Exact original generator contexts, key "
        "binding and declared combination counts; no "
        "physical copy, coordinate or contact "
        "inference.",
    },
    "quaternary_interpretation": {
        "label": "Which interface classifications and "
        "family-site comparisons are "
        "supported?",
        "topic": "quaternary_interpretation",
        "required_options": [],
        "scope": "All source-bound interface findings "
        "and individual family comparisons, "
        "including explicit uncertainty; no "
        "assembly geometry or biological "
        "relevance inferred.",
    },
    "quaternary_structure": {
        "label": "What do sources state about subunits, assemblies and interfaces?",
        "topic": "quaternary_structure",
        "required_options": [],
        "scope": "Original subunit field, structure-local "
        "assembly records and interface statements "
        "with exact support; source-declared "
        "contexts remain distinct.",
    },
    "ligand_site_comparisons": {
        "label": "Which retained ligand contacts overlap annotated sites?",
        "topic": "ligand_site_comparisons",
        "required_options": [],
        "scope": "Source-bound canonical comparisons with "
        "explicit unknowns; no atomic proximity, "
        "revision agreement or "
        "aggregate/instance merge.",
    },
    "annotated_regions": {
        "label": "Which individual annotations can I explore in structures?",
        "topic": "annotated_regions",
        "required_options": [],
        "scope": "Original annotations and exact "
        "source-supported canonical-region questions; "
        "unplaced and unsupported records stay "
        "visible.",
    },
    "structure_ligands": {
        "label": "Which ligand instances and contacts are "
        "declared in retained structures?",
        "topic": "ligand_instances",
        "required_options": [],
        "scope": "Original structure-local instances, recorded "
        "chains and contact coordinates/distances; no "
        "assembly or aggregated-contact join.",
    },
    "sequence_annotations": {
        "label": "Which sequence and positional annotations are retained?",
        "topic": "sequence",
        "required_options": [],
        "scope": "Original sequence fields and annotation "
        "locations; no coordinate projection or "
        "alignment.",
    },
    "predicted_models": {
        "label": "Which predicted models and source confidence metrics are retained?",
        "topic": "predicted_structures",
        "required_options": [],
        "scope": "Original model declarations, source metrics "
        "and recorded sequence/isoform context; "
        "separate from experimental structures.",
    },
    "retained_sites": {
        "label": "Which annotated sites and contact statements are retained?",
        "topic": "sites",
        "required_options": [],
        "scope": "Original active, binding and family-model sites "
        "plus ligand/interface contact statements; no new "
        "overlap or proximity calculation.",
    },
    "knowledge_differences": {
        "label": "What do these supplied protein captures state alike or differently?",
        "topic": "comparative_context",
        "required_options": ["other_ref"],
        "scope": "Typed original field/relationship/state "
        "records; positional features require an "
        "explicit caller map. No alignment or "
        "identity merge.",
    },
    "publications": {
        "label": "Which publications and original source links are retained?",
        "topic": "literature",
        "required_options": [],
        "scope": "Original citations, ECO support, curated "
        "statements, mentions and activity records; "
        "publication links are not project Evidence.",
    },
    "variant_tissue_context": {
        "label": "What tissue context is retained for population variants?",
        "topic": "variants",
        "required_options": [],
        "scope": "Original scoped native rules, "
        "genomic/transcript/CDS context and "
        "per-tissue unknowns; no clinical "
        "inference or acquisition.",
    },
    "isoform_tissue_context": {
        "label": "What tissue context is retained for individual isoforms?",
        "topic": "variants",
        "required_options": [],
        "scope": "Original scoped native rules, "
        "genomic/transcript/CDS context and "
        "per-tissue unknowns; no clinical "
        "inference or acquisition.",
    },
    "sequence_changes": {
        "label": "Which natural variants and experimental "
        "sequence changes are retained?",
        "topic": "sequence_changes",
        "required_options": [],
        "scope": "Original annotation occurrences, substitutions "
        "and source support; no genomic correspondence "
        "or clinical inference.",
    },
    "related_proteins": {
        "label": "Which comparative relationships and supplied proteins are retained?",
        "topic": "comparative_context",
        "required_options": [],
        "scope": "Captured records and explicit inputs; no "
        "identity, coordinate correspondence or "
        "causality inference.",
    },
    "protein_associations": {
        "label": "Which disease, pathway and interaction relationships are retained?",
        "topic": "associations",
        "required_options": [],
        "scope": "Captured records and explicit inputs; no "
        "identity, coordinate correspondence or "
        "causality inference.",
    },
    "sequence_differences": {
        "label": "How do these explicitly supplied captured "
        "sequences differ at equal positions?",
        "topic": "comparative_context",
        "required_options": ["other_ref"],
        "scope": "Captured records and explicit inputs; no "
        "identity, coordinate correspondence or "
        "causality inference.",
    },
}
TOPICS["protein"] = {
    "function": (
        "Protein function",
        "Retained function, catalytic annotations and identity; no inferred function.",
    ),
    "bioactivities": (
        "Measured molecules and assay context",
        "Retained molecule, measurement-group and activity records "
        "with units, original assay/citation context and source "
        "support.",
    ),
    "structures": (
        "Experimental structures",
        "Existing inventory, original state rules and pinned support.",
    ),
    "sequence": (
        "Sequence and annotations",
        "Original sequence, units, checksums and source positional annotations.",
    ),
    "annotated_regions": (
        "Annotated regions and structural context",
        "Individual source annotations with their axes, "
        "original support and explicit structural questions.",
    ),
    "predicted_structures": (
        "Predicted models",
        "Source model versions, metrics, ranges and sequence "
        "context; separate from experiments.",
    ),
    "sites": (
        "Sites and contact statements",
        "Original functional-site fields and ligand/interface contacts with "
        "their numbering.",
    ),
    "ligand_site_comparisons": (
        "Ligand contacts and annotated-site comparisons",
        "Source-bound comparisons, partial findings and "
        "uncomputed coordinate context with original "
        "inputs.",
    ),
    "ligand_instances": (
        "Ligand instances in structures",
        "Original structure-local ligand instances, recorded "
        "chains and contact coordinates/distances.",
    ),
    "quaternary_structure": (
        "Subunits, assemblies and interfaces",
        "Original source declarations with structure-local "
        "assembly context, interface numbering and complete "
        "support.",
    ),
    "quaternary_interpretation": (
        "Interface classifications and family-site comparisons",
        "Source-bound interface findings and all "
        "family-site pairs, with original inputs and "
        "explicit uncomputed context.",
    ),
    "assembly_generation": (
        "Assembly components and operations",
        "Original assembly declarations, key binding and "
        "declared combination counts; physical copies and "
        "contacts remain uncomputed.",
    ),
    "variants": (
        "Variants, isoforms and tissue context",
        "Original population-variant and isoform tissue scope, exact "
        "input support and per-tissue unknowns.",
    ),
    "sequence_changes": (
        "Natural variants and mutagenesis",
        "Original protein substitutions and source annotations, "
        "separate from population genomic variants.",
    ),
    "comparative_context": (
        "Related proteins and explicit comparisons",
        "Source relationships and explicitly supplied protein "
        "comparisons; no identity merge.",
    ),
    "associations": (
        "Protein biological associations",
        "Original disease, pathway and interaction records; source "
        "channels and recorded direction stay distinct.",
    ),
    "literature": (
        "Publications and stored source links",
        "Original citations, ECO support, curated statements, mentions "
        "and source activity records, with complete publication "
        "context.",
    ),
    "sources": ("Source statements", "Original statements retained from sources."),
    "coverage": (
        "Knowledge coverage",
        "Original source/area knowledge states and their classification inputs.",
    ),
    "quality": (
        "Stored quality records",
        "Complete original quality, enrichment and selection records.",
    ),
    "content": ("Explore all content", "Complete retained Card content."),
}
PROTEIN_LABELS = {
    "function": "Protein function",
    "bioactivities": "Measured molecules and assay context",
    "structures": "Experimental structures",
    "sequence": "Sequence and annotations",
    "annotated_regions": "Annotated regions and structural context",
    "predicted_structures": "Predicted models",
    "sites": "Sites and contact statements",
    "ligand_site_comparisons": "Ligand contacts and annotated-site comparisons",
    "ligand_instances": "Ligand instances in structures",
    "quaternary_structure": "Subunits, assemblies and interfaces",
    "quaternary_interpretation": "Interface classifications and family-site comparisons",
    "assembly_generation": "Assembly components and operations",
    "variants": "Variants, isoforms and tissue context",
    "sequence_changes": "Natural variants and mutagenesis",
    "comparative_context": "Related proteins and explicit comparisons",
    "associations": "Retained molecular and clinical associations",
    "literature": "Publications and stored source links",
    "sources": "Source statements",
    "coverage": "Knowledge coverage",
    "quality": "Stored quality records",
    "content": "Explore all content",
}
