"""Original SDK224 topic/question declarations; no current catalog is read."""

NATURE_TOPICS = {
    "protein": (
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
    ),
    "small_molecule": (
        "chemistry",
        "properties",
        "classification",
        "activity_context",
        "clinical",
    ),
    "disease": ("definition", "classification", "identity"),
}

QUESTIONS = {
    "protein": {
        "function": {
            "label": "What do the sources state this protein does?",
            "topic": "function",
            "required_options": [],
            "scope": "Retained function and catalytic "
            "annotations, with original support.",
        },
        "region_coverage": {
            "label": "What do retained structures tell us about this region?",
            "topic": "structures",
            "required_options": ["sequence_ref", "region"],
            "scope": "Explicit canonical UniProt "
            "positions; sequence coverage alone "
            "does not establish coordinate "
            "completeness.",
        },
        "measured_molecules": {
            "label": "Which molecules have retained "
            "measurements, and what supports "
            "each result?",
            "topic": "bioactivities",
            "required_options": [],
            "scope": "Original molecule, "
            "measurement-group, "
            "activity-record and "
            "assay/citation context with "
            "units and support; concentration "
            "bands do not establish mechanism "
            "or efficacy.",
        },
        "assembly_generation": {
            "label": "Which components and operations "
            "are declared for each retained "
            "assembly?",
            "topic": "assembly_generation",
            "required_options": [],
            "scope": "Exact original generator "
            "contexts, key binding and "
            "declared combination counts; no "
            "physical copy, coordinate or "
            "contact inference.",
        },
        "quaternary_interpretation": {
            "label": "Which interface "
            "classifications and "
            "family-site comparisons "
            "are supported?",
            "topic": "quaternary_interpretation",
            "required_options": [],
            "scope": "All source-bound "
            "interface findings and "
            "individual family "
            "comparisons, including "
            "explicit uncertainty; no "
            "assembly geometry or "
            "biological relevance "
            "inferred.",
        },
        "quaternary_structure": {
            "label": "What do sources state about subunits, assemblies and interfaces?",
            "topic": "quaternary_structure",
            "required_options": [],
            "scope": "Original subunit field, "
            "structure-local assembly "
            "records and interface "
            "statements with exact support; "
            "source-declared contexts "
            "remain distinct.",
        },
        "ligand_site_comparisons": {
            "label": "Which retained ligand contacts overlap annotated sites?",
            "topic": "ligand_site_comparisons",
            "required_options": [],
            "scope": "Source-bound canonical "
            "comparisons with explicit "
            "unknowns; no atomic "
            "proximity, revision "
            "agreement or "
            "aggregate/instance merge.",
        },
        "annotated_regions": {
            "label": "Which individual annotations can I explore in structures?",
            "topic": "annotated_regions",
            "required_options": [],
            "scope": "Original annotations and exact "
            "source-supported canonical-region "
            "questions; unplaced and "
            "unsupported records stay "
            "visible.",
        },
        "structure_ligands": {
            "label": "Which ligand instances and "
            "contacts are declared in retained "
            "structures?",
            "topic": "ligand_instances",
            "required_options": [],
            "scope": "Original structure-local "
            "instances, recorded chains and "
            "contact coordinates/distances; no "
            "assembly or aggregated-contact "
            "join.",
        },
        "sequence_annotations": {
            "label": "Which sequence and positional annotations are retained?",
            "topic": "sequence",
            "required_options": [],
            "scope": "Original sequence fields and "
            "annotation locations; no "
            "coordinate projection or "
            "alignment.",
        },
        "predicted_models": {
            "label": "Which predicted models and source "
            "confidence metrics are retained?",
            "topic": "predicted_structures",
            "required_options": [],
            "scope": "Original model declarations, "
            "source metrics and recorded "
            "sequence/isoform context; separate "
            "from experimental structures.",
        },
        "retained_sites": {
            "label": "Which annotated sites and contact statements are retained?",
            "topic": "sites",
            "required_options": [],
            "scope": "Original active, binding and "
            "family-model sites plus "
            "ligand/interface contact statements; "
            "no new overlap or proximity "
            "calculation.",
        },
        "publications": {
            "label": "Which publications and original source links are retained?",
            "topic": "literature",
            "required_options": [],
            "scope": "Original citations, ECO support, "
            "curated statements, mentions and "
            "activity records; publication links "
            "are not project Evidence.",
        },
    },
    "small_molecule": {
        "clinical_context": {
            "label": "What indications and studies do the sources report?",
            "topic": "clinical",
            "required_options": [],
            "scope": "ChEMBL indications, "
            "individual cited-trial "
            "occurrences and fetched "
            "registry records; "
            "source/query gaps remain "
            "explicit and no efficacy is "
            "inferred.",
        },
        "measured_targets": {
            "label": "Which supplied target "
            "contexts retain "
            "measurements for this exact "
            "molecule?",
            "topic": "activity_context",
            "required_options": [],
            "scope": "Explicit source identity "
            "edges and captured target "
            "pins; no target search, "
            "implicit identity merge or "
            "inactivity/efficacy "
            "inference.",
        },
        "chemical_identity": {
            "label": "Which chemical entity do these records describe?",
            "topic": "chemistry",
            "required_options": [],
            "scope": "Retained identifiers, "
            "representations and "
            "source-stated identity "
            "links; no computed "
            "chemistry.",
        },
        "property_context": {
            "label": "What properties are retained, and on what source basis?",
            "topic": "properties",
            "required_options": [],
            "scope": "Stored values, units, source methods and original alternatives.",
        },
        "classification": {
            "label": "Which chemical classes and source-stated roles are retained?",
            "topic": "classification",
            "required_options": [],
            "scope": "Original chemical classes, "
            "direct/inherited roles and "
            "exact source support; no "
            "target activity or "
            "therapeutic inference.",
        },
        "publications": {
            "label": "Which publications and original source links are retained?",
            "topic": "literature",
            "required_options": [],
            "scope": "Original citations, ECO "
            "support, curated statements, "
            "mentions and activity records; "
            "publication links are not "
            "project Evidence.",
        },
    },
    "disease": {
        "meaning": {
            "label": "What does this disease term mean?",
            "topic": "definition",
            "required_options": [],
            "scope": "Ontology definition, scoped synonyms and "
            "retained term metadata; not a diagnosis.",
        },
        "classification": {
            "label": "Which broader terms are stated?",
            "topic": "classification",
            "required_options": [],
            "scope": "Retained parent relationships; "
            "equivalent and related identifiers "
            "have a separate identity route.",
        },
        "publications": {
            "label": "Which publications and original source links are retained?",
            "topic": "literature",
            "required_options": [],
            "scope": "Original citations, ECO support, "
            "curated statements, mentions and "
            "activity records; publication links "
            "are not project Evidence.",
        },
    },
}

