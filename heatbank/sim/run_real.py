"""Run REAL weather (a CSV you have the right to use) through the planner, one shift per calendar day, with a simulated crew.

    python -m heatbank.sim.run_real --csv data/real/abudhabi_2025-07.csv --csv-licence "NASA POWER, CC BY 4.0, retrieved 2026-11-05" --out out/real

What this is: real weather, SIMULATED workers. It tests the weather path (data quality, gates, planner, alert levels over many real days).
It does NOT validate that alerts match what happens to people (plan honesty rule): that needs measured human data (V4) or a pilot.
Time stamps must be LOCAL (shift hours 07-17 are read from the string). Days with fewer than 10 shift hours are skipped and listed."""
import argparse, csv, math, os, sys
from collections import Counter, defaultdict
from .. import config
from ..archetypes.archetypes import build_archetypes
from ..provenance import write_meta
from ..strain.phs_wrapper import StrainEngine
from ..weather.csv_provider import CsvProvider
from . import tracker as T
from .harness import simulate_worker, shift_hours, lead_time


def _num(x):
    return x is not None and x == x


def quality(hours):
    sh = shift_hours(hours)
    vmax = config.VALID_RANGES["v_ms"][1]
    q = {"hours": len(hours), "shift_hours": len(sh),
         "tdb_missing": sum(1 for h in sh if not _num(h.tdb_c)), "rh_missing": sum(1 for h in sh if not _num(h.rh_pct)),
         "wind_missing": sum(1 for h in sh if not _num(h.wind_ms)), "solar_missing": sum(1 for h in sh if not _num(h.solar_wm2)),
         "wind_over_limit": sum(1 for h in sh if _num(h.wind_ms) and h.wind_ms > vmax),
         "tdb_over_50": sum(1 for h in sh if _num(h.tdb_c) and h.tdb_c > config.VALID_RANGES["tdb_c"][1]),
         "tdb_below_15": sum(1 for h in sh if _num(h.tdb_c) and h.tdb_c < config.VALID_RANGES["tdb_c"][0]),
         "utc_like": any(("Z" in h.time_iso or "+" in h.time_iso[10:]) for h in hours[:48])}
    ok = [h.tdb_c for h in sh if _num(h.tdb_c)]
    q["tdb_min"], q["tdb_max"] = (min(ok), max(ok)) if ok else (None, None)
    return q


