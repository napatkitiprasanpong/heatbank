"""C2 heat-index engine: WBGT via thermofeel (K2, Apache-2.0).

Plan U6: thermofeel function names/signatures are not confirmed. WBGT is context/reporting in Part 1
(PHS is driven by tdb, tr, v, rh), so a mismatch must not break the pipeline: errors surface as None + reason.
Fill WBGT_CALL once scripts/check_signatures.py shows the installed signature."""
from typing import Callable, Optional, Tuple

WBGT_CALL: Optional[Callable] = None   # set to a callable(WeatherHour) -> float after checking the installed version


def compute_wbgt(hour) -> Tuple[Optional[float], str]:
    if WBGT_CALL is None:
        return None, "WBGT not configured (U6)"
    try:
        return float(WBGT_CALL(hour)), "ok"
    except Exception as e:
        return None, f"WBGT error: {e!r}"
