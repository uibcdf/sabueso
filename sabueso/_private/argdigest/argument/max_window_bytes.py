def digest_max_window_bytes(max_window_bytes, caller=None):
    from sabueso.core.exploration_transport import byte_budget

    return byte_budget("max_window_bytes", max_window_bytes)
