from sabueso._private.argdigest._shared import options, positive_int


def digest_trials(trials, caller=None):
    """ClinicalTrials.gov studies cited by the indications: None (off) or options
    {limit}."""
    return options("trials", trials, caller, {"limit": positive_int})
