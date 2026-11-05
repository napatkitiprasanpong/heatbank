# v0.5.3: what scripts/diagnose_phs.py showed on pythermalcomfort 4.8.0 (2026-11-05)
* **Red could not occur (bug, fixed).** Once a limit is already passed the library returns **1 minute**, not 0. `fraction = 1 - 1/21` stayed Orange forever, so every earlier PLAN SAFETY "PASS" was hollow. Now: limits of 1 minute or less count as exceeded (0 min), and predicted t_re at or above 38.0 C is Red regardless. Rerun V2: the earlier V2 numbers are void.
* **A12 resolved:** cumulative sweat carries; limits are counted from the start of the current segment (Q4: 248 - 120 = 128).
* **U11 mostly supported:** the rectal limit behaves as 38.0 C (limit reached at 42 min when t_re ends at 38.06; d_lim collapses right after 38.0). Still cite the standard.
* **Acclimatisation works** (38 C humid: t_re 37.54 vs 38.43 in the 2023 model). It was identical in V2 only because the 480 cap and the water-loss limit dominated (A11). At 45 C dry both reach the limit in 30 min.
* **A9 changed:** seated rest in shade DOES cool a strained worker, even at 44 C dry air (38.09 -> 37.44 C in 30 min; 37.1 C settles after an hour at 33 C). The earlier "rest does not cool" came from a threshold sitting on that asymptote and from rest at 100 W/m2. Thresholds moved (strained above 37.4 C, recovery drop 0.05 C). Humid heat may differ: check hot_humid.
* **Gulf-like conditions (45 C air, tr 50, rh 25, acclimatised, heavy):** a fresh worker has about 21 minutes; the model's t_re plateaus near 38.4 C and sweat reaches 10 L over 10 h. That is the case the planner must call "no heavy work".
New switch: `heatbank simulate --probe-min 720` shows how much the 480-minute cap distorts the ratio (A11).

---

# v0.5.2: first real V2 results and what they mean (2026-11-05)
Read these as questions, not findings. All simulated, synthetic weather, UNVERIFIED archetypes.
1. **Plan safety PASS everywhere is hollow.** Red never appears in any run, not even for 10 hours of continuous heavy work at 47 C ("0/12 reached the model limit"). A check that cannot fail proves nothing. Either PHS 2023 really allows that (then the alert basis is wrong, because it would never warn) or the carried-state probe does not behave as assumed (Q2/Q4 in `scripts/diagnose_phs.py`).
2. **Acclimatised and not acclimatised give identical numbers** (A01=A02, A03=A04 ... in all scenarios). The flag may have no effect in the 2023 model, or is not reaching it (Q1).
3. **"Rest did not cool a strained worker" fires even on the 12-22 C cool day** (36 crew-hours). Rest was modelled at 100 W/m2, which is light work, not rest (equilibrium core temperature is above 36.8). v0.5.2 uses 58 W/m2 (seated rest, allowed by the 2023 limit of 56). The recovery rule still needs checking against Q3.
4. **The fresh-start allowable time hits the 480-minute cap in 38 to 39 % of probes** (A11): the "fraction used" ratio rests on that cap in over a third of hours.
5. `heatbank simulate --rest-area` did not exist (flag only on `run_v2`): fixed. The cooled-cabin file you sent was a copy of the forecast-only run, so it is not a result. Summaries are now also saved under a tagged name so runs do not overwrite each other.
Next: run `python scripts\diagnose_phs.py` and send `out/diagnose_phs.txt`; then rerun the three V2 variants.

---

# v0.5 real-library result (2026-11-05)
`integration_check.py` on your machine, pythermalcomfort 4.8.0: **7/7 PASS** (smoke test clean, library carries its sweat total so the tracker uses it directly, 8/8 V3 faults, pages boot). Result fields confirmed: `t_re, t_sk, t_cr, t_cr_eq, t_sk_t_cr_wg, d_lim_loss_50, d_lim_loss_95, d_lim_t_re, sweat_loss_g, sweat_rate_watt, evap_load_wm2_min`. One PHS call is about 0.3 to 1.6 ms, so a full V2 run takes seconds (B2 resolved). A12 resolved on this version (sweat carries). U5/U6 resolved for 4.8.0: pin `pythermalcomfort==4.8.0`. `d_lim_t_re` can equal the 480 cap when the limit is never reached (A11 stays relevant).
The one unit-test error (`test_grid`) was an old test calling the library the v3 way; fixed in v0.5.1. Next: run the real V2 (`heatbank simulate`, `heatbank simulate --forecast-only`) and read PLAN SAFETY, A9, A11.

---

