"""v0.4 tests: audit round 2 (A1/A12 wrapper, A9 rest area, A10 body state, A13 Gulf day, A15 break log) and an end-to-end
integration check that Parts 1, 2 and 3 work together. TOY model and fakes only: these prove plumbing and rules, not physiology."""
import dataclasses, itertools, json, os, shutil, subprocess, tempfile, unittest
from types import SimpleNamespace
from heatbank import config
from heatbank.alerts import engine as alerts
from heatbank.archetypes.archetypes import build_archetypes
from heatbank.export import build_pack, DEMO_ROSTER, DEMO_ZONES
from heatbank.fallback import fallback
from heatbank.planner.planner import plan_hour, baseline_work_min
from heatbank.sim.harness import simulate_worker, shift_hours
from heatbank.sim.toy_model import toy_phs
from heatbank.sim.tracker import ExposureTracker, rest_conditions
from heatbank.strain import phs_wrapper
from heatbank.strain.phs_wrapper import StrainEngine
from heatbank.weather.scenarios import SyntheticScenario, SCENARIOS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = {a.id: a for a in build_archetypes()}


def strict_phs(tdb, tr, v, rh, met, clo, posture, wme=0, round_output=True, limit_inputs=True, acclimatized=100, drink=1, duration=480,
               t_re=36.8, t_sk=34.1, t_cr=36.8, t_cr_eq=36.8, t_sk_t_cr_wg=0.3):
    """A phs() with a fixed signature (no **kwargs) that, like the library as recalled, has NO sweat_loss_g input."""
    kw = dict(duration=duration, t_re=t_re)
    return toy_phs(tdb, tr, v, rh, met, clo, posture, **kw)


def carrying_phs(tdb, tr, v, rh, met, clo, posture=2, **kw):
    """Toy that ALSO carries a cumulative sweat total when told (to exercise the sweat_carries=True branch)."""
    r = toy_phs(tdb, tr, v, rh, met, clo, posture, **kw)
    r.sweat_loss_g += float(kw.get("sweat_loss_g", 0.0))
    return r


