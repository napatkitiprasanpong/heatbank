"""C3 strain engine: thin wrapper around pythermalcomfort PHS (ISO 7933).

Plan U5/U6: the exact kwarg and result-attribute names of the installed version are NOT confirmed.
All of them live in the two mapping dicts below so a mismatch is a one-line fix. Run
scripts/check_signatures.py after installing to see what your version really exposes.

Rules kept here: P2 (out-of-range or failure => fail-safe 0 min, never extrapolate) and P3 (no identifiers)."""
from dataclasses import dataclass, field
from typing import Callable, Optional, Dict, Any
from . import validity
from .. import config

# our name -> pythermalcomfort kwarg name (UNVERIFIED, v2-style names)
PHS_KWARGS = {"posture": "posture", "acclimatized": "acclimatized", "drink": "drink", "duration": "duration"}
# state carry-over: our name -> kwarg name AND result attribute name (UNVERIFIED)
STATE_FIELDS = ["t_re", "t_sk", "t_cr", "t_cr_eq", "t_sk_t_cr_wg", "sweat_loss_g"]
# result attributes holding the limits in minutes (UNVERIFIED)
LIMIT_FIELDS = {"tre": "d_lim_t_re", "loss95": "d_lim_loss_95", "loss50": "d_lim_loss_50"}


@dataclass
class PhsState:
    values: Dict[str, float] = field(default_factory=dict)   # empty => model defaults (start of exposure)


@dataclass
class StrainResult:
    status: str                       # validity.OK / ABOVE_RANGE / BELOW_RANGE / INVALID / MODEL_ERROR
    safe_minutes: Optional[float]     # None only when heat strain is not modelled (BELOW_RANGE)
    fail_safe: bool                   # True => Part 2 must treat as Red
    limiting: str = ""
    t_re_end: Optional[float] = None
    sweat_loss_g: Optional[float] = None
    reasons: list = field(default_factory=list)
    state: PhsState = field(default_factory=PhsState)


def _get(res: Any, name: str):
    x = res[name] if isinstance(res, dict) else getattr(res, name)
    try:
        import numpy as np
        return float(np.asarray(x).ravel()[0])
    except ImportError:
        return float(x[0] if isinstance(x, (list, tuple)) else x)


def _default_phs() -> Callable:
    from pythermalcomfort.models import phs   # raises ImportError if not installed: caller decides
    return phs


