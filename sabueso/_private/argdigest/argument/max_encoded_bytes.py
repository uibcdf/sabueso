def digest_max_encoded_bytes(max_encoded_bytes, caller=None):
    from sabueso.core.exploration_transport import byte_budget

    return byte_budget("max_encoded_bytes", max_encoded_bytes)
