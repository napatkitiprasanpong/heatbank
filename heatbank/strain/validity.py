"""Model validity gate (plan section 7, P2). Outside the valid range HeatBank does not extrapolate."""
import math
from typing import List, Tuple
from .. import config

OK, ABOVE, BELOW, INVALID = "OK", "ABOVE_RANGE", "BELOW_RANGE", "INVALID"


def check_inputs(tdb_c, tr_c, v_ms, rh_pct, met_wm2, clo) -> Tuple[str, List[str]]:
    vals = {"tdb_c": tdb_c, "tr_minus_tdb_c": (tr_c - tdb_c) if (tr_c is not None and tdb_c is not None) else None, "v_ms": v_ms, "met_wm2": met_wm2, "clo": clo}
    reasons = []
    if any(x is None or (isinstance(x, float) and math.isnan(x)) for x in list(vals.values()) + [rh_pct]):
        return INVALID, ["missing or NaN input"]
    lo, hi = config.RH_RANGE
    if not lo <= rh_pct <= hi:
        return INVALID, [f"rh_pct {rh_pct} outside {lo}-{hi}"]
    above = [k for k, x in vals.items() if x > config.VALID_RANGES[k][1]]
    below = [k for k, x in vals.items() if x < config.VALID_RANGES[k][0]]
    if above:
        return ABOVE, [f"{k}={vals[k]} above {config.VALID_RANGES[k][1]}" for k in above]
    if below:
        return BELOW, [f"{k}={vals[k]} below {config.VALID_RANGES[k][0]}" for k in below]
    return OK, reasons
