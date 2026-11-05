"""heatbank command line.  Run `heatbank --help` (after `pip install -e .`) or `python -m heatbank.cli --help`.

  heatbank check                      what is installed, what is still unverified
  heatbank safe-minutes  --scenario hot_humid          safe minutes per hour per archetype (Part 1 pipeline)
  heatbank plan          --scenario hot_humid          shift plan: work/rest per hour, alert level, water estimate, heavy-work windows
  heatbank simulate      [--toy]                       V2 scenario stress test (SIMULATED)
  heatbank faults                                      V3 fault injection
Add --toy to any command to use the TOY stand-in model (loud banner, never a result)."""
import argparse, os, sys
from . import __version__, config
from .archetypes.archetypes import build_archetypes, unverified
from .pipeline import run_day, write_csv
from .planner.planner import day_outlook
from .provenance import write_meta, DISCLAIMER
from .sim import run_v2, run_v3
from .sim.harness import simulate_worker
from .sim.toy_model import toy_phs, TOY_LABEL
from .strain.phs_wrapper import StrainEngine, self_check
from .weather import cache
from .weather.factory import make_provider
from .weather.scenarios import SCENARIOS

REAL_LABEL = "pythermalcomfort PHS (ISO 7933)"


def _add_source(p):
    p.add_argument("--scenario", choices=sorted(SCENARIOS), help="synthetic scenario (D4)")
    p.add_argument("--csv"); p.add_argument("--csv-licence", default="", help="declare the licence/source of the CSV")
    p.add_argument("--open-meteo", nargs=2, type=float, metavar=("LAT", "LON"))
    p.add_argument("--allow-noncommercial", action="store_true", help="acknowledge Open-Meteo free-tier terms (U2)")
    p.add_argument("--cache", default="data/cache/last_forecast.json")
    p.add_argument("--toy", action="store_true", help="TOY model instead of PHS (not physiology)")
    p.add_argument("--out", default="out")


def _engine(toy):
    if toy:
        print(f"*** {TOY_LABEL}: demo only, numbers are NOT results ***", file=sys.stderr)
        return StrainEngine(toy_phs), TOY_LABEL
    eng = StrainEngine()
    try:
        problems = self_check(eng.phs)
    except ImportError:
        raise SystemExit("pythermalcomfort is not installed. Run: pip install -e .   (or use --toy for a demo)")
    if problems:
        print("[warning] installed phs() differs from the wrapper mapping (U6):", "; ".join(problems), file=sys.stderr)
    smoke = eng.smoke_test()
    if smoke:    # audit A1: do not turn an integration bug into an all-Red "safe" output
        raise SystemExit("model smoke test failed, refusing to produce results: " + "; ".join(smoke) + "\nRun scripts/check_signatures.py")
    return eng, REAL_LABEL


def _hours(a):
    """Weather with offline-first fallback (P5): provider -> cache; never silent."""
    prov = make_provider(a.scenario, a.csv, a.csv_licence, a.open_meteo, a.allow_noncommercial)
    try:
        hours = prov.hours(); cache.save(a.cache, prov.name, prov.licence_note, hours)
        return prov, hours, 0.0
    except Exception as e:
        hours, age, fresh = cache.load(a.cache)
        print(f"[degraded] provider failed ({e!r}); cache age {age:.0f} min, fresh={fresh}", file=sys.stderr)
        if not hours: raise SystemExit("no data and no cache: nothing to compute (fail safe)")
        return prov, hours, age


def cmd_check(a):
    print(f"HeatBank {__version__} | {DISCLAIMER}")
    for mod in ("pythermalcomfort", "thermofeel"):
        try:
            m = __import__(mod); print(f"  {mod}: installed, version {getattr(m, '__version__', '?')}")
        except ImportError:
            print(f"  {mod}: NOT installed")
    try:
        probs = self_check(StrainEngine().phs); print("  phs() mapping:", "OK" if not probs else "; ".join(probs))
    except ImportError:
        print("  phs() mapping: cannot check (library missing)")
    print(f"  archetypes with UNVERIFIED values: {len(unverified(build_archetypes()))}/12")
    print(f"  Open-Meteo opt-in required: {config.OPEN_METEO_REQUIRES_OPT_IN} (plan U2)")
    print("  For full signature details run: python scripts/check_signatures.py")


