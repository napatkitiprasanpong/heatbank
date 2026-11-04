"""V2 simulation harness. Everything produced here is SIMULATED (synthetic weather, simulated archetypes). No real-world claim."""
import random
from dataclasses import dataclass, field
from typing import List, Optional
from .. import config
from ..alerts import engine as alerts
from ..planner.planner import plan_hour
from ..strain.phs_wrapper import StrainEngine
from ..weather.types import WeatherHour
from .tracker import ExposureTracker, lookahead_remaining


@dataclass
class RunResult:
    archetype: str
    mode: str                      # 'planned' or 'continuous'
    adherence: float
    minutes_at: dict               # level name -> minutes
    first_orange_min: Optional[int]
    first_red_min: Optional[int]
    worked_min: int
    steps: int
    hourly: list = field(default_factory=list)


def shift_hours(hours: List[WeatherHour]) -> List[WeatherHour]:
    lo, hi = config.SHIFT_HOURS
    return [h for h in hours if lo <= int(h.time_iso[11:13]) < hi]


def simulate_worker(engine: StrainEngine, archetype, hours: List[WeatherHour], mode: str = "planned",
                    adherence: float = 1.0, seed: int = 0, degraded: bool = False, lookahead: int = None) -> RunResult:
    rng = random.Random(f"{seed}-{archetype.id}-{mode}-{adherence}")
    trk = ExposureTracker(engine, archetype)
    minutes_at = {n: 0 for n in alerts.NAMES}
    t, first_o, first_r, worked = 0, None, None, 0
    steps, hourly = 0, []
    la = config.PLAN_LOOKAHEAD_H if lookahead is None else lookahead
    sh = shift_hours(hours)
    for i, h in enumerate(sh):
        rem, frac, fs = trk.remaining_and_fraction(h)
        if mode == "planned":
            if la > 0 and not fs:                     # audit A3: size the hour against the worse of now and the next hour(s)
                rem_la = lookahead_remaining(trk, sh[i:i + 1 + la])
                if rem_la is None: fs = True
                else: rem = min(rem, rem_la)
            plan = plan_hour(rem, fail_safe=fs, degraded=degraded, heavy_task=archetype.task == "heavy")
            work_budget = plan.work_min
        else:
            work_budget = 60
        sweat_before, level_h = trk.sweat_g, 0
        for off in range(0, 60, config.STEP_MIN):
            planned_work = off < work_budget
            working = planned_work or (mode == "planned" and rng.random() > adherence)   # skipped rest = worked anyway
            r = trk.step(h, config.STEP_MIN, working)
            _, frac, fs = trk.remaining_and_fraction(h)
            a = alerts.compose(frac, fs)
            level_h = max(level_h, a.level)
            minutes_at[a.name] += config.STEP_MIN
            worked += config.STEP_MIN if working else 0
            if a.level >= alerts.ORANGE and first_o is None: first_o = t
            if a.level >= alerts.RED and first_r is None: first_r = t
            t += config.STEP_MIN; steps += 1
        hourly.append({"hour": h.time_iso[11:13], "work_planned_min": work_budget, "level_max": alerts.NAMES[level_h],
                       "fraction_used_end": None if frac is None else round(frac, 3),
                       "water_est_ml": round(trk.sweat_g - sweat_before),
                       "rotate": bool(mode == "planned" and plan.rotate_suggested)})
    return RunResult(archetype.id, mode, adherence, minutes_at, first_o, first_r, worked, steps, hourly)


def lead_time(r: RunResult) -> Optional[int]:
    """Minutes from first Orange to model limit (first Red) for a continuous-work worker. None if limit never reached."""
    if r.first_red_min is None or r.first_orange_min is None: return None
    return r.first_red_min - r.first_orange_min
