from sabueso._private.argdigest._shared import refuse


def digest_organism(organism, caller=None):
    """An NCBI taxonomy id (int, or digits) or an organism name."""
    if isinstance(organism, bool):
        raise refuse("organism", organism, caller, "expected a taxonomy id or a name")
    if isinstance(organism, int) and organism > 0:
        return organism
    if isinstance(organism, str) and organism.strip():
        return int(organism) if organism.strip().isdigit() else organism.strip()
    raise refuse("organism", organism, caller, "expected a taxonomy id or a name")
