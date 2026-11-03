def digest_max_decoded_bytes(max_decoded_bytes, caller=None):
    from sabueso.core.exploration_transport import byte_budget

    return byte_budget("max_decoded_bytes", max_decoded_bytes)
