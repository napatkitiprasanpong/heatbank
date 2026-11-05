"""C6 alert engine. 4 levels, ONE action each, pictogram id + short text key. Text is English placeholder only:
Thai and a third language arrive in Part 3 and Thai must be human-reviewed (plan C6)."""
from dataclasses import dataclass
from typing import Optional
from .. import config

GREEN, YELLOW, ORANGE, RED = 0, 1, 2, 3
NAMES = ["Green", "Yellow", "Orange", "Red"]
ACTIONS = {   # level -> (action_key, pictogram id, English text)
    GREEN:  ("normal_work", "pic_water", "Normal work. Keep water within reach."),
    YELLOW: ("drink_shade_break", "pic_shade", "Drink water and take your scheduled shade break."),
    ORANGE: ("reduce_cool_now", "pic_cooldown", "Reduce intensity or rotate task. Cool down now."),
    RED:    ("stop_cool_buddy", "pic_stop_medic", "Stop heavy work. Cool down. Buddy check. Call the medic if symptoms."),
}


@dataclass
class Alert:
    level: int
    name: str
    action_key: str
    pictogram: str
    text_en: str
    fraction_used: Optional[float]
    degraded_banner: Optional[str]
    reasons: list


def level_from_fraction(f: float) -> int:
    y, o, r = config.ALERT_FRACTIONS
    return RED if f >= r else ORANGE if f >= o else YELLOW if f >= y else GREEN


def compose(fraction_used: Optional[float], fail_safe: bool = False, fallback=None) -> Alert:
    """Never lowers (P2): fail-safe or missing fraction => Red; fallback can only raise."""
    reasons = []
    if fail_safe or fraction_used is None:
        level = RED; reasons.append("fail-safe: model gate or missing fraction")
    else:
        level = level_from_fraction(fraction_used)
    banner = None
    if fallback is not None:
        raised = fallback.apply(level)
        if raised > level: reasons.append(f"raised {NAMES[level]} -> {NAMES[raised]} by degraded mode")
        level = raised
        banner = fallback.banner_key
        reasons += fallback.reasons
    key, pic, text = ACTIONS[level]
    return Alert(level, NAMES[level], key, pic, text, fraction_used, banner, reasons)


def state_fraction(t_re_c: Optional[float]) -> Optional[float]:
    """Audit A10: how far predicted rectal temperature has moved from base toward the limit (0..1). None if unknown."""
    if t_re_c is None: return None
    span = config.STATE_T_RE_LIMIT_C - config.STATE_T_RE_BASE_C
    return min(1.0, max(0.0, (t_re_c - config.STATE_T_RE_BASE_C) / span))


def state_level(t_re_c: Optional[float]) -> Optional[int]:
    """Body-state reading, shown NEXT TO the conditions level. It never replaces or lowers it (P2). None when unknown."""
    f = state_fraction(t_re_c)
    return None if f is None else level_from_fraction(f)
