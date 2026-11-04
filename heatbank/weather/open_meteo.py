"""D1 Open-Meteo adapter. UNRESOLVED licence (plan U2): free tier is non-commercial only, CC BY 4.0
credit required. Disabled unless the caller opts in. Not tested against the live API in Part 1 (no network
in the build sandbox); the response layout below is from memory of the public docs: verify it."""
import json
import urllib.parse
import urllib.request
from typing import List
from .types import WeatherHour
from .. import config

BASE = "https://api.open-meteo.com/v1/forecast"
HOURLY = "temperature_2m,relative_humidity_2m,wind_speed_10m,shortwave_radiation,surface_pressure"


class LicenceGuardError(RuntimeError):
    pass


def parse_response(payload: dict) -> List[WeatherHour]:
    h = payload["hourly"]
    n = len(h["time"])
    return [WeatherHour(
        time_iso=h["time"][i], tdb_c=h["temperature_2m"][i], rh_pct=h["relative_humidity_2m"][i],
        wind_ms=h["wind_speed_10m"][i], solar_wm2=h.get("shortwave_radiation", [None] * n)[i],
        pressure_hpa=h.get("surface_pressure", [None] * n)[i]) for i in range(n)]


class OpenMeteoProvider:
    name = "open-meteo"
    licence_note = ("Open-Meteo, CC BY 4.0, free tier NON-COMMERCIAL only. Credit: Weather data by Open-Meteo.com. "
                    "Status UNRESOLVED (U2).")

    def __init__(self, lat: float, lon: float, allow_noncommercial: bool = False, forecast_days: int = 2):
        if config.OPEN_METEO_REQUIRES_OPT_IN and not allow_noncommercial:
            raise LicenceGuardError(
                "Open-Meteo free tier is non-commercial only (plan D1/U2). Resolve the licence, then pass "
                "allow_noncommercial=True.")
        self.lat, self.lon, self.forecast_days = lat, lon, forecast_days

    def hours(self) -> List[WeatherHour]:
        q = urllib.parse.urlencode({
            "latitude": self.lat, "longitude": self.lon, "hourly": HOURLY, "wind_speed_unit": "ms",
            "timezone": "auto", "forecast_days": self.forecast_days})
        with urllib.request.urlopen(f"{BASE}?{q}", timeout=20) as r:
            return parse_response(json.load(r))
