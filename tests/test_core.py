import os, tempfile, unittest
from heatbank import config
from heatbank.archetypes.archetypes import build_archetypes, unverified
from heatbank.pipeline import run_day
from heatbank.strain import radiant, validity
from heatbank.strain.phs_wrapper import StrainEngine
from heatbank.weather import cache
from heatbank.weather.open_meteo import OpenMeteoProvider, LicenceGuardError, parse_response
from heatbank.weather.scenarios import SyntheticScenario
from tests.fakes import fake_phs, boom_phs


class Radiant(unittest.TestCase):
    def test_globe_equals_air_gives_air(self):
        self.assertAlmostEqual(radiant.tr_from_globe(30.0, 30.0, 1.0), 30.0, places=6)

    def test_hot_globe_gives_tr_above_globe(self):
        self.assertGreater(radiant.tr_from_globe(45.0, 35.0, 1.0), 45.0)


class Validity(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(validity.check_inputs(35, 45, 1, 50, 165, 0.5)[0], validity.OK)
    def test_above_range(self):
        self.assertEqual(validity.check_inputs(52, 45, 1, 50, 165, 0.5)[0], validity.ABOVE)
        self.assertEqual(validity.check_inputs(35, 45, 4, 50, 165, 0.5)[0], validity.ABOVE)
    def test_below_range(self):
        self.assertEqual(validity.check_inputs(10, 12, 1, 50, 165, 0.5)[0], validity.BELOW)
    def test_invalid(self):
        self.assertEqual(validity.check_inputs(float("nan"), 45, 1, 50, 165, 0.5)[0], validity.INVALID)
        self.assertEqual(validity.check_inputs(35, 45, 1, 120, 165, 0.5)[0], validity.INVALID)


class Engine(unittest.TestCase):
    def test_fail_safe_when_out_of_range(self):
        r = StrainEngine(fake_phs).run_segment(55, 60, 1, 30, 165, 0.5, 2, 100)
        self.assertTrue(r.fail_safe); self.assertEqual(r.safe_minutes, 0.0)

    def test_model_error_is_fail_safe(self):
        r = StrainEngine(boom_phs).run_segment(35, 45, 1, 50, 165, 0.5, 2, 100)
        self.assertEqual(r.status, "MODEL_ERROR"); self.assertTrue(r.fail_safe); self.assertEqual(r.safe_minutes, 0.0)

    def test_takes_conservative_limit(self):
        r = StrainEngine(fake_phs).run_segment(35, 45, 1, 50, 165, 0.5, 2, 100)
        self.assertEqual(r.limiting, "rectal temperature")
        self.assertAlmostEqual(r.safe_minutes, 480 - 40 * 10 - 0.5 * 65)

    def test_hotter_never_gives_more_minutes(self):
        e = StrainEngine(fake_phs)
        mins = [e.run_segment(t, 45, 1, 50, 165, 0.5, 2, 100).safe_minutes for t in (30, 35, 40, 45)]
        self.assertEqual(mins, sorted(mins, reverse=True))

    def test_state_carry_over_passed_to_model(self):
        seen = {}
        def spy(*a, **k): seen.update(k); return fake_phs(*a, **k)
        e = StrainEngine(spy)
        first = e.run_segment(35, 45, 1, 50, 165, 0.5, 2, 100, duration_min=30)
        e.run_segment(35, 45, 1, 50, 165, 0.5, 2, 100, duration_min=30, state=first.state)
        self.assertIn("t_re", seen)


class Weather(unittest.TestCase):
    def test_scenarios_are_synthetic_and_24h(self):
        for s in ("hot_humid", "hot_dry", "cool"):
            hs = SyntheticScenario(s).hours()
            self.assertEqual(len(hs), 24); self.assertTrue(all(h.synthetic for h in hs))
        self.assertGreater(max(h.tdb_c for h in SyntheticScenario("hot_dry").hours()),
                           max(h.tdb_c for h in SyntheticScenario("hot_humid").hours()))

    def test_open_meteo_blocked_without_opt_in(self):
        with self.assertRaises(LicenceGuardError): OpenMeteoProvider(13.7, 100.5)

    def test_open_meteo_parse_hand_made_payload(self):   # layout assumed, NOT from live API
        p = {"hourly": {"time": ["t0"], "temperature_2m": [30], "relative_humidity_2m": [60],
                        "wind_speed_10m": [1.2], "shortwave_radiation": [500], "surface_pressure": [1008]}}
        self.assertEqual(parse_response(p)[0].tdb_c, 30)

    def test_cache_freshness_and_missing(self):
        hs = SyntheticScenario("cool").hours()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "c.json")
            cache.save(path, "x", "note", hs, now=1000.0)
            _, age, fresh = cache.load(path, now=1000.0 + 60 * 10)
            self.assertTrue(fresh); self.assertAlmostEqual(age, 10.0)
            _, age, fresh = cache.load(path, now=1000.0 + 60 * (config.MAX_FORECAST_AGE_MIN + 1))
            self.assertFalse(fresh)
            self.assertEqual(cache.load(os.path.join(d, "none.json")), ([], float("inf"), False))


class Pipeline(unittest.TestCase):
    def test_runs_all_archetypes_all_hours(self):
        archs = build_archetypes()
        rows = run_day(SyntheticScenario("hot_humid").hours(), archs, StrainEngine(fake_phs))
        self.assertEqual(len(archs), 12); self.assertEqual(len(rows), 24 * 12)
        self.assertTrue(all(r["synthetic"] for r in rows))
        self.assertEqual(len(unverified(archs)), 12)   # nothing claimed as verified yet

    def test_cool_day_not_flagged_fail_safe_by_validity_only(self):
        rows = run_day(SyntheticScenario("cool").hours(), build_archetypes(), StrainEngine(fake_phs))
        self.assertFalse(any(r["fail_safe"] for r in rows))


@unittest.skipUnless(__import__("importlib").util.find_spec("pythermalcomfort"), "pythermalcomfort not installed")
class V1WrapperMatchesLibrary(unittest.TestCase):
    """V1 (partial): wrapper output must equal a direct library call. Uses the REAL library; kwarg names are U6."""
    def test_grid(self):
        from pythermalcomfort.models import phs
        from heatbank.strain.phs_wrapper import _get, LIMIT_FIELDS
        e = StrainEngine()
        for tdb, rh, met, clo in [(30, 50, 100, 0.5), (35, 60, 165, 0.5), (40, 30, 230, 0.9), (45, 20, 165, 0.7)]:
            r = e.run_segment(tdb, tdb + 10, 1.0, rh, met, clo, 2, 100)
            lib = phs(tdb, tdb + 10, 1.0, rh, met, clo, 2, acclimatized=100, drink=1, duration=480)
            exp = min(_get(lib, LIMIT_FIELDS["tre"]), _get(lib, LIMIT_FIELDS["loss95"]), 480.0)
            self.assertAlmostEqual(r.safe_minutes, exp, places=6)


if __name__ == "__main__":
    unittest.main()
