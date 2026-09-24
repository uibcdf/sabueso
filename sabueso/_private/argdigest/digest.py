"""ArgDigest adapter for Sabueso: the decorator bound to Sabueso's configuration."""

from argdigest import arg_digest as _arg_digest


def arg_digest(*args, **kwargs):
    """Sabueso's argument digestion decorator (``sabueso._argdigest``)."""
    return _arg_digest(config="sabueso._argdigest", *args, **kwargs)
