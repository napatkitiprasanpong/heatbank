# Review packet (send this today; three reviewers, each needs about 30 minutes)

Context for every reviewer: HeatBank is a competition prototype that plans work/rest in hot weather. It is **not a medical device**
and nothing here has been used with real workers. Please mark anything you would change. Deadline for replies: 2026-11-12.

## 1. Thai reader (native speaker, ideally someone who has worked on a site)
Open `dashboard/index.html`, switch to Thai, and read every screen at several hours and in each connection state. Or read the table below.
Questions: Is each sentence natural and unambiguous to a site worker? Is any word too formal or misleading? Does Red clearly mean stop?
Are the action sentences short enough to read at a glance?
Source of truth: `heatbank/i18n/strings.py` (keys under `_TH`). Draft written by Claude; **not reviewed**. Send back corrected lines by key.

## 2. Occupational health or first-aid professional
Review only these items:
* Red card text (`red_card_body` in EN and TH): "Call the medic or emergency number now. Move the person to shade or a cool place. Cool the body with water and air. Do not leave them alone. Do this if they are confused, faint, very unwell, or have stopped sweating."
* The four one-line actions (Green/Yellow/Orange/Red) in `alerts/engine.py`.
* Proposed thresholds: Yellow at 50 %, Orange at 75 %, Red at 100 % of the PHS allowable time; body-state mapping from 37.0 to 38.0 C predicted rectal temperature; 30 min cap on work per hour in degraded mode. Are these sensible as *starting* values, and what source would you cite?
* Is "rest in shade" an acceptable assumption for a worker already at Orange in 40 C air? (Audit A9.)

## 3. Licence reader (anyone careful; a university librarian or legal clinic is ideal)
Please read the actual terms and tell us, in plain words, for a **prize-winning competition prototype that might later pilot commercially**:
* Open-Meteo free tier: is a competition entry with prize money "non-commercial"? Is written permission or a paid plan needed? (U2)
* NOAA GFS, DWD ICON open data, Copernicus ERA5: may we use them, with what attribution, and for commercial use? (U3)
* HTT and PROSPIE datasets: licence at the source, and whether they contain environment and workload columns. (U4)
* pythermalcomfort (MIT) and thermofeel (Apache-2.0): confirm the notices we must keep. (K1, K2)
Not legal advice; we only need a careful reading we can cite in `DATA_SOURCES.md`.

## 4. Optional: the owner reads the official FAQ and rules (U1)
Especially: what data may we use, who owns IP, required documentation format, video length, whether prize eligibility has conditions.
