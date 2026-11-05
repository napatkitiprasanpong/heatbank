"""C9 fallback / fault logic. Principle P2: uncertainty, stale data or sensor failure RAISES the alert level, never lowers it.
All thresholds are PROPOSED (config.py)."""
from dataclasses import dataclass, field
from typing import List, Optional
from .. import config
from ..alerts.engine import ORANGE, RED


@dataclass
class FallbackState:
    degraded: bool = False
    reasons: List[str] = field(default_factory=list)
    min_level: int = 0
    raise_by: int = 0
    use_node: bool = True
    banner_key: Optional[str] = None

    def apply(self, clean_level: int) -> int:
        return min(RED, max(clean_level + self.raise_by, self.min_level))


def frozen(readings: List[float], n: int = None) -> bool:
    n = n or config.FROZEN_READINGS
    return len(readings) >= n and len(set(readings[-n:])) == 1


def spiked(readings: List[float], jump: float = None) -> bool:
    jump = jump or config.SPIKE_C
    return any(abs(b - a) > jump for a, b in zip(readings, readings[1:]))


def evaluate(forecast_age_min: Optional[float], have_forecast: bool = True, offline: bool = False,
             node_readings: Optional[List[float]] = None, battery_pct: Optional[float] = None,
             model_fail_safe: bool = False) -> FallbackState:
    fs = FallbackState()
    def flag(reason, banner, min_level=0, raise_by=0):
        fs.degraded = True; fs.reasons.append(reason); fs.banner_key = fs.banner_key or banner
        fs.min_level = max(fs.min_level, min_level); fs.raise_by = max(fs.raise_by, raise_by)
    if not have_forecast or forecast_age_min is None:
        flag("no forecast available", "banner_no_data", min_level=RED)
    elif forecast_age_min > config.MAX_FORECAST_AGE_MIN:
        flag(f"forecast stale ({forecast_age_min:.0f} min)", "banner_stale", min_level=ORANGE, raise_by=1)
    elif offline:
        flag("offline, using fresh cached forecast", "banner_offline")
    if node_readings:
        if frozen(node_readings): fs.use_node = False; flag("site sensor frozen", "banner_sensor", raise_by=1)
        elif spiked(node_readings): fs.use_node = False; flag("site sensor spike", "banner_sensor", raise_by=1)
    if battery_pct is not None and battery_pct < config.LOW_BATTERY_PCT:
        flag(f"low battery ({battery_pct:.0f}%)", "banner_battery")
    if model_fail_safe:
        flag("model gate / model error", "banner_model", min_level=RED)
    return fs


def adherence_raise(planned_work_min: float, worked_min: float, level: int):
    """Audit A15. The phone cannot see what the worker did, so an optional local break log tells it. Working longer than the plan
    (plus a grace period) RAISES the shown level by one; it never lowers it (P2). Returns (level, overdue).
    Mirrored in dashboard/core.js (parity test)."""
    overdue = worked_min > planned_work_min + config.ADHERENCE_GRACE_MIN
    return (min(RED, level + 1) if overdue else level), overdue
