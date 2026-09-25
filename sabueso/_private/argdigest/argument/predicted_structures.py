from sabueso._private.argdigest._shared import boolean


def digest_predicted_structures(predicted_structures, caller=None):
    return boolean("predicted_structures", predicted_structures, caller)
