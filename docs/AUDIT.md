# Audit: plot holes and bottlenecks (v0.3.0, written 2026-11-04)

Method: read every module of Parts 1-2, ran the toy-model flows, probed suspicious behaviour, then fixed what could be fixed
without a decision from the owner. Nothing here was run against the real `pythermalcomfort`: it is not installed in the build
environment and there is no network. Items marked *from memory* are my recollection of the library and must be confirmed by
`python scripts/check_signatures.py`.

Status words: **FIXED** (code + test), **MITIGATED** (guard added, root cause open), **OPEN** (needs the owner or real data).

## Critical: could sink the submission or the claims

| ID | Finding | Status |
|---|---|---|
| A1 | **Fail-safe masks integration bugs.** Any exception inside `phs()` becomes `MODEL_ERROR`, which means fail-safe, which means Red. If one kwarg name is wrong, *every* hour for *every* worker is Red, V3 still passes ("never below baseline"), and the output looks cautious instead of broken. The unit tests use fakes, so they cannot see it. The wrapper also passes `sweat_loss_g` back in as input; *from memory* `phs()` takes `sweat_rate` as input and only returns `sweat_loss_g`, and unknown kwargs may be silently ignored, which would make carry-over (the core of the tracker) a no-op. | **MITIGATED.** `StrainEngine.smoke_test()` checks that a clean call works and that carried state changes the result; the CLI and V2 refuse to write results if it fails; model errors are counted and printed in the V2 summary; `check_signatures.py` probes which state kwargs the library accepts. Root cause (the real names) is **OPEN** until you run the script. |
| A2 | **Radiant temperature in forecast-only mode is a constant +15 C.** Wrong at night (no sun, so about tdb), wrong in strong sun, and at tdb >= 46 C it pushes tr past the model's 60 C limit, so the validity gate returns Red for the afternoon. Abu Dhabi summers routinely exceed that, and tr is the biggest input to PHS. V2 never exercised this path because the synthetic scenarios carry a globe temperature. | **MITIGATED.** `run_v2 --forecast-only` and `export --forecast-only` now run the fallback path; `TR_FALLBACK_MODE = "solar"` scales the offset by forecast shortwave radiation (night: tr = tdb). Default stays `constant` until you decide; neither number has a citation. **OPEN:** replace with a documented method (thermofeel MRT or a Liljegren-derived globe temperature), and decide what the product says when tr > 60 C: with no shade/sun attribute on archetypes the only honest output is Red. |
| A5 | **The plan never says how aggregates get from phones to the dashboard.** "Computed on the phone, no accounts, supervisors see only aggregates" needs a transport, and every transport carries some identifier (device id, IP address, timing). | **FIXED by design.** The supervisor view is built from the task roster (zone x worker type x headcount), not from device reports; there is no upload channel. Trade-off: it shows what the plan implies for each crew group, not what each person did. If a consented live mode is ever added, it needs secure aggregation or a trusted collector and its own governance review. |
| A6 | **Minimum group size k conflicts with safety.** Hiding any cell under k hides exactly the case that matters: one Red group in a crew of twelve. | **FIXED.** Small zones are pooled, never shown alone; the site status is the worst level of *any* group and is shown as level + action with no count (`dashboard_model.py`, test `test_small_group_never_hides_a_hazard`). |
| A7 | **The node's "bias correction" conflicts with P2.** A correction that makes the site look cooler than the forecast would lower alerts on one cheap sensor. | **FIXED.** Only upward corrections are applied by default; cooling corrections are reported and ignored (`SITE_BIAS_ALLOW_COOLING`); frozen or spiking data is never learned from. |
| A8 | **Nothing real has run.** Every number in `out/` so far is from the toy model or fakes. `check_signatures.py` output has not come back, so U5 and U6 are open and V1 has not run. 16 days remain. | **OPEN. This is the critical path.** See "Schedule". |

## Design holes (decide before submission)

