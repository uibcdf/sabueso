"""Original SDK202 argument shapes, independent of current public digesters."""

import re

from ..errors import ArgumentError


def digest_publication_ref(value):
    if isinstance(value, str):
        normalized = value.strip()
        if re.fullmatch(
            r"pubmed:[1-9][0-9]*|doi:10\.[0-9]{4,9}/\S+|"
            r"europepmc:MED:[1-9][0-9]*|europepmc:PMC:PMC[1-9][0-9]*|"
            r"uniprot\.citation:\S+",
            normalized,
        ):
            return normalized
    raise ArgumentError("publication_ref requires an exact native publication key.")


def digest_item_ref(value):
    if isinstance(value, str) and re.fullmatch(r"XI_[0-9a-f]{64}", value):
        return value
    raise ArgumentError("item_refs requires exact XI_ references.")