# v0.5 hotfix (2026-11-05): first contact with the real library

Your `check_signatures.py` run (pythermalcomfort **4.8.0**, thermofeel 2.3.0) showed the v0.4 wrapper was wrong in ways the toy model could
not reveal. Fixed from the docstring you sent: `posture` must be text ("standing"); `met` is in **met units** (we keep W/m2 and convert, 58.15);
the default model is ISO 7933:**2023** (met limit 56 to 250 W/m2, not 100 to 450); the radiant limit is **0 < tr - tdb < 60**, not tr below 60
(this removes the Gulf "cliff" A19: tr is no longer gated, only air above 50 C or an excess above 60 C); carry-over has two more inputs
(`sweat_rate_watt`, `evap_load_wm2_min`); `round_output=False` is used when chaining; `limit_inputs=False` because our own gate decides.
NaN results now fail safe with a clear reason. **Still unknown until the next run:** the names of the result attributes (d_lim_t_re etc.).
The old A1 "massive silent Red" worry came true exactly as predicted: 20 model errors, all Red, and the smoke test caught it.

---

# Audit round 2 (v0.4.0, 2026-11-04): what changed, what is still open

Method: unpacked both zips, ran the 70 tests, ran every CLI path and the V2/V3/export flows end to end on the toy model, read every
module, probed suspicious behaviour, fixed what could be fixed **without the real library**, and added tests (99 now). A headless test
runs both web pages in a fake DOM (no browser here). **Still nothing has run against the real `pythermalcomfort`** (not installed, no
network). Every number from the toy model is plumbing, never a result.

## Do Parts 1, 2 and 3 work together?
Yes, on the toy model. `python scripts/integration_check.py --toy` runs the chain and prints PASS/FAIL per step: library import,
wrapper smoke test, weather -> tracker -> planner, V3 faults, pack export + supervisor aggregation, both pages booting with every control
exercised, and a compute-time projection. The pack's hourly levels equal a direct simulation for all 12 archetypes (test
`test_end_to_end_pack_is_consistent_with_the_simulation`), the site status is never below any listed zone, and the JavaScript fallback rule equals the
Python one over 128 cases. What this does NOT prove: that the wrapper's kwarg and attribute names match the real library, and that the
pages look right (layout, colour, touch targets need a real browser, `docs/DEMO_CHECKLIST.md`).
Integration defects found and fixed this round: (1) the toy model accepted `sweat_loss_g` as an input exactly like the wrapper passed it, so
the tests could not see a wrong name; (2) V3 always used the toy baseline even with the real library (`faults --real` now); (3) `heavyWindows`
printed `07:00-9:00` (caught by a new test); (4) the charter promised an automatic buddy notification that no code can send (A18).

## Status of every earlier finding

| ID | v0.4 status | What was done / what is left |
|---|---|---|
| A1 | **MITIGATED, root cause OPEN** | `sweat_loss_g` is no longer passed as an input (state INPUT and OUTPUT names are split). State kwargs the installed `phs()` does not accept are dropped, counted and reported by the smoke test instead of crashing everything to Red. The smoke test also runs inside `integration_check.py`. The real names stay open until you run `scripts/check_signatures.py` (it now writes one file for you to attach). |
| A2 | **MITIGATED** | Default radiant fallback is now `"solar"` (night: tr = tdb; unknown solar: the conservative constant). Still uncited, still a placeholder. New test documents the trade-off: with the constant every hour above 45 C air is gated, with solar only the sunniest. |
| A3 | FIXED (v0.3) | Look-ahead one hour. |
| A4 | MITIGATED | PLAN SAFETY line stays. With the rest-area check (A9) toy `hot_dry` no longer reaches Red under a perfect plan, because the plan says "no work" instead; the new `gulf_peak` scenario does fail, as it should. |
| A5, A6, A7 | FIXED (v0.3) | Unchanged. |
| A8 | **OPEN, critical path** | Needs your `check_signatures.py` output. |
| A9 | **FIXED in code, numbers OPEN** | Rest area is a parameter (`shade`, `fan`, `cooled_cabin`; `run_v2 --rest-area`). The tracker tests whether 30 min of rest lowers predicted rectal temperature; if not, the planner outputs **no work** and the phone says "move to a cooler rest area". Limit: a worker with no accumulated strain cannot be tested, so the first hour is planned as before. Whether real PHS recovers at 40 C+ in shade is unknown until the real run. |
| A10 | **FIXED in code, thresholds OPEN** | Every hourly row and the phone show a second line, "Body model (while resting)", from predicted rectal temperature (base 37.0, limit 38.0, recalled from ISO 7933, **U11 unverified**) using the same 50/75/100 % fractions. It never lowers the conditions level. |
| A11 | **INSTRUMENTED, OPEN** | V2 now prints how often the fresh-start allowable time hit the 480-minute cap (toy: about 35 %). The ratio understates strain when the cap binds (the unsafe direction). Decide after the real run; options: raise the probe length if the library allows it, or use rectal-temperature margin. |
| A12 | **MITIGATED** | The smoke test detects whether the library carries its water-loss total; the tracker sums segments itself when it does not (and when unknown, which can only overstate). `config.WATER_GUARD_G` (off by default) can force Red at a limit once the ISO 7933 value is confirmed (U10). |
| A13 | **FIXED** | New `gulf_peak` scenario (air to 47 C, strong sun). Its tr leaves the model range, so hours are Red by the validity gate with no work planned. |
| A14 | MITIGATED (v0.3) | Relabelled. Still needs a counterfactual definition, see `PILOT_PROTOCOL.md`. |
| A15 | **FIXED (optional)** | Phone has a local break log ("Back at work" / "Break started"). Working past the plan plus 5 min grace raises the shown level by one, never lowers it. Stored only in that browser, never sent. If nobody uses it, the limit stands: adherence is unobserved. |
| A16 | FIXED by design (v0.3) | |
| A17 | OPEN | `check_signatures.py` now lists any test files inside the installed package. |

