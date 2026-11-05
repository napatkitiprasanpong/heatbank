"""One command that answers: do Parts 1, 2 and 3 work together on THIS machine?
    python scripts/integration_check.py          real pythermalcomfort (needs it installed)
    python scripts/integration_check.py --toy    plumbing only, no library needed
Prints a PASS/FAIL table, projected V2 run time (audit B2) and writes out/integration_check.txt. Exit code 1 on any FAIL."""
import argparse, io, os, shutil, subprocess, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from heatbank import config
from heatbank.archetypes.archetypes import build_archetypes
from heatbank.export import build_pack, write_js, DEMO_ROSTER, DEMO_ZONES
from heatbank.sim.harness import simulate_worker
from heatbank.sim.toy_model import toy_phs, TOY_LABEL
from heatbank.strain.phs_wrapper import StrainEngine
from heatbank.weather.scenarios import SyntheticScenario

ap = argparse.ArgumentParser(); ap.add_argument("--toy", action="store_true"); a = ap.parse_args()
rows, eng = [], StrainEngine(toy_phs if a.toy else None)
label = TOY_LABEL if a.toy else "real pythermalcomfort"


def step(name, fn):
    t0 = time.time()
    try: ok, note = fn()
    except Exception as e: ok, note = False, repr(e)[:300]
    rows.append((name, "PASS" if ok else "FAIL", note, time.time() - t0)); return ok


def s_import():
    if a.toy: return True, "toy model (no library)"
    import pythermalcomfort; return True, "pythermalcomfort " + getattr(pythermalcomfort, "__version__", "?")


def s_smoke():
    p = eng.smoke_test(); return not p, ("; ".join(p) if p else f"ok; sweat carried by library: {eng.sweat_carries}; warnings: {len(eng.warnings)}")


def s_sim():
    r = simulate_worker(eng, build_archetypes()[8], SyntheticScenario("hot_humid").hours(), "planned", 1.0)
    return eng.model_errors == 0 and len(r.hourly) > 0, f"{len(r.hourly)} shift hours, model errors {eng.model_errors}"


def s_faults():
    p = subprocess.run([sys.executable, "-m", "heatbank.cli", "faults"] + ([] if a.toy else ["--real"]), cwd=ROOT, capture_output=True, text=True)
    return p.returncode == 0 and "FAIL" not in p.stdout, f"{p.stdout.count('PASS')} PASS"


def s_pack():
    d = tempfile.mkdtemp(); path = os.path.join(d, "data.js")
    pack = build_pack(eng, SyntheticScenario("hot_humid").hours(), build_archetypes(), DEMO_ROSTER, DEMO_ZONES, label, "synthetic:hot_humid")
    write_js(pack, path); shutil.rmtree(d); return True, f"{len(pack['plans'])} archetypes, {len(pack['supervisor']['zones'])} zones listed"


def s_dom():
    if not shutil.which("node"): return True, "node not installed: SKIPPED (install node to run the page smoke test)"
    d = tempfile.mkdtemp(); shutil.copytree(os.path.join(ROOT, "dashboard"), os.path.join(d, "dashboard"))
    write_js(build_pack(eng, SyntheticScenario("hot_humid").hours(), build_archetypes(), DEMO_ROSTER, DEMO_ZONES, label, "synthetic:hot_humid"), os.path.join(d, "dashboard", "data.js"))
    p = subprocess.run(["node", os.path.join(ROOT, "tests", "dom_smoke.js"), os.path.join(d, "dashboard")], capture_output=True, text=True); shutil.rmtree(d)
    return p.returncode == 0, p.stdout.strip()[:200]


def s_time():
    e = StrainEngine(toy_phs if a.toy else None); hrs = SyntheticScenario("hot_dry").hours(); t0 = time.time()
    for ar in build_archetypes()[:2]: simulate_worker(e, ar, hrs, "continuous")
    dt = time.time() - t0; per = dt / max(e.calls, 1); full = per * 19900
    return True, f"{e.calls} calls in {dt:.1f}s = {per*1000:.1f} ms per call; projected full V2 (about 19,900 calls) = {full/60:.1f} min" + ("  -> SLOW: raise STEP_MIN or cut archetypes" if full > 900 else "")


ok = all([step("1 library import", s_import), step("2 wrapper smoke test (A1/A12)", s_smoke), step("3 Part 1+2: weather->tracker->planner", s_sim),
          step("4 V3 fault injection", s_faults), step("5 Part 3: pack export + supervisor aggregation", s_pack),
          step("6 front end boots, controls work (fake DOM)", s_dom), step("7 compute time (B2)", s_time)])
out = [f"HeatBank v{__import__('heatbank').__version__} integration check, model: {label}", ""] + [f"{n:<52} {r}  {t:5.1f}s  {note}" for n, r, note, t in rows]
out += ["", "ALL PASS" if ok else "SOMETHING FAILED", "Numbers from --toy are NOT results." if a.toy else "Also run the unit tests: python -m unittest discover -s tests -t ."]
os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
with open(os.path.join(ROOT, "out", "integration_check.txt"), "w", encoding="utf-8") as fh: fh.write("\n".join(out))
print("\n".join(out)); sys.exit(0 if ok else 1)
