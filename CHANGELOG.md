# Changelog
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
