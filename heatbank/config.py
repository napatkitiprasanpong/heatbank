"""HeatBank configuration. Everything here is a PROPOSED design parameter, not clinical guidance.

Plan refs: section 7 (validity limits, U5), principle P2 (fail safe), section 9 (data rules).
"""

# Model input validity limits. PROPOSED: quoted from the pythermalcomfort ISO 7933:2004 docstring
# (plan U5). Confirm the 2023-mode limits before submission. Outside range => no extrapolation.
VALID_RANGES = {
    "tdb_c": (15.0, 50.0),     # air temperature, C
    "tr_c": (-1e9, 1e9),       # (unused: v0.5 gates on tr - tdb, below)
    "tr_minus_tdb_c": (0.0, 60.0),   # from the 4.8.0 docstring: 0 < (tr - tdb) < 60 (7933 limits)
    "v_ms": (0.0, 3.0),        # air speed, m/s
    "met_wm2": (56.0, 250.0),  # metabolic rate, W/m2: 0.96 to 4.3 met in the 2023 standard (the 2004 standard allowed 100 to 450)
    "clo": (0.1, 1.0),         # clothing insulation, clo
}
RH_RANGE = (0.0, 100.0)

# v0.5.4 (bug fix, P2): physical plausibility. Real weather files use fill values such as -999 for missing data (NASA POWER does).
# Before this check, tdb = -999 was treated as a very cold hour (clamped up to 15 C by CLAMP_COOL_UP) and came out GREEN with a 480-minute
# allowance, and solar = -999 was read as night (tr = tdb). Anything outside these ranges is a sensor/data fault, never weather:
# air temperature => INVALID (fail-safe Red); globe temperature or solar radiation => treated as UNKNOWN (conservative fallback).
PLAUSIBLE = {
    "tdb_c": (-60.0, 65.0),
    "tg_c": (-60.0, 100.0),
    "solar_wm2": (-5.0, 1500.0),    # small negative values are sensor noise at night; they are floored at 0 by the caller
}

# PHS run length used to read the maximum allowable exposure time (minutes). PROPOSED.
PHS_DURATION_MIN = 480

# Forecast older than this is "stale" and must raise the alert level in Part 2 (P2). PROPOSED.
MAX_FORECAST_AGE_MIN = 180

# Air speed at the worker from forecast wind. Identity for now; a height/shelter correction needs
# a cited source before it is added (never silently clip: clipping changes the risk).
def air_speed_from_wind(wind_ms: float) -> float:
    return wind_ms

# Mean radiant temperature when no globe temperature exists. PLACEHOLDER, conservative-ish, must be
# replaced by a documented method (thermofeel MRT or own node, U6). Always reported in the output.
TR_FALLBACK_OFFSET_C = 15.0
# Audit A2: the constant offset is wrong at night (no sun) and too small in strong sun. "solar" mode scales the offset by
# forecast shortwave radiation. DEFAULT STAYS "constant" until the owner decides; neither number has a citation yet.
TR_FALLBACK_MODE = "solar"             # "constant" | "solar". v0.4: default is "solar" (night tr = tdb). Still uncited, see AUDIT A2
TR_SOLAR_GAIN_C = 15.0                 # PLACEHOLDER: offset at 1000 W/m2 in "solar" mode (same as the old constant at full sun)

# Synthetic-scenario assumption only: globe temp = air temp + k * solar/1000. Labelled synthetic.
SYNTH_GLOBE_RISE_AT_1000WM2_C = 5.0   # was 12.0 in Part 1: pushed tr past the 60 C model limit (see README)

# Open-Meteo free tier is non-commercial only (plan D1/U2): it must be switched on explicitly.
OPEN_METEO_REQUIRES_OPT_IN = True

# --- Part 1 fix: cool-side handling (decision, revertible) ---------------------------------------
# Below the model's lower tdb/tr bound we do NOT skip the hour (that left safe_minutes=None). We evaluate at the
# bound instead: raising tdb/tr to the bound can only make the estimate more cautious (P2), and it is not
# extrapolation. Set False to get the old BELOW_RANGE/None behaviour.
CLAMP_COOL_UP = True

# --- Part 2: planner, alerts, fallback, simulation (ALL PROPOSED, configurable, not clinical guidance) --
ALERT_FRACTIONS = (0.50, 0.75, 1.00)   # Yellow, Orange, Red thresholds on fraction of allowable exposure used (plan s.7, U7)
PLAN_WORK_FRACTION = 0.50              # planner works at most this fraction of the remaining allowable time per hour
PLAN_ROUND_MIN = 5                     # planned work blocks are rounded DOWN to this many minutes
DEGRADED_WORK_CAP_MIN = 30             # max work minutes per hour while in degraded mode (conservative preset)
REST_MET_WM2 = 58.0                    # v0.5.2: seated rest = 1 met (58 W/m2). The 2023 standard allows >= 56 W/m2; 100 W/m2 was the 2004 floor and is light WORK, not rest
STEP_MIN = 10                          # simulation / tracker step, minutes
SHIFT_HOURS = (7, 17)                  # simulated shift 07:00-17:00
FROZEN_READINGS = 6                    # identical consecutive node readings => frozen sensor
SPIKE_C = 8.0                          # one-reading jump above this => spike fault
LOW_BATTERY_PCT = 20.0

