"""Resolves plan U5/U6 on YOUR machine: prints what the installed libraries really expose.
Run:  python scripts/check_signatures.py   and paste the output back so the wrapper can be fixed to match."""
import importlib, inspect, sys

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
        r = phs(35, 45, 1.0, 50, 165, 0.5, 2, duration=480)
        print("phs result type:", type(r)); print("phs result:", r)
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
        r1 = phs(35, 45, 1.0, 50, 230, 0.9, 2, duration=120)
        names = [n for n in dir(r1) if not n.startswith("_")]
        print("result attributes:", names)
        for kw in ("t_re", "t_sk", "t_cr", "t_cr_eq", "t_sk_t_cr_wg", "sweat_rate", "sweat_loss_g"):
            try:
                phs(35, 45, 1.0, 50, 230, 0.9, 2, duration=60, **{kw: getattr(r1, kw)})
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
        for _ in range(n): phs(35, 45, 1.0, 50, 165, 0.5, 2, duration=480)
        per = (time.time() - t0) / n
        print(f"\nPHS time per 480-minute call: {per*1000:.1f} ms")
        print(f"projected full V2 run (about 15,400 real calls with the cache): {per*15400/60:.1f} minutes")
        if per * 15400 > 600:
            print("  -> slow. Options: raise config.STEP_MIN, shorten config.PHS_DURATION_MIN for the remaining-time probe, or cut archetypes for V2.")
    except Exception as e:
        print("timing probe failed:", repr(e))
