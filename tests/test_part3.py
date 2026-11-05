import dataclasses, json, os, re, shutil, subprocess, unittest, itertools
from heatbank import config
from heatbank.alerts import engine as alerts
from heatbank.archetypes.archetypes import build_archetypes
from heatbank.dashboard_model import aggregate, leaks_small_group
from heatbank.export import build_pack, write_js, DEMO_ROSTER, DEMO_ZONES
from heatbank.fallback import fallback
from heatbank.i18n import strings
from heatbank.sim.harness import simulate_worker
from heatbank.sim.toy_model import toy_phs
from heatbank.sim.tracker import ExposureTracker
from heatbank.site import bias
from heatbank.strain import radiant
from heatbank.strain.phs_wrapper import StrainEngine
from heatbank.weather.scenarios import SyntheticScenario
from tests import fakes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASH = os.path.join(ROOT, "dashboard")


class I18n(unittest.TestCase):
    def test_all_languages_complete(self):
        for l in strings.LANGS: self.assertEqual(strings.missing_keys(l), [], l)

    def test_english_matches_alert_engine(self):
        for lvl, (key, _, text) in alerts.ACTIONS.items(): self.assertEqual(strings.get("en", "action_" + key), text)

    def test_unknown_language_falls_back_to_english(self):
        self.assertEqual(strings.get("xx", "level_3"), "Red")

    def test_thai_is_marked_draft(self):
        self.assertIn("review", strings.REVIEW_STATUS["th"].lower())


class Dashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hours = SyntheticScenario("hot_humid").hours()
        cls.pack = build_pack(StrainEngine(toy_phs), cls.hours, build_archetypes(), DEMO_ROSTER, DEMO_ZONES, "TOY", "synthetic:hot_humid")

    def test_no_listed_zone_below_k(self):
        self.assertFalse(leaks_small_group(self.pack["supervisor"]))
        self.assertEqual(self.pack["supervisor"]["pooled_groups"], 1)        # the 3-person zone D
        self.assertNotIn("D", [z["id"] for z in self.pack["supervisor"]["zones"]])

    def test_small_group_never_hides_a_hazard(self):
        """A lone Red group must still raise the site status even though its zone is pooled away."""
        per = {a.id: [{"hour": f"{7+i:02d}", "level_max": "Green", "work_planned_min": 60, "rotate": False} for i in range(3)] for a in build_archetypes()}
        per["A09"][1]["level_max"] = "Red"
        roster = {"A": {"A01": 6}, "B": {"A09": 2}}                           # B is tiny and the only Red group
        agg = aggregate(roster, {}, per, k=5)
        self.assertEqual([z["id"] for z in agg["zones"]], ["A"])              # B not listed
        self.assertEqual(agg["site"][1]["worst"], 3)                          # but the site status is Red
        self.assertEqual(agg["site"][0]["worst"], 0)

    def test_pool_below_k_is_dropped_but_counts_toward_site(self):
        per = {a.id: [{"hour": "07", "level_max": "Orange", "work_planned_min": 20, "rotate": True}] for a in build_archetypes()}
        agg = aggregate({"X": {"A01": 2}, "Y": {"A02": 2}}, {}, per, k=5)     # pool = 4 < 5
        self.assertEqual(agg["zones"], []); self.assertEqual(agg["site"][0]["worst"], 2)

    def test_pack_has_no_identifiers_or_names(self):
        txt = json.dumps(self.pack).lower()
        for bad in ("worker_id", "employee", "badge", "phone_number", "email", "surname"):   # zone names are allowed, person names are not
            self.assertNotIn(bad, txt)

    def test_pack_is_labelled_synthetic_with_disclaimer(self):
        p = self.pack["provenance"]; self.assertTrue(p["synthetic"]); self.assertIn("Not a medical device", p["disclaimer"])

    def test_pack_is_json_and_writes_js(self):
        path = os.path.join(ROOT, "out_test_data.js"); write_js(self.pack, path)
        try:
            with open(path, encoding="utf-8") as fh: body = fh.read().split("window.HEATBANK = ", 1)[1].rstrip().rstrip(";")
            self.assertEqual(json.loads(body)["pack_version"], 1)
        finally:
            for f in (path, path + ".meta.json"):
                if os.path.exists(f): os.remove(f)


