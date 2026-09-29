from sabueso._private.argdigest._shared import refuse
from sabueso._private.argdigest.argument.residue_map import digest_residue_map


def digest_residue_maps(residue_maps, caller=None):
    """None, or ``{card_id: {position: reference position}}`` with positive integers."""
    if residue_maps is None:
        return None
    if isinstance(residue_maps, dict) and all(isinstance(k, str) for k in residue_maps):
        try:
            return {
                k: digest_residue_map(v, caller) or {} for k, v in residue_maps.items()
            }
        except Exception:
            pass
    raise refuse(
        "residue_maps",
        residue_maps,
        caller,
        "expected None or {card_id: {position: reference position}} with positive integers",
    )
