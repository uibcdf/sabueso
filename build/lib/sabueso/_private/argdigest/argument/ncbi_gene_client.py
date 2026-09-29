from sabueso._private.argdigest._shared import client


def digest_ncbi_gene_client(ncbi_gene_client, caller=None):
    """A source client (duck-typed), or None for the online default."""
    return client("ncbi_gene_client", ncbi_gene_client, caller)
