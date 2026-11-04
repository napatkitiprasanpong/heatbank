"""Mean radiant temperature (tr), needed by PHS. ISO 7726 forced-convection globe formula
(globe d = 0.15 m, emissivity 0.95). Cross-check against pythermalcomfort.mean_radiant_tmp once installed (V1)."""
from .. import config


def tr_from_globe(tg_c: float, tdb_c: float, v_ms: float, d_m: float = 0.15, emissivity: float = 0.95) -> float:
    v = max(v_ms, 0.0)
    t4 = (tg_c + 273.15) ** 4 + (1.1e8 * v ** 0.6 / (emissivity * d_m ** 0.4)) * (tg_c - tdb_c)
    return t4 ** 0.25 - 273.15


def tr_fallback(tdb_c: float, solar_wm2=None) -> float:
    """PLACEHOLDER when no globe temperature exists. Reported as radiant_source='fallback_offset'.
    Mode "solar" (config.TR_FALLBACK_MODE) scales the offset by forecast shortwave radiation; with no solar value it
    falls back to the constant offset (never lower than known)."""
    if config.TR_FALLBACK_MODE == "solar" and solar_wm2 is not None:
        return tdb_c + config.TR_SOLAR_GAIN_C * max(0.0, solar_wm2) / 1000.0
    return tdb_c + config.TR_FALLBACK_OFFSET_C
