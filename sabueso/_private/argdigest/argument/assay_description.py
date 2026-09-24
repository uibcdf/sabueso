from sabueso._private.argdigest._shared import optional_text


def digest_assay_description(assay_description, caller=None):
    """How the publication describes the assay (conditions, test concentration)."""
    return optional_text("assay_description", assay_description, caller)
