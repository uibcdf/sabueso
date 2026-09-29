from sabueso._private.argdigest._shared import boolean


def digest_interfaces(interfaces, caller=None):
    return boolean("interfaces", interfaces, caller)
