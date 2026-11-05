"""python -m heatbank.sim.run_v2 [--toy] [--adherence 1.0 0.7]  ->  out/v2_results.csv + out/v2_summary.md"""
import argparse, csv, dataclasses, os
from ..archetypes.archetypes import build_archetypes
from ..strain.phs_wrapper import StrainEngine
from ..weather.scenarios import SyntheticScenario, SCENARIOS
from .harness import simulate_worker, lead_time
from .toy_model import toy_phs, TOY_LABEL
from ..provenance import write_meta
from .. import config

REAL = "real_day"      # scenario name used for the NASA POWER replay (D8)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--toy", action="store_true", help="use the TOY model (no pythermalcomfort needed). Not physiology.")
    ap.add_argument("--adherence", nargs="+", type=float, default=[1.0, 0.7])
    ap.add_argument("--out", default="out")
    ap.add_argument("--forecast-only", action="store_true",
                    help="strip the (synthetic) globe temperature so the radiant FALLBACK path runs: this is what a site without a node gets")
    ap.add_argument("--rest-area", choices=sorted(config.REST_AREAS), default=config.REST_AREA,
                    help="where rest happens (audit A9). 'shade' is the default; 'cooled_cabin' shows what a cooled rest area would change")
    ap.add_argument("--probe-min", type=int, default=None, help="length of the allowable-time probe (default 480). Try 720 to see how much the 480 cap distorts 'fraction used' (A11)")
    a = ap.parse_args(argv)
    return run(a.toy, a.adherence, a.out, a.forecast_only, a.rest_area, a.probe_min)


