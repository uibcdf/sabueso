import re

from sabueso._private.argdigest._shared import refuse

REF = re.compile(r"[a-z][a-z0-9_.]*:\S.*")


def digest_object_ref(object_ref, caller=None):
    """A reference ``<namespace>:<id>``, e.g. ``uniprot:P60174`` or ``pdb.ligand:PGA``."""
    if isinstance(object_ref, str) and REF.fullmatch(object_ref.strip()):
        return object_ref.strip()
    raise refuse("object_ref", object_ref, caller, 'expected "<namespace>:<id>"')
