HeatBank: 3-Minute Pitch Video Storyboard

Nov 8, 2026 · @napat

## Overview

A 3:00 explainer in 11 scenes: 387 words of voice-over, about 129 words per minute, laid over your existing slides plus three short screen captures.

- Format: 16:9, English voice-over with English subtitles. Thai subtitles are optional (see Production tips).
- Structure: the problem (0:00 to 0:26), how HeatBank works (0:26 to 1:42), safety and honesty (1:42 to 2:33), then pilot and ask (2:33 to 3:00).
- Tone: calm and plain. Every result is called simulated and the open issue is shown, matching your honesty rule.
- Sources: your slide deck and project plan v1.0 only. No claim here goes beyond them.

## Storyboard at a glance

Eleven scenes fill 180 seconds, with the most time on how HeatBank works (26 s) and the four alert levels (22 s).

|  # | Time | Length (s) | Scene | Visual source  |
|  1 | 0:00 to 0:13 | 13 | The need | New motion graphic with the ILO figures  |
|  2 | 0:13 to 0:26 | 13 | The gap | New motion graphic, three icons  |
|  3 | 0:26 to 0:36 | 10 | Meet HeatBank | Title slide with the gauge  |
|  4 | 0:36 to 1:02 | 26 | How it works | Architecture slide, plus terminal capture  |
|  5 | 1:02 to 1:24 | 22 | Four levels, one action each | Four-levels slide  |
|  6 | 1:24 to 1:42 | 18 | Privacy by design | Captures of worker.html and supervisor.html  |
|  7 | 1:42 to 1:59 | 17 | Fail safe | Fail-safe banner, 8 of 8 card, 138 tests stat  |
|  8 | 1:59 to 2:19 | 20 | Simulated results | Warning-time chart slide  |
|  9 | 2:19 to 2:33 | 14 | What is still open | Success-measures slide, Red card  |
|  10 | 2:33 to 2:49 | 16 | Path to pilot | Path to pilot slide  |
|  11 | 2:49 to 3:00 | 11 | Close | Closing slide  |

## Scene by scene

### Scene 1 · The need · 0:00 to 0:13

- Visual: the deck's dark teal background. Three figures count up one at a time, timed to the voice.
- On-screen text: "2.2% of working hours lost to heat by 2030", then " = 80 million jobs", then "Construction: about 19% of those hours". Source line: "ILO (2019)".
- Voice-over: "The ILO projects that by 2030, heat will cost 2.2 percent of working hours, the equivalent of 80 million jobs. Construction carries about 19 percent of those hours."
- Subtitles: cues 1 to 4.

### Scene 2 · The gap · 0:13 to 0:26

- Visual: three flat icons appear with the phrases: a thermometer with one fixed line, a worker tagged with task, clothing and acclimatisation, and a phone with an eye crossed out.
- On-screen text: "General thresholds", "Task, clothing, acclimatisation", "Safety is not surveillance".
- Voice-over: "Supervisors usually only have general thresholds. But heat strain depends on the task, the clothing and acclimatisation. And tools that watch bodies can turn safety into surveillance."
- Subtitles: cues 5 to 8.

### Scene 3 · Meet HeatBank · 0:26 to 0:36

- Visual: the title slide. The gauge needle sweeps up and settles at 60%, Yellow. The wordmark lands first, then the tagline.
- On-screen text: "HeatBank", "A heat budget for every shift", and under the gauge "Illustrative example, not a result".
- Voice-over: "This is HeatBank. A heat budget for every shift. We plan safe exposure before the shift starts, like a budget you spend down."
- Subtitles: cues 9 to 12.

### Scene 4 · How it works · 0:36 to 1:02

- Visual: the architecture slide. Boxes 1 to 5 light up in order as the voice names them: Weather at 0:36, Heat index at 0:42, Strain model at 0:45, Planner at 0:52.
- Cut-away: 4 seconds of a real terminal run of heatbank plan --scenario hot_humid at about 0:52. Record the real output, do not mock it.
- On-screen text: "Forecast cached for offline use", "ISO 7933 Predicted Heat Strain", "Can only hold or reduce exposure".
- Voice-over: "HeatBank takes an hourly weather forecast, cached so it works offline. It calculates wet-bulb globe temperature. Then it runs the ISO 7933 Predicted Heat Strain model, minute by minute, for each simulated worker type. The planner turns that into safe minutes, work and rest cycles. And it can only hold or reduce exposure, never push past the model limit."
- Subtitles: cues 13 to 21.

