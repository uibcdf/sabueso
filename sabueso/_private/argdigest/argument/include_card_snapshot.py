from sabueso._private.argdigest._shared import boolean


def digest_include_card_snapshot(include_card_snapshot, caller=None):
    return boolean("include_card_snapshot", include_card_snapshot, caller)
