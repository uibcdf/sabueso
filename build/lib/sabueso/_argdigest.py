"""ArgDigest configuration for Sabueso (uibcdf/sabueso#31), as in the sibling components.

Axis 2, the value contract of each argument, lives in one digester per argument name.
Axis 1, the argument contract of each function: a closed signature is held to its own
parameters, and a function with ``**kwargs`` declares its domain in FUNCTION_SOURCE.
"""

DIGESTION_SOURCE = "sabueso._private.argdigest.argument"
DIGESTION_STYLE = "package"
STRICTNESS = "warn"
SKIP_PARAM = "skip_digestion"

FUNCTION_SOURCE = "sabueso._private.argdigest.function"
DOMAIN_SOURCE = "sabueso._private.argdigest.domain"
UNKNOWN_ARGUMENT = "error"