class Wrapper(unittest.TestCase):
    def test_sweat_loss_is_never_passed_as_an_input(self):
        seen = {}
        def spy(tdb, tr, v, rh, met, clo, posture=2, **kw):
            seen.update(kw); return toy_phs(tdb, tr, v, rh, met, clo, posture, **kw)
        e = StrainEngine(spy); s = e.run_segment(35, 45, 1, 50, 230, 0.9, 2, 100, 1, duration_min=60).state
        e.run_segment(35, 45, 1, 50, 230, 0.9, 2, 100, 1, duration_min=60, state=s)
        self.assertNotIn("sweat_loss_g", seen); self.assertIn("t_re", seen)

    def test_unaccepted_state_kwargs_are_dropped_not_crashed_and_reported(self):
        def narrow(tdb, tr, v, rh, met, clo, posture, acclimatized=100, drink=1, duration=480, t_re=36.8):
            return toy_phs(tdb, tr, v, rh, met, clo, posture, duration=duration, t_re=t_re)
        e = StrainEngine(narrow); s = e.run_segment(35, 45, 1, 50, 230, 0.9, 2, 100, 1, duration_min=60).state
        r = e.run_segment(35, 45, 1, 50, 230, 0.9, 2, 100, 1, duration_min=60, state=s)
        self.assertEqual(r.status, "OK"); self.assertEqual(e.model_errors, 0)
        self.assertIn("t_sk", e.dropped_state_kwargs)
        self.assertTrue(any("does not accept" in p for p in StrainEngine(narrow).smoke_test()))

    def test_strict_signature_engine_passes_smoke_test(self):
        e = StrainEngine(strict_phs); self.assertEqual(e.smoke_test(), []); self.assertEqual(e.model_errors, 0)

    def test_sweat_restart_is_detected_and_warned(self):
        e = StrainEngine(toy_phs); self.assertEqual(e.smoke_test(), [])
        self.assertIs(e.sweat_carries, False); self.assertTrue(any("A12" in w for w in e.warnings))

    def test_sweat_carry_is_detected_when_the_library_carries(self):
        # a library that carries must be CALLED with the previous total, so the wrapper cannot see it unless it is an accepted input;
        # here we simulate a library whose total is cumulative by itself:
        total = {"s": 0.0}
        def cum(tdb, tr, v, rh, met, clo, posture=2, **kw):
            r = toy_phs(tdb, tr, v, rh, met, clo, posture, **kw)
            if "t_re" not in kw: total["s"] = 0.0
            total["s"] += r.sweat_loss_g; r.sweat_loss_g = total["s"]; return r
        e = StrainEngine(cum); e.smoke_test(); self.assertIs(e.sweat_carries, True)

    def test_tracker_sums_when_restart_and_replaces_when_carry(self):
        h = shift_hours(SyntheticScenario("hot_humid").hours())[0]
        e1 = StrainEngine(toy_phs); e1.sweat_carries = False; t1 = ExposureTracker(e1, A["A09"]); t1.step(h, 30, True); t1.step(h, 30, True)
        e2 = StrainEngine(toy_phs); e2.sweat_carries = True; t2 = ExposureTracker(e2, A["A09"]); t2.step(h, 30, True); t2.step(h, 30, True)
        self.assertAlmostEqual(t1.sweat_g, 2 * t2.sweat_g, places=3)           # toy segment totals are equal, so sum = 2x last
        e3 = StrainEngine(toy_phs); t3 = ExposureTracker(e3, A["A09"]); t3.step(h, 30, True); t3.step(h, 30, True)
        self.assertAlmostEqual(t3.sweat_g, t1.sweat_g, places=3)               # unknown (None) behaves like restart: can only overstate (P2)

    def test_water_guard_only_raises(self):
        h = shift_hours(SyntheticScenario("cool").hours())[0]
        e = StrainEngine(toy_phs); t = ExposureTracker(e, A["A01"]); t.step(h, 60, True)
        base = t.remaining_and_fraction(h)
        config.WATER_GUARD_G = 1.0
        try: guarded = t.remaining_and_fraction(h)
        finally: config.WATER_GUARD_G = None
        self.assertEqual(guarded, (0.0, 1.0, False)); self.assertLessEqual(base[1], guarded[1])

    def test_cap_diagnostic_counts_probes(self):
        e = StrainEngine(toy_phs); hrs = SyntheticScenario("cool").hours()
        simulate_worker(e, A["A01"], hrs, "planned", 1.0)
        self.assertGreater(e.cap_checks, 0); self.assertLessEqual(e.cap_hits, e.cap_checks)


class RestArea(unittest.TestCase):
    def _strained_tracker(self, scenario, aid="A09", hour_idx=4):
        hrs = shift_hours(SyntheticScenario(scenario).hours()); e = StrainEngine(toy_phs); t = ExposureTracker(e, A[aid])
        for h in hrs[:hour_idx]: t.step(h, 60, True)
        return t, hrs[hour_idx]

    def test_no_strain_means_unknown_not_failure(self):
        e = StrainEngine(toy_phs); t = ExposureTracker(e, A["A09"]); h = shift_hours(SyntheticScenario("hot_dry").hours())[0]
        self.assertIsNone(t.rest_recovers(h))

    def test_shade_recovers_on_a_mild_day_but_not_on_a_very_hot_one_toy(self):
        t, h = self._strained_tracker("hot_humid"); self.assertTrue(t.rest_recovers(h))
        t2, h2 = self._strained_tracker("hot_dry", hour_idx=7); self.assertIs(t2.rest_recovers(h2), False)

    def test_cooled_cabin_recovers_where_shade_does_not(self):
        t, h = self._strained_tracker("hot_dry", hour_idx=7)
        self.assertIs(t.rest_recovers(h), False)
        config.REST_AREA = "cooled_cabin"
        try: self.assertTrue(t.rest_recovers(h))
        finally: config.REST_AREA = "shade"

    def test_rest_conditions_presets(self):
        h = shift_hours(SyntheticScenario("hot_dry").hours())[6]
        tdb, tr, v, rh = rest_conditions(h); self.assertEqual((tdb, tr), (h.tdb_c, h.tdb_c))
        config.REST_AREA = "fan"
        try: self.assertGreaterEqual(rest_conditions(h)[2], 1.5)
        finally: config.REST_AREA = "shade"

    def test_planner_gives_no_work_when_rest_does_not_cool_and_never_more_than_baseline_P1(self):
        for rem in (10.0, 60.0, 200.0, 480.0):
            p = plan_hour(rem, rest_ok=False); self.assertEqual(p.work_min, 0); self.assertTrue(p.needs_cooler_rest)
            self.assertLessEqual(p.work_min, baseline_work_min(rem))
            self.assertLessEqual(plan_hour(rem, rest_ok=True).work_min, baseline_work_min(rem))

    def test_harness_reports_rest_flag_per_hour(self):
        r = simulate_worker(StrainEngine(toy_phs), A["A09"], SyntheticScenario("hot_dry").hours(), "planned", 1.0)
        self.assertGreater(r.no_recovery_hours, 0); self.assertTrue(any(h["rest_ok"] is False for h in r.hourly))