### Scene 5 · Four levels, one action each · 1:02 to 1:24

- Visual: the four-levels slide. Cards slide in on their word: Green at 1:06, Yellow at 1:08, Orange at 1:11, Red at 1:14. A 0 to 100% bar fills at 1:19 as the voice says "share of the budget used".
- On-screen text: each card's action line from the slide, plus a constant small note: "Thresholds are proposed, not clinical guidance".
- Voice-over: "Workers see one of four levels, each with one action. Green: work normally. Yellow: drink and take a shade break. Orange: reduce intensity and cool down. Red: stop heavy work, and call the medic if there are symptoms. Each level is simply the share of the budget used."
- Subtitles: cues 22 to 30.

### Scene 6 · Privacy by design · 1:24 to 1:42

- Visual: split screen. Left, a capture of worker.html on a phone frame: pick a worker type, see one level and one action, toggle English to Thai. Right, a capture of supervisor.html showing crew counts by zone with no names.
- On-screen chips: "No accounts", "No upload", "Crew totals only". At 1:37 a charter card: "Charter: no discipline, pay or ranking".
- Voice-over: "Privacy is built into the architecture. Everything runs on the worker's phone, with no accounts and no upload. Supervisors see crew totals only, never names or readings. And a draft worker charter bans use for discipline, pay or ranking."
- Subtitles: cues 31 to 37.

### Scene 7 · Fail safe · 1:42 to 1:59

- Visual: the fail-safe banner from the architecture slide. A small level bar jumps from Yellow to Orange when a "STALE DATA" tag appears at 1:45, labelled "Illustrative". Then the "8 of 8" card at 1:51, then the "138 automated tests" stat at 1:55.
- On-screen text: "Stale, offline or out-of-range data can only raise the level", "8 of 8 fault-injection tests pass", "138 automated tests".
- Voice-over: "When things go wrong, HeatBank fails safe. Stale, offline or out-of-range data can only raise the alert level, never lower it. We ran eight fault-injection tests, and all eight passed. The code ships with 138 automated tests."
- Subtitles: cues 38 to 44.

### Scene 8 · Simulated results · 1:59 to 2:19

- Visual: the warning-time chart slide. Bars grow by scenario: Gulf peak, Hot dry, Hot humid, with the median bar in orange (60, 70, 70 minutes). A "SIMULATED" stamp stays top right for the whole scene.
- On-screen text: "Median warning: 60 to 70 minutes", and the slide's footer "Synthetic weather and globe temperature; not a validated lead time".
- Voice-over: "In simulation, across twelve worker types on three hot days, the median warning, from first Orange to the model limit, was 60 to 70 minutes of continuous work. These numbers are simulated, from synthetic weather, and are not a validated lead time."
- Subtitles: cues 45 to 51.

### Scene 9 · What is still open · 2:19 to 2:33

- Visual: the Red card from the success-measures slide fills the frame. "21 to 34%" counts up. A second line fades in: the defect audit log.
- On-screen text: "Crew-time at Red under shade-only rest, three hot simulated days", "Open issue, shown openly".
- Voice-over: "We also show what is unsolved. With shade-only rest, simulated crews still spend 21 to 34 percent of their time at Red on hot days. Every defect we found is logged."
- Subtitles: cues 52 to 56.

### Scene 10 · Path to pilot · 2:33 to 2:49

- Visual: the path-to-pilot slide. The Prepare card highlights at 2:33, then the Pilot card at 2:37. At 2:45 a line fades in under the cards.
- On-screen text: "Timeline figures are assumptions, not commitments", and at 2:45 "Decision support, not a medical device".
- Voice-over: "Next come clinician, Thai-language and licence reviews, then a two-to-four-week pilot at one site with two to four crews, compared with the site's current threshold rule. HeatBank is decision support, not a medical device."
- Subtitles: cues 57 to 63.

### Scene 11 · Close · 2:49 to 3:00

- Visual: the closing slide. Its three chips appear one by one on a slow zoom out.
- On-screen text: "Plan the heat budget before the shift starts", "Protect before productivity", "Fail safe, never lower", "Data stays on the device".
- Voice-over: "HeatBank. Plan the heat budget before the shift starts. We are looking for a pilot partner and expert reviews."
- Subtitles: cues 64 to 67.

