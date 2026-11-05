(function () {
  "use strict";
  var P = window.HEATBANK, C = window.HBCore, U = window.HBUI, h = U.h, SV = P.supervisor;
  var demo = !!P.provenance.synthetic;
  var S = { lang: "en", idx: 4, cond: "ok" };
  var L = function (k, v) { return C.fmt(P.strings[S.lang][k], v); };

  function condState() {
    if (demo) {
      return { ok: { haveForecast: true, offline: false, ageMin: 20 }, offline: { haveForecast: true, offline: true, ageMin: 20 },
               stale: { haveForecast: true, offline: true, ageMin: 300 }, none: { haveForecast: false, offline: true, ageMin: null } }[S.cond];
    }
    return { haveForecast: true, offline: !navigator.onLine, ageMin: C.ageMinutes(P, Date.now()) };
  }
  function pill(level, label) { return h("span", { class: "lvpill lv" + level }, [U.shape(level, 18), h("span", { text: label || L("level_" + level) })]); }

  function render() {
    var main = document.getElementById("main"), ban = document.getElementById("banners");
    main.textContent = ""; ban.textContent = "";
    document.documentElement.lang = S.lang;
    var idx = demo ? S.idx : C.hourIndex(P, Date.now(), false, 0);
    var st = condState();
    if (idx < 0) st = { haveForecast: false, offline: st.offline, ageMin: null };
    var noData = idx < 0 || !st.haveForecast;
    var dbanner = C.degrade(0, st, P).banner;
    if (demo) ban.appendChild(h("div", { class: "banner demo", text: L("banner_demo") }));
    if (dbanner) ban.appendChild(h("div", { class: "banner", role: "status", text: L(dbanner) }));

    // Hour picker (demo) so the presenter can walk through the day.
    if (demo) {
      var bar = h("div", { class: "hours", role: "group", "aria-label": L("hour") });
      SV.site.forEach(function (s, i) {
        var b = h("button", { type: "button", "aria-pressed": String(i === S.idx) }, [U.shape(s.worst, 16), h("span", { text: s.hour + ":00" })]);
        b.addEventListener("click", function () { S.idx = i; render(); }); bar.appendChild(b);
      });
      main.appendChild(bar);
    }

    // Site status: highest level of ANY group. Level + action only. No counts, no zone, no names.
    var siteLevel = noData ? 3 : C.degrade(SV.site[idx].worst, st, P).level;   // no forecast => Red, no table
    var key = P.action_keys[siteLevel];
    main.appendChild(h("section", { class: "slab lv" + siteLevel }, [
      h("div", { class: "word" }, [U.shape(siteLevel, 36), h("span", { text: L("level_" + siteLevel) })]),
      h("div", { style: "justify-self:end" }, [U.pictogram(["pic_water", "pic_shade", "pic_cooldown", "pic_stop_medic"][siteLevel], 72)]),
      h("p", { class: "action", text: L("action_" + key) })
    ]));
    main.appendChild(h("p", { class: "muted", text: L("site_worst") + ": " + L("site_worst_note") }));

    if (!noData) {
      var nc = C.nextChange(SV.site.map(function (s) { return s.worst; }), idx);
      main.appendChild(h("p", { text: L("next_change") + ": " + (nc ? L("changes_to", { level: L("level_" + nc.level), hour: P.hours[nc.index] }) : L("no_change")) }));
      var hw = C.heavyWindows(SV.site.map(function (s) { return s.worst; }), P.hours, 1);
      main.appendChild(h("p", { text: L("heavy_windows") + ": " + (hw.length ? hw.map(function (w) { return w.from + ":00-" + w.to + ":00"; }).join(", ") : L("heavy_none")) + ". " + L("heavy_note") }));
      var tb = h("table", { class: "zones" }, [
        h("thead", {}, [h("tr", {}, ["zone", "crew_size", "site_worst", "first_break", "rotation"].map(function (k) {
          return h("th", { scope: "col", text: L(k === "site_worst" ? "col_level" : k) }); }))])]);
      var body = h("tbody");
      SV.zones.forEach(function (z) {
        var r = z.hours[idx], lvl = C.degrade(r.worst, st, P).level;
        var counts = h("div", { class: "counts" });
        r.counts.forEach(function (n, lv) { counts.appendChild(h("span", { class: n ? "" : "zero" }, [U.shape(lv, 14), h("span", { text: String(n) })])); });
        var name = z.name === null ? L("pooled") : z.name;
        body.appendChild(h("tr", {}, [
          h("td", { "data-label": L("zone"), text: name }),
          h("td", { "data-label": L("crew_size"), text: String(z.n) }),
          h("td", { "data-label": L("col_level") }, [pill(lvl), counts]),
          h("td", { "data-label": L("first_break"), text: r.first_break_min === null ? L("no_break_needed") : L("at_minute", { n: r.first_break_min }) }),
          h("td", { "data-label": L("rotation"), text: r.rotate ? L("rotate_yes") : L("rotate_no") })]));
      });
      tb.appendChild(body); main.appendChild(tb);
    }
    main.appendChild(h("p", { class: "muted", text: L("privacy_note") + " " + L("small_groups_note", { k: SV.k }) }));
    renderStatic(st);
  }

  function renderStatic(st) {
    [["t-app", "app_name"], ["t-wk", "worker_view"], ["t-lang", "language"], ["t-demo", "demo_controls"], ["t-cond", "condition"]].forEach(function (p) {
      document.getElementById(p[0]).textContent = L(p[1]); });
    var cond = document.getElementById("cond"); cond.textContent = "";
    ["ok", "offline", "stale", "none"].forEach(function (c) { var o = h("option", { value: c, text: L("cond_" + c) }); if (c === S.cond) o.selected = true; cond.appendChild(o); });
    var f = document.getElementById("foot"); f.textContent = "";
    f.appendChild(h("p", { text: L("disclaimer") }));
    if (P.provenance.synthetic) f.appendChild(h("p", { class: "chip", text: L("simulated") }));
    f.appendChild(h("p", { text: P.provenance.strain_model + " | " + P.provenance.weather_source }));
    if (P.lang_status[S.lang] && S.lang !== "en") f.appendChild(h("p", { text: P.lang_status[S.lang] }));
    document.getElementById("demo").style.display = demo ? "" : "none";
  }

  S.lang = U.initLang(P, function (l) { S.lang = l; render(); });
  document.getElementById("cond").addEventListener("change", function (e) { S.cond = e.target.value; render(); });
  render();
})();
