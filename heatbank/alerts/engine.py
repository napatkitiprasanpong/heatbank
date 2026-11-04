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