## New findings this round

| ID | Finding | Status |
|---|---|---|
| A18 | **Escalation did not exist.** The plan (R3) and the challenge (clinical escalation, "emergency escalations" metric) need it, and the charter said an unanswered Red alerts a buddy. The prototype has no transport, by design (A5), so that sentence was false. | **PARTLY FIXED.** The Red screen has "Call the site medic" (number given at export: `--medic-tel`, never invented) and "Message my buddy" (number kept on the phone). The worker starts both. No automatic notification. Charter section 5 corrected. |
| A19 | **The validity gate is a cliff.** In the toy Gulf run 13:00 is Red by the gate (tr 60.5 C) and 14:00 is Green (tr 59.8 C): hotter, yet lower. Real PHS will probably say "almost no minutes" at 59 C, but nothing guarantees monotonic behaviour at the edge. | **OPEN, decide after the real run.** Candidate P2 rule: within 3 C of any range limit, raise one level. Not implemented because it is a design choice with no citation. |
| A20 | **Supervisor view gave no task timing** (R5 asks for breaks, rotation and task timing). | **FIXED.** Supervisor shows "Best hours for heavy tasks" = hours when every group is Green or Yellow. Presentation of model output, conservative (worst group). |
| A21 | **Scope.** The challenge title says "extreme heat and other climate-related occupational risks". HeatBank covers heat only. | **OPEN, state it.** Say so in the pitch; smoke, dust, UV, storms are future work, not claims. |
| A22 | **"Personalised prevention" is archetype-level.** The worker picks their own type on the phone (nothing leaves the device), but nothing learns from the person. | **OPEN, state it.** Individual or wearable signals are a documented future option, not built. |
| A23 | Hydration is a flag, health status and multi-day prior exposure are not modelled (acclimatisation is a yes/no input). | OPEN, in `LIMITATIONS.md`. |
| A24 | Unattended escalation (Red unanswered) cannot work without a transport that carries an identifier. | By design; a consented live mode would need its own governance review. |

## Bottlenecks, round 2

* **B1 Schedule.** 16 days left on 11-04. Everything real waits on one command: `python scripts/check_signatures.py`. It now saves `out/check_signatures_output.txt`, so you attach one file.
* **B2 Compute.** One full V2 run is about 19,900 PHS calls now (the Gulf scenario added a fourth day). `scripts/integration_check.py` times it on your machine and says whether to raise `STEP_MIN`. The stateless cache stays.
* **B3 People.** `docs/REVIEW_PACKET.md` is a ready-to-send packet for the three reviewers (Thai strings, first-aid wording, licence questions). Send it today.
* **B4 Scope cut order unchanged.** Never cut V3, the charter or the data declaration. Cut first: node, V4, third language, UTCI.

## Decisions I need from you (each has a safe default already in the code)
1. A10 thresholds: keep 37.0 to 38.0 as a proposal, or give me the source you want to cite.
2. A19: do you want the "raise one level near the model edge" rule?
3. Rest area for the demo: `shade` (honest default) or show a `cooled_cabin` comparison in the pitch.
4. Medic number for the demo (or leave it unset and say so).

---

# Original audit (v0.3.0, written 2026-11-04). Status column is as of v0.3; see the v0.4 block above for the current state.

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
