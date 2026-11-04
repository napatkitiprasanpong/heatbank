"""Exposure tracking with PHS carry-over (plan s.7): fraction used = 1 - remaining/fresh-start allowable time,
both evaluated for continued WORK under current conditions. Rest segments run in shade (tr = tdb, met = REST_MET)."""
from typing import Optional, Tuple
from .. import config
from ..strain import radiant
from ..strain.phs_wrapper import StrainEngine, PhsState
from ..weather.types import WeatherHour


def work_conditions(h: WeatherHour):
    v = config.air_speed_from_wind(h.wind_ms)
    tr = radiant.tr_from_globe(h.tg_c, h.tdb_c, v) if h.tg_c is not None else radiant.tr_fallback(h.tdb_c, h.solar_wm2)
    return h.tdb_c, tr, v, h.rh_pct


def lookahead_remaining(trk, hours_ahead) -> Optional[float]:
    """Remaining allowable minutes for continued work, taking the WORSE of now and the next hours' conditions (audit A3).
    Only ever lowers the number, so it can only reduce planned work (P1). None when any evaluation is fail-safe."""
    worst = None
    for h in hours_ahead:
        rem, _, fs = trk.remaining_and_fraction(h)
        if fs: return None
        worst = rem if worst is None else min(worst, rem)
    return worst


class ExposureTracker:
    def __init__(self, engine: StrainEngine, archetype):
        self.engine, self.a, self.state = engine, archetype, PhsState()
        self.sweat_g = 0.0          # cumulative simulated sweat loss, g (model output, not a measurement)

    def _run(self, h, working: bool, minutes: float, state):
        tdb, tr, v, rh = work_conditions(h)
        if not working:
            tr, met = tdb, config.REST_MET_WM2          # shade assumption (PROPOSED)
        else:
            met = self.a.met_wm2
        return self.engine.run_segment(tdb, tr, v, rh, met, self.a.clo, self.a.posture,
                                       100 if self.a.acclimatized else 0, self.a.drink, duration_min=minutes, state=state)

    def step(self, h: WeatherHour, minutes: float, working: bool):
        r = self._run(h, working, minutes, self.state)
        if not r.fail_safe and r.state.values:
            self.state = r.state
            if r.sweat_loss_g is not None: self.sweat_g = r.sweat_loss_g
        return r

    def remaining_and_fraction(self, h: WeatherHour) -> Tuple[Optional[float], Optional[float], bool]:
        """(remaining allowable minutes, fraction used, fail_safe) for continued work now."""
        fresh = self._run(h, True, config.PHS_DURATION_MIN, PhsState())
        if fresh.fail_safe or fresh.safe_minutes is None:
            return 0.0, None, True
        now = self._run(h, True, config.PHS_DURATION_MIN, self.state)
        if now.fail_safe or now.safe_minutes is None:
            return 0.0, None, True
        s0, rem = fresh.safe_minutes, now.safe_minutes
        frac = 1.0 if s0 <= 0 else min(max(1.0 - rem / s0, 0.0), 1.0 + 1e-9)
        return rem, (1.0 if rem <= 0 else frac), False
