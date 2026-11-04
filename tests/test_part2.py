import unittest
from heatbank import config
from heatbank.alerts import engine as alerts
from heatbank.archetypes.archetypes import build_archetypes
from heatbank.fallback import fallback
from heatbank.planner.planner import plan_hour, baseline_work_min, suggest_shift_windows
from heatbank.sim.harness import simulate_worker, lead_time
from heatbank.sim.toy_model import toy_phs
from heatbank.sim.tracker import ExposureTracker
from heatbank.sim import run_v3
from heatbank.strain.phs_wrapper import StrainEngine, self_check
from heatbank.weather.scenarios import SyntheticScenario


class Alerts(unittest.TestCase):
    def test_thresholds(self):
        f = alerts.level_from_fraction
        self.assertEqual([f(x) for x in (0, .49, .5, .74, .75, .99, 1, 1.5)], [0, 0, 1, 1, 2, 2, 3, 3])

    def test_failsafe_and_missing_are_red(self):
        self.assertEqual(alerts.compose(0.0, fail_safe=True).level, alerts.RED)
        self.assertEqual(alerts.compose(None).level, alerts.RED)

    def test_fallback_never_lowers(self):
        for f in (0.0, 0.3, 0.6, 0.8, 1.2):
            clean = alerts.compose(f).level
            for kw in run_v3.FAULTS.values():
                fs = fallback.evaluate(**kw)
                self.assertGreaterEqual(alerts.compose(f, fallback=fs).level, clean)

    def test_one_action_per_level(self):
        self.assertEqual(len({alerts.ACTIONS[l][0] for l in range(4)}), 4)


class Planner(unittest.TestCase):
    def test_p1_never_exceeds_baseline(self):
        for rem in (None, 0, 10, 40, 90, 200, 480):
            for fs in (False, True):
                for dg in (False, True):
                    p = plan_hour(rem, fail_safe=fs, degraded=dg)
                    self.assertLessEqual(p.work_min, p.baseline_work_min); self.assertEqual(p.work_min + p.rest_min, 60)

    def test_more_remaining_never_means_less_work(self):
        w = [baseline_work_min(r) for r in range(0, 481, 5)]
        self.assertEqual(w, sorted(w))

    def test_failsafe_plans_no_work(self):
        self.assertEqual(plan_hour(300, fail_safe=True).work_min, 0)

    def test_degraded_cap(self):
        self.assertLessEqual(plan_hour(480, degraded=True).work_min, config.DEGRADED_WORK_CAP_MIN)

    def test_windows(self):
        self.assertEqual(suggest_shift_windows([60, 60, 20, 10, 50, 60]), [(0, 1), (4, 5)])


class Fallback(unittest.TestCase):
    def test_detectors(self):
        self.assertTrue(fallback.frozen([30.0] * 6)); self.assertFalse(fallback.frozen([30.0, 30.1] * 4))
        self.assertTrue(fallback.spiked([30, 31, 45])); self.assertFalse(fallback.spiked([30, 31, 32]))

    def test_no_forecast_red_stale_orange(self):
        self.assertEqual(fallback.evaluate(None, have_forecast=False).apply(0), alerts.RED)
        self.assertGreaterEqual(fallback.evaluate(config.MAX_FORECAST_AGE_MIN + 5).apply(0), alerts.ORANGE)

    def test_v3_all_pass(self):
        self.assertTrue(run_v3.run())


class Sim(unittest.TestCase):
    def setUp(self):
        self.engine = StrainEngine(toy_phs)
        self.hours = SyntheticScenario("hot_humid").hours()
        self.arch = build_archetypes()[8]

    def test_tracker_fraction_rises_with_work_and_falls_with_rest(self):
        h = self.hours[12]; t = ExposureTracker(self.engine, self.arch)
        f0 = t.remaining_and_fraction(h)[1]
        for _ in range(6): t.step(h, 10, True)
        f1 = t.remaining_and_fraction(h)[1]
        for _ in range(6): t.step(h, 10, False)
        f2 = t.remaining_and_fraction(h)[1]
        self.assertLess(f0, f1); self.assertLess(f2, f1)

    def test_planned_not_worse_than_continuous(self):
        c = simulate_worker(self.engine, self.arch, self.hours, "continuous")
        p = simulate_worker(self.engine, self.arch, self.hours, "planned", 1.0)
        self.assertLessEqual(p.minutes_at["Red"], c.minutes_at["Red"])
        self.assertLessEqual(p.worked_min, c.worked_min)      # P1: plan never adds work

    def test_deterministic_seed(self):
        a = simulate_worker(self.engine, self.arch, self.hours, "planned", 0.7, seed=3)
        b = simulate_worker(self.engine, self.arch, self.hours, "planned", 0.7, seed=3)
        self.assertEqual(a, b)

    def test_self_check_flags_missing_kwarg(self):
        def bad(tdb, tr, v, rh, met, clo, posture): ...
        self.assertTrue(self_check(bad)); self.assertEqual(self_check(toy_phs), [])


class CoolClamp(unittest.TestCase):
    def test_cool_hour_is_computed_not_skipped(self):
        r = StrainEngine(toy_phs).run_segment(10, 12, 1, 60, 165, 0.5, 2, 100)
        self.assertEqual(r.status, "OK_CLAMPED"); self.assertIsNotNone(r.safe_minutes); self.assertFalse(r.fail_safe)

    def test_scenarios_stay_inside_radiant_limit(self):
        from heatbank.strain import radiant, validity
        for s in ("hot_humid", "hot_dry", "cool"):
            for h in SyntheticScenario(s).hours():
                tr = radiant.tr_from_globe(h.tg_c, h.tdb_c, h.wind_ms)
                self.assertLessEqual(tr, config.VALID_RANGES["tr_c"][1])


if __name__ == "__main__":
    unittest.main()
