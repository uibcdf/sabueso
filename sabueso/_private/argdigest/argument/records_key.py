from sabueso._private.argdigest._shared import optional_text


def digest_records_key(records_key, caller=None):
    return optional_text("records_key", records_key, caller)
