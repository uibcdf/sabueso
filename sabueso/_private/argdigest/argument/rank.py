from sabueso._private.argdigest._shared import refuse

#: NCBI Taxonomy ranks. A misspelt rank ("genera") would otherwise put every card in the
#: None group, silently. A rank NCBI adds later must be added here (RISKS).
NCBI_RANKS = frozenset(
    {
        "acellular root",
        "cellular root",
        "realm",
        "domain",
        "superkingdom",
        "kingdom",
        "subkingdom",
        "superphylum",
        "phylum",
        "subphylum",
        "superclass",
        "class",
        "subclass",
        "infraclass",
        "cohort",
        "subcohort",
        "superorder",
        "order",
        "suborder",
        "infraorder",
        "parvorder",
        "superfamily",
        "family",
        "subfamily",
        "tribe",
        "subtribe",
        "genus",
        "subgenus",
        "section",
        "subsection",
        "series",
        "subseries",
        "species group",
        "species subgroup",
        "species",
        "forma specialis",
        "subspecies",
        "varietas",
        "subvariety",
        "forma",
        "serogroup",
        "serotype",
        "strain",
        "isolate",
        "clade",
        "morph",
        "genotype",
        "biotype",
        "pathogroup",
        "no rank",
    }
)


def digest_rank(rank, caller=None):
    """An NCBI Taxonomy rank (case-insensitive), e.g. ``"genus"``."""
    if isinstance(rank, str) and rank.strip().lower() in NCBI_RANKS:
        return rank.strip().lower()
    raise refuse(
        "rank",
        rank,
        caller,
        "expected an NCBI Taxonomy rank, e.g. 'genus', 'family', 'order', 'species'",
    )
