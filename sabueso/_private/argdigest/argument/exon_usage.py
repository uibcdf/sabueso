from sabueso._private.argdigest._shared import boolean


def digest_exon_usage(exon_usage, caller=None):
    return boolean("exon_usage", exon_usage, caller)