class StrainEngine:
    def __init__(self, phs_fn: Optional[Callable] = None):
        self._phs = phs_fn
        self._cache: Dict[tuple, "StrainResult"] = {}   # stateless calls only (fresh-start allowable time repeats a lot)
        self.calls = 0            # real model invocations (cache hits excluded)
        self.model_errors = 0     # MODEL_ERROR results: a non-zero count with a "clean" input means an integration bug (audit A1)

    @property
    def phs(self) -> Callable:
        if self._phs is None:
            self._phs = _default_phs()
        return self._phs

    def run_segment(self, tdb_c, tr_c, v_ms, rh_pct, met_wm2, clo, posture, acclimatized, drink=1,
                    duration_min=None, state: Optional[PhsState] = None) -> StrainResult:
        stateless = not (state and state.values)
        key = (tdb_c, tr_c, v_ms, rh_pct, met_wm2, clo, posture, acclimatized, drink, duration_min)
        if stateless and key in self._cache:
            return self._cache[key]
        res = self._run_segment(tdb_c, tr_c, v_ms, rh_pct, met_wm2, clo, posture, acclimatized, drink, duration_min, state)
        if stateless:
            self._cache[key] = res
        return res

    def smoke_test(self) -> list:
        """Audit A1. Returns a list of problems; empty = the wrapper really talks to the model.
        1) a clean mid-range call must NOT end in MODEL_ERROR (otherwise every output silently becomes Red);
        2) carry-over must have an effect: continuing from the state after 2 h of heavy work must give LESS remaining
           time than a fresh start (otherwise the state kwargs are silently ignored and the tracker is wrong)."""
        args = (35.0, 45.0, 1.0, 50.0, 230.0, 0.9, 2, 0, 1)
        before = self.model_errors
        first = self.run_segment(*args, duration_min=120)
        if first.status in ("MODEL_ERROR", validity.INVALID) or first.safe_minutes is None:
            return [f"clean call failed: {first.status} {first.reasons}"]
        if not first.state.values:
            return ["model returned no carry-over state (STATE_FIELDS names wrong?)"]
        fresh = self.run_segment(*args, duration_min=config.PHS_DURATION_MIN)
        cont = self.run_segment(*args, duration_min=config.PHS_DURATION_MIN, state=first.state)
        problems = []
        if cont.status == "MODEL_ERROR":
            problems.append(f"continuing from carried state failed: {cont.reasons}")
        elif fresh.safe_minutes is not None and cont.safe_minutes is not None and not cont.safe_minutes < fresh.safe_minutes:
            problems.append(f"carry-over has no effect (fresh {fresh.safe_minutes:.0f} min, continued {cont.safe_minutes:.0f} min): state kwargs probably ignored")
        return problems

    def _run_segment(self, tdb_c, tr_c, v_ms, rh_pct, met_wm2, clo, posture, acclimatized, drink=1,
                    duration_min=None, state: Optional[PhsState] = None) -> StrainResult:
        self.calls += 1
        clamped = []
        if config.CLAMP_COOL_UP:
            for name, val in (("tdb_c", tdb_c), ("tr_c", tr_c)):
                lo = config.VALID_RANGES[name][0]
                if val is not None and val == val and val < lo:
                    clamped.append(f"{name} {val:.1f} raised to model minimum {lo}")
                    if name == "tdb_c": tdb_c = lo
                    else: tr_c = lo
        status, reasons = validity.check_inputs(tdb_c, tr_c, v_ms, rh_pct, met_wm2, clo)
        reasons = clamped + reasons
        if status in (validity.ABOVE, validity.INVALID):
            return StrainResult(status, 0.0, True, "validity gate", reasons=reasons)
        if status == validity.BELOW:
            return StrainResult(status, None, False, "below model range (heat strain not modelled)", reasons=reasons)
        dur = duration_min or config.PHS_DURATION_MIN
        kw = {PHS_KWARGS["posture"]: posture, PHS_KWARGS["acclimatized"]: acclimatized,
              PHS_KWARGS["drink"]: drink, PHS_KWARGS["duration"]: dur}
        if state and state.values:
            kw.update(state.values)
        try:
            res = self.phs(tdb_c, tr_c, v_ms, rh_pct, met_wm2, clo, **kw)
            tre, l95 = _get(res, LIMIT_FIELDS["tre"]), _get(res, LIMIT_FIELDS["loss95"])
            new_state = PhsState({k: _get(res, k) for k in STATE_FIELDS if _has(res, k)})
            t_re_end = _get(res, "t_re") if _has(res, "t_re") else None
            sweat = _get(res, "sweat_loss_g") if _has(res, "sweat_loss_g") else None
        except Exception as e:   # any model failure => fail safe, never silent
            self.model_errors += 1
            return StrainResult("MODEL_ERROR", 0.0, True, "model error", reasons=[repr(e)])
        # PROPOSED: conservative limit = smaller of rectal-temp limit and 95th-percentile water-loss limit
        limiting, minutes = ("rectal temperature", tre) if tre <= l95 else ("water loss (95%)", l95)
        minutes = max(0.0, min(minutes, float(dur)))
        return StrainResult("OK_CLAMPED" if clamped else validity.OK, minutes, False, limiting, t_re_end, sweat,
                            reasons, new_state)


def _has(res, name):
    return (name in res) if isinstance(res, dict) else hasattr(res, name)


def self_check(phs_fn: Callable) -> list:
    """Return a list of problems between our mapping dicts and the installed phs() signature (U6). Empty = looks OK.
    Result attribute names can only be checked by a real call; see scripts/check_signatures.py."""
    import inspect
    try:
        sig = inspect.signature(phs_fn)
    except (TypeError, ValueError):
        return ["cannot inspect phs signature"]
    params = sig.parameters
    accepts_kw = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())
    problems = []
    wanted = list(PHS_KWARGS.values()) + STATE_FIELDS
    for k in wanted:
        if k not in params and not accepts_kw:
            problems.append(f"phs() has no parameter {k!r}")
    return problems
