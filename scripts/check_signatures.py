"""Resolves plan U5/U6 on YOUR machine: prints what the installed libraries really expose.
Run:  python scripts/check_signatures.py   and paste the output back so the wrapper can be fixed to match."""
import importlib, inspect, os, sys, io


class _Tee(io.TextIOBase):
    """Everything printed here is also saved to out/check_signatures_output.txt so you can attach ONE file."""
    def __init__(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True); self.f = open(path, "w", encoding="utf-8"); self.o = sys.__stdout__
    def write(self, s): self.o.write(s); self.f.write(s); return len(s)
    def flush(self): self.o.flush(); self.f.flush()


sys.stdout = _Tee(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out", "check_signatures_output.txt"))
import platform, subprocess
print("python", platform.python_version(), platform.platform())
try: print(subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout)
except Exception as e: print("pip freeze failed", e)

def show(modname):
    try:
        m = importlib.import_module(modname)
        print(f"{modname} version:", getattr(m, "__version__", "?"))
        return m
    except ImportError as e:
        print(f"{modname}: NOT INSTALLED ({e})")

ptc = show("pythermalcomfort")
if ptc:
    models = importlib.import_module("pythermalcomfort.models")
    phs = getattr(models, "phs", None)
    print("phs signature:", inspect.signature(phs) if phs else "MISSING")
    print("phs docstring:\n", inspect.getdoc(phs))
    try:
        print("phs source file:", inspect.getsourcefile(phs))
        pk = os.path.dirname(os.path.dirname(inspect.getsourcefile(phs)))
        shipped = [os.path.join(r, f) for r, _, fs in os.walk(pk) for f in fs if "test" in f.lower() and f.endswith(".py")]
        print("test files shipped inside the package (plan A17/V1):", shipped[:10] or "NONE")
    except Exception as e:
        print("could not locate source:", repr(e))
    try:
        ps = inspect.signature(phs).parameters
        print("phs has a 'model' parameter:", "model" in ps, (ps["model"].default if "model" in ps else ""))
        if "model" in ps:
            for m in ("7933-2004", "7933-2023"):
                try: r = phs(35, 45, 1.0, 50, 2.84, 0.5, 'standing', duration=480, model=m); print(f"  model={m!r} accepted; d_lim_t_re =", getattr(r, "d_lim_t_re", "?"))
                except Exception as e: print(f"  model={m!r} REJECTED:", repr(e))
    except Exception as e:
        print("model probe failed:", repr(e))
    try:
        r = phs(35, 45, 1.0, 50, 2.84, 0.5, 'standing', duration=480)
        print("phs result type:", type(r)); print("phs result:", r)
        import dataclasses
        if dataclasses.is_dataclass(r): print("RESULT FIELDS:", [f.name for f in dataclasses.fields(r)])
    except Exception as e:
        print("phs sample call failed:", repr(e))
tf = show("thermofeel")
if tf:
    for n in dir(tf):
        if "wbgt" in n.lower() or "mean_radiant" in n.lower() or "utci" in n.lower():
            print(n, inspect.signature(getattr(tf, n)))


# --- audit A1: does carry-over really work, and does the wrapper's smoke test pass? ------------------------------
if ptc:
    sys.path.insert(0, ".")
    try:
        from heatbank.strain.phs_wrapper import StrainEngine
        print("\nwrapper smoke test (empty list = OK):", StrainEngine().smoke_test())
    except Exception as e:
        print("wrapper smoke test could not run:", repr(e))
    try:
        r1 = phs(35, 45, 1.0, 50, 3.96, 0.9, 'standing', duration=120, round_output=False)
        names = [n for n in dir(r1) if not n.startswith("_")]
        print("result attributes:", names)
        for kw in ("t_re", "t_sk", "t_cr", "t_cr_eq", "t_sk_t_cr_wg", "sweat_rate_watt", "evap_load_wm2_min", "sweat_loss_g"):
            try:
                phs(35, 45, 1.0, 50, 3.96, 0.9, 'standing', duration=60, round_output=False, **{kw: getattr(r1, kw)})
                print(f"  accepted as input: {kw}")
            except Exception as e:
                print(f"  REJECTED as input: {kw}: {e!r}")
    except Exception as e:
        print("carry-over probe failed:", repr(e))

# --- audit B2: how slow is one real PHS call? (decides whether the V2 run takes seconds or half an hour) -------------
if ptc:
    import time
    try:
        n = 20; t0 = time.time()
        for _ in range(n): phs(35, 45, 1.0, 50, 2.84, 0.5, 'standing', duration=480)
        per = (time.time() - t0) / n
        print(f"\nPHS time per 480-minute call: {per*1000:.1f} ms")
        print(f"projected full V2 run (about 15,400 real calls with the cache): {per*15400/60:.1f} minutes")
        if per * 15400 > 600:
            print("  -> slow. Options: raise config.STEP_MIN, shorten config.PHS_DURATION_MIN for the remaining-time probe, or cut archetypes for V2.")
    except Exception as e:
        print("timing probe failed:", repr(e))

print("\nDONE. Attach out/check_signatures_output.txt (one file) to your next message.")