def run(toy: bool, adherence_levels, out: str, forecast_only: bool = False, rest_area: str = None, probe_min: int = None, real_provider=None):
    class a: adherence, out_dir = adherence_levels, out
    a.out = out
    if rest_area: config.REST_AREA = rest_area
    if probe_min: config.PHS_DURATION_MIN = probe_min
    engine = StrainEngine(toy_phs if toy else None)
    if not toy:
        problems = engine.smoke_test()
        if problems:
            raise SystemExit("model smoke test failed, refusing to write results (audit A1): " + "; ".join(problems))
    label = TOY_LABEL if toy else "pythermalcomfort PHS (ISO 7933), SIMULATED crew, synthetic weather"
    archs = build_archetypes()
    os.makedirs(a.out, exist_ok=True)
    rows = []
    names = sorted(SCENARIOS) + ([REAL] if real_provider is not None else [])
    real_hours = real_provider.hours() if real_provider is not None else None     # D8: a real day; may raise with a clear message
    for sc in names:
        hours = real_hours if sc == REAL else SyntheticScenario(sc).hours()
        if forecast_only:      # audit A2: exercise the radiant fallback, the path a node-less site actually uses
            hours = [dataclasses.replace(h, tg_c=None) for h in hours]
        for ar in archs:
            cont = simulate_worker(engine, ar, hours, "continuous")
            rows.append(dict(scenario=sc, archetype=ar.id, mode="continuous", adherence="", lead_time_min=lead_time(cont),
                             **{f"min_{k}": v for k, v in cont.minutes_at.items()}, worked_min=cont.worked_min, no_recovery_hours=0))
            for adh in a.adherence:
                pl = simulate_worker(engine, ar, hours, "planned", adh)
                rows.append(dict(scenario=sc, archetype=ar.id, mode="planned", adherence=adh, lead_time_min="",
                                 **{f"min_{k}": v for k, v in pl.minutes_at.items()}, worked_min=pl.worked_min,
                                 no_recovery_hours=pl.no_recovery_hours))
    with open(os.path.join(a.out, "v2_results.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    # summary
    L = [f"# V2 scenario stress test: SIMULATED\n",
         f"Radiant input: **{'forecast-only fallback (' + config.TR_FALLBACK_MODE + ' mode)' if forecast_only else 'synthetic globe temperature (optimistic: no fallback exercised)'}**.\n",
         f"Model: **{label}**. Weather: synthetic (D4){' plus one real day (D8)' if real_provider is not None else ''}. Crew: 12 simulated archetypes (UNVERIFIED parameters). Rest area assumed: **{config.REST_AREA}**.",
         "No real-world lead time or false-alarm claim can be made from this (plan honesty rule).\n"]
    if real_provider is not None:
        L.insert(2, f"Scenario **{REAL}** uses REAL weather: {real_provider.name} (NASA POWER, D8; gridded reanalysis/satellite data, a replay, not a forecast, not measured at the site). "
                    f"The crew is still SIMULATED. {real_provider.licence_note}\n")
    for sc in names:
        cont = [r for r in rows if r["scenario"] == sc and r["mode"] == "continuous"]
        leads = [r["lead_time_min"] for r in cont if r["lead_time_min"] not in (None, "")]
        L.append(f"## {sc}\n")
        full = [r for r in rows if r["scenario"] == sc and r["mode"] == "planned" and r["adherence"] == 1.0]
        if full:   # audit A4: the real P1 check. Following the plan perfectly must never reach the model limit.
            red_full = sum(r["min_Red"] for r in full)
            L.append(f"- PLAN SAFETY (100% adherence, time at Red must be 0): **{'PASS' if red_full == 0 else 'FAIL, ' + str(red_full) + ' crew-minutes at Red'}**")
            nr = sum(r["no_recovery_hours"] for r in full)
            if nr: L.append(f"- Rest area '{config.REST_AREA}' did not cool a strained worker in {nr} crew-hours; the plan said NO WORK there (audit A9). "
                            f"Re-run with --rest-area fan or cooled_cabin to see what a better rest area changes.")
        L.append(f"- Continuous work, no plan: {len(leads)}/12 archetypes reached the model limit; lead time Orange->limit (min): "
                 + (f"min {min(leads)}, median {sorted(leads)[len(leads)//2]}, max {max(leads)}" if leads else "n/a (limit not reached)"))
        for adh in a.adherence:
            pl = [r for r in rows if r["scenario"] == sc and r["mode"] == "planned" and r["adherence"] == adh]
            tot = sum(r["min_Green"] + r["min_Yellow"] + r["min_Orange"] + r["min_Red"] for r in pl)
            red = sum(r["min_Red"] for r in pl); org = sum(r["min_Orange"] for r in pl)
            worked = sum(r["worked_min"] for r in pl)
            L.append(f"- Planned, simulated adherence {adh:.0%}: time at Red {red/tot:.1%}, at Orange {org/tot:.1%}, share of shift worked {worked/tot:.1%}")
        if sc == "cool":
            pl = [r for r in rows if r["scenario"] == sc and r["mode"] == "planned" and r["adherence"] == a.adherence[0]]
            tot = sum(r["min_Green"] + r["min_Yellow"] + r["min_Orange"] + r["min_Red"] for r in pl)
            fa = sum(r["min_Orange"] + r["min_Red"] for r in pl) / tot
            L.append(f"- Orange/Red share of crew-time on the cool control day (NOT a validated false-alarm rate: the model judges itself, no ground truth): {fa:.1%}")
        L.append("")
    L.append(f"Model calls: {engine.calls}; model errors: {engine.model_errors} (must be 0 for a real run).")
    if engine.cap_checks:
        L.append(f"A11 check: the fresh-start allowable time hit the {config.PHS_DURATION_MIN}-minute cap in {engine.cap_hits}/{engine.cap_checks} "
                 f"probes ({engine.cap_hits / engine.cap_checks:.0%}). If this is large, 'fraction used' depends on an arbitrary cap in those hours.")
    for w in engine.warnings: L.append(f"WARNING: {w}")
    L.append(f"Sweat total carried by the library: {engine.sweat_carries} (None = not tested, False = restarts; tracker sums it itself).")
    with open(os.path.join(a.out, "v2_summary.md"), "w", encoding="utf-8") as fh: fh.write("\n".join(L))
    tag = f"{'forecast_only' if forecast_only else 'globe'}_{config.REST_AREA}_probe{config.PHS_DURATION_MIN}"          # v0.5.2: a copy that is not overwritten by the next run
    with open(os.path.join(a.out, f"v2_summary_{tag}.md"), "w", encoding="utf-8") as fh: fh.write("\n".join(L))
    write_meta(os.path.join(a.out, "v2_results.csv"), source="synthetic scenarios" + (f" + {real_provider.name}" if real_provider is not None else ""),
               licence_note="Generated by the team (D4)" + (f"; {real_provider.licence_note}" if real_provider is not None else ""),
               synthetic=True, model=label)
    print("\n".join(L))


if __name__ == "__main__":
    main()