| ID | Finding | Status |
|---|---|---|
| A3 | **The planner was myopic.** It sized each hour against the current hour's conditions only, so a rising morning temperature overshoots. This undermines the headline claim "plan before conditions arrive". | **FIXED.** `PLAN_LOOKAHEAD_H = 1`: work is sized against the worse of now and the next hour. It can only lower planned work (test `test_lookahead_never_adds_work_P1`). The phone and supervisor views also show "next change" from the full-day plan. |
| A4 | **The P1 check was a tautology.** `work = min(work, base)` where `base` comes from the same number. The real P1 question is whether *following the plan* keeps people under the model limit. | **MITIGATED.** V2 now prints `PLAN SAFETY` per scenario: time at Red under 100 % adherence must be zero. It already **FAILS on `hot_dry` with the toy model**, because the toy's shade rest does not recover above 40 C. Whether real PHS does the same is unknown, and it is the most important number V2 will produce. |
| A9 | **Rest is assumed to recover.** Rest is modelled in shade at 100 W/m2 with tr = tdb. At high air temperature, shade alone may not cool anyone, and "rest" in the plan becomes false comfort. | **OPEN.** Make the rest area a site parameter (shade / fan / air-conditioned cabin) and have the planner say which one it assumes. If PHS shows no recovery, the planner must say "no work" rather than "rest 50 min". |
| A10 | **Alert level conflates two things:** "conditions are hostile for continued work" and "this person's body is near the limit". A worker who is resting exactly as told still sees Red, which is the alarm fatigue the challenge text warns about. | **OPEN.** Recommend two readings on the phone: a condition level for the task, and a state level while resting based on predicted rectal temperature (`t_re_end` is already returned). Needs your decision because section 7 of the plan defines the basis. |
| A11 | **Fraction used depends on the 480-minute cap.** `fraction = 1 - remaining / fresh_allowable`, both capped at `PHS_DURATION_MIN`. In mild weather both hit the cap, so the ratio says "used" because of an arbitrary cap. This is the likely cause of the 40 % Orange/Red on the cool control day in the toy run (toy artefact in part). | **OPEN.** Check with real PHS. If it persists, use an absolute remaining-minutes threshold or the rectal-temperature margin instead of the ratio. |
| A12 | **Water loss may not carry over.** *From memory*, PHS restarts its water-loss total from zero when continued, so the water limit is under-estimated after the first segment, and the planner's "min of rectal and water limit" quietly becomes rectal-only. The toy model hides it (water limit is always rectal + 30). | **OPEN.** Check on the real library; if it does not carry, track cumulative sweat loss in `ExposureTracker` and compare it with the limit yourself. |
| A13 | **Synthetic scenarios were tuned to stay inside the model.** The globe rise was cut from 12 C to 5 C so tr would stay under 60 C, and a test asserts it. That makes V2 flatter than reality, and it hides the Gulf case in A2. | **OPEN.** Add a "Gulf peak" scenario (tdb 46-48 C, strong sun) and report what the system does there, even if the answer is "Red all afternoon, validity gate". |
| A14 | **V2's "false-alarm rate" is circular.** The same model decides whether an alert was needed. | **MITIGATED.** The summary now calls it "Orange/Red share of crew-time", not a false-alarm rate. Define a counterfactual measure (alert issued, but continuous work to end of shift would not have reached the limit) and still label it model self-consistency. |
| A15 | **The phone cannot see what the worker did.** Adherence is unobserved. If the view assumes the plan was followed, a worker who skipped breaks is under-warned, which breaks P2. | **OPEN.** Either add a two-button "break started / back at work" log (local, minimal, optional) and assume continuous work when nothing is logged, or state the limit plainly in the documentation. |
| A16 | **The plan says computation is on the phone; PHS is Python.** The static view cannot run ISO 7933. | **FIXED by design, stated plainly.** Python precomputes plan tables per worker *type* (no people) and exports them to `dashboard/data.js`; the browser only displays them and applies the stale-forecast rule itself. A JavaScript port of PHS is possible (MIT code, keep the notice) but costs days and needs its own V1. |
| A17 | **V1 may be impossible as written.** The plan's pass criterion is "run the test cases shipped with pythermalcomfort". Package wheels usually do not ship the test suite. | **OPEN.** Check the installed package. If absent, V1 becomes (a) wrapper equals direct library call (plumbing only) and (b) a few ISO 7933 worked examples you obtain legitimately, or say so in the documentation. |

## Smaller items

* Frozen-sensor rule (6 identical readings) can fire on a sensor with coarse resolution in stable conditions; define the sampling interval and resolution with the node. Spike rule looks at the whole history list, so one spike stays flagged until it scrolls out.
* The first-aid wording on the phone is generic and **must** be reviewed by a clinician or occupational-health professional; it is shown in the Red state only and says it is a draft.
* Thai strings are a draft written by Claude and flagged "needs human review" in the UI. You said you would review them; that is a submission blocker.
* The stop pictogram is a no-entry bar in an octagon, not a red cross, because the red cross is a protected emblem.
* Alert fractions (50/75/100 %), k = 5, 30-minute degraded cap and 180-minute stale limit are all proposals (U7). They are labelled as such in the UI footer and the docs.
* The pooled-zone rule means a crew of fewer than five people sees only a site status. That is intended, but say it in the pitch.

## Bottlenecks

**B1 Schedule (the real one).** Everything after `check_signatures.py` depends on its output. Until it runs, there are no real results, A1/A2/A11/A12 are unknown, and V1 cannot start. Today is 2026-11-04; registration closes 11-10 and submission is 11-20.

**B2 Compute.** One full V2 run makes about 15,400 real PHS calls (24,300 requests, 37 % saved by the new cache), and each call integrates up to 480 minutes. On the toy model that is 0.4 s; with real PHS it is `15,400 x time per call`. `check_signatures.py` now prints the time per call and the projected run time. If it is more than about ten minutes: raise `STEP_MIN` to 15, shorten `PHS_DURATION_MIN` for the remaining-time probe (interacts with A11), or run V2 on 6 archetypes.

**B3 Review capacity.** Three things need a human who is not Claude: Thai strings, first-aid wording, and the licence reading for D1/D2 (U2, U3). Start them now; they are waiting on people, not code.

**B4 Scope.** Cut order from the plan still applies: node firmware does not exist and is first to go; V4 second; third language third; UTCI fourth. Never cut V3, the charter or the data declaration.

## Schedule (from today, 2026-11-04)

| When | Do | Why now |
|---|---|---|
| Nov 4-5 | Run `python scripts/check_signatures.py`, send the output. Run `make test`. | Unblocks A1, A2, A11, A12, B2. |
| Nov 5-6 | Read the official FAQ and rules (U1). Decide weather source (U2/U3). Register the team. | Registration closes Nov 10; a missed rule can disqualify. |
| Nov 6-9 | First real V2 run, both `--forecast-only` and with globe. Add the Gulf scenario (A13). | The PLAN SAFETY line decides whether the planner is sound. |
| Nov 9-12 | Decide A9, A10, A15 with the real numbers in hand. Send Thai strings and first-aid text for review. | Design decisions need data. |
| Nov 13-17 | Finish docs with real results; record the demo (`docs/DEMO_CHECKLIST.md`). | |
| Nov 19 | Submit. | One day of buffer before Nov 20. |
