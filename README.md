# HeatBank: a heat budget for every shift

Planning-stage prototype for the Climate-Resilient Worker Health challenge. **Not a medical device.** Thresholds are PROPOSED
parameters, not clinical guidance. Everything runs on synthetic data unless you supply data you have the right to use.
Version 0.5.0. Status: Parts 1-3 of 3 built (weather -> PHS -> safe minutes -> planner -> alerts -> fallback -> simulation -> phone and supervisor views, Thai/English, site-bias software, documentation pack). **Nothing has run against the real PHS yet: start with `python scripts/check_signatures.py`.** Read `docs/AUDIT.md` first.

## Quick start
    pip install -e .                       # installs pythermalcomfort + thermofeel
    heatbank check                         # what is installed, what is unverified
    python scripts/check_signatures.py     # resolves plan U5/U6, send the output to Claude
    make verify                            # 99 tests + toy integration check (no library needed)
    make check                             # on your machine with the library: writes the two files to send back
    heatbank plan --scenario hot_humid     # shift plan with alerts and water estimate (real PHS)
    heatbank simulate                      # V2 stress test, writes out/v2_summary.md
    heatbank simulate --forecast-only      # V2 on the path a node-less site really uses (radiant fallback)
heatbank faults                        # V3 fault injection
python -m heatbank.export --toy        # builds dashboard/data.js; drop --toy once PHS works
open dashboard/index.html              # worker view, supervisor view: static, no server, no network
    heatbank plan --scenario hot_humid --toy --archetype A09    # demo without the library; TOY, not results

Without installing anything: `python -m heatbank.cli ...` works from this folder.

## Where things are
See `docs/REQUIREMENTS_TRACE.md` (are the requirements met?), `docs/AUDIT.md` (plot holes, bottlenecks, schedule), `docs/GOVERNANCE_CHARTER.md` (draft), `docs/DEMO_CHECKLIST.md`, `docs/ARCHITECTURE.md` (component map), `docs/LIMITATIONS.md` (every proposed parameter and open item),
`docs/VALIDATION.md` (V1-V5 status), `DATA_SOURCES.md` (data declaration), `LICENSES/` (third-party notices).

## Rules the code enforces
P1 the planner can only hold or reduce exposure. P2 stale data, faults or out-of-range input only raise the alert level.
P3 no identifiers, no real people. P4 each output file has a `.meta.json` declaring source, synthetic flag and model.
P5 provider failure falls back to the cache and says so. Open-Meteo stays off until you resolve its non-commercial licence (U2).
