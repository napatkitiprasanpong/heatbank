r"""Answers four questions about the REAL pythermalcomfort that the first V2 run raised. Run:  python scripts\diagnose_phs.py
Writes out/diagnose_phs.txt (attach that one file). Nothing here changes any setting; it only prints what the library does.
 Q1 Does the acclimatized flag change anything (A01 and A02 were identical in V2)?
 Q2 Why does continuous heavy work never reach the limit (0/12 in every scenario, even 47 C)?
 Q3 Does seated rest in shade lower rectal temperature, and how fast?
 Q4 How is d_lim_* counted when a run continues from a carried state (from segment start, or from t=0)?"""
import io, os, sys, dataclasses
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
os.makedirs(OUT, exist_ok=True)
_f = open(os.path.join(OUT, "diagnose_phs.txt"), "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a); print(s); _f.write(s + "\n")

from pythermalcomfort.models import phs
from heatbank import config
M = lambda w: w / config.W_PER_MET
STATE = ["t_sk", "t_cr", "t_re", "t_cr_eq", "t_sk_t_cr_wg", "sweat_rate_watt", "evap_load_wm2_min"]
def call(tdb, tr, v, rh, met_w, clo, dur, state=None, acc=100, model="7933-2023", posture="standing"):
    kw = dict(duration=dur, acclimatized=acc, drink=1, model=model, limit_inputs=False, round_output=False)
    if state: kw.update({k: getattr(state, k) for k in STATE})
    return phs(tdb, tr, v, rh, M(met_w), clo, posture, **kw)
def row(r): return f"t_re={r.t_re:.2f} t_cr={r.t_cr:.2f} sweat_g={r.sweat_loss_g:.0f} d_t_re={r.d_lim_t_re:.0f} d_loss50={r.d_lim_loss_50:.0f} d_loss95={r.d_lim_loss_95:.0f}"

def section(t): P("\n" + "=" * 8, t)

try:
    section("Q1 acclimatized 100 vs 0 (heavy 230 W/m2, 0.5 clo, v=1, 45 C air, tr 50, rh 25), 480 min")
    for model in ("7933-2023", "7933-2004"):
        for acc in (100, 0):
            P(f"model {model} acclimatized={acc}:", row(call(45, 50, 1.0, 25, 230, 0.5, 480, acc=acc, model=model)))
    P("Also at 38 C / 60 % humidity, 165 W/m2:")
    for model in ("7933-2023", "7933-2004"):
        for acc in (100, 0):
            P(f"model {model} acclimatized={acc}:", row(call(38, 42, 1.0, 60, 165, 0.5, 480, acc=acc, model=model)))
except Exception as e: P("Q1 FAILED", repr(e))

try:
    section("Q2 continuous heavy work, 10-minute steps chained exactly like the tracker (gulf-like: 45 C, tr 50, rh 25, v 2.5, 0.5 clo, acclimatised)")
    st = None; t = 0
    for i in range(60):
        r = call(45, 50, 2.5, 25, 230, 0.5, 10, state=st); st = r; t += 10
        if i % 3 == 2:
            fresh = call(45, 50, 2.5, 25, 230, 0.5, 480)
            now = call(45, 50, 2.5, 25, 230, 0.5, 480, state=st)
            P(f"t={t:3d} min | segment: {row(r)} || probe from state (480): d_t_re={now.d_lim_t_re:.0f} d_loss95={now.d_lim_loss_95:.0f} | fresh probe: d_t_re={fresh.d_lim_t_re:.0f} d_loss95={fresh.d_lim_loss_95:.0f}")
except Exception as e: P("Q2 FAILED", repr(e))

try:
    section("Q3 rest after 90 min heavy work at 33 C (tr 40): seated rest 58 W/m2 vs 100 W/m2, in shade (tr=tdb=33), print every 10 min")
    st = None
    for _ in range(9): st = call(33, 40, 1.0, 50, 230, 0.9, 10, state=st)
    P("end of work:", row(st))
    for rest_w in (58, 100):
        s2 = st
        for i in range(1, 7):
            s2 = call(33, 33, 1.0, 50, rest_w, 0.9, 10, state=s2)
            P(f"rest {rest_w} W/m2, +{i*10:2d} min: t_re={s2.t_re:.2f} t_cr={s2.t_cr:.2f} sweat_g={s2.sweat_loss_g:.0f}")
    P("same but 44 C air, shade:")
    st = None
    for _ in range(9): st = call(44, 50, 1.0, 20, 230, 0.9, 10, state=st)
    P("end of work:", row(st))
    s2 = st
    for i in range(1, 7):
        s2 = call(44, 44, 1.0, 20, 58, 0.9, 10, state=s2); P(f"rest 58 W/m2 at 44 C, +{i*10:2d} min: t_re={s2.t_re:.2f}")
except Exception as e: P("Q3 FAILED", repr(e))

try:
    section("Q4 how d_lim_* is counted: one 600 min run vs 120 min then a 480 min probe from its state (38 C, tr 45, rh 40, 230 W/m2)")
    a = call(38, 45, 1.0, 40, 230, 0.5, 600); P("single 600 min:", row(a))
    b = call(38, 45, 1.0, 40, 230, 0.5, 120); P("first 120 min:", row(b))
    c = call(38, 45, 1.0, 40, 230, 0.5, 480, state=b); P("then 480 from state:", row(c))
    P("If d_lim values in the last line are near the single-run value minus 120, they count from the segment start; if near the single-run value, from t=0.")
except Exception as e: P("Q4 FAILED", repr(e))
P("\nDONE. Attach out/diagnose_phs.txt")
