"""Exposure tracking with PHS carry-over (plan s.7): fraction used = 1 - remaining/fresh-start allowable time,
both evaluated for continued WORK under current conditions. Rest segments run where config.REST_AREA says (default: shade,
tr = tdb, met = REST_MET). v0.4: the rest area is a parameter, recovery is tested (A9), cumulative sweat is tracked here (A12),
and a body-state reading is available next to the conditions level (A10)."""
from typing import Optional, Tuple
from .. import config
from ..alerts import engine as alerts
from ..strain import radiant
from ..strain.phs_wrapper import StrainEngine, PhsState
from ..weather.types import WeatherHour


def work_conditions(h: WeatherHour):
    v = config.air_speed_from_wind(h.wind_ms)
    tr = radiant.tr_from_globe(h.tg_c, h.tdb_c, v) if h.tg_c is not None else radiant.tr_fallback(h.tdb_c, h.solar_wm2)
    return h.tdb_c, tr, v, h.rh_pct


def rest_conditions(h: WeatherHour):
    """Inputs for a rest segment at the configured rest area (audit A9). Never invents a cooler place than the preset says."""
    p = config.REST_AREAS[config.REST_AREA]
    tdb = h.tdb_c if p["tdb"] is None else p["tdb"]
    tr = tdb if p["tr"] == "tdb" else p["tr"]
    v = config.air_speed_from_wind(h.wind_ms) if p["v"] is None else p["v"]
    if p.get("v_min") is not None: v = max(v, p["v_min"])
    rh = h.rh_pct if p["rh"] is None else p["rh"]
    return tdb, tr, v, rh


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
        if working:
            tdb, tr, v, rh = work_conditions(h); met = self.a.met_wm2
        else:
            tdb, tr, v, rh = rest_conditions(h); met = config.REST_MET_WM2      # rest area assumption (PROPOSED)
        return self.engine.run_segment(tdb, tr, v, rh, met, self.a.clo, self.a.posture,
                                       100 if self.a.acclimatized else 0, self.a.drink, duration_min=minutes, state=state)

    def step(self, h: WeatherHour, minutes: float, working: bool):
        r = self._run(h, working, minutes, self.state)
        if not r.fail_safe and r.state.values:
            self.state = r.state
            if r.sweat_loss_g is not None:
                # A12: if the library does not carry its sweat total, sum segments ourselves. Unknown (None) => sum, which can only overstate (P2).
                if self.engine.sweat_carries is True: self.sweat_g = r.sweat_loss_g
                else: self.sweat_g += r.sweat_loss_g
        return r

    def t_re(self) -> Optional[float]:
        return self.state.values.get("t_re") if self.state and self.state.values else None

    def state_level(self) -> Optional[int]:
        """Body-state reading from predicted rectal temperature (A10). None before any exposure."""
        return alerts.state_level(self.t_re())

    def strained(self) -> bool:
        t = self.t_re()
        return t is not None and t > config.STATE_T_RE_BASE_C + config.STRAINED_ABOVE_C

    def rest_recovers(self, h: WeatherHour) -> Optional[bool]:
        """Audit A9. Would resting here for REST_RECOVERY_MIN minutes lower predicted rectal temperature? Does not change state.
        None = cannot tell (no accumulated strain yet, or the model did not answer): callers treat None as 'not shown to fail'."""
        t0 = self.t_re()
        if t0 is None or not self.strained(): return None
        r = self._run(h, False, config.REST_RECOVERY_MIN, self.state)
        if r.fail_safe or r.t_re_end is None: return None
        return r.t_re_end <= t0 - config.REST_RECOVERY_EPS_C

    def remaining_and_fraction(self, h: WeatherHour) -> Tuple[Optional[float], Optional[float], bool]:
        """(remaining allowable minutes, fraction used, fail_safe) for continued work now."""
        fresh = self._run(h, True, config.PHS_DURATION_MIN, PhsState())
        if fresh.fail_safe or fresh.safe_minutes is None:
            return 0.0, None, True
        now = self._run(h, True, config.PHS_DURATION_MIN, self.state)
        if now.fail_safe or now.safe_minutes is None:
            return 0.0, None, True
        s0, rem = fresh.safe_minutes, now.safe_minutes
        t = self.t_re()
        if t is not None and t >= config.STATE_T_RE_LIMIT_C:     # predicted core temperature is past the ISO limit: Red, whatever the minute counting says
            return 0.0, 1.0, False
        self.engine.cap_checks += 1                                            # A11 diagnostic: ratio rests on the cap when s0 is capped
        if s0 >= config.PHS_DURATION_MIN - 1e-9: self.engine.cap_hits += 1
        if config.WATER_GUARD_G is not None and self.sweat_g >= config.WATER_GUARD_G:   # A12 optional guard, only ever raises
            return 0.0, 1.0, False
        frac = 1.0 if s0 <= 0 else min(max(1.0 - rem / s0, 0.0), 1.0 + 1e-9)
        return rem, (1.0 if rem <= 0 else frac), False
