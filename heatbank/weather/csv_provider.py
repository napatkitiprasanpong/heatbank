"""Read hourly weather from a CSV we have the right to use (e.g. our own sensor node, D3).
Columns: time_iso,tdb_c,rh_pct,wind_ms[,solar_wm2,pressure_hpa,tg_c]"""
import csv
from typing import List
from .types import WeatherHour


# v0.5.4: common fill values for missing data (NASA POWER uses -999). They must never be read as measurements.
FILL_VALUES = {-999.0, -9999.0, -99999.0, 999.0, 9999.0}
NAN = float("nan")


class CsvProvider:
    def __init__(self, path: str, licence_note: str):
        if not licence_note.strip():
            raise ValueError("licence_note is required: declare where this data comes from (P4).")
        self.path, self.licence_note, self.name = path, licence_note, f"csv:{path}"

    def hours(self) -> List[WeatherHour]:
        def f(row, k):                                   # optional column: blank or fill value => None (unknown)
            v = row.get(k, "")
            if v in ("", None): return None
            x = float(v)
            return None if x in FILL_VALUES or x != x else x

        def req(row, k):                                 # required column: blank or fill value => NaN, which the model gate turns into fail-safe Red
            v = row.get(k, "")
            if v in ("", None): return NAN
            x = float(v)
            return NAN if x in FILL_VALUES else x
        out = []
        with open(self.path, newline="") as fh:
            for row in csv.DictReader(fh):
                out.append(WeatherHour(
                    time_iso=row["time_iso"], tdb_c=req(row, "tdb_c"), rh_pct=req(row, "rh_pct"),
                    wind_ms=req(row, "wind_ms"), solar_wm2=f(row, "solar_wm2"),
                    pressure_hpa=f(row, "pressure_hpa"), tg_c=f(row, "tg_c")))
        return out
