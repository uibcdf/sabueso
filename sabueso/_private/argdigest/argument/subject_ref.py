from sabueso._private.argdigest._shared import refuse
from sabueso._private.argdigest.argument.object_ref import REF


def digest_subject_ref(subject_ref, caller=None):
    """None (any subject), or a reference ``<namespace>:<id>`` such as ``uniprot:P52270``."""
    if subject_ref is None:
        return None
    if isinstance(subject_ref, str) and REF.fullmatch(subject_ref.strip()):
        return subject_ref.strip()
    raise refuse("subject_ref", subject_ref, caller, 'expected "<namespace>:<id>"')
