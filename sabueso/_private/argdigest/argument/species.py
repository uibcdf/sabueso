from sabueso._private.argdigest._shared import positive_int, refuse


def digest_species(species, caller=None):
    """An NCBI taxonomy id."""
    reason = positive_int(species)
    if reason:
        raise refuse("species", species, caller, reason)
    return species