def run(csv_path, licence, out, rest_area=None, adherence=1.0):
    if rest_area: config.REST_AREA = rest_area
    hours = CsvProvider(csv_path, licence).hours()
    q = quality(hours)
    engine = StrainEngine()
    problems = engine.smoke_test()
    if problems: raise SystemExit("model smoke test failed, refusing to run: " + "; ".join(problems))
    # instrumentation: which limit is binding when a worker is at Red (water loss vs rectal temperature)?
    why = Counter(); orig = T.ExposureTracker.remaining_and_fraction
    def wrapped(self, h):
        rem, frac, fs = orig(self, h)
        if frac is not None and frac >= 1.0 - 1e-9 and not fs:
            why["water loss" if "water" in self._run(h, True, config.PHS_DURATION_MIN, self.state).limiting else "rectal temperature"] += 1
        return rem, frac, fs
    T.ExposureTracker.remaining_and_fraction = wrapped
    by_day = defaultdict(list)
    for h in hours: by_day[h.time_iso[:10]].append(h)
    archs = build_archetypes(); rows, skipped, done = [], [], {}
    try:
        for day, hs in sorted(by_day.items()):
            sh = shift_hours(hs)
            if len(sh) < config.SHIFT_HOURS[1] - config.SHIFT_HOURS[0]: skipped.append((day, len(sh))); continue
            ok = [h for h in sh if _num(h.tdb_c)]
            tmax = max((h.tdb_c for h in ok), default=float("nan"))
            wmax = max((h.wind_ms for h in sh if _num(h.wind_ms)), default=float("nan"))
            gate_c = gate_p = tot_p = red_rest = red_work = 0; worked = 0; reached = 0; leads = []
            for a in archs:
                cont = simulate_worker(engine, a, hs, "continuous")
                if cont.first_red_min is not None: reached += 1
                lt = lead_time(cont)
                if lt is not None: leads.append(lt)
                pl = simulate_worker(engine, a, hs, "planned", adherence)
                tot_p += sum(pl.minutes_at.values()); worked += pl.worked_min
                gate_p += sum(1 for r in pl.hourly if r["gate"])
                for r in pl.hourly:
                    if r["level_max"] == "Red" and not r["gate"]:
                        if r["work_planned_min"] == 0: red_rest += 1
                        else: red_work += 1
                for k in ("Green", "Yellow", "Orange", "Red"): rows.append((day, a.id, k, pl.minutes_at[k]))
            n = len(archs) * len(sh)
            lv = defaultdict(int)
            for d_, a_, k, m in rows:
                if d_ == day: lv[k] += m
            rows_day = dict(day=day, tmax=round(tmax, 1), wind_max=round(wmax, 1), cont_reached_limit=f"{reached}/{len(archs)}",
                            median_lead_min=sorted(leads)[len(leads) // 2] if leads else "", planned_red_pct=round(100 * lv["Red"] / tot_p, 1),
                            planned_orange_pct=round(100 * lv["Orange"] / tot_p, 1), planned_worked_pct=round(100 * worked / tot_p, 1),
                            gated_pct=round(100 * gate_p / n, 1), red_hours_resting=red_rest, red_hours_with_work=red_work)
            done[day] = rows_day
    finally:
        T.ExposureTracker.remaining_and_fraction = orig
    summary = [done[d] for d in sorted(done)]
    os.makedirs(out, exist_ok=True)
    cp = os.path.join(out, "real_weather_days.csv")
    if summary:
        with open(cp, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
        write_meta(cp, source=csv_path, licence_note=licence, synthetic=False, model="pythermalcomfort PHS (ISO 7933), SIMULATED crew, REAL weather")
    L = ["# Real-weather run (real weather, SIMULATED crew, UNVERIFIED archetypes)", "",
         f"Source: `{csv_path}`. Licence note: {licence}. Rest area: {config.REST_AREA}. Plan followed at {adherence:.0%}.", "",
         "## Data quality (shift hours only)", ""] + [f"- {k}: {v}" for k, v in q.items()]
    if q["utc_like"]: L.append("- **WARNING: timestamps look like UTC. Shift hours are read from the string, so convert to local time first.**")
    if q["wind_over_limit"]: L.append(f"- **{q['wind_over_limit']} shift hours have wind above the model's {config.VALID_RANGES['v_ms'][1]} m/s limit: each is Red by the validity gate (check what height the wind is for).**")
    L += ["", "## Per day", ""]
    if summary:
        cols = list(summary[0]); L += ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        L += ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in summary]
    if skipped: L += ["", "Skipped (incomplete shift): " + ", ".join(f"{d} ({n} h)" for d, n in skipped)]
    tot = sum(why.values())
    if tot: L += ["", f"Red evaluations by binding limit (planned runs, gate excluded): " + ", ".join(f"{k} {v} ({v / tot:.0%})" for k, v in why.most_common())]
    L += ["", f"Model calls {engine.calls}, model errors {engine.model_errors} (must be 0).",
          "Honesty: real weather does not make this a validation. Alert levels are model outputs for simulated workers."]
    with open(os.path.join(out, "real_weather_summary.md"), "w", encoding="utf-8") as fh: fh.write("\n".join(L))
    print("\n".join(L))
    return summary, q, why


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True); ap.add_argument("--csv-licence", required=True, help="declare where the data comes from (P4)")
    ap.add_argument("--out", default="out/real"); ap.add_argument("--rest-area", choices=sorted(config.REST_AREAS))
    ap.add_argument("--adherence", type=float, default=1.0)
    a = ap.parse_args(argv)
    run(a.csv, a.csv_licence, a.out, a.rest_area, a.adherence)


if __name__ == "__main__":
    main()
