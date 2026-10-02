import re

from sabueso._private.argdigest._shared import refuse


def digest_publication_ref(publication_ref, caller=None):
    """A native publication reference read by the literature view, without aliases."""
    if isinstance(publication_ref, str):
        value = publication_ref.strip()
        if re.fullmatch(
            r"pubmed:[1-9][0-9]*|doi:10\.[0-9]{4,9}/\S+|"
            r"europepmc:MED:[1-9][0-9]*|europepmc:PMC:PMC[1-9][0-9]*|"
            r"uniprot\.citation:\S+",
            value,
        ):
            return value
    raise refuse(
        "publication_ref",
        publication_ref,
        caller,
        "expected a pubmed:, doi:, europepmc:MED:, europepmc:PMC: or uniprot.citation: reference",
    )
