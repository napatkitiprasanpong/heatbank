"""Download hourly NASA POWER weather for one site and write a CSV that heatbank's CsvProvider reads.

    python scripts/fetch_nasa_power.py --lat 24.45 --lon 54.38 --start 2025-07-01 --end 2025-07-31 --out data/real/abudhabi_2025-07.csv

Licence (read from power.larc.nasa.gov on 2026-11-05): CC BY 4.0, no API key. Credit NASA POWER in DATA_SOURCES.md.
Variables: T2M air temp (C), RH2M (%), WS2M wind at 2 m (m/s: worker height, so no 10 m correction is needed), ALLSKY_SFC_SW_DWN (W/m2), PS (kPa).
Grid data: MERRA-2 / CERES at roughly 0.5 degree, NOT a point measurement. Say so in the documentation.
Time: asks for LST (local solar time) because heatbank's shift hours (07-17) are read straight from the timestamp string. UTC would shift the shift.

UNTESTED against the live service (the build sandbox has no network). The request names and the JSON layout (properties.parameter.<VAR>.<YYYYMMDDHH>)
are from memory of the POWER docs: if a call fails, open https://power.larc.nasa.gov/api/pages/ and fix PARAMS / parse(). parse() IS unit-tested on a mock.
Fill value is -999: written as blank, which the loader turns into 'missing' (fail-safe Red), never into a measurement."""
import argparse, csv, json, os, sys, urllib.parse, urllib.request

URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"
VARS = "T2M,RH2M,WS2M,ALLSKY_SFC_SW_DWN,PS"
FILL = -999.0


def parse(payload: dict):
    p = payload["properties"]["parameter"]
    keys = sorted(p["T2M"])
    rows = []
    for k in keys:                                   # k = YYYYMMDDHH
        def g(name, scale=1.0):
            v = p.get(name, {}).get(k)
            return "" if v is None or float(v) == FILL else round(float(v) * scale, 3)
        rows.append({"time_iso": f"{k[0:4]}-{k[4:6]}-{k[6:8]}T{k[8:10]}:00", "tdb_c": g("T2M"), "rh_pct": g("RH2M"), "wind_ms": g("WS2M"),
                     "solar_wm2": g("ALLSKY_SFC_SW_DWN"), "pressure_hpa": g("PS", 10.0), "tg_c": ""})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, required=True); ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--start", required=True, help="YYYY-MM-DD"); ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    q = urllib.parse.urlencode({"parameters": VARS, "community": "RE", "latitude": a.lat, "longitude": a.lon,
                                "start": a.start.replace("-", ""), "end": a.end.replace("-", ""), "format": "JSON", "time-standard": "LST"})
    with urllib.request.urlopen(f"{URL}?{q}", timeout=60) as r:
        rows = parse(json.load(r))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["time_iso", "tdb_c", "rh_pct", "wind_ms", "solar_wm2", "pressure_hpa", "tg_c"])
        w.writeheader(); w.writerows(rows)
    blanks = sum(1 for r in rows for k in ("tdb_c", "rh_pct", "wind_ms") if r[k] == "")
    print(f"wrote {len(rows)} hours to {a.out}; required fields missing: {blanks}")
    print("DATA_SOURCES.md row: NASA POWER hourly (MERRA-2/CERES), NASA Langley, CC BY 4.0, https://power.larc.nasa.gov/, "
          f"retrieved <today>, lat {a.lat} lon {a.lon} {a.start}..{a.end}, personal data: no, credit: 'NASA POWER Project'.")


if __name__ == "__main__":
    main()
