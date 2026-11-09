"""Frozen SDK227 namespace spelling and original assertion-value accessor."""

NAMESPACES = {
    "mondo": "MONDO",
    "doid": "DOID",
    "omim": "OMIM",
    "omimps": "OMIMPS",
    "orphanet": "Orphanet",
    "orpha": "Orphanet",
    "ordo": "Orphanet",
    "mesh": "MESH",
    "efo": "EFO",
    "ncit": "NCIT",
    "medgen": "MEDGEN",
    "umls": "UMLS",
    "icd10cm": "ICD10CM",
    "icd10who": "ICD10WHO",
    "icd9": "ICD9",
    "sctid": "SCTID",
    "snomedct": "SCTID",
    "icd11.foundation": "icd11.foundation",
    "oncotree": "ONCOTREE",
    "decipher": "DECIPHER",
}


def normalize(curie: str) -> str | None:
    """MONDO's spelling of a disease id, from the forms users and sources write:
    ``doid:9352``, ``DOID:9352``, ``doid:DOID:9352``, ``efo:EFO:0001360``,
    ``EFO_0001360``, ``ORPHA:586``. None when the namespace is not one MONDO maps."""
    text = str(curie).strip()
    if ":" not in text and "_" in text:
        text = text.replace("_", ":", 1)
    namespace, _, local = text.partition(":")
    if ":" in local and local.split(":", 1)[0].lower() == namespace.lower():
        local = local.split(":", 1)[1]
    elif ":" in local and local.split(":", 1)[0].lower() in NAMESPACES:
        namespace, _, local = local.partition(":")
    prefix = NAMESPACES.get(namespace.lower())
    if prefix is None or not local:
        return None
    return f"{prefix}:{local}"


def assertion_value(assertion):
    if "normalized_value" in assertion:
        return assertion["normalized_value"]
    return assertion.get("asserted_value")
