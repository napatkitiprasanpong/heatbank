# Validation status

| ID | Test | Status |
|---|---|---|
| V1 | Wrapper vs library on a grid | Written (`tests/test_core.py`), skipped until pythermalcomfort is installed. Shipped test cases not yet located (D7). |
| V2 | Scenario stress test | Harness done (`heatbank simulate [--forecast-only]`). Now prints a PLAN SAFETY pass/fail and the model-error count. Only run with the TOY model so far: no results yet. Toy `hot_dry` already FAILS plan safety (audit A9). |
| V3 | Fault injection | Done, 8/8 pass: level never below clean baseline, banner always shown (`heatbank faults`). Model-independent. |
| V4 | HTT comparison | Not started (optional, licence unverified, U4). |
| V5 | Site bias test | Software done (`heatbank/site/bias.py`, `python -m heatbank.site.demo`). Plumbing demo only, synthetic node data. Needs a real node for a real result. |

## Tests
`make test` runs 70 tests (about 0.5 s): Parts 1-2, plus Part 3 (strings, aggregation, k and safety override, front-end offline check,
JS-vs-Python fallback parity via node, site bias, engine smoke test, look-ahead P1, forecast-only V2). One test is skipped until
`pythermalcomfort` is installed.

## v0.4 additions
`make verify` runs 99 tests plus `scripts/integration_check.py --toy` (Parts 1-3 end to end, both pages in a fake DOM). On your machine
`make check` runs `check_signatures.py` and the real integration check. V3 can use the real model: `heatbank faults --real`.
V2 now also covers `gulf_peak`, reports the 480-minute cap share (A11), rest-area findings (A9) and library sweat behaviour (A12).
Measures for a real pilot: `docs/PILOT_PROTOCOL.md`. Requirement-by-requirement status: `docs/REQUIREMENTS_TRACE.md`.