TOPICS = {
    "protein": {
        "function": (
            "Protein function",
            "Retained function, catalytic annotations and "
            "identity; no inferred function.",
        ),
        "bioactivities": (
            "Measured molecules and assay context",
            "Retained molecule, measurement-group and "
            "activity records with units, original "
            "assay/citation context and source support.",
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
            "Individual source annotations with their "
            "axes, original support and explicit "
            "structural questions.",
        ),
        "predicted_structures": (
            "Predicted models",
            "Source model versions, metrics, ranges "
            "and sequence context; separate from "
            "experiments.",
        ),
        "sites": (
            "Sites and contact statements",
            "Original functional-site fields and ligand/interface "
            "contacts with their numbering.",
        ),
        "ligand_site_comparisons": (
            "Ligand contacts and annotated-site comparisons",
            "Source-bound comparisons, partial "
            "findings and uncomputed coordinate "
            "context with original inputs.",
        ),
        "ligand_instances": (
            "Ligand instances in structures",
            "Original structure-local ligand instances, "
            "recorded chains and contact "
            "coordinates/distances.",
        ),
        "quaternary_structure": (
            "Subunits, assemblies and interfaces",
            "Original source declarations with "
            "structure-local assembly context, "
            "interface numbering and complete "
            "support.",
        ),
        "quaternary_interpretation": (
            "Interface classifications and family-site comparisons",
            "Source-bound interface findings "
            "and all family-site pairs, with "
            "original inputs and explicit "
            "uncomputed context.",
        ),
        "assembly_generation": (
            "Assembly components and operations",
            "Original assembly declarations, key "
            "binding and declared combination counts; "
            "physical copies and contacts remain "
            "uncomputed.",
        ),
        "literature": (
            "Publications and stored source links",
            "Original citations, ECO support, curated "
            "statements, mentions and source activity records, "
            "with complete publication context.",
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
    },
    "small_molecule": {
        "chemistry": (
            "Chemical identity",
            "Retained chemical representations and source-stated identity links.",
        ),
        "properties": (
            "Physicochemical properties",
            "Stored values, units, source methods and alternatives.",
        ),
        "classification": (
            "Chemical classes and source-stated roles",
            "Retained classes, direct/inherited "
            "roles and original source support; no "
            "therapeutic inference.",
        ),
        "activity_context": (
            "Targets, measurements and assay context",
            "Exact molecule identity joins into "
            "explicitly supplied target captures, "
            "preserving original measurements and "
            "source/query scope.",
        ),
        "clinical": (
            "Indications and clinical studies",
            "Source indications, individual cited trials "
            "and retained registry records, with separate "
            "phases, support and original request scope.",
        ),
        "literature": (
            "Publications and stored source links",
            "Original citations, ECO support, curated "
            "statements, mentions and source activity "
            "records, with complete publication "
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
    },
    "disease": {
        "definition": (
            "Disease definition",
            "Ontology definition, scoped synonyms and retained term metadata.",
        ),
        "classification": (
            "Disease classification",
            "Retained parent relationships; identity terminology is separate.",
        ),
        "identity": (
            "Identity terminology",
            "Equivalent identifiers and related xrefs, explicitly separated.",
        ),
        "literature": (
            "Publications and stored source links",
            "Original citations, ECO support, curated "
            "statements, mentions and source activity records, "
            "with complete publication context.",
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
    },
}
