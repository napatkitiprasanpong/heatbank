# HeatBank: a heat budget for every shift

A software-first heat-strain planner for outdoor and industrial crews, built for the **Climate-Resilient Worker Health** challenge statement of the Future Health Digital Innovation Challenge (Hack2skill, Abu Dhabi).

> **Not a medical device.** HeatBank gives planning recommendations, not diagnoses. All thresholds are **proposed design parameters**, not clinical guidance. Every result in this repository is **simulated**: synthetic weather (or a one-day replay of real weather) and a simulated crew. No real workers, no personal data, and no real-world validation.

Version **0.6.0** | Python 3.9+ | Owner: Napat Kitiprasanpong

## The idea

Most heat-stress tools react after the body is already strained, using one fixed threshold. HeatBank treats safe exposure as a **budget**. For each task, hour and worker type it computes how many minutes of work a standards-based model allows, then turns that budget into a work/rest schedule with graded alerts.

```
weather -> ISO 7933 Predicted Heat Strain (PHS) -> safe minutes per task and hour
        -> planner (work/rest, rotation, water) -> 4-level alert + one action
        -> worker phone view  +  supervisor view (crew aggregates only)
```

**Three differentiators**

1. **Forecast-driven safe minutes** from ISO 7933 (via `pythermalcomfort`), computed before conditions arrive, with heat load carried across the shift.
2. **Optional site correction.** Software that learns how far gridded weather is from a site sensor (software only; no firmware yet).
3. **Governance by architecture.** No accounts, no identifiers, no upload channel. Supervisors see group levels and actions, never individual readings, and groups smaller than 5 are pooled.

## Design rules enforced in code

| Rule | Meaning |
|---|---|
| **P1** Protection before productivity | The planner can only hold or reduce exposure relative to the conservative baseline. It never extends it. |
| **P2** Fail safe | Stale data, sensor faults and out-of-range inputs can only **raise** the alert level. The model never extrapolates. |
| **P3** Data minimisation | No identifiers and no real people. Archetypes are simulated. |
| **P4** Transparency | Every output file has a `.meta.json` sidecar declaring source, synthetic flag and model. |
| **P5** Offline-first | Provider failure falls back to the cache and says so. The views are static files that work offline. |

## Alert levels (PROPOSED, configurable)

Based on the fraction of the PHS allowable exposure time used, with carry-over across work and rest.

| Level | Used | Action |
|---|---|---|
| Green | < 50% | Normal work, water available |
| Yellow | 50% to < 75% | Drink and take a scheduled shade break |
| Orange | 75% to < 100% | Reduce intensity or rotate, cool rest now |
| Red | 100%+, predicted rectal temperature at or above 38.0 C, or any fail-safe | Stop heavy work, cool down, buddy check, call the medic if symptoms |

Level is shown as word, shape, colour and pictogram. English and Thai are supported. **The Thai text is a draft and has not been reviewed by a person.**

## Quick start

```bash
pip install -e .                       # installs pythermalcomfort 4.8.0 + thermofeel 2.3.0 (pinned)
heatbank check                         # what is installed, what is unverified
python scripts/check_signatures.py     # probe the library's calling convention and result fields
make verify                            # unit tests + toy integration check (no library needed)
make check                             # with the library: real integration check

heatbank plan --scenario hot_humid     # shift plan with alerts and water estimate (real PHS)
heatbank safe-minutes                  # safe minutes per hour per archetype
heatbank simulate                      # V2 stress test, writes out/v2_summary.md
heatbank simulate --forecast-only      # path a node-less site really uses (radiant fallback)
heatbank simulate --rest-area cooled_cabin   # shade | fan | cooled_cabin
heatbank faults [--real]               # V3 fault injection

python -m heatbank.export              # build dashboard/data.js (add --toy to skip the library)
open dashboard/index.html              # worker view + supervisor view: static, no server, no network
```

**Real weather replay (NASA POWER, D8):**

```bash
python -m heatbank.export --nasa-power 24.45 54.38 2025-07-15
```

Needs internet once. Pick a date at least a week old so solar data exists. Later runs work offline. `plan` and `simulate` accept the same three values. Local time is UTC+4 unless you pass `--utc-offset`. This is a replay of gridded data, not a forecast and not a site measurement.

`--toy` runs a stand-in model that shows the plumbing. **Toy numbers are not results.**

## What is built

- **Pipeline:** weather providers with offline cache, PHS wrapper with validity gate, exposure tracker with carry-over, planner with look-ahead, alert engine, fallback logic.
- **Views:** offline worker phone view (alert, action, Red first-aid card, call-medic and message-buddy buttons whose numbers stay on the phone) and supervisor view (zone table, first break, rotation, best hours for heavy tasks).
- **Evidence tooling:** V2 scenario stress test, V3 fault injection, V5 site-bias software.
- **Governance:** draft worker charter, data declaration, pilot protocol, requirements trace, limitations and audit log.

## Validation status

| ID | Test | Status |
|---|---|---|
| V1 | Wrapper vs library on a grid | Done (grid test). The library's own shipped test cases were not located. |
| V2 | Scenario stress test (12 simulated archetypes) | Run on the real model with **synthetic weather**. See below. |
| V3 | Fault injection | **8/8 pass**: the level never falls below the clean baseline and a degraded banner is always shown. |
| V4 | HTT dataset comparison | Not started (licence unverified, optional). |
| V5 | Site bias | Software only; plumbing demo with synthetic node data. No real sensor. |

