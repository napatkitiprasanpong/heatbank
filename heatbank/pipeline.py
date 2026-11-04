"""Weather -> (WBGT) -> PHS per archetype -> safe minutes per hour. Part 1 output feeds the Part 2 planner."""
import csv
from typing import List, Optional
from . import config
from .archetypes.archetypes import Archetype
from .strain import radiant, wbgt
from .strain.phs_wrapper import StrainEngine
from .weather.types import WeatherHour

FIELDS = ["time_iso", "archetype", "tdb_c", "rh_pct", "v_ms", "tr_c", "radiant_source", "wbgt_c", "wbgt_note",
          "status", "fail_safe", "safe_minutes", "limiting", "synthetic", "reasons"]


def run_day(hours: List[WeatherHour], archetypes: List[Archetype], engine: Optional[StrainEngine] = None) -> List[dict]:
    engine = engine or StrainEngine()
    rows = []
    for h in hours:
        v = config.air_speed_from_wind(h.wind_ms)
        if h.tg_c is not None:
            tr, src = radiant.tr_from_globe(h.tg_c, h.tdb_c, v), "globe"
        else:
            tr, src = radiant.tr_fallback(h.tdb_c, h.solar_wm2), "fallback_offset"
        w, wnote = wbgt.compute_wbgt(h)
        for a in archetypes:
            r = engine.run_segment(h.tdb_c, tr, v, h.rh_pct, a.met_wm2, a.clo, a.posture,
                                   100 if a.acclimatized else 0, a.drink)
            rows.append({"time_iso": h.time_iso, "archetype": a.id, "tdb_c": h.tdb_c, "rh_pct": h.rh_pct,
                         "v_ms": v, "tr_c": round(tr, 2), "radiant_source": src,
                         "wbgt_c": None if w is None else round(w, 2), "wbgt_note": wnote,
                         "status": r.status, "fail_safe": r.fail_safe,
                         "safe_minutes": None if r.safe_minutes is None else round(r.safe_minutes, 1),
                         "limiting": r.limiting, "synthetic": h.synthetic, "reasons": "; ".join(r.reasons)})
    return rows


def write_csv(rows: List[dict], path: str):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
