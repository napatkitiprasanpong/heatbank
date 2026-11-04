"""Offline-first cache (P5). Stores the latest forecast with a timestamp; reports age so Part 2 can fail safe (P2)."""
import json
import os
import time
from typing import List, Tuple
from .types import WeatherHour
from .. import config


def save(path: str, provider_name: str, licence_note: str, hours: List[WeatherHour], now: float = None):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    doc = {"fetched_at": now if now is not None else time.time(), "provider": provider_name,
           "licence_note": licence_note, "hours": [h.to_dict() for h in hours]}
    with open(path, "w") as fh:
        json.dump(doc, fh)


def load(path: str, now: float = None) -> Tuple[List[WeatherHour], float, bool]:
    """Return (hours, age_minutes, fresh). Missing/corrupt cache => ([], inf, False): never 'fresh'."""
    try:
        with open(path) as fh:
            doc = json.load(fh)
        hours = [WeatherHour(**h) for h in doc["hours"]]
        age = ((now if now is not None else time.time()) - float(doc["fetched_at"])) / 60.0
    except (OSError, ValueError, KeyError, TypeError):
        return [], float("inf"), False
    return hours, age, age <= config.MAX_FORECAST_AGE_MIN