def cmd_safe(a):
    eng, label = _engine(a.toy); prov, hours, _ = _hours(a)
    rows = run_day(hours, build_archetypes(), eng)
    os.makedirs(a.out, exist_ok=True); path = os.path.join(a.out, "safe_minutes.csv"); write_csv(rows, path)
    write_meta(path, source=prov.name, licence_note=prov.licence_note, synthetic=hours[0].synthetic, model=label)
    print(f"wrote {len(rows)} rows to {path}")


def cmd_plan(a):
    eng, label = _engine(a.toy); prov, hours, age = _hours(a)
    archs = [x for x in build_archetypes() if not a.archetype or x.id == a.archetype]
    os.makedirs(a.out, exist_ok=True)
    lines = [f"# HeatBank shift plan ({prov.name}){'  SYNTHETIC' if hours[0].synthetic else ''}",
             f"Model: {label}. {DISCLAIMER}", ""]
    csv_rows = []
    for ar in archs:
        out = day_outlook(eng, ar, hours)
        sim = simulate_worker(eng, ar, hours, "planned", 1.0)
        lines += [f"## {ar.id}: {ar.label}", "",
                  "| hour | allowable if rested (min) | work / rest (min) | conditions level | body state (model) | used at end | water est. (ml) | note |", "|---|---|---|---|---|---|---|---|"]
        for o, hr in zip(out["hours"], sim.hourly):
            lines.append(f"| {hr['hour']}:00 | {'fail-safe' if o['fail_safe'] else o['allowable_min']} | {hr['work_planned_min']} / {60 - hr['work_planned_min']} | {hr['level_max']} | {hr.get('state_level') or '-'} | {hr['fraction_used_end']} | {hr['water_est_ml']} | {'rest area does not cool: move to cooler rest' if not hr.get('rest_ok', True) else ('outside model range: Red' if hr.get('gate') else '')} |")
            csv_rows.append(dict(archetype=ar.id, **hr, allowable_fresh_min=o["allowable_min"], fail_safe=o["fail_safe"]))
        from .planner.planner import suggest_shift_windows
        w = suggest_shift_windows([h["work_planned_min"] for h in sim.hourly]); first = out["hours"][0]["hour"]
        lines += ["", "Hours where the plan allows heavy work (>=45 work min/hour): " + (", ".join(f"{int(first)+s}:00-{int(first)+e+1}:00" for s, e in w) or "none"), ""]
    lines.append("Water figures are simulated sweat loss, not a prescription. A plan is a recommendation; people decide.")
    md = os.path.join(a.out, "shift_plan.md"); open(md, "w").write("\n".join(lines))
    import csv as _csv
    cp = os.path.join(a.out, "shift_plan.csv")
    with open(cp, "w", newline="") as fh:
        w_ = _csv.DictWriter(fh, fieldnames=list(csv_rows[0])); w_.writeheader(); w_.writerows(csv_rows)
    write_meta(cp, source=prov.name, licence_note=prov.licence_note, synthetic=hours[0].synthetic, model=label,
               extra={"forecast_age_min": age})
    print("\n".join(lines))


def main(argv=None):
    p = argparse.ArgumentParser(prog="heatbank", description="HeatBank planning prototype. " + DISCLAIMER)
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="installed libraries and open items").set_defaults(fn=cmd_check)
    s = sub.add_parser("safe-minutes", help="safe minutes per hour per archetype"); _add_source(s); s.set_defaults(fn=cmd_safe)
    s = sub.add_parser("plan", help="shift plan with alerts and water estimate"); _add_source(s)
    s.add_argument("--archetype", help="e.g. A09 (default: all 12)"); s.set_defaults(fn=cmd_plan)
    s = sub.add_parser("simulate", help="V2 scenario stress test (SIMULATED)")
    s.add_argument("--toy", action="store_true"); s.add_argument("--adherence", nargs="+", type=float, default=[1.0, 0.7])
    s.add_argument("--out", default="out"); s.add_argument("--forecast-only", action="store_true")
    s.add_argument("--rest-area", choices=sorted(config.REST_AREAS), default=config.REST_AREA, help="where rest happens (audit A9)")
    s.add_argument("--probe-min", type=int, default=None, help="allowable-time probe length, default 480 (try 720, audit A11)")
    s.set_defaults(fn=lambda a: run_v2.run(a.toy, a.adherence, a.out, a.forecast_only, a.rest_area, a.probe_min))
    s = sub.add_parser("faults", help="V3 fault injection"); s.add_argument("--real", action="store_true", help="baseline from real pythermalcomfort instead of the toy model")
    s.set_defaults(fn=lambda a: sys.exit(0 if run_v3.run(a.real) else 1))
    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
