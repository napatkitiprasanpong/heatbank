# HeatBank: a heat budget for every shift

Planning-stage prototype for the Climate-Resilient Worker Health challenge. **Not a medical device.** Thresholds are PROPOSED
parameters, not clinical guidance. Everything runs on synthetic data unless you supply data you have the right to use.
Version 0.6.0. Status: Parts 1-3 of 3 built (weather -> PHS -> safe minutes -> planner -> alerts -> fallback -> simulation -> phone and supervisor views, Thai/English, site-bias software, documentation pack). **Nothing has run against the real PHS yet: start with `python scripts/check_signatures.py`.** Read `docs/AUDIT.md` first.

## Quick start

```
pip install -e .                       # installs pythermalcomfort 4.8.0 + thermofeel 2.3.0 (pinned)
heatbank check                         # what is installed, what is unverified
python scripts/check_signatures.py     # probes the library's calling convention and prints result fields
make verify                            # 107 tests + toy integration check (no library needed)
make check                             # with the library installed: writes the two files to send back
heatbank plan --scenario hot_humid     # shift plan with alerts and water estimate (real PHS)
heatbank simulate                      # V2 stress test, writes out/v2_summary.md
heatbank simulate --forecast-only      # V2 on the path a node-less site really uses (radiant fallback)
heatbank simulate --rest-area fan      # where rest happens: cooled_cabin, fan or shade
heatbank faults                        # V3 fault injection (add --real for the real model)
python -m heatbank.export --toy        # builds dashboard/data.js; drop --toy to use the real PHS
open dashboard/index.html              # worker view, supervisor view: static, no server, no network
heatbank plan --scenario hot_humid --toy --archetype A09    # demo without the library; TOY, not results
```

REAL weather (NASA POWER, D8): `python -m heatbank.export --nasa-power 24.45 54.38 2025-07-15` (needs internet once; place and date are yours to choose,
pick a date at least a week old so solar data exists), then open `dashboard/index.html`. `heatbank plan --nasa-power ...` and `heatbank simulate --nasa-power ...` take the same three values. Local time is UTC+4 unless you pass `--utc-offset`.

Without installing anything: `python -m heatbank.cli ...` works from this folder.

`make verify` runs without the library, so four tests that need pythermalcomfort are skipped there. Install the library to run all of them.

## Commands

| Command | What it does |
|---|---|
| `heatbank check` | Installed libraries and open items |
| `heatbank safe-minutes` | Safe minutes per hour per archetype |
| `heatbank plan` | Shift plan with alerts and water estimate |
| `heatbank simulate` | V2 scenario stress test (SIMULATED). Options: `--toy`, `--forecast-only`, `--rest-area`, `--probe-min`, `--adherence`, `--out` |
| `heatbank faults` | V3 fault injection |

All results are simulated or proposed, never validated clinical output.

## Where things are

- `docs/REQUIREMENTS_TRACE.md`: are the requirements met?
- `docs/AUDIT.md`: plot holes, bottlenecks, schedule
- `docs/GOVERNANCE_CHARTER.md`: draft
- `docs/DEMO_CHECKLIST.md`
- `docs/ARCHITECTURE.md`: component map
- `docs/LIMITATIONS.md`: every proposed parameter and open item
- `docs/VALIDATION.md`: V1-V5 status
- `docs/PILOT_PROTOCOL.md` and `docs/REVIEW_PACKET.md`: for a real pilot and for outside reviewers
- `DATA_SOURCES.md`: data declaration
- `LICENSES/`: third-party notices
- `node/README.md`: optional site sensor node (software side only, no firmware yet)

## Rules the code enforces

- **P1** the planner can only hold or reduce exposure.
- **P2** stale data, faults or out-of-range input only raise the alert level.
- **P3** no identifiers, no real people.
- **P4** each output file has a `.meta.json` declaring source, synthetic flag and model.
- **P5** provider failure falls back to the cache and says so. Open-Meteo stays off until you resolve its non-commercial licence (U2).