# --- Part 3 (audit fixes) ---------------------------------------------------------------------------
PLAN_LOOKAHEAD_H = 1                   # planner sizes work against the worse of this hour and the next N hours (audit A3). 0 = old behaviour
DASH_MIN_GROUP_K = 5                   # supervisor view: crew groups smaller than k are pooled, never shown alone (plan C8, PROPOSED)
EXPORT_STALE_RAISE = 1                 # levels added when a cached pack is older than MAX_FORECAST_AGE_MIN (mirrors fallback.evaluate)
EXPORT_STALE_MIN_LEVEL = 2             # ...and the floor (Orange)
SITE_BIAS_MAX_C = 6.0                  # site-node bias correction is clipped to +/- this (PROPOSED)
SITE_BIAS_MIN_SAMPLES = 6              # need this many paired readings before any correction is applied
SITE_BIAS_ALLOW_COOLING = False        # P2: a correction that would LOWER the estimated heat is ignored unless this is True

# --- Part 4 (audit round 2). ALL PROPOSED, none is clinical guidance. -------------------------------------------------
# A9: where do people rest? PHS decides whether that place actually cools them. Each preset overrides the rest-segment inputs;
# None keeps the outdoor value. tr is set to tdb for shade (no sun). Cabin values are placeholders to be justified.
REST_AREA = "shade"
REST_AREAS = {
    "shade":        dict(tdb=None, tr="tdb", rh=None, v=None, v_min=None),
    "fan":          dict(tdb=None, tr="tdb", rh=None, v=None, v_min=1.5),
    "cooled_cabin": dict(tdb=26.0, tr=26.0, rh=50.0, v=0.2, v_min=None),
}
REST_RECOVERY_MIN = 30          # minutes of rest simulated to test whether the rest area lowers predicted rectal temperature
REST_RECOVERY_EPS_C = 0.05      # the drop must be at least this to count as recovery
STRAINED_ABOVE_C = 0.40         # v0.5.3: "strained" = predicted t_re this far above STATE_T_RE_BASE_C (0.10 sat on the seated-rest asymptote of about 37.1 C: false 'no cooling')
# A10: second reading, body state. Maps predicted rectal temperature to a level with the SAME fractions as ALERT_FRACTIONS.
# Never lowers the conditions level; it is shown next to it. 38.0 is recalled from ISO 7933 and must be confirmed (U11).
STATE_T_RE_BASE_C = 37.0
STATE_T_RE_LIMIT_C = 38.0
# A12: optional cumulative sweat-loss guard (g). None = off. ISO 7933 water-loss limits are recalled as 5 % (95th percentile) and
# 7.5 % (50th) of body mass; confirm before use (U10). When set, reaching it forces fraction used = 1.0 (Red).
WATER_GUARD_G = None
# A15: phone-side break log. Worked minutes this hour beyond the plan (plus grace) RAISE the shown level by one. Local only.
ADHERENCE_GRACE_MIN = 5

# R2/R3 escalation (audit A18): the prototype has NO automatic notification (it would need a transport, which carries an identifier,
# see A5). Instead the Red screen offers one-tap call/message that the WORKER starts. The site medic number is supplied at export
# time (--medic-tel) and is never invented here.
MEDIC_TEL = None

# --- v0.5: facts read from the installed pythermalcomfort 4.8.0 docstring (user's machine, 2026-11-05) -------------------
PHS_MODEL = "7933-2023"        # library default; "7933-2004" is the other option
W_PER_MET = 58.15              # the library takes met in met units; we keep W/m2 everywhere else
PHS_LIMIT_INPUTS = False       # we gate inputs ourselves (validity.py) and never extrapolate, so the library's NaN-on-limit is switched off

# --- v0.5.3: facts measured with scripts/diagnose_phs.py on pythermalcomfort 4.8.0 (2026-11-05) --------------------------
# d_lim_t_re / d_lim_loss_* return 1 (not 0) when the limit is ALREADY exceeded at the start of the run. Treat <= this as exceeded (0 min).
LIMIT_EXCEEDED_MIN = 1.0
# Predicted t_re at or above this means the ISO 7933 rectal-temperature limit is passed (the library's d_lim_t_re collapses to 1 right after 38.0).
# Same number as STATE_T_RE_LIMIT_C; belt and braces so Red cannot depend on the library's minute counting.
