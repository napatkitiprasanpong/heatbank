"""D8 NASA POWER hourly adapter: REAL (reanalysis + satellite-derived) weather for one place and one day.

Why this source: NASA's open-data listing says there are no restrictions on use, access or download of POWER data and asks
that the POWER project is cited (the two listings we read tag the licence differently, CC0 and CC BY 4.0, so we cite NASA,
which satisfies both). No API key, no account, no personal data. Declared in DATA_SOURCES.md (D8).

What it is NOT: a forecast, a measurement at the site, or a resolution a worker would feel. POWER hourly meteorology is
gridded model output (about 0.5 x 0.625 degrees), solar comes from satellite-based products at about 1 degree. Wind is at 10 m,
not at the worker. There is no globe temperature, so radiant temperature uses the solar fallback (config.TR_FALLBACK_MODE).
Say "replay of a real day", never "live".

Honesty about testing: the build sandbox could not reach NASA, so this parser was written from the public API page
(power.larc.nasa.gov/docs/services/api/temporal/hourly/) and the documented JSON layout, and is tested ONLY against a fixture
that mimics that layout (tests/test_nasa_power.py). The first real download on your machine is the real test. If the layout
differs, parse errors name what was found and the raw response is kept on disk so it can be inspected.
Unverified items: hour-stamp convention (start or end of hour), exact units string of the solar parameter.
"""
import datetime
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import List, Optional
from .types import WeatherHour

BASE = "https://power.larc.nasa.gov/api/temporal/hourly/point"
PARAMS = ("T2M", "RH2M", "WS10M", "PS", "ALLSKY_SFC_SW_DWN")
CREDIT = "Weather data: NASA Langley Research Center (LaRC) POWER Project, funded through the NASA Earth Science/Applied Science Program."
FILL_DEFAULT = -999.0


class NasaPowerError(RuntimeError):
    pass


def _unit_factor(param: str, units: Optional[str]) -> float:
    """Factor that converts the reported unit to the unit WeatherHour uses. Unknown units raise: no silent guessing."""
    u = (units or "").strip().lower().replace(" ", "")
    if param == "PS":                     # WeatherHour wants hPa; POWER documents surface pressure in kPa
        table = {"kpa": 10.0, "hpa": 1.0, "mb": 1.0, "mbar": 1.0, "pa": 0.01, "": 10.0}
    elif param == "ALLSKY_SFC_SW_DWN":    # hourly value is an hourly mean: W/m2 and Wh/m2 per hour are the same number
        table = {"w/m^2": 1.0, "w/m2": 1.0, "wh/m^2": 1.0, "wh/m2": 1.0, "wh/m^2/hr": 1.0, "w-hr/m^2": 1.0, "": 1.0}
    else:
        return 1.0
    if u not in table:
        raise NasaPowerError(f"unexpected unit {units!r} for {param}: refusing to guess a conversion (check the saved raw file)")
    return table[u]


def parse_response(payload: dict, utc_offset_h: float, local_date: str) -> List[WeatherHour]:
    """Turn a POWER hourly JSON payload (UTC stamps) into local-clock WeatherHour rows for one local date.
    Fill values (-999) are never used. If any value is missing for an hour, that hour is dropped and reported."""
    try:
        par = payload["properties"]["parameter"]
    except (KeyError, TypeError):
        keys = list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
        raise NasaPowerError(f"unexpected response layout (top-level: {keys}). Open the saved raw file and compare with the API page.")
    missing_p = [p for p in PARAMS if p not in par]
    if missing_p:
        raise NasaPowerError(f"parameters missing from response: {missing_p}; got {sorted(par)}")
    fill = FILL_DEFAULT
    try: fill = float(payload.get("header", {}).get("fill_value", FILL_DEFAULT))
    except (TypeError, ValueError): pass
    meta = payload.get("parameters") or {}
    fac = {p: _unit_factor(p, (meta.get(p) or {}).get("units")) for p in PARAMS}
    stamps = sorted(par["T2M"])
    out, dropped = [], []
    for s in stamps:
        try: utc = datetime.datetime.strptime(s, "%Y%m%d%H")
        except ValueError: raise NasaPowerError(f"unexpected time stamp {s!r} (expected YYYYMMDDHH)")
        loc = utc + datetime.timedelta(hours=utc_offset_h)
        if loc.strftime("%Y-%m-%d") != local_date: continue
        vals = {p: par[p].get(s) for p in PARAMS}
        if any(v is None or float(v) == fill for v in vals.values()):
            dropped.append(loc.strftime("%H:00")); continue
        out.append(WeatherHour(
            time_iso=loc.strftime("%Y-%m-%dT%H:00"), tdb_c=float(vals["T2M"]), rh_pct=min(100.0, max(0.0, float(vals["RH2M"]))),
            wind_ms=float(vals["WS10M"]) * fac["WS10M"], solar_wm2=max(0.0, float(vals["ALLSKY_SFC_SW_DWN"]) * fac["ALLSKY_SFC_SW_DWN"]),
            pressure_hpa=float(vals["PS"]) * fac["PS"], tg_c=None, synthetic=False))
    if dropped:
        raise NasaPowerError(f"missing values (fill {fill}) for local hours {dropped} on {local_date}: not interpolated (never invent data). "
                             "Pick another date; solar data lags meteorology by several days.")
    if not out:
        raise NasaPowerError(f"no rows for local date {local_date} in the response (UTC offset {utc_offset_h:+g} h)")
    return out


