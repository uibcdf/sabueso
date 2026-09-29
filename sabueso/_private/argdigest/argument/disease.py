from sabueso._private.argdigest._shared import refuse


def digest_disease(disease, caller=None):
    """A disease card, or a non-empty disease id (``mondo:``, ``doid:``, ``ORPHA:``…)."""
    meta = getattr(disease, "meta", None)
    if isinstance(meta, dict) and meta.get("entity_type") == "disease":
        return disease
    if isinstance(disease, str) and disease.strip():
        return disease.strip()
    raise refuse("disease", disease, caller, "expected a disease card or a disease id")
