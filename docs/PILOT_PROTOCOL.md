# Pilot protocol and path to pilot (DRAFT, v0.4)

Nothing here has been run with real workers. It exists so the submission can say exactly what would be measured, how, and without
individual surveillance. Everything is collected as **crew-shift counts**, never per named person.

## 1. Measures (challenge outcome 6)
| Measure | Definition | Collected how | Privacy |
|---|---|---|---|
| Alert lead time | Minutes between the first Orange for a crew group and the first reported heat-illness symptom or forced stop in that group (or end of shift if none) | Shift log by the supervisor: time of first Orange (from the pack), time of any stop | Group level |
| False-alarm rate (counterfactual) | Share of Orange/Red crew-hours in which crews that ignored the alert and kept working had no symptom, stop or near-miss report | Same log plus an anonymous end-of-shift tick box per crew | Group level; never judge one worker |
| Adherence | Share of planned break minutes taken | Supervisor tally per crew-shift, or the optional on-phone break log shown as a crew total only if workers agree | Local by default |
| Symptoms / incidents | Count of heat-related symptoms reported, per crew-shift | Existing site incident process | Counts only |
| Emergency escalations | Count of medic calls and transfers | Site medic log | Counts only |
| Compliance | Share of crew-shifts that followed the plan's work/rest split within 10 minutes | Supervisor tally | Group level |
| Lost work time | Minutes of planned work not done because of the plan, versus minutes lost to heat illness | Site records | Group level |

Never reported: any individual's data, any ranking, any use for pay or discipline (charter section 3).

## 2. Design (suggested)
* 2 to 4 weeks, one site, 2 to 4 crews, hot season. Before/after or crew-by-crew staggered start; decide with an occupational-health adviser.
* Agree with worker representatives first; workers can stop any time without penalty.
* Compare against the site's existing rule (fixed WBGT thresholds), not against nothing.
* Pre-register the measures above so results cannot be chosen afterwards.

## 3. Safety stops
Stop the pilot for a crew if the plan ever allows more exposure than the site's existing rule (it should not: P1), if a symptom is
reported during a Green level that the team cannot explain, or if any worker asks.

## 4. Path to pilot and commercial viability: questions for the owner (not answered here on purpose)
I cannot invent market sizes or legal facts. Write these yourself, with sources:
1. Who pays for heat safety today at the sites you target (contractor, owner, insurer, regulator)? What rule or regulation applies where?
2. Who would host the pilot (a contractor, a university hospital partner, a labour-health body), and have you spoken to them?
3. What does HeatBank cost to run? (Static pages and a nightly forecast job: say what you will actually host.)
4. Weather data: which licensed source will a paid deployment use (U2/U3)?
5. Regulatory position: "decision support, not a medical device" needs checking with someone qualified before any claim.
6. What is in the readiness assessment the challenge mentions, and what would you ask them for?
