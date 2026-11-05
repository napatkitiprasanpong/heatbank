# Demo and submission checklist

## Before recording (run in this order)
1. `pip install -e .` then `make check` (writes `out/check_signatures_output.txt` and `out/integration_check.txt`) and fix the two mapping dicts in `strain/phs_wrapper.py` if needed (U5/U6, audit A1).
2. `make test` : all green except tests that need the real library, which should now run too.
3. `heatbank check` : no UNVERIFIED surprises you cannot explain.
4. Real run: `heatbank simulate` and `heatbank simulate --forecast-only` . Read the `PLAN SAFETY` line for each scenario and the model-error count (must be 0).
5. `python -m heatbank.export --scenario hot_humid` (without `--toy`) then open `dashboard/index.html`. No server needed.
6. Thai strings reviewed by a human; first-aid wording reviewed by a clinician (or removed from the demo).
7. `DATA_SOURCES.md` matches what the run actually used. Weather source decision (U2/U3) recorded.

## Demo script (about 3 minutes; every number on screen must come from the real run, not the toy)
| Time | Show | Say |
|---|---|---|
| 0:00 | Worker view, hot-humid, heavy-work archetype at 07:00 | "This is a heat budget for one worker type. Green now." |
| 0:30 | Drag the hour slider to 11:00 | "Same worker later: Orange, one action, plan says work 10 minutes, rest 50, rotate heavy tasks. Level is shown as shape, word and picture." |
| 1:00 | Switch language to Thai | "Thai draft, reviewed by a Thai speaker." (only say this if true) |
| 1:20 | Connection: Offline 5 hours | "The forecast is old, so the level goes up and a banner says why. Never down." |
| 1:40 | Connection: No forecast | "No data means Red. Plan content is hidden, not guessed." |
| 2:00 | Supervisor view | "Zones, counts, first break, rotation. Small crews are pooled. The site status shows the worst group with no counts, so a small group cannot hide." |
| 2:15 | Red screen | "Help is one tap, started by the worker. Nothing is sent automatically." |
| 2:30 | `out/v2_summary.md` | State PLAN SAFETY result honestly. "Simulated. We do not claim real-world lead time or false-alarm rate." |
| 2:50 | Governance charter | "Data use restriction, pooled groups, no individual health data." |

## Do not say
* Anything about real-world accuracy, lead time or false alarms. Only simulation exists.
* "Validated", "clinically proven", "medical device".
* That Thai text is reviewed unless it is.

## Submission pack (T6/T7)
- [ ] Repo with README, `DATA_SOURCES.md` complete, `LICENSES/` with notices for pythermalcomfort (MIT) and thermofeel (Apache-2.0) and citations (Tartarini and Schiavon 2020; Brimicombe et al. 2022)
- [ ] `docs/`: architecture, assumptions and limitations, validation status with real V1/V2/V3, `AUDIT.md`, governance charter
- [ ] Every output has its `.meta.json`; synthetic data labelled everywhere
- [ ] Demo video (under the length the organisers allow; check U1)
- [ ] Technical documentation in the format the organisers ask for (U1)
- [ ] Team registered, lead 18+, before 2026-11-10
- [ ] Submitted by 2026-11-19, one day before the deadline