**Tests:** 138 unit tests pass (5 skip without the library). Both web pages are exercised in a fake DOM.

### V2 headline results (simulated; generated at v0.5.3)

Synthetic weather, 12 simulated archetypes with unverified parameters, 100% adherence, real PHS.

| Scenario | No plan: archetypes reaching the model limit | Planned, shade rest: time at Red | Planned, cooled cabin: time at Red (share of shift worked) |
|---|---|---|---|
| cool (control) | 2/12 | 0.0% | 0.0% (99.2%) |
| hot_humid | 10/12 | 22.4% | 0.0% (65.3%) |
| hot_dry | 12/12 | 20.6% | 0.0% (43.9%) |
| gulf_peak | 12/12 | 33.9% | 0.0% (35.3%) |

**Read this honestly.** With shade as the rest area and an optimistic synthetic globe temperature, the plan **fails** the plan-safety check in all three hot scenarios. It passes with a cooled-cabin rest area and in the forecast-only (solar fallback) run. Passing there is partly achieved by assigning much less work. The "cool day" Orange/Red share is a model self-consistency number, not a validated false-alarm rate. Result files go to `out/` (git-ignored), so re-run `heatbank simulate` to regenerate them. These runs predate the NASA POWER source; no real-weather V2 result exists yet.

## Known limitations

- **Simulation only.** No claim of real-world lead time, false-alarm rate or protection. A pilot with legally usable, consented data is needed (`docs/PILOT_PROTOCOL.md`).
- **Population model.** PHS does not know individual health, medication, illness or hydration beyond a flag. Archetype-level, not individual.
- **Heat only.** Other climate-related occupational risks are not covered.
- **Alert fractions (50/75/100%) and group size k = 5 are proposals** that need literature or pilot calibration.
- **Archetype metabolic rate and clothing values are unverified** and need citations.
- **480-minute cap** affects the allowable-time ratio in roughly 40% of probes (audit A11).
- **Rest-area assumption** strongly changes the outcome (audit A9).
- **Views show precomputed plan tables** per worker type; PHS does not run in the browser.
- **No hardware:** the site node has software only, no firmware. No field test, dust or phone-battery handling.
- **Thai text, first-aid wording and the charter are unreviewed** by a native reader, a clinician or a lawyer (`docs/REVIEW_PACKET.md`).
- **Open-Meteo is off** until its non-commercial free-tier licence is resolved. NASA POWER is the first real source and its parser has been tested against a fixture only.

Full list: `docs/LIMITATIONS.md` and `docs/AUDIT.md`.

## Repository layout

```
heatbank/            Python package
  weather/           providers (scenarios, CSV, NASA POWER, Open-Meteo), cache
  strain/            PHS wrapper, validity gate, radiant temperature, WBGT hook
  archetypes/        simulated worker types
  planner/  alerts/  fallback/  i18n/  sim/  site/
  cli.py  config.py  export.py  dashboard_model.py  provenance.py
dashboard/           static worker + supervisor views (no server, no CDN, no analytics)
scripts/             check_signatures, integration_check, diagnose_phs, fetch_nasa_power
tests/               138 tests + headless page test
docs/                architecture, audit, limitations, validation, charter, pilot protocol, trace
node/                optional site sensor node (software side only)
LICENSES/            third-party notices
DATA_SOURCES.md      declaration of every data source
```

## Data and licences

Every data source is declared in [`DATA_SOURCES.md`](DATA_SOURCES.md). The prototype uses no real worker data and no personal data. Weather is synthetic (team-generated) or a NASA POWER replay. No web fonts, CDN scripts, analytics or third-party icon sets are used (enforced by a test).

Third-party software:

- **pythermalcomfort** (MIT). Tartarini and Schiavon, 2020, *SoftwareX* 12, 100578.
- **thermofeel** (Apache-2.0). Brimicombe et al., 2022, *SoftwareX* 18, 101005.
- **Weather data:** NASA Langley Research Center (LaRC) POWER Project, funded through the NASA Earth Science/Applied Science Program.

No code was copied from repositories without a licence. The patented ECTemp method (US 10,702,165 B2) is not used. This is not legal advice.

**Project licence:** not yet chosen. Add a `LICENSE` file before publishing if you want others to reuse the code.

## Documentation

[`REQUIREMENTS_TRACE`](docs/REQUIREMENTS_TRACE.md) | [`ARCHITECTURE`](docs/ARCHITECTURE.md) | [`AUDIT`](docs/AUDIT.md) | [`LIMITATIONS`](docs/LIMITATIONS.md) | [`VALIDATION`](docs/VALIDATION.md) | [`GOVERNANCE_CHARTER`](docs/GOVERNANCE_CHARTER.md) | [`PILOT_PROTOCOL`](docs/PILOT_PROTOCOL.md) | [`REVIEW_PACKET`](docs/REVIEW_PACKET.md) | [`DEMO_CHECKLIST`](docs/DEMO_CHECKLIST.md) | [`CHANGELOG`](CHANGELOG.md)