## Full voice-over script

387 words, read at about 129 words per minute with a one-second pause between scenes. Each paragraph is one scene.

The ILO projects that by 2030, heat will cost 2.2 percent of working hours, the equivalent of 80 million jobs. Construction carries about 19 percent of those hours.

Supervisors usually only have general thresholds. But heat strain depends on the task, the clothing and acclimatisation. And tools that watch bodies can turn safety into surveillance.

This is HeatBank. A heat budget for every shift. We plan safe exposure before the shift starts, like a budget you spend down.

HeatBank takes an hourly weather forecast, cached so it works offline. It calculates wet-bulb globe temperature. Then it runs the ISO 7933 Predicted Heat Strain model, minute by minute, for each simulated worker type. The planner turns that into safe minutes, work and rest cycles. And it can only hold or reduce exposure, never push past the model limit.

Workers see one of four levels, each with one action. Green: work normally. Yellow: drink and take a shade break. Orange: reduce intensity and cool down. Red: stop heavy work, and call the medic if there are symptoms. Each level is simply the share of the budget used.

Privacy is built into the architecture. Everything runs on the worker's phone, with no accounts and no upload. Supervisors see crew totals only, never names or readings. And a draft worker charter bans use for discipline, pay or ranking.

When things go wrong, HeatBank fails safe. Stale, offline or out-of-range data can only raise the alert level, never lower it. We ran eight fault-injection tests, and all eight passed. The code ships with 138 automated tests.

In simulation, across twelve worker types on three hot days, the median warning, from first Orange to the model limit, was 60 to 70 minutes of continuous work. These numbers are simulated, from synthetic weather, and are not a validated lead time.

We also show what is unsolved. With shade-only rest, simulated crews still spend 21 to 34 percent of their time at Red on hot days. Every defect we found is logged.

Next come clinician, Thai-language and licence reviews, then a two-to-four-week pilot at one site with two to four crews, compared with the site's current threshold rule. HeatBank is decision support, not a medical device.

HeatBank. Plan the heat budget before the shift starts. We are looking for a pilot partner and expert reviews.

## Subtitle file (67 cues)

