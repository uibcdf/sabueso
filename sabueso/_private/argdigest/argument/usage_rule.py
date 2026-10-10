"""Select a supported comparative tissue rule without guessing its version."""

from sabueso._private.argdigest._shared import refuse


def digest_usage_rule(usage_rule, caller=None):
    if isinstance(usage_rule, str) and usage_rule in {
        "pext_at_variant@1",
        "pext_at_variant@2",
        "isoform_exon_usage@2",
        "isoform_exon_usage@3",
    }:
        return usage_rule
    raise refuse(
        "usage_rule", usage_rule, caller, "expected a supported tissue usage rule"
    )
