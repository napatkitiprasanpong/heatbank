"""V3 fault injection. Pass: alert level never falls below the clean-data baseline AND a degraded banner is shown.
python -m heatbank.sim.run_v3   (uses the TOY model for the physiology part; the fallback logic itself is model-independent)"""
from ..alerts import engine as alerts
from ..fallback import fallback
from ..strain.phs_wrapper import StrainEngine
from .toy_model import toy_phs
from ..archetypes.archetypes import build_archetypes
from ..weather.scenarios import SyntheticScenario
from .tracker import ExposureTracker
from .harness import shift_hours


def clean_fraction():
    hs = shift_hours(SyntheticScenario("hot_humid").hours())
    ar = [a for a in build_archetypes() if a.task == "moderate"][0]
    trk = ExposureTracker(StrainEngine(toy_phs), ar)
    h = hs[4]
    for _ in range(12): trk.step(h, 10, True)
    _, frac, fs = trk.remaining_and_fraction(h)
    return frac, fs


FAULTS = {
    "network killed, fresh cache":     dict(forecast_age_min=30, offline=True),
    "network killed, stale cache":     dict(forecast_age_min=400, offline=True),
    "network killed, no cache":        dict(forecast_age_min=None, have_forecast=False, offline=True),
    "forecast frozen (age grows)":     dict(forecast_age_min=720),
    "sensor frozen":                   dict(forecast_age_min=10, node_readings=[33.1] * 8),
    "sensor spike":                    dict(forecast_age_min=10, node_readings=[33.0, 33.2, 47.5, 33.1]),
    "out-of-range input":              dict(forecast_age_min=10, model_fail_safe=True),
    "low battery":                     dict(forecast_age_min=10, battery_pct=12),
}


def run():
    frac, _ = clean_fraction()
    clean = alerts.compose(frac).level
    rows, ok_all = [], True
    for name, kw in FAULTS.items():
        fs = fallback.evaluate(**kw)
        a = alerts.compose(frac, fail_safe=kw.get("model_fail_safe", False), fallback=fs)
        passed = a.level >= clean and a.degraded_banner is not None
        ok_all &= passed
        rows.append((name, alerts.NAMES[clean], a.name, a.degraded_banner or "-", "PASS" if passed else "FAIL"))
    print(f"clean baseline level: {alerts.NAMES[clean]} (fraction used {frac:.2f}, TOY model)\n")
    print(f"{'fault':34}{'baseline':10}{'with fault':12}{'banner':18}result")
    for r in rows: print(f"{r[0]:34}{r[1]:10}{r[2]:12}{r[3]:18}{r[4]}")
    return ok_all


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)
