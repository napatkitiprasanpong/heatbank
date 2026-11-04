"""TOY stand-in for PHS so the harness can run without pythermalcomfort. NOT PHYSIOLOGY. Outputs from it must never be
reported as results: the harness stamps every output 'TOY MODEL'. It only has the right *shape*: heat gain rises with
air temperature and workload, it carries state, and light rest recovers."""
from types import SimpleNamespace

TOY_LABEL = "TOY MODEL (not physiology)"


def toy_phs(tdb, tr, v, rh, met, clo, posture=2, **kw):
    dur = float(kw.get("duration", 480))
    t0 = float(kw.get("t_re", 37.0))
    s0 = float(kw.get("sweat_loss_g", 0.0))
    if met <= 100.0:
        net = -0.0020 if tdb < 40 else 0.0005             # toy recovery at rest in the shade
    else:
        net = 0.0002 * (tdb - 28) + 0.00006 * (met - 100) + 0.00003 * (tr - tdb) + 0.0003 * (clo - 0.5) + 0.00001 * (rh - 50)
        net = max(net, 0.0001)
    t_end = max(36.5, t0 + net * dur)
    d_t = dur if net <= 0 else min(dur, max(0.0, (38.0 - t0) / net))
    return SimpleNamespace(d_lim_t_re=d_t, d_lim_loss_95=min(dur, d_t + 30.0), d_lim_loss_50=min(dur, d_t + 60.0),
                           t_re=t_end, t_sk=34.0, t_cr=t_end, t_cr_eq=t_end, t_sk_t_cr_wg=0.3,
                           sweat_loss_g=s0 + 8.0 * dur * max(0.2, met / 165.0))
