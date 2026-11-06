def digest_max_logical_bytes(max_logical_bytes, caller=None):
    from sabueso.core.exploration_transport import byte_budget

    return byte_budget("max_logical_bytes", max_logical_bytes)
