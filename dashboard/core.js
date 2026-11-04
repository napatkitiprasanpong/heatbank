/* HeatBank front-end logic. Pure functions, no DOM, no network. Mirrors heatbank/fallback/fallback.py (P2: only ever RAISES).
   Tested for parity against the Python rules by tests/test_part3.py (needs node). */
(function (root) {
  "use strict";
  var RED = 3;

  // Same precedence as fallback.evaluate: no forecast -> Red; stale -> raise +1 and floor Orange; offline with fresh cache -> banner only.
  function degrade(level, st, cfg) {
    var minLevel = 0, raiseBy = 0, banner = null;
    if (!st.haveForecast || st.ageMin === null || st.ageMin === undefined || isNaN(st.ageMin)) {
      minLevel = RED; banner = "banner_no_data";
    } else if (st.ageMin > cfg.max_age_min) {
      minLevel = cfg.stale_min_level; raiseBy = cfg.stale_raise; banner = "banner_stale";
    } else if (st.offline) {
      banner = "banner_offline";
    }
    return { level: Math.min(RED, Math.max(level + raiseBy, minLevel)), banner: banner };
  }

  // Index of the shift hour to show, or -1 when the pack does not cover it (treated as "no forecast" -> Red).
  function hourIndex(pack, nowMs, demo, demoIdx) {
    if (demo) return demoIdx >= 0 && demoIdx < pack.hours.length ? demoIdx : -1;
    var d = new Date(nowMs);
    var pad = function (n) { return (n < 10 ? "0" : "") + n; };
    var today = d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
    if (pack.provenance.weather_date !== today) return -1;
    return pack.hours.indexOf(pad(d.getHours()));
  }

  function ageMinutes(pack, nowMs) {
    var t = Date.parse(pack.generated_at);
    return isNaN(t) ? null : Math.max(0, (nowMs - t) / 60000);
  }

  // First later hour whose planned level differs from now (planned levels, before any degraded-mode raise).
  function nextChange(levels, idx) {
    for (var i = idx + 1; i < levels.length; i++) if (levels[i] !== levels[idx]) return { index: i, level: levels[i] };
    return null;
  }

  function fmt(s, vars) {
    return String(s).replace(/\{(\w+)\}/g, function (_, k) { return vars && vars[k] !== undefined ? vars[k] : "{" + k + "}"; });
  }

  var api = { degrade: degrade, hourIndex: hourIndex, ageMinutes: ageMinutes, nextChange: nextChange, fmt: fmt };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.HBCore = api;
})(typeof window !== "undefined" ? window : this);
