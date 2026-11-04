# Architecture (Parts 1-3)

```
weather provider --> cache (P5) --> [C1]  WeatherHour: tdb, rh, wind, solar, (globe temp)
                                      |
                  globe temp -> tr (ISO 7726)  |  no globe temp -> placeholder offset (reported)
                                      v
 [C2] WBGT hook (thermofeel, unconfirmed U6)    [C3] StrainEngine -> PHS (ISO 7933), validity gate, fail-safe
                                      |  safe minutes, carry-over state
                                      v
 [C4] archetypes (simulated) --> ExposureTracker: fraction used = 1 - remaining / fresh-start allowable
                                      |
                      [C5] planner (P1: hold or reduce only)      [C9] fallback (P2: only raises)
                                      |                                   |
                                      +-------------> [C6] alert engine <-+   4 levels, one action each
                                                          |
                              plan table, water estimate, V2 harness, V3 fault injection
```

| Plan ID | Component | File |
|---|---|---|
| C1 | Weather ingestion, cache, providers | `heatbank/weather/` (`scenarios.py`, `csv_provider.py`, `open_meteo.py`, `cache.py`, `factory.py`) |
| C2 | Heat-index engine (WBGT hook) | `heatbank/strain/wbgt.py` |
| C3 | Strain engine (PHS wrapper) | `heatbank/strain/phs_wrapper.py`, `validity.py`, `radiant.py` |
| C4 | Worker archetypes | `heatbank/archetypes/archetypes.py` |
| C5 | Planner | `heatbank/planner/planner.py` |
| C6 | Alert engine | `heatbank/alerts/engine.py` |
| C9 | Fallback / fault logic | `heatbank/fallback/fallback.py` |
| V2 / V3 | Simulation, fault injection | `heatbank/sim/` |
| C7 | Site node bias correction + V5 (software only; no firmware) | `heatbank/site/bias.py`, `node/README.md` |
| C8 | Supervisor aggregation (min group size k, safety override) | `heatbank/dashboard_model.py` |
| C6 (i18n) | English + Thai (draft) strings | `heatbank/i18n/strings.py` |
| Export | Plan tables and aggregates for the static views | `heatbank/export.py` -> `dashboard/data.js` |
| Views | Worker phone view, supervisor view (static, offline) | `dashboard/*.html`, `core.js`, `ui.js`, `worker.js`, `supervisor.js` |

Principles in code: **P1** `plan_hour` asserts work <= baseline. **P2** `alerts.compose` and `FallbackState.apply` can only raise;
out-of-range input never extrapolates. **P3** no identifiers anywhere; archetypes are simulated. **P4** every output has a
`.meta.json` sidecar. **P5** provider failure falls back to the cache and says so.

The plan's `src/...` layout became the `heatbank/...` Python package so it can be installed and imported.

## Part 3: how the views get their numbers
```
Python (where PHS lives)                                    Browser (static files, no network)
simulate_worker per worker TYPE --> plan tables --+
roster (zone x type x headcount) --> aggregate()  +--> data.js --> worker.html / supervisor.html
                                     (k pooling,                   core.js applies the stale-forecast rule itself
                                      site worst level)            (P2: only raises) from generated_at
```
* No per-device upload exists. The supervisor view comes from the task roster, not from phones (audit A5).
* The browser cannot run PHS, so it displays precomputed tables for worker types and re-applies the P2 fallback rules by itself,
  because a phone offline in a van keeps ageing the data (audit A16). `tests/test_part3.py` checks that `core.js` and `fallback.py`
  agree on a grid of cases.
* No web fonts, CDNs or analytics (test enforces it). Level is shown as word + shape + colour + pictogram.
