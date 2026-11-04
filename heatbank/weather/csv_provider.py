"""Read hourly weather from a CSV we have the right to use (e.g. our own sensor node, D3).
Columns: time_iso,tdb_c,rh_pct,wind_ms[,solar_wm2,pressure_hpa,tg_c]"""
import csv
from typing import List
from .types import WeatherHour


class CsvProvider:
    def __init__(self, path: str, licence_note: str):
        if not licence_note.strip():
            raise ValueError("licence_note is required: declare where this data comes from (P4).")
        self.path, self.licence_note, self.name = path, licence_note, f"csv:{path}"

    def hours(self) -> List[WeatherHour]:
        def f(row, k):
            v = row.get(k, "")
            return float(v) if v not in ("", None) else None
        out = []
        with open(self.path, newline="") as fh:
            for row in csv.DictReader(fh):
                out.append(WeatherHour(
                    time_iso=row["time_iso"], tdb_c=float(row["tdb_c"]), rh_pct=float(row["rh_pct"]),
                    wind_ms=float(row["wind_ms"]), solar_wm2=f(row, "solar_wm2"),
                    pressure_hpa=f(row, "pressure_hpa"), tg_c=f(row, "tg_c")))
        return out
