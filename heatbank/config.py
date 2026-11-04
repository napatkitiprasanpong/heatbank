"""HeatBank configuration. Everything here is a PROPOSED design parameter, not clinical guidance.

Plan refs: section 7 (validity limits, U5), principle P2 (fail safe), section 9 (data rules).
"""

# Model input validity limits. PROPOSED: quoted from the pythermalcomfort ISO 7933:2004 docstring
# (plan U5). Confirm the 2023-mode limits before submission. Outside range => no extrapolation.
VALID_RANGES = {
    "tdb_c": (15.0, 50.0),     # air temperature, C
    "tr_c": (0.0, 60.0),       # mean radiant temperature, C
    "v_ms": (0.0, 3.0),        # air speed, m/s
    "met_wm2": (100.0, 450.0), # metabolic rate, W/m2
    "clo": (0.1, 1.0),         # clothing insulation, clo
}
RH_RANGE = (0.0, 100.0)

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
TR_FALLBACK_MODE = "constant"          # "constant" | "solar"
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
REST_MET_WM2 = 100.0                   # rest modelled at the lowest valid met (real rest is lower: conservative)
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
