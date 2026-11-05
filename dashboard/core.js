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

  // Audit A15. Optional local break log: {hourKey, workedMs, since|null}. Pure so it can be tested; storage is the caller's job.
  function pad2(n) { return (n < 10 ? "0" : "") + n; }
  function hourKey(nowMs) { var d = new Date(nowMs); return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate()) + "T" + pad2(d.getHours()); }
  function hourStartMs(nowMs) { var d = new Date(nowMs); d.setMinutes(0, 0, 0); return d.getTime(); }
  function workedNow(rec, nowMs) {
    var key = hourKey(nowMs), same = rec && rec.hourKey === key;
    var w = same ? (rec.workedMs || 0) : 0;
    var since = rec && rec.since !== null && rec.since !== undefined ? (same ? rec.since : hourStartMs(nowMs)) : null;
    var run = since === null ? 0 : Math.max(0, nowMs - since);
    return { hourKey: key, workedMs: w, since: since, minutes: Math.floor((w + run) / 60000) };
  }
  function startWork(rec, nowMs) { var r = workedNow(rec, nowMs); return { hourKey: r.hourKey, workedMs: r.workedMs, since: r.since === null ? nowMs : r.since }; }
  function startBreak(rec, nowMs) { var r = workedNow(rec, nowMs); return { hourKey: r.hourKey, workedMs: r.workedMs + (r.since === null ? 0 : Math.max(0, nowMs - r.since)), since: null }; }
  // Mirrors fallback.adherence_raise: working past the plan (plus grace) RAISES the level by one, never lowers it (P2).
  function adherenceRaise(planned, worked, level, grace) {
    var overdue = worked > planned + grace;
    return { level: overdue ? Math.min(RED, level + 1) : level, overdue: overdue };
  }

  // R5 task timing: contiguous runs of hours where EVERY crew group is at or below maxLevel (default Yellow). Display only; uses the worst group, so conservative.
  function heavyWindows(levels, hours, maxLevel) {
    var m = maxLevel === undefined ? 1 : maxLevel, out = [], start = -1;
    for (var i = 0; i <= levels.length; i++) {
      var ok = i < levels.length && levels[i] <= m;
      if (ok && start < 0) start = i;
      if (!ok && start >= 0) { out.push({ from: hours[start], to: pad2(parseInt(hours[i - 1], 10) + 1) }); start = -1; }
    }
    return out;
  }

  function fmt(s, vars) {
    return String(s).replace(/\{(\w+)\}/g, function (_, k) { return vars && vars[k] !== undefined ? vars[k] : "{" + k + "}"; });
  }

  var api = { degrade: degrade, hourIndex: hourIndex, ageMinutes: ageMinutes, nextChange: nextChange, fmt: fmt, heavyWindows: heavyWindows,
              hourKey: hourKey, workedNow: workedNow, startWork: startWork, startBreak: startBreak, adherenceRaise: adherenceRaise };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.HBCore = api;
})(typeof window !== "undefined" ? window : this);