class RealLibraryFacts(unittest.TestCase):
    """Behaviour measured on pythermalcomfort 4.8.0 (scripts/diagnose_phs.py, 2026-11-05), reproduced with fakes."""
    def test_limit_already_exceeded_is_zero_minutes_not_one(self):
        def exceeded(tdb, tr, v, rh, met, clo, posture=2, **kw):
            return SimpleNamespace(d_lim_t_re=1, d_lim_loss_95=1, d_lim_loss_50=1, t_re=38.4, t_sk=36, t_cr=38.3, t_cr_eq=38.3,
                                   t_sk_t_cr_wg=0.3, sweat_loss_g=5000.0, sweat_rate_watt=300.0, evap_load_wm2_min=1.0)
        r = StrainEngine(exceeded).run_segment(35, 45, 1, 50, 230, 0.9, 2, 100)
        self.assertEqual(r.safe_minutes, 0.0); self.assertIn("already exceeded", r.limiting)

    def test_core_temperature_past_limit_is_red_even_if_minutes_look_positive(self):
        e = StrainEngine(toy_phs); t = ExposureTracker(e, A["A09"]); h = shift_hours(SyntheticScenario("cool").hours())[0]
        t.state = phs_wrapper.PhsState({"t_re": 38.2}); rem, frac, fs = t.remaining_and_fraction(h)
        self.assertEqual((rem, frac, fs), (0.0, 1.0, False))
        self.assertEqual(alerts.compose(frac, fs).level, alerts.RED)

    def test_strained_threshold_sits_above_the_rest_asymptote(self):
        self.assertGreater(config.STATE_T_RE_BASE_C + config.STRAINED_ABOVE_C, 37.2)    # seated rest settles near 37.1 C (Q3)


class BodyState(unittest.TestCase):
    def test_state_level_is_monotone_and_uses_alert_fractions(self):
        lv = [alerts.state_level(t / 100) for t in range(3600, 3900, 5)]
        self.assertEqual(lv, sorted(lv)); self.assertEqual(alerts.state_level(36.9), alerts.GREEN); self.assertEqual(alerts.state_level(38.2), alerts.RED)
        self.assertIsNone(alerts.state_level(None))

    def test_hourly_rows_carry_both_readings_and_conditions_level_is_untouched(self):
        r = simulate_worker(StrainEngine(toy_phs), A["A09"], SyntheticScenario("hot_humid").hours(), "planned", 1.0)
        for row in r.hourly:
            self.assertIn(row["level_max"], alerts.NAMES); self.assertIn(row["state_level"], alerts.NAMES + [None])


