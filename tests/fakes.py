"""Fake PHS for tests ONLY: deterministic and monotone, NOT physiology. Real V1 runs need pythermalcomfort."""
from types import SimpleNamespace

def fake_phs(tdb, tr, v, rh, met, clo, posture=2, **kw):
    lim = max(0.0, 480.0 - 40.0 * (tdb - 25.0) - 0.5 * (met - 100.0))
    lim = min(lim, float(kw.get("duration", 480)))
    return SimpleNamespace(d_lim_t_re=lim, d_lim_loss_95=lim + 30.0, d_lim_loss_50=lim + 60.0,
                           t_re=37.2, t_sk=34.0, t_cr=37.0, t_cr_eq=37.0, t_sk_t_cr_wg=0.3, sweat_loss_g=500.0)

def boom_phs(*a, **k):
    raise RuntimeError("model blew up")
