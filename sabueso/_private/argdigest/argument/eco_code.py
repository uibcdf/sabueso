import re

from sabueso._private.argdigest._shared import refuse

ECO = re.compile(r"ECO:[0-9]{7}")


def digest_eco_code(eco_code, caller=None):
    """None or an Evidence & Conclusion Ontology code, e.g. ECO:0000269."""
    if eco_code is None or (isinstance(eco_code, str) and ECO.fullmatch(eco_code)):
        return eco_code
    raise refuse("eco_code", eco_code, caller, 'expected "ECO:" + 7 digits')