class Adherence(unittest.TestCase):
    def test_python_rule_never_lowers_P2(self):
        for lvl, planned, worked in itertools.product(range(4), (0, 20, 60), (0, 20, 25, 26, 60)):
            out, overdue = fallback.adherence_raise(planned, worked, lvl); self.assertGreaterEqual(out, lvl)
            self.assertEqual(overdue, worked > planned + config.ADHERENCE_GRACE_MIN)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_js_adherence_matches_python(self):
        cases = [dict(l=l, p=p, w=w) for l, p, w in itertools.product(range(4), (0, 20, 60), (0, 20, 25, 26, 61))]
        script = ("const C=require(process.argv[1]);const d=JSON.parse(require('fs').readFileSync(0,'utf8'));"
                  "console.log(JSON.stringify(d.cases.map(c=>{const r=C.adherenceRaise(c.p,c.w,c.l,d.g);return [r.level,r.overdue]})));")
        out = subprocess.run(["node", "-e", script, os.path.join(ROOT, "dashboard", "core.js")], input=json.dumps({"cases": cases, "g": config.ADHERENCE_GRACE_MIN}),
                             capture_output=True, text=True, check=True).stdout
        py = [list(fallback.adherence_raise(c["p"], c["w"], c["l"])) for c in cases]
        self.assertEqual(json.loads(out), py)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_js_break_log_accumulates_and_resets_each_hour(self):
        script = ("const C=require(process.argv[1]);const t0=new Date(2026,10,4,9,0,30).getTime();"
                  "let r={hourKey:'',workedMs:0,since:null};r=C.startWork(r,t0);"
                  "const a=C.workedNow(r,t0+20*60000).minutes;r=C.startBreak(r,t0+20*60000);const b=C.workedNow(r,t0+50*60000).minutes;"
                  "r=C.startWork(r,t0+50*60000);const c=C.workedNow(r,t0+55*60000).minutes;"
                  "const d=C.workedNow(r,new Date(2026,10,4,10,5,0).getTime()).minutes;"   # crossed into the next hour while working
                  "console.log(JSON.stringify([a,b,c,d]));")
        out = json.loads(subprocess.run(["node", "-e", script, os.path.join(ROOT, "dashboard", "core.js")], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(out, [20, 20, 25, 5])


class GulfDay(unittest.TestCase):
    def _hotter(self, extra):
        return [dataclasses.replace(h, tdb_c=h.tdb_c + extra, tg_c=None) for h in SyntheticScenario("gulf_peak").hours()]

    def test_gate_hours_are_red_with_no_work_whatever_the_radiant_mode(self):
        """Library limit (4.8.0 docstring): air temperature 15 to 50 C. A day 5 C hotter than gulf_peak goes past it."""
        hrs = self._hotter(5.0)
        for mode in ("constant", "solar"):
            config.TR_FALLBACK_MODE = mode
            try: r = simulate_worker(StrainEngine(toy_phs), A["A01"], hrs, "planned", 1.0)
            finally: config.TR_FALLBACK_MODE = "solar"
            gated = [h for h in r.hourly if h["gate"]]
            self.assertTrue(gated, mode)
            self.assertTrue(all(h["level_max"] == "Red" and h["work_planned_min"] == 0 for h in gated), (mode, gated))

    def test_radiant_excess_above_60_is_gated(self):
        from heatbank.strain import validity
        self.assertEqual(validity.check_inputs(40.0, 100.5, 1.0, 40.0, 150.0, 0.5)[0], validity.ABOVE)
        self.assertEqual(validity.check_inputs(40.0, 99.0, 1.0, 40.0, 150.0, 0.5)[0], validity.OK)

    def test_tr_below_air_temp_is_raised_not_rejected(self):
        r = StrainEngine(toy_phs).run_segment(35.0, 30.0, 1.0, 50.0, 150.0, 0.5, 2, 100)
        self.assertEqual(r.status, "OK_CLAMPED"); self.assertFalse(r.fail_safe)

    def test_unmodified_gulf_day_is_inside_the_2023_limits_but_still_hard(self):
        r = simulate_worker(StrainEngine(toy_phs), A["A09"], SyntheticScenario("gulf_peak").hours(), "planned", 1.0)
        self.assertFalse(any(h["gate"] for h in r.hourly))

    def test_real_library_argument_conversion(self):
        seen = {}
        def spy(tdb, tr, v, rh, met, clo, posture, **kw): seen.update(met=met, posture=posture, **kw); return toy_phs(tdb, tr, v, rh, met * 58.15, clo, **{k: x for k, x in kw.items() if k in ("duration", "t_re")})
        e = StrainEngine(None); e._phs = spy       # behave as the real library: _real stays True
        e.run_segment(35.0, 45.0, 1.0, 50.0, 232.6, 0.9, 2, 100, 1, duration_min=60)
        self.assertEqual(seen["posture"], "standing"); self.assertAlmostEqual(seen["met"], 4.0, places=2)
        self.assertEqual(seen["model"], "7933-2023"); self.assertIs(seen["limit_inputs"], False); self.assertIs(seen["round_output"], False)

    def test_scenario_registered(self):
        self.assertIn("gulf_peak", SCENARIOS)


class SupervisorTiming(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_heavy_windows(self):
        script = ("const C=require(process.argv[1]);const H=['07','08','09','10','11','12'];"
                  "console.log(JSON.stringify([C.heavyWindows([0,1,2,3,1,0],H),C.heavyWindows([2,3,3,3,3,3],H),C.heavyWindows([0,0,0,0,0,0],H),C.heavyWindows([],[])]));")
        out = json.loads(subprocess.run(["node", "-e", script, os.path.join(ROOT, "dashboard", "core.js")], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(out, [[{"from": "07", "to": "09"}, {"from": "11", "to": "13"}], [], [{"from": "07", "to": "13"}], []])


class Escalation(unittest.TestCase):
    def test_tel_is_sanitised_and_never_invented(self):
        from heatbank.export import _clean_tel
        self.assertIsNone(_clean_tel(None)); self.assertIsNone(_clean_tel("")); self.assertIsNone(_clean_tel("ab"))
        self.assertEqual(_clean_tel("+66 (0) 2-123 4567"), "+6602123 4567".replace(" ", ""))
        self.assertEqual(_clean_tel('1669"><script>'), "1669")

    def test_pack_carries_medic_number_only_when_given(self):
        hrs = SyntheticScenario("cool").hours(); eng = StrainEngine(toy_phs)
        self.assertIsNone(build_pack(eng, hrs, build_archetypes()[:2], None, None, "TOY", "x")["escalation"]["medic_tel"])
        config.MEDIC_TEL = "1669"
        try: self.assertEqual(build_pack(eng, hrs, build_archetypes()[:2], None, None, "TOY", "x")["escalation"]["medic_tel"], "1669")
        finally: config.MEDIC_TEL = None


class Integration(unittest.TestCase):
    """Parts 1, 2 and 3 working together on the TOY model: weather -> pipeline -> tracker/planner -> pack -> front end."""
    def test_end_to_end_pack_is_consistent_with_the_simulation(self):
        eng = StrainEngine(toy_phs); hrs = SyntheticScenario("hot_humid").hours()
        pack = build_pack(eng, hrs, build_archetypes(), DEMO_ROSTER, DEMO_ZONES, "TOY", "synthetic:hot_humid")
        for a in build_archetypes():
            sim = simulate_worker(eng, a, hrs, "planned", 1.0)
            self.assertEqual([r["level_max"] for r in pack["plans"][a.id]], [r["level_max"] for r in sim.hourly])
        self.assertEqual(pack["adherence_grace_min"], config.ADHERENCE_GRACE_MIN)
        self.assertIn("state_line", pack["strings"]["th"])
        site_worst = [s["worst"] for s in pack["supervisor"]["site"]]
        for i, w in enumerate(site_worst):         # site status is the max over all archetypes in the roster, never lower than any zone
            for z in pack["supervisor"]["zones"]: self.assertGreaterEqual(w, z["hours"][i]["worst"])

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_pages_boot_in_a_fake_dom_and_every_control_works(self):
        d = tempfile.mkdtemp()
        try:
            shutil.copytree(os.path.join(ROOT, "dashboard"), os.path.join(d, "dashboard"))
            from heatbank.export import write_js
            write_js(build_pack(StrainEngine(toy_phs), SyntheticScenario("hot_humid").hours(), build_archetypes(), DEMO_ROSTER, DEMO_ZONES, "TOY", "synthetic:hot_humid"),
                     os.path.join(d, "dashboard", "data.js"))
            p = subprocess.run(["node", os.path.join(ROOT, "tests", "dom_smoke.js"), os.path.join(d, "dashboard")], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        finally: shutil.rmtree(d, ignore_errors=True)

    def test_v2_summary_has_new_diagnostics_and_covers_gulf(self):
        from heatbank.sim import run_v2
        d = tempfile.mkdtemp()
        try:
            import io, contextlib
            with contextlib.redirect_stdout(io.StringIO()): run_v2.run(True, [1.0], d)
            with open(os.path.join(d, "v2_summary.md"), encoding="utf-8") as fh: md = fh.read()
            for s in ("## gulf_peak", "A11 check", "Rest area assumed", "Sweat total carried"): self.assertIn(s, md)
        finally: shutil.rmtree(d, ignore_errors=True); config.REST_AREA = "shade"


if __name__ == "__main__":
    unittest.main()
