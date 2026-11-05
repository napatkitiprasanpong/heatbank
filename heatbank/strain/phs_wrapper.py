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
# state carry-over. v0.4 (audit A1/A12): INPUT names and OUTPUT names are separate. sweat_loss_g is a result only: from memory it is
# NOT an input of phs(), so it is no longer passed back in. Cumulative sweat is tracked by ExposureTracker (see sweat_carries).
STATE_INPUT_FIELDS = ["t_re", "t_sk", "t_cr", "t_cr_eq", "t_sk_t_cr_wg", "sweat_rate_watt", "evap_load_wm2_min"]   # names from the 4.8.0 docstring
STATE_FIELDS = STATE_INPUT_FIELDS                                            # kept for older imports
SWEAT_FIELD = "sweat_loss_g"
POSTURE_NAMES = {1: "sitting", 2: "standing", 3: "crouching"}      # library wants text (4.8.0)
# result attributes holding the limits in minutes (UNVERIFIED: first real run will confirm)
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
        self._real = phs_fn is None     # the real library needs met in met units and posture as text; injected fakes keep W/m2 and int codes
        self._cache: Dict[tuple, "StrainResult"] = {}   # stateless calls only (fresh-start allowable time repeats a lot)
        self.sweat_carries = None   # None = unknown (smoke test not run): the tracker then SUMS segments, which can only overstate (P2)
        self.warnings: list = []    # non-blocking findings from smoke_test (shown in V2 summary)
        self.dropped_state_kwargs: set = set()   # state kwargs the installed phs() does not accept (blocking in smoke_test)
        self.cap_checks = 0         # A11 diagnostic: fresh-start allowable-time probes
        self.cap_hits = 0           # ...of which reached the PHS_DURATION_MIN cap (the ratio then rests on an arbitrary cap)
        self._accepted_cache = None
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

    def _accepted(self):
        """(set of accepted parameter names or None, has **kwargs). None when the signature cannot be inspected."""
        if self._accepted_cache is None:
            import inspect
            try:
                ps = inspect.signature(self.phs).parameters
                self._accepted_cache = ({n for n, p in ps.items()}, any(p.kind is inspect.Parameter.VAR_KEYWORD for p in ps.values()))
            except (TypeError, ValueError):
                self._accepted_cache = (None, True)
        return self._accepted_cache

    def smoke_test(self) -> list:
        """Audit A1/A12. Returns BLOCKING problems; empty = the wrapper really talks to the model. Non-blocking findings go to
        self.warnings.
        1) a clean mid-range call must NOT end in MODEL_ERROR (otherwise every output silently becomes Red);
        2) state kwargs the library does not accept are reported (they would otherwise be dropped or ignored);
        3) carry-over must have an effect: continuing from the state after 2 h of heavy work must give LESS remaining time than a
           fresh start (otherwise the state kwargs are silently ignored and the tracker is wrong);
        4) does the library carry its sweat/water-loss total across segments? Sets self.sweat_carries."""
        self.warnings = []
        args = (35.0, 45.0, 1.0, 50.0, 230.0, 0.9, 2, 0, 1)
        first = self.run_segment(*args, duration_min=120)
        if first.status in ("MODEL_ERROR", validity.INVALID) or first.safe_minutes is None:
            return [f"clean call failed: {first.status} {first.reasons}"]
        if not first.state.values:
            return ["model returned no carry-over state (STATE_INPUT_FIELDS names wrong?)"]
        fresh = self.run_segment(*args, duration_min=config.PHS_DURATION_MIN)
        cont = self.run_segment(*args, duration_min=config.PHS_DURATION_MIN, state=first.state)
        problems = []
        if self.dropped_state_kwargs:
            problems.append("installed phs() does not accept state kwargs " + ", ".join(sorted(self.dropped_state_kwargs)) + ": carry-over is incomplete")
        if cont.status == "MODEL_ERROR":
            problems.append(f"continuing from carried state failed: {cont.reasons}")
        elif fresh.safe_minutes is not None and cont.safe_minutes is not None and not cont.safe_minutes < fresh.safe_minutes:
            problems.append(f"carry-over has no effect (fresh {fresh.safe_minutes:.0f} min, continued {cont.safe_minutes:.0f} min): state kwargs probably ignored")
        seg2 = self.run_segment(*args, duration_min=60, state=first.state)
        if first.sweat_loss_g is None or seg2.sweat_loss_g is None:
            self.sweat_carries = None
            self.warnings.append("result has no sweat_loss_g: water use cannot be reported or tracked (check SWEAT_FIELD)")
        else:
            self.sweat_carries = seg2.sweat_loss_g >= 0.99 * first.sweat_loss_g
            if not self.sweat_carries:
                self.warnings.append("A12: the library's sweat/water-loss total restarts for each segment, so its water-loss limit is "
                                     "under-estimated after the first segment. The tracker sums sweat itself; set config.WATER_GUARD_G after "
                                     "confirming the ISO 7933 limit (U10).")
        return problems

    def _run_segment(self, tdb_c, tr_c, v_ms, rh_pct, met_wm2, clo, posture, acclimatized, drink=1,
                    duration_min=None, state: Optional[PhsState] = None) -> StrainResult:
        self.calls += 1
        clamped = []
        if config.CLAMP_COOL_UP:
            lo = config.VALID_RANGES["tdb_c"][0]
            if tdb_c is not None and tdb_c == tdb_c and tdb_c < lo:
                clamped.append(f"tdb_c {tdb_c:.1f} raised to model minimum {lo}"); tdb_c = lo
        if tdb_c is not None and tr_c is not None and tr_c == tr_c and tdb_c == tdb_c and tr_c < tdb_c:
            clamped.append(f"tr_c {tr_c:.1f} raised to tdb {tdb_c:.1f} (library range starts at tr = tdb)"); tr_c = tdb_c
        status, reasons = validity.check_inputs(tdb_c, tr_c, v_ms, rh_pct, met_wm2, clo)
        reasons = clamped + reasons
        if status in (validity.ABOVE, validity.INVALID):
            return StrainResult(status, 0.0, True, "validity gate", reasons=reasons)
        if status == validity.BELOW:
            return StrainResult(status, None, False, "below model range (heat strain not modelled)", reasons=reasons)
        dur = duration_min or config.PHS_DURATION_MIN
        kw = {PHS_KWARGS["posture"]: posture, PHS_KWARGS["acclimatized"]: acclimatized,
              PHS_KWARGS["drink"]: drink, PHS_KWARGS["duration"]: dur}
        met_arg = met_wm2
        if self._real:
            kw["posture"] = POSTURE_NAMES.get(posture, posture)       # 1/2/3 -> "sitting"/"standing"/"crouching"
            met_arg = met_wm2 / config.W_PER_MET
            kw["model"] = config.PHS_MODEL
            kw["limit_inputs"] = config.PHS_LIMIT_INPUTS
            kw["round_output"] = False                                  # docstring: avoids rounding drift when chaining segments
        if state and state.values:
            kw.update(state.values)
            acc, var_kw = self._accepted()
            if acc is not None and not var_kw:       # drop (and remember) state kwargs this phs() cannot take: never crash, never hide it
                for k in [k for k in kw if k in STATE_INPUT_FIELDS and k not in acc]:
                    self.dropped_state_kwargs.add(k); del kw[k]
        try:
            res = self.phs(tdb_c, tr_c, v_ms, rh_pct, met_arg, clo, **kw)
            tre, l95 = _get(res, LIMIT_FIELDS["tre"]), _get(res, LIMIT_FIELDS["loss95"])
            if tre != tre or l95 != l95:     # NaN: the library refused or could not evaluate; never read as "unlimited"
                raise ValueError(f"model returned NaN limits (d_lim_t_re={tre}, d_lim_loss_95={l95}); inputs: tdb={tdb_c} tr={tr_c} v={v_ms} rh={rh_pct} met={met_arg:.2f} clo={clo}")
            new_state = PhsState({k: _get(res, k) for k in STATE_INPUT_FIELDS if _has(res, k)})
            t_re_end = _get(res, "t_re") if _has(res, "t_re") else None
            sweat = _get(res, "sweat_loss_g") if _has(res, "sweat_loss_g") else None
        except Exception as e:   # any model failure => fail safe, never silent
            self.model_errors += 1
            extra = ""
            if isinstance(e, AttributeError):
                try:
                    import dataclasses as _dc
                    extra = " | result fields: " + ", ".join(f.name for f in _dc.fields(res)) if _dc.is_dataclass(res) else " | result dir: " + ", ".join(n for n in dir(res) if not n.startswith("_"))
                except Exception: pass
            return StrainResult("MODEL_ERROR", 0.0, True, "model error", reasons=[repr(e) + extra])
        # PROPOSED: conservative limit = smaller of rectal-temp limit and 95th-percentile water-loss limit
        limiting, minutes = ("rectal temperature", tre) if tre <= l95 else ("water loss (95%)", l95)
        minutes = max(0.0, min(minutes, float(dur)))
        if minutes <= config.LIMIT_EXCEEDED_MIN:      # 4.8.0 returns 1, not 0, once the limit is already passed (diagnose_phs Q2)
            minutes, limiting = 0.0, limiting + " (already exceeded)"
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
    wanted = list(PHS_KWARGS.values()) + STATE_INPUT_FIELDS
    for k in wanted:
        if k not in params and not accepts_kw:
            problems.append(f"phs() has no parameter {k!r}")
    return problems
