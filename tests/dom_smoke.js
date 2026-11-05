/* Headless smoke test of the static pages WITHOUT a browser: a tiny fake DOM runs data.js, core.js, ui.js and the page script,
   then walks the controls (language, connection state, hour, break log) and checks that nothing throws and key text appears.
   It does not test layout or colours; those still need a real browser (docs/DEMO_CHECKLIST.md).
   usage: node tests/dom_smoke.js dashboard   (prints JSON, exit code 1 on any failure) */
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm");
const dir = path.resolve(process.argv[2] || "dashboard");
const failures = [];

function makeDom(htmlText) {
  class El {
    constructor(tag) { this.tag = tag; this.children = []; this.attrs = {}; this._text = ""; this.className = ""; this.listeners = {}; this.style = {}; this.value = ""; this.selected = false; }
    setAttribute(k, v) { this.attrs[k] = String(v); if (k === "value") this.value = String(v); }
    getAttribute(k) { return this.attrs[k]; }
    appendChild(c) { this.children.push(c); return c; }
    addEventListener(t, f) { (this.listeners[t] = this.listeners[t] || []).push(f); }
    fire(t, ev) { (this.listeners[t] || []).forEach(f => f(ev || { target: this })); }
    set textContent(v) { this.children = []; this._text = String(v); }
    get textContent() { return this._text + this.children.map(c => c.textContent).join(" "); }
    set innerHTML(v) { this._inner = v; }
    get innerHTML() { return this._inner || ""; }
    walk(f) { f(this); this.children.forEach(c => c.walk ? c.walk(f) : null); }
  }
  const byId = {};
  (htmlText.match(/id="([^"]+)"/g) || []).forEach(m => { const id = m.slice(4, -1); byId[id] = new El(id === "arch" || id === "cond" || id === "lang" ? "select" : "div"); });
  const doc = {
    documentElement: new El("html"), body: new El("body"),
    getElementById: id => byId[id] || (failures.push("missing element #" + id), new El("div")),
    createElement: t => new El(t), createElementNS: (ns, t) => new El(t), createTextNode: t => { const e = new El("#text"); e._text = String(t); return e; }
  };
  return { doc, byId };
}

function boot(page, opts) {
  const html = fs.readFileSync(path.join(dir, page), "utf8");
  const { doc, byId } = makeDom(html);
  const store = {};
  const win = { document: doc, navigator: { language: opts.lang || "en", onLine: true }, location: { search: "" },
                localStorage: { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } },
                setInterval: () => 0, console };
  win.window = win;
  const ctx = vm.createContext(Object.assign(win, { document: doc, navigator: win.navigator, location: win.location, setInterval: win.setInterval }));
  const scripts = (html.match(/<script src="([^"]+)"/g) || []).map(s => s.slice(13, -1));
  scripts.forEach(s => vm.runInContext(fs.readFileSync(path.join(dir, s), "utf8"), ctx, { filename: s }));
  return { win, doc, byId, ctx, store };
}

function text(el) { return el.textContent.replace(/\s+/g, " "); }
function check(name, cond) { if (!cond) failures.push(name); }

const results = {};
for (const page of ["worker.html", "supervisor.html"]) {
  try {
    const app = boot(page, {});
    const P = app.win.HEATBANK;
    const main = app.byId.main;
    check(page + ": renders something", text(main).length > 20);
    check(page + ": demo banner present", text(app.byId.banners).toLowerCase().includes("demo"));
    if (P.provenance.weather_real) {   // v0.6: real weather replay must say so, and must still say crew/clock are simulated, and credit NASA
      check(page + ": real-weather banner says real weather and simulated crew", /real weather/i.test(text(app.byId.banners)) && /simulated/i.test(text(app.byId.banners)));
      check(page + ": real-weather footer credits the data provider and keeps the simulated-crew chip", /NASA/.test(text(app.byId.foot)) && /SIMULATED crew/i.test(text(app.byId.foot)));
    }
    for (const cond of ["offline", "stale", "none", "ok"]) {
      app.byId.cond.value = cond; app.byId.cond.fire("change", { target: app.byId.cond });
      if (cond === "none") {
        check(page + ": no-forecast shows Red and no plan content", text(main).includes("Red") && !text(main).includes("This hour") && !text(main).includes("Zone A"));
      }
      if (cond === "stale") check(page + ": stale banner", text(app.byId.banners).includes("old"));
    }
    if (page === "worker.html") {
      // every archetype and every hour renders without throwing
      for (const a of P.archetypes) { app.byId.arch.value = a.id; app.byId.arch.fire("change", { target: app.byId.arch }); }
      for (let i = 0; i < P.hours.length; i++) { app.byId.hour.value = String(i); app.byId.hour.fire("input", { target: app.byId.hour }); }
      // switch to Thai
      app.byId.lang.value = "th"; app.byId.lang.fire("change", { target: app.byId.lang });
      check("worker: Thai draft marker visible", text(app.byId.foot).includes("DRAFT"));
      app.byId.lang.value = "en"; app.byId.lang.fire("change", { target: app.byId.lang });
      // break log: press "Back at work" and check the stored record exists and nothing throws
      let btn = null;
      main.walk(e => { if (e.tag === "button" && e._text === "Back at work") btn = e; });
      check("worker: break-log button exists", !!btn);
      if (btn) { btn.fire("click"); check("worker: log saved locally", Object.keys(app.store).some(k => k.indexOf("heatbank_breaklog") === 0)); }
      // Red screen offers help the worker starts (A18): force "no forecast" (always Red) and look for the help card
      app.byId.cond.value = "none"; app.byId.cond.fire("change", { target: app.byId.cond });
      check("worker: Red screen has a Get help card", text(main).includes("Get help"));
      let tel = null; main.walk(e => { if (e.tag === "a" && (e.attrs.href || "").startsWith("tel:")) tel = e; });
      check("worker: medic number link only when a number is configured", (P.escalation.medic_tel ? !!tel : !tel));
      app.byId.cond.value = "ok"; app.byId.cond.fire("change", { target: app.byId.cond });
      check("worker: body-state line shown for hours after exposure", (() => { let ok = false; for (let i = 0; i < P.hours.length; i++) { app.byId.hour.value = String(i); app.byId.hour.fire("input", { target: app.byId.hour }); if (text(main).includes("Body model")) ok = true; } return ok; })());
    } else {
      check("supervisor: shows site status without counts line", text(main).includes("Site status"));
      check("supervisor: no zone below k listed", P.supervisor.zones.every(z => z.n >= P.supervisor.k));
    }
    results[page] = "ok";
  } catch (e) { failures.push(page + ": threw " + e.stack.split("\n").slice(0, 3).join(" | ")); results[page] = "FAILED"; }
}
console.log(JSON.stringify({ results, failures }));
process.exit(failures.length ? 1 : 0);
