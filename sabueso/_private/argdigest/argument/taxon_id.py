from sabueso._private.argdigest._shared import positive_int, refuse


def digest_taxon_id(taxon_id, caller=None):
    if taxon_id is None:
        return None
    reason = positive_int(taxon_id)
    if reason:
        raise refuse("taxon_id", taxon_id, caller, reason)
    return taxon_id
