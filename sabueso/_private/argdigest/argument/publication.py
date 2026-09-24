import re

from sabueso._private.argdigest._shared import refuse

PUBLICATION = re.compile(r"pubmed:[1-9][0-9]*|doi:10\.[0-9]{4,9}/\S+")


def digest_publication(publication, caller=None):
    """``pubmed:<id>`` or ``doi:<doi>``: the record a curated assertion comes from."""
    if isinstance(publication, str) and PUBLICATION.fullmatch(publication.strip()):
        return publication.strip()
    raise refuse(
        "publication", publication, caller, 'expected "pubmed:<id>" or "doi:10.<...>"'
    )
