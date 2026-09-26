from sabueso._private.argdigest._shared import boolean


def digest_ncbi_gene(ncbi_gene, caller=None):
    return boolean("ncbi_gene", ncbi_gene, caller)