1 | 00:00:00,500 --> 00:00:03,000 | The ILO projects that by 2030,
2 | 00:00:03,000 --> 00:00:06,000 | heat will cost 2.2 percent of working hours,
3 | 00:00:06,000 --> 00:00:08,500 | the equivalent of 80 million jobs.
4 | 00:00:09,000 --> 00:00:12,500 | Construction carries about 19 percent of those hours.
5 | 00:00:13,500 --> 00:00:16,500 | Supervisors usually only have general thresholds.
6 | 00:00:16,500 --> 00:00:19,500 | But heat strain depends on the task,
7 | 00:00:19,500 --> 00:00:21,500 | the clothing and acclimatisation.
8 | 00:00:22,000 --> 00:00:25,500 | And tools that watch bodies can turn safety into surveillance.
9 | 00:00:26,500 --> 00:00:28,000 | This is HeatBank.
10 | 00:00:28,300 --> 00:00:30,500 | A heat budget for every shift.
11 | 00:00:31,000 --> 00:00:34,000 | We plan safe exposure before the shift starts,
12 | 00:00:34,000 --> 00:00:35,800 | like a budget you spend down.
13 | 00:00:36,500 --> 00:00:39,500 | HeatBank takes an hourly weather forecast,
14 | 00:00:39,500 --> 00:00:41,500 | cached so it works offline.
15 | 00:00:42,000 --> 00:00:44,500 | It calculates wet-bulb globe temperature.
16 | 00:00:45,000 --> 00:00:48,500 | Then it runs the ISO 7933 Predicted Heat Strain model,
17 | 00:00:48,500 --> 00:00:51,500 | minute by minute, for each simulated worker type.
18 | 00:00:52,000 --> 00:00:54,500 | The planner turns that into safe minutes,
19 | 00:00:54,500 --> 00:00:56,000 | work and rest cycles.
20 | 00:00:56,500 --> 00:00:59,000 | And it can only hold or reduce exposure,
21 | 00:00:59,000 --> 00:01:01,500 | never push past the model limit.
22 | 00:01:02,500 --> 00:01:04,500 | Workers see one of four levels,
23 | 00:01:04,500 --> 00:01:06,000 | each with one action.
24 | 00:01:06,500 --> 00:01:08,000 | Green: work normally.
25 | 00:01:08,300 --> 00:01:10,500 | Yellow: drink and take a shade break.
26 | 00:01:11,000 --> 00:01:13,500 | Orange: reduce intensity and cool down.
27 | 00:01:14,000 --> 00:01:17,000 | Red: stop heavy work, and call the medic
28 | 00:01:17,000 --> 00:01:18,500 | if there are symptoms.
29 | 00:01:19,000 --> 00:01:21,000 | Each level is simply the share
30 | 00:01:21,000 --> 00:01:23,000 | of the budget used.
31 | 00:01:24,500 --> 00:01:27,500 | Privacy is built into the architecture.
32 | 00:01:28,000 --> 00:01:30,500 | Everything runs on the worker's phone,
33 | 00:01:30,500 --> 00:01:32,500 | with no accounts and no upload.
34 | 00:01:33,000 --> 00:01:35,000 | Supervisors see crew totals only,
35 | 00:01:35,000 --> 00:01:36,500 | never names or readings.
36 | 00:01:37,000 --> 00:01:39,000 | And a draft worker charter bans use
37 | 00:01:39,000 --> 00:01:41,500 | for discipline, pay or ranking.
38 | 00:01:42,500 --> 00:01:45,000 | When things go wrong, HeatBank fails safe.
39 | 00:01:45,300 --> 00:01:47,500 | Stale, offline or out-of-range data
40 | 00:01:47,500 --> 00:01:49,500 | can only raise the alert level,
41 | 00:01:49,500 --> 00:01:50,500 | never lower it.
42 | 00:01:51,000 --> 00:01:53,000 | We ran eight fault-injection tests,
43 | 00:01:53,000 --> 00:01:54,500 | and all eight passed.
44 | 00:01:55,000 --> 00:01:58,500 | The code ships with 138 automated tests.
45 | 00:01:59,500 --> 00:02:02,000 | In simulation, across twelve worker types
46 | 00:02:02,000 --> 00:02:04,500 | on three hot days, the median warning,
47 | 00:02:04,500 --> 00:02:07,000 | from first Orange to the model limit,
48 | 00:02:07,300 --> 00:02:10,500 | was 60 to 70 minutes of continuous work.
49 | 00:02:11,500 --> 00:02:13,500 | These numbers are simulated,
50 | 00:02:13,500 --> 00:02:15,000 | from synthetic weather,
51 | 00:02:15,000 --> 00:02:18,500 | and are not a validated lead time.
52 | 00:02:19,500 --> 00:02:21,500 | We also show what is unsolved.
53 | 00:02:22,000 --> 00:02:24,500 | With shade-only rest, simulated crews
54 | 00:02:24,500 --> 00:02:27,000 | still spend 21 to 34 percent
55 | 00:02:27,000 --> 00:02:29,500 | of their time at Red on hot days.
56 | 00:02:30,000 --> 00:02:32,500 | Every defect we found is logged.
57 | 00:02:33,500 --> 00:02:36,000 | Next come clinician, Thai-language
58 | 00:02:36,000 --> 00:02:37,500 | and licence reviews,
59 | 00:02:37,500 --> 00:02:40,500 | then a two-to-four-week pilot at one site
60 | 00:02:40,500 --> 00:02:42,000 | with two to four crews,
61 | 00:02:42,000 --> 00:02:45,000 | compared with the site's current threshold rule.
62 | 00:02:45,300 --> 00:02:47,000 | HeatBank is decision support,
63 | 00:02:47,000 --> 00:02:48,500 | not a medical device.
64 | 00:02:49,500 --> 00:02:50,500 | HeatBank.
65 | 00:02:51,000 --> 00:02:54:500 | Plan the heat budget before the shift starts.
66 | 00:02:55:500 --> 00:02:58:000 | We are looking for a pilot partner
67 | 00:02:58:000 --> 00:02:59:500 | and expert reviews.

## Accuracy checklist

Every number in the voice-over comes from the submission deck or project plan; nothing was added.

## Production tips

- Keep the deck footer "not a medical device · simulated results are labelled as simulated" on every frame.
- Keep the "SIMULATED" stamp on the whole of scene 8, and the "illustrative" label on the scene 3 gauge and the scene 7 stale-data demo.
- Re-time the subtitles to the recorded voice. The cues assume about 129 words per minute.