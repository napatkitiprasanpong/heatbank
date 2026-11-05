(function () {
  "use strict";
  var P = window.HEATBANK, C = window.HBCore, U = window.HBUI, h = U.h;
  var demo = !!P.provenance.synthetic;
  var S = { lang: "en", aid: "A09", idx: 0, cond: "ok" };
  // Optional break log (audit A15). Lives in this browser only (localStorage, guarded); nothing is ever sent anywhere.
  var LOGKEY = "heatbank_breaklog_v1";
  function loadLog() { try { var x = JSON.parse(window.localStorage.getItem(LOGKEY)); if (x && typeof x === "object") return x; } catch (e) {} return { hourKey: "", workedMs: 0, since: null }; }
  function saveLog(r) { try { window.localStorage.setItem(LOGKEY, JSON.stringify(r)); } catch (e) {} S.log = r; }
  S.log = loadLog();
  var L = function (k, v) { return C.fmt(P.strings[S.lang][k], v); };

  function condState() {
    if (demo) {
      return { ok: { haveForecast: true, offline: false, ageMin: 20 }, offline: { haveForecast: true, offline: true, ageMin: 20 },
               stale: { haveForecast: true, offline: true, ageMin: 300 }, none: { haveForecast: false, offline: true, ageMin: null } }[S.cond];
    }
    return { haveForecast: true, offline: !navigator.onLine, ageMin: C.ageMinutes(P, Date.now()) };
  }

  function render() {
    var main = document.getElementById("main"), ban = document.getElementById("banners");
    main.textContent = ""; ban.textContent = "";
    document.documentElement.lang = S.lang;
    var plan = P.plans[S.aid];
    var idx = demo ? S.idx : C.hourIndex(P, Date.now(), false, 0);
    var st = condState();
    if (idx < 0) st = { haveForecast: false, offline: st.offline, ageMin: null };   // pack does not cover now: no forecast (P2)
    var row = idx >= 0 ? plan[idx] : null;
    var planned = row ? P.level_names.indexOf(row.level_max) : 3;
    var d = C.degrade(planned, st, P);
    var level = d.level;
    var worked = C.workedNow(S.log, Date.now()).minutes, overdue = false;
    if (row && st.haveForecast) {   // A15: working past the plan raises the shown level by one, never lowers it
      var ar = C.adherenceRaise(degradedWork(row.work_planned_min, st, d), worked, level, P.adherence_grace_min === undefined ? 5 : P.adherence_grace_min);
      level = ar.level; overdue = ar.overdue;
    }

    if (demo) ban.appendChild(h("div", { class: "banner demo", text: P.provenance.weather_real ? L("banner_demo_realwx", { date: P.provenance.weather_date }) : L("banner_demo") }));
    if (d.banner) ban.appendChild(h("div", { class: "banner", role: "status", text: L(d.banner) }));

    var key = P.action_keys[level], picId = ["pic_water", "pic_shade", "pic_cooldown", "pic_stop_medic"][level];
    var slab = h("section", { class: "slab lv" + level, "aria-label": L("level_" + level) }, [
      h("div", { class: "word" }, [U.shape(level, 36), h("span", { text: L("level_" + level) })]),
      h("div", { style: "justify-self:end" }, [U.pictogram(picId, 72)]),
      h("p", { class: "action", text: L("action_" + key) })
    ]);
    main.appendChild(slab);

    if (overdue) main.appendChild(h("p", { class: "banner", role: "status", text: L("overdue_note") }));
    if (row && st.haveForecast && row.gate) main.appendChild(h("p", { class: "banner", role: "status", text: L("gate_note") }));
    if (row && st.haveForecast && row.rest_ok === false) main.appendChild(h("p", { class: "banner", role: "status", text: L("norecovery_note") }));
    if (row && st.haveForecast && row.state_level) {   // A10: second reading, next to (never instead of) the conditions level
      main.appendChild(h("p", { class: "muted", text: L("state_line", { level: L("level_" + P.level_names.indexOf(row.state_level)) }) + " " + L("state_note") }));
    }
    if (row && st.haveForecast) {   // no forecast => no plan content at all, only the fail-safe slab
      var frac = Math.max(0, Math.min(1, row.fraction_used_end || 0)), pct = Math.round(frac * 100);
      var w = degradedWork(row.work_planned_min, st, d);
      main.appendChild(h("section", { class: "card" }, [
        h("h2", { text: L("heat_budget") }),
        h("div", { class: "budget", role: "img", "aria-label": L("heat_budget") + " " + pct + "%" }, [
          h("div", { class: "band b0" }), h("div", { class: "band b1" }), h("div", { class: "band b2" }),
          h("div", { class: "cut", style: "left:50%" }), h("div", { class: "cut", style: "left:75%" }),
          h("div", { class: "fill", style: "width:" + pct + "%" }), h("div", { class: "pct", text: pct + "%" })]),
        h("div", { class: "ticks" }, [h("span", { style: "left:50%", text: "50%" }), h("span", { style: "left:75%", text: "75%" }), h("span", { style: "left:100%", text: "100%" })]),
        h("p", { class: "muted", text: L("budget_note") })
      ]));
      main.appendChild(h("section", { class: "card" }, [
        h("h2", { text: L("this_hour") + " " + row.hour + ":00" }),
        h("div", { class: "strip" }, [
          w > 0 ? h("div", { class: "w", style: "width:" + (w / 60 * 100) + "%", text: L("work") + " " + w }) : null,
          w < 60 ? h("div", { class: "r", style: "width:" + ((60 - w) / 60 * 100) + "%", text: L("rest") + " " + (60 - w) }) : null]),
        h("p", { class: "muted", text: L("work_rest_line", { w: w, r: 60 - w }) + (row.rotate ? " " + L("rotate_yes") + "." : "") })
      ]));
      main.appendChild(h("section", { class: "card" }, [
        h("h2", { text: L("log_title") }),
        h("div", { class: "ctrl" }, [
          (function () { var b = h("button", { type: "button", text: L("log_work") }); b.addEventListener("click", function () { saveLog(C.startWork(S.log, Date.now())); render(); }); return b; })(),
          (function () { var b = h("button", { type: "button", text: L("log_break") }); b.addEventListener("click", function () { saveLog(C.startBreak(S.log, Date.now())); render(); }); return b; })()]),
        h("p", { class: "muted", text: L("log_worked", { n: worked }) + " " + L("log_note") })
      ]));
      var levels = plan.map(function (r) { return P.level_names.indexOf(r.level_max); });
      var nc = C.nextChange(levels, idx);
      main.appendChild(h("section", { class: "card" }, [
        h("h2", { text: L("next_change") }),
        h("p", { text: nc ? L("changes_to", { level: L("level_" + nc.level), hour: P.hours[nc.index] }) : L("no_change") })
      ]));
      var ul = h("ul", { class: "day", "aria-label": L("today") });
      plan.forEach(function (r, i) {
        var lv = levels[i];
        ul.appendChild(h("li", { class: "lv-cell lv" + lv + (i === idx ? " now" : "") }, [
          h("div", { text: r.hour + ":00" }), h("div", { class: "sh" }, [U.shape(lv, 22)]), h("div", { text: L("level_" + lv) }),
          h("div", { class: "muted", text: r.work_planned_min + " " + L("min") })]));
      });
      main.appendChild(h("section", { class: "card" }, [h("h2", { text: L("today") }), ul]));
    }
    if (level >= 3) {
      main.appendChild(h("section", { class: "card redcard" }, [h("h2", { text: L("red_card_title") }), h("p", { text: L("red_card_body") }),
        h("p", { class: "muted", text: L("red_card_review") })]));
      main.appendChild(escalationCard());
    }
    renderStatic(st);
  }

  // Audit A18: one-tap help that the WORKER starts. Nothing is sent by the page itself. Numbers are reduced to digits and a leading +.
  function cleanTel(x) { var t = String(x || "").replace(/[^0-9+]/g, ""); t = (t.charAt(0) === "+" ? "+" : "") + t.replace(/\+/g, ""); return t.length >= 3 ? t : ""; }
  function escalationCard() {
    var medic = cleanTel(P.escalation && P.escalation.medic_tel), kids = [h("h2", { text: L("esc_title") })];
    kids.push(medic ? h("a", { class: "btn", href: "tel:" + medic, text: L("esc_call") + " (" + medic + ")" }) : h("p", { class: "muted", text: L("esc_none") }));
    var saved = ""; try { saved = window.localStorage.getItem("heatbank_buddy_v1") || ""; } catch (e) {}
    var inp = h("input", { type: "tel", id: "buddy", value: saved, "aria-label": L("esc_buddy_label"), placeholder: L("esc_buddy_label") });
    inp.value = saved;
    var link = h("a", { class: "btn", href: saved ? "sms:" + cleanTel(saved) + "?&body=" + encodeURIComponent(L("esc_msg")) : "#", text: L("esc_buddy") });
    inp.addEventListener("change", function () {
      var v = cleanTel(inp.value); try { window.localStorage.setItem("heatbank_buddy_v1", v); } catch (e) {}
      link.setAttribute("href", v ? "sms:" + v + "?&body=" + encodeURIComponent(L("esc_msg")) : "#");
    });
    kids.push(h("label", {}, [h("span", { class: "muted", text: L("esc_buddy_label") }), inp]), link, h("p", { class: "muted", text: L("esc_note") }));
    return h("section", { class: "card" }, kids);
  }

  // Degraded mode never lengthens work; when raised, show at most the conservative cap (mirrors planner.DEGRADED_WORK_CAP_MIN = 30).
  function degradedWork(work, st, d) { return d.banner && d.banner !== "banner_offline" ? Math.min(work, P.degraded_work_cap_min || 30) : work; }

  function renderStatic(st) {
    ["t-app", "t-sup", "t-lang", "t-demo", "t-arch", "t-hour", "t-cond"].forEach(function (id) {
      var el = document.getElementById(id), m = { "t-app": "app_name", "t-sup": "supervisor_view", "t-lang": "language", "t-demo": "demo_controls", "t-arch": "archetype", "t-hour": "hour", "t-cond": "condition" }[id];
      el.textContent = L(m);
    });
    var cond = document.getElementById("cond"); var cur = cond.value || "ok"; cond.textContent = "";
    ["ok", "offline", "stale", "none"].forEach(function (c) { var o = h("option", { value: c, text: L("cond_" + c) }); if (c === S.cond) o.selected = true; cond.appendChild(o); });
    fillArch();
    document.getElementById("hourlabel").textContent = P.hours[S.idx] + ":00";
    var f = document.getElementById("foot"); f.textContent = "";
    f.appendChild(h("p", { text: L("disclaimer") }));
    if (P.provenance.synthetic) f.appendChild(h("p", { class: "chip", text: P.provenance.weather_real ? L("simulated_realwx", { date: P.provenance.weather_date }) : L("simulated") }));
    if (P.provenance.attribution) f.appendChild(h("p", { text: P.provenance.attribution }));
    f.appendChild(h("p", { text: P.provenance.strain_model + " | " + P.provenance.weather_source }));
    if (P.lang_status[S.lang] && S.lang !== "en") f.appendChild(h("p", { text: P.lang_status[S.lang] }));
    if (st && st.ageMin !== null && st.ageMin !== undefined) f.appendChild(h("p", { text: L("updated") + ": " + L("age_min", { n: Math.round(st.ageMin) }) }));
    document.getElementById("demo").style.display = demo ? "" : "none";
  }

  function archLabel(a) {
    return L("task_" + a.task) + ", " + L("cloth_" + a.clothing) + ", " + L(a.acclimatized ? "acc_yes" : "acc_no");
  }
  function fillArch() {
    var arch = document.getElementById("arch"); arch.textContent = "";
    P.archetypes.forEach(function (a) { var o = h("option", { value: a.id, text: a.id + ": " + archLabel(a) }); if (a.id === S.aid) o.selected = true; arch.appendChild(o); });
  }
  function boot() {
    S.lang = U.initLang(P, function (l) { S.lang = l; render(); });
    var arch = document.getElementById("arch"); fillArch();
    arch.addEventListener("change", function () { S.aid = arch.value; render(); });
    var hr = document.getElementById("hour"); hr.max = P.hours.length - 1; hr.value = Math.min(4, P.hours.length - 1); S.idx = +hr.value;
    hr.addEventListener("input", function () { S.idx = +hr.value; render(); });
    document.getElementById("cond").addEventListener("change", function (e) { S.cond = e.target.value; render(); });
    render();
  }
  boot();
  setInterval(function () { if (S.log && S.log.since !== null) render(); }, 30000);
})();
