# Changelog
## 0.5.3
- Fix: limits of 1 minute (library's 'already exceeded') are 0; t_re at or above 38.0 is Red. Earlier V2 results are void.
- Rest check thresholds corrected; `--probe-min`; 107 tests.
## 0.5.2
- `heatbank simulate --rest-area`; summaries also saved with a tag; seated rest now 58 W/m2; `scripts/diagnose_phs.py` (acclimatisation, limit counting, recovery traces).
## 0.5.1
- V1 grid test uses the 4.8.0 calling convention and gains four real-library sanity tests (monotonic in heat and workload, carry-over, shade recovery). Versions pinned in requirements.txt.
## 0.5.0 (hotfix after first real-library run)
- Wrapper matches pythermalcomfort 4.8.0: posture text, met in met units, ISO 7933:2023 limits (met 56-250 W/m2, tr-tdb 0-60), two extra carry-over inputs, round_output=False, limit_inputs=False, NaN fail-safe with reason.
- check_signatures probes fixed and now prints result fields. 101 tests.
## 0.4.0 (audit round 2)
- Wrapper: state inputs split from outputs, `sweat_loss_g` no longer passed in, unsupported state kwargs dropped and reported, sweat carry-over detected, optional water guard.
- Planner/tracker: configurable rest area with a recovery test (no work if rest does not cool), body-state second reading, cap diagnostic, solar radiant fallback by default.
- New scenario `gulf_peak`; V2 `--rest-area`; V3 `--real`.
- Phone: body-state line, out-of-range note, optional local break log, Get help card (call medic, message buddy). Supervisor: best hours for heavy tasks.
- Tools: `scripts/integration_check.py`, `tests/dom_smoke.js`, `make verify` / `make check`; `check_signatures.py` saves one output file.
- Docs: AUDIT round 2, REQUIREMENTS_TRACE, PILOT_PROTOCOL, REVIEW_PACKET; charter section 5 corrected. 99 tests (was 70).
## 0.3.0 (Part 3 + audit)
- Added: phone view and supervisor view (static, offline, EN/TH), strings module, export pack, aggregation with minimum group size and safety override, site-bias software and V5, governance charter, demo checklist, audit.
- Fixed/guarded (docs/AUDIT.md): A1 smoke test + model-error counter, A2 forecast-only V2 + solar radiant option, A3 planner look-ahead, A4 PLAN SAFETY line in V2, A6 safety override, A7 upward-only bias, stateless PHS cache (37 % fewer calls), check_signatures probes for carry-over and timing.
- Relabelled the V2 cool-day figure so it is not read as a validated false-alarm rate.
- 70 tests (was 41).
## 0.2.0 (Parts 1 + 2 combined)
- One installable package `heatbank` with a single CLI (`check`, `safe-minutes`, `plan`, `simulate`, `faults`).
- Added: planner, alert engine, fallback logic, exposure tracker with carry-over, V2 harness, V3 fault injection.
- Added: shift plan with water estimate and heavy-work hours, provenance sidecar for every output, provider factory.
- Fixed: synthetic globe rise exceeded the 60 C radiant limit; cool hours were skipped (now evaluated at the model minimum).
- Docs: architecture, limitations, validation status.
## 0.1.0 (Part 1)
- Weather providers + cache, PHS wrapper with validity gate, archetypes, DATA_SOURCES.md.