class FrontEnd(unittest.TestCase):
    def test_no_external_requests_in_static_files(self):
        """Offline-first and privacy (P3, P5): no CDN, no web fonts, no analytics. The SVG namespace string is not a request."""
        for fn in os.listdir(DASH):
            if not fn.endswith((".html", ".js", ".css")): continue
            with open(os.path.join(DASH, fn), encoding="utf-8") as fh: txt = fh.read().replace("http://www.w3.org/2000/svg", "")
            self.assertIsNone(re.search(r"https?://", txt), fn)
            self.assertNotIn("@import", txt, fn)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_js_degrade_matches_python_fallback(self):
        cfg = {"max_age_min": config.MAX_FORECAST_AGE_MIN, "stale_min_level": config.EXPORT_STALE_MIN_LEVEL, "stale_raise": config.EXPORT_STALE_RAISE}
        cases = [dict(level=l, have=h, offline=o, age=a) for l, h, o, a in
                 itertools.product(range(4), (True, False), (True, False), (None, 0, 60, 179, 180, 181, 400, 720))]
        script = ("const C=require(process.argv[1]);const d=JSON.parse(require('fs').readFileSync(0,'utf8'));"
                  "console.log(JSON.stringify(d.cases.map(c=>C.degrade(c.level,{haveForecast:c.have,offline:c.offline,ageMin:c.age},d.cfg).level)));")
        out = subprocess.run(["node", "-e", script, os.path.join(DASH, "core.js")], input=json.dumps({"cases": cases, "cfg": cfg}),
                             capture_output=True, text=True, check=True).stdout
        js = json.loads(out)
        py = [fallback.evaluate(c["age"], have_forecast=c["have"], offline=c["offline"]).apply(c["level"]) for c in cases]
        self.assertEqual(js, py)
        for c, j in zip(cases, js): self.assertGreaterEqual(j, c["level"])     # P2: never lowers

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_js_next_change_and_hour_index(self):
        script = ("const C=require(process.argv[1]);"
                  "const P={hours:['07','08','09'],provenance:{weather_date:'2026-01-01'}};"
                  "console.log(JSON.stringify([C.nextChange([1,1,2],0),C.nextChange([2,2],0),C.hourIndex(P,0,true,1),C.hourIndex(P,0,true,9),"
                  "C.hourIndex(P,Date.parse('2026-06-01T08:00:00'),false,0)]));")
        out = json.loads(subprocess.run(["node", "-e", script, os.path.join(DASH, "core.js")], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(out, [{"index": 2, "level": 2}, None, 1, -1, -1])


class SiteBias(unittest.TestCase):
    def setUp(self):
        self.fc = SyntheticScenario("hot_humid", "2026-01-01").hours() + SyntheticScenario("hot_humid", "2026-01-02").hours()

    def _node(self, off):
        return [bias.NodeObs(h.time_iso, h.tdb_c + off + (0.1 if i % 2 else -0.1), 60.0) for i, h in enumerate(self.fc)]

    def test_hotter_site_is_corrected_upward(self):
        r = bias.estimate_bias(self.fc, self._node(2.5)); self.assertAlmostEqual(r.applied_bias_c, 2.5, delta=0.3)

    def test_cooler_site_is_ignored_by_default_P2(self):
        r = bias.estimate_bias(self.fc, self._node(-2.5)); self.assertEqual(r.applied_bias_c, 0.0); self.assertLess(r.raw_bias_c, 0)

    def test_cooling_only_when_explicitly_allowed(self):
        config.SITE_BIAS_ALLOW_COOLING = True
        try: self.assertLess(bias.estimate_bias(self.fc, self._node(-2.5)).applied_bias_c, 0)
        finally: config.SITE_BIAS_ALLOW_COOLING = False

    def test_correction_is_clipped(self):
        self.assertEqual(bias.estimate_bias(self.fc, self._node(20)).applied_bias_c, config.SITE_BIAS_MAX_C)

    def test_frozen_sensor_is_not_learned_from(self):
        node = [bias.NodeObs(h.time_iso, 40.0, 60.0) for h in self.fc]
        r = bias.estimate_bias(self.fc, node); self.assertEqual(r.applied_bias_c, 0.0); self.assertIn("frozen", r.reason)

    def test_too_few_samples(self):
        self.assertEqual(bias.estimate_bias(self.fc, self._node(2.5)[:3]).applied_bias_c, 0.0)

    def test_v5_reduces_error_for_biased_site(self):
        r = bias.v5_bias_test(self.fc, self._node(2.5)); self.assertTrue(r["reduces_error"]); self.assertLess(r["mae_corrected_c"], r["mae_forecast_c"])

    def test_v5_needs_enough_data(self):
        self.assertEqual(bias.v5_bias_test(self.fc, self._node(2.5)[:5])["status"], "NOT ENOUGH DATA")


class AuditFixes(unittest.TestCase):
    def test_smoke_test_passes_for_toy_and_catches_ignored_state_and_errors(self):
        self.assertEqual(StrainEngine(toy_phs).smoke_test(), [])
        self.assertTrue(any("carry-over" in p for p in StrainEngine(fakes.fake_phs).smoke_test()))
        self.assertTrue(any("clean call failed" in p for p in StrainEngine(fakes.boom_phs).smoke_test()))

    def test_model_errors_are_counted_not_hidden(self):
        e = StrainEngine(fakes.boom_phs); r = e.run_segment(35, 45, 1, 50, 165, 0.5, 2, 0)
        self.assertTrue(r.fail_safe); self.assertEqual(e.model_errors, 1)

    def test_stateless_calls_are_cached(self):
        e = StrainEngine(toy_phs); a = (35, 45, 1, 50, 165, 0.5, 2, 0)
        e.run_segment(*a); e.run_segment(*a); self.assertEqual(e.calls, 1)

    def test_stateful_calls_are_not_cached(self):
        e = StrainEngine(toy_phs); a = (35, 45, 1, 50, 165, 0.5, 2, 0)
        s = e.run_segment(*a, duration_min=60).state
        e.run_segment(*a, duration_min=60, state=s); e.run_segment(*a, duration_min=60, state=s); self.assertEqual(e.calls, 3)

    def test_radiant_constant_mode_still_available(self):
        config.TR_FALLBACK_MODE = "constant"
        try: self.assertEqual(radiant.tr_fallback(30.0, 0.0), 45.0)
        finally: config.TR_FALLBACK_MODE = "solar"

    def test_radiant_solar_mode_is_default_night_equals_air_temp(self):
        self.assertEqual(config.TR_FALLBACK_MODE, "solar")                    # v0.4 default
        self.assertEqual(radiant.tr_fallback(27.0, 0.0), 27.0)
        self.assertEqual(radiant.tr_fallback(30.0, 1000.0), 45.0)
        self.assertEqual(radiant.tr_fallback(30.0, None), 45.0)               # unknown solar: keep the conservative constant (P2)

    def test_lookahead_never_adds_work_P1(self):
        eng = StrainEngine(toy_phs)
        for sc in ("hot_humid", "hot_dry", "cool"):
            hs = SyntheticScenario(sc).hours()
            for a in build_archetypes()[::3]:
                w0 = simulate_worker(eng, a, hs, "planned", 1.0, lookahead=0).worked_min
                w1 = simulate_worker(eng, a, hs, "planned", 1.0, lookahead=1).worked_min
                self.assertLessEqual(w1, w0, (sc, a.id))

    def test_forecast_only_v2_runs_and_reports_plan_safety(self):
        import tempfile
        from heatbank.sim import run_v2
        d = tempfile.mkdtemp(); run_v2.run(True, [1.0], d, forecast_only=True)
        with open(os.path.join(d, "v2_summary.md"), encoding="utf-8") as fh: md = fh.read()
        self.assertIn("PLAN SAFETY", md); self.assertIn("forecast-only fallback", md); self.assertIn("model errors", md)


if __name__ == "__main__":
    unittest.main()