class NasaPowerProvider:
    """Real weather replay from NASA POWER. The raw response is kept in `cache_dir`, so the demo works offline afterwards (P5)."""
    licence_note = ("NASA POWER, no restrictions on use per NASA's open-data listing; cite the POWER project. "
                    + CREDIT + " Real reanalysis/satellite data, NOT a forecast, NOT measured at the site.")

    def __init__(self, lat: float, lon: float, date: str, utc_offset_h: float = 4.0, cache_dir: str = "data/real",
                 refresh: bool = False, timeout: int = 60):
        datetime.datetime.strptime(date, "%Y-%m-%d")        # fail early on a bad date
        if not (-90 <= lat <= 90 and -180 <= lon <= 180): raise ValueError("latitude/longitude out of range")
        self.lat, self.lon, self.date, self.utc_offset_h = lat, lon, date, utc_offset_h
        self.cache_dir, self.refresh, self.timeout = cache_dir, refresh, timeout
        self.name = f"nasa-power:{lat:.2f},{lon:.2f},{date}"
        self.retrieved_utc: Optional[str] = None

    @property
    def cache_path(self) -> str:
        return os.path.join(self.cache_dir, f"nasa_power_{self.lat:.2f}_{self.lon:.2f}_{self.date}.json")

    def request_url(self) -> str:
        d = datetime.datetime.strptime(self.date, "%Y-%m-%d")      # ask for the day before and after: local day can straddle UTC days
        q = urllib.parse.urlencode({
            "parameters": ",".join(PARAMS), "community": "SB", "longitude": self.lon, "latitude": self.lat,
            "start": (d - datetime.timedelta(days=1)).strftime("%Y%m%d"), "end": (d + datetime.timedelta(days=1)).strftime("%Y%m%d"),
            "format": "JSON", "time-standard": "UTC"})
        return f"{BASE}?{q}"

    def _download(self) -> dict:
        url, last = self.request_url(), None
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "heatbank-prototype/0.6 (hackathon; contact: project owner)"})
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                body = e.read(300).decode("utf-8", "replace")
                raise NasaPowerError(f"NASA POWER answered HTTP {e.code}: {body!r}")    # a 4xx/5xx will not fix itself in seconds
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last = e; time.sleep(1.5 * (attempt + 1))
        raise NasaPowerError(f"could not reach NASA POWER ({last!r}). Run once with internet; afterwards the saved file is used offline.")

    def raw(self) -> dict:
        if os.path.exists(self.cache_path) and not self.refresh:
            with open(self.cache_path, encoding="utf-8") as fh: doc = json.load(fh)
            self.retrieved_utc = doc.get("retrieved_utc")
            return doc["payload"]
        payload = self._download()
        self.retrieved_utc = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        os.makedirs(self.cache_dir, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as fh:        # saved BEFORE parsing, so a layout surprise can be inspected
            json.dump({"retrieved_utc": self.retrieved_utc, "request_url": self.request_url(), "source": "NASA POWER hourly API",
                       "credit": CREDIT, "payload": payload}, fh)
        return payload

    def hours(self) -> List[WeatherHour]:
        return parse_response(self.raw(), self.utc_offset_h, self.date)
