# Assumptions, parameters and open items

All values below are PROPOSED design parameters in `heatbank/config.py`. They are not clinical guidance (plan U7).

| Parameter | Value | Basis | Status |
|---|---|---|---|
| Model input limits | tdb 15-50 C, tr 0-60 C, v 0-3 m/s, met 100-450 W/m2, clo 0.1-1 | pythermalcomfort ISO 7933:2004 docstring | confirm 2023 mode (U5) |
| Cool-side handling | tdb/tr raised to the model minimum, then evaluated | only makes the result more cautious | decision, `CLAMP_COOL_UP` |
| Safe minutes | min(rectal-temperature limit, 95th-percentile water-loss limit) | conservative choice | verify against ISO 7933 text |
| Alert fractions | 50 / 75 / 100 % of allowable exposure used | starting values | literature needed (U7) |
| Planner | works at most 50 % of remaining allowable time, rounded down to 5 min, max 60 | conservative baseline | literature needed |
| Degraded cap | 30 work min per hour | conservative preset | proposal |
| Rest model | shade (tr = tdb), met 100 W/m2 (real rest is lower) | conservative | proposal |
| Stale forecast | older than 180 min => at least Orange, +1 level | proposal | proposal |
| Sensor faults | 6 identical readings = frozen, jump > 8 C = spike | proposal | proposal |
| Radiant fallback | tr = tdb + 15 C when no globe temperature | placeholder | replace with a documented method |
| Planner look-ahead | worse of this hour and the next 1 h | audit A3 | proposal |
| Dashboard minimum group size k | 5, groups below are pooled | plan C8 | proposal (U7) |
| Site-bias correction | upward only, clip +/- 6 C, >= 6 paired hours | audit A7, P2 | proposal |
| Radiant fallback mode | `constant` (default) or `solar` | audit A2 | undecided |
| Thai text and first-aid wording | drafts | needs human and clinical review | UNVERIFIED |
| Archetype met / clo | 100/165/230 W/m2; 0.5/0.9 clo | from memory of ISO 8996/7243/9920 | UNVERIFIED, cite before submission |

## Not verified in this build
- The real `pythermalcomfort` and `thermofeel` were never run here (no network). Argument and result names are in two dicts in `phs_wrapper.py`; run `heatbank check` and `scripts/check_signatures.py`.
- Whether PHS `sweat_loss_g` is cumulative from the passed-in state (the water estimate assumes it is).
- Open-Meteo response layout (from memory) and licence (non-commercial only, U2).
- No V2 result exists for the real model. The `--toy` model has the right shape, not physiology.

## Honest limits of the design
- Simulation only: no claim of real-world lead time, false-alarm rate or protection. Needs a pilot with legally usable, consented data.
- PHS is a population model for average workers; it does not know about individual health, medication or illness.
- Recommendation only. Not a medical device. The system never decides for the supervisor or the worker.

## Added in v0.3.0 (see docs/AUDIT.md for the full list)
- The static views show precomputed plan tables for worker *types*; they do not run PHS in the browser (A16).
- The supervisor view reflects the plan for each crew group, not what individuals actually did (A5, A15).
- Rest is assumed to recover in shade; this may be false at high air temperature (A9).
- Alert level mixes "hostile conditions" and "body near limit" (A10).
- No site-node firmware exists. `heatbank/site/bias.py` is software only; the demo uses synthetic node data and proves plumbing, not a sensor.
