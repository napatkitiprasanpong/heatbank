# Requirements trace (v0.4.0, 2026-11-04)

Three checks in one place: (A) the plan's requirements R1-R6, (B) the official challenge text (problem statement, six desired outcomes,
six judging criteria), (C) the plan's hard constraints. Status words: **MET** (built and tested), **PARTIAL** (built, with a stated gap),
**NOT BUILT**, **BLOCKED** (needs something only you can supply). "Tested" means toy model or fakes unless it says real.
Honest headline: the *architecture and rules* are built and tested; the *physiology results* do not exist yet because the real model has not run.

## A. Plan requirements R1-R6

| ID | Plan requirement | Status | Evidence | Gap |
|---|---|---|---|---|
| R1 | Dynamic heat-risk: environment + workload + shift context (+ optional consented signals), individual or crew | **PARTIAL** | PHS per archetype from weather, met, clo, posture, acclimatisation, drinking access; carry-over through the shift (`sim/tracker.py`); crew view from roster | Needs real PHS run (BLOCKED on `check_signatures.py`). Consented worker signals NOT BUILT (plan says documented future option). Hydration is a flag; health status and multi-day exposure not modelled (A23). |
| R2 | Graded multilingual warnings, simple levels, one safe action each (hydrate, rest, cool, reduce intensity, shift change, clinical escalation) | **PARTIAL** | 4 levels with shape + word + pictogram + text (`alerts/engine.py`, `dashboard/`); EN + TH; Red card with first-aid text and Get help (call medic, message buddy) | Thai is a **draft**, needs a human (REVIEW_PACKET). Third language not chosen. First-aid wording needs clinician review. "Shift change" is shown as heavy-task windows and rotation, not as a separate action. Escalation is worker-started only (A18, A24). |
| R3 | Worker-first governance: consent, minimisation, strict access, no disciplinary use | **PARTIAL** | No accounts, no identifiers, no upload channel (A5); pooled groups with safety override (A6); break log and buddy number stay on the phone; charter draft; tests check the pack carries no identifier fields | No consent flow because nothing personal is collected (a consent screen is needed before any future signal). Charter is a draft: legal, occupational-health and worker-representative review not done. Use restriction is policy, not enforceable by code. |
| R4 | Field-ready: heat, connectivity, battery, dust, PPE; safe fallback when sensors or networks fail | **PARTIAL** | Offline-first static pages; stale/offline/no-forecast rules in Python and JS with a parity test; V3 fault injection 8/8 (toy baseline; `faults --real` for real); PPE as clo in archetypes; validity gate; rest-area check | **No field test and no hardware.** Connectivity and heat are simulated. Dust: not addressed. Battery: only a sensor-node rule exists, no phone battery behaviour. Node firmware not built (node software only). |
| R5 | Supervisor decision support: crew/site views for breaks, rotation, task timing, no individual clinical detail | **MET (in the prototype)** | Supervisor page: site status, zone table, first break, rotation, best hours for heavy tasks (new, A20), pooled small groups | Built from the roster plan, not from what people did (A5 trade-off). Not shown to any real supervisor. |
| R6 | Report lead time, false-alarm rate, adherence, incidents, escalations, compliance, lost work time | **PARTIAL** | V2 reports simulated lead time, plan safety, share of time at levels, simulated adherence; `PILOT_PROTOCOL.md` defines all seven measures for a real pilot | No real measurements exist. "False-alarm rate" in V2 is a model self-consistency number and is labelled so (A14). |

## B. Official challenge text

### Desired outcomes (the same six, restated against the build)
| Challenge outcome | Status | Short answer |
|---|---|---|
| Dynamic heat-risk assessment | **PARTIAL** | Yes for environment, workload, PPE, acclimatisation, shift accumulation. No wearable or physiological signals (optional in the text). Archetype-level, not individual (A22). |
| Clear, graded warnings, multilingual | **PARTIAL** | Yes, 4 levels, one action each, EN + draft TH. Needs human review and a third language if you want one. |
| Worker-first governance | **PARTIAL** | Strong by architecture; the policy documents are drafts. |
| Field-ready with safe fallback | **PARTIAL** | Fallback logic is built and tested; field demonstration is not (no hardware, no dust/battery work). |
| Supervisor decision support without clinical detail | **MET** | See R5. |
| Safety and productivity measures | **PARTIAL** | Defined (`PILOT_PROTOCOL.md`) and simulated; not measured. Do not claim real numbers. |

