"""C5 planner. Rule P1: output may only HOLD or REDUCE exposure versus the conservative baseline; it never extends
exposure to gain output. Output is a recommendation; humans decide."""
from dataclasses import dataclass
from typing import List, Optional
from .. import config


@dataclass
class HourPlan:
    work_min: int
    rest_min: int
    baseline_work_min: int
    rotate_suggested: bool
    note: str


def baseline_work_min(remaining_allowable_min: float) -> int:
    """Conservative baseline: at most PLAN_WORK_FRACTION of the remaining allowable time, max 60, rounded DOWN."""
    w = min(60.0, max(0.0, remaining_allowable_min) * config.PLAN_WORK_FRACTION)
    r = config.PLAN_ROUND_MIN
    return int(w // r * r)


def plan_hour(remaining_allowable_min: Optional[float], fail_safe: bool = False, degraded: bool = False,
              heavy_task: bool = False) -> HourPlan:
    base = baseline_work_min(remaining_allowable_min or 0.0)
    work = base
    note = ""
    if fail_safe or remaining_allowable_min is None:
        work, note = 0, "fail-safe: no work planned, cool down"
    elif degraded:
        work = min(work, config.DEGRADED_WORK_CAP_MIN)
        note = "degraded mode: conservative preset"
    work = min(work, base)                       # P1 enforced in code, not by convention
    assert 0 <= work <= base <= 60
    rotate = heavy_task and work < 60 and not fail_safe
    return HourPlan(work, 60 - work, base, rotate, note)


def suggest_shift_windows(hourly_work_min: List[int], min_work: int = 45) -> List[tuple]:
    """Contiguous hour-index windows where planned work >= min_work: candidate slots for heavy tasks."""
    out, start = [], None
    for i, w in enumerate(hourly_work_min + [-1]):
        if w >= min_work and start is None: start = i
        if w < min_work and start is not None: out.append((start, i - 1)); start = None
    return out


def day_outlook(engine, archetype, hours) -> dict:
    """Fresh-start view of a day: for each shift hour the baseline work minutes if the worker starts that hour rested,
    plus the windows where heavy work is least constrained. Recommendation only (P1)."""
    from ..sim.tracker import ExposureTracker
    from ..sim.harness import shift_hours
    rows = []
    for h in shift_hours(hours):
        rem, _, fs = ExposureTracker(engine, archetype).remaining_and_fraction(h)
        p = plan_hour(rem, fail_safe=fs, heavy_task=archetype.task == "heavy")
        rows.append({"hour": h.time_iso[11:13], "allowable_min": None if fs else round(rem), "work_min": p.work_min, "fail_safe": fs})
    return {"hours": rows, "heavy_windows": suggest_shift_windows([r["work_min"] for r in rows])}