### Problem statement points that are easy to miss
| Statement | Status | Note |
|---|---|---|
| "extreme heat and **other climate-related** occupational risks" | **NOT BUILT** | Heat only (A21). Say so plainly. |
| Risk depends on workload, clothing/PPE, acclimatisation, **hydration, health status, prior exposure** | **PARTIAL** | First three yes; hydration is a flag; health status no; prior exposure only within the shift. |
| "Heat strain can develop quietly and deteriorate quickly" | **PARTIAL** | Continuous tracking within the shift and look-ahead; no real-time body signal. |
| Supervisors "often have only general thresholds" | **MET (design)** | Group-specific levels instead of one threshold. |
| "Poorly calibrated alerts can be ignored" | **PARTIAL** | Alert fractions are proposals (U7); A10 second reading and A11 diagnostic exist to reduce false Reds; calibration needs real data or literature. |
| "Over-collection can become surveillance" | **MET** | Nothing personal collected. |
| "Individual risk data could be misused in employment decisions" | **MET (by architecture)** | There is no individual risk data to misuse; charter states the rule. |
| "Works in realistic field conditions" | **NOT BUILT** | Simulated only. |

### Judging criteria
| Criterion | Where you stand | Biggest weakness | Fix |
|---|---|---|---|
| Health impact and clinical relevance | ISO 7933 PHS is a recognised standard model; levels map to actions | Nothing validated; no clinician has seen it; thresholds are proposals | Run real PHS; get one occupational-health reviewer; state limits (honesty rule) |
| Technical depth and architecture | Strongest area: model chain, carry-over, planner look-ahead, fail-safe, 99 tests, headless page test | Real model not yet connected | `check_signatures.py` |
| Working solution and demo quality | Pages work offline; demo script exists | Everything on screen is toy until the real run | Real run, then record (`DEMO_CHECKLIST.md`) |
| Responsible AI, safety, data governance | Very strong: P1/P2 enforced and tested, no personal data, pooled groups, data declaration, charter, honesty labels | Charter/Thai/first-aid unreviewed | REVIEW_PACKET |
| Scalability and deployment readiness | Static, offline, no server, cheap to deploy | Weather licence unresolved (U2/U3); a server-less design has no live crew data by choice | Resolve source; say the trade-off |
| Commercial viability and path to pilot | Pilot protocol drafted | **No commercial section exists.** Do not invent market numbers. | You write who pays and why (questions in `PILOT_PROTOCOL.md`, section 4) |

## C. Hard constraints from the plan

| Constraint | Status |
|---|---|
| Organisers supply no data; only data we may use; declare every source | **MET in code** (`DATA_SOURCES.md`, `.meta.json` per output). U1: you still must read the official FAQ. |
| No personal data | **MET** |
| Protection before productivity (P1) | **MET in code**, with tests; whether *real* plans are safe is the PLAN SAFETY line from the real run |
| Fail safe (P2) | **MET**, including the new break-log and body-state rules (they only raise or add) |
| Not a medical device; honest claims; simulated is labelled | **MET** |
| No code copied from repos without licence; avoid ECTemp | **MET** (no K3/K4 code used) |
| Open-Meteo off until licence resolved (U2) | **MET** (opt-in flag) |

## What you must do for the claims above to become true
1. `python scripts/check_signatures.py` and attach `out/check_signatures_output.txt`; then `python scripts/integration_check.py` and attach `out/integration_check.txt`.
2. Read the official rules and FAQ (U1) and decide the weather source (U2/U3) before registration closes 2026-11-10.
3. Send `docs/REVIEW_PACKET.md` to the Thai reviewer, an occupational-health reviewer and whoever reads licences.
4. Write the commercial paragraph yourself (who pays, who runs the pilot).
