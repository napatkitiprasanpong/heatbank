"""v0.5.4 regression tests: missing-data fill values, multi-day files, stale cache. All run on the toy model (no library needed)."""
import csv, os, tempfile, unittest
from heatbank import config
from heatbank.alerts import engine as alerts
from heatbank.archetypes.archetypes import build_archetypes
from heatbank.sim.harness import simulate_worker
from heatbank.sim.toy_model import toy_phs
from heatbank.sim.tracker import ExposureTracker, work_conditions
from heatbank.strain import radiant
from heatbank.strain.phs_wrapper import StrainEngine
from heatbank.weather.csv_provider import CsvProvider
from heatbank.weather.scenarios import SyntheticScenario
from heatbank.weather.types import WeatherHour


def _level(engine, arch, h):
    rem, frac, fs = ExposureTracker(engine, arch).remaining_and_fraction(h)
    return alerts.compose(frac, fs).level


class FillValues(unittest.TestCase):
    def setUp(self):
        self.e = StrainEngine(toy_phs)
        self.a = build_archetypes()[8]

    def test_fill_value_air_temperature_is_failsafe_not_cold(self):
        for bad in (-999.0, -99.0, -9999.0, 200.0):
            h = WeatherHour("2026-07-15T12:00", bad, 50.0, 1.0, solar_wm2=800.0)
            self.assertEqual(_level(self.e, self.a, h), alerts.RED, bad)

    def test_fill_value_solar_is_unknown_not_night(self):
        self.assertEqual(radiant.tr_fallback(35.0, -999.0), radiant.tr_fallback(35.0, None))
        self.assertGreater(radiant.tr_fallback(35.0, -999.0), 35.0)
        self.assertEqual(radiant.tr_fallback(35.0, float("nan")), radiant.tr_fallback(35.0, None))

    def test_small_negative_solar_is_night(self):
        self.assertEqual(radiant.tr_fallback(30.0, -0.4), 30.0)

    def test_fill_value_globe_is_ignored(self):
        h = WeatherHour("2026-07-15T12:00", 35.0, 50.0, 1.0, solar_wm2=800.0, tg_c=-999.0)
        _, tr, _, _ = work_conditions(h)
        self.assertEqual(tr, radiant.tr_fallback(35.0, 800.0))

    def test_csv_fill_values(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "w.csv")
            with open(p, "w", newline="") as fh:
                w = csv.writer(fh); w.writerow(["time_iso", "tdb_c", "rh_pct", "wind_ms", "solar_wm2", "pressure_hpa", "tg_c"])
                w.writerow(["2026-07-15T12:00", "-999", "50", "1.0", "-999", "1005", ""])
                w.writerow(["2026-07-15T13:00", "36", "-999", "1.0", "900", "", ""])
            hs = CsvProvider(p, "test data, generated for this test").hours()
        self.assertNotEqual(hs[0].tdb_c, hs[0].tdb_c)         # NaN
        self.assertIsNone(hs[0].solar_wm2)
        self.assertNotEqual(hs[1].rh_pct, hs[1].rh_pct)       # NaN
        for h in hs:
            self.assertEqual(_level(self.e, self.a, h), alerts.RED)


class MultiDay(unittest.TestCase):
    def test_each_day_is_a_fresh_shift(self):
        e = StrainEngine(toy_phs)
        a = [x for x in build_archetypes() if x.task == "heavy"][0]
        d = lambda date: SyntheticScenario("hot_humid", date=date).hours()
        one = simulate_worker(e, a, d("2026-07-01"), "planned")
        three = simulate_worker(e, a, d("2026-07-01") + d("2026-07-02") + d("2026-07-03"), "planned")
        n = len(one.hourly)
        for k in range(3):
            self.assertEqual([h["work_planned_min"] for h in three.hourly[k * n:(k + 1) * n]],
                             [h["work_planned_min"] for h in one.hourly], f"day {k + 1}")



class Tools(unittest.TestCase):
    def test_nasa_parse_maps_fill_to_blank_and_kpa_to_hpa(self):
        import importlib.util
        sp = importlib.util.spec_from_file_location("fetch", os.path.join(os.path.dirname(__file__), "..", "scripts", "fetch_nasa_power.py"))
        m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
        pl = {"properties": {"parameter": {"T2M": {"2026070112": 38.2, "2026070113": -999}, "RH2M": {"2026070112": 41, "2026070113": 40},
              "WS2M": {"2026070112": 2.1, "2026070113": 2.0}, "ALLSKY_SFC_SW_DWN": {"2026070112": 900, "2026070113": -999}, "PS": {"2026070112": 100.5, "2026070113": 100.4}}}}
        r = m.parse(pl)
        self.assertEqual(r[0]["time_iso"], "2026-07-01T12:00"); self.assertEqual(r[0]["pressure_hpa"], 1005.0)
        self.assertEqual(r[1]["tdb_c"], ""); self.assertEqual(r[1]["solar_wm2"], "")

    def test_v4_selftest_if_library_present(self):
        try:
            import pythermalcomfort  # noqa
        except ImportError:
            self.skipTest("pythermalcomfort not installed")
        import importlib.util
        sp = importlib.util.spec_from_file_location("v4", os.path.join(os.path.dirname(__file__), "..", "scripts", "v4_compare.py"))
        m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
        self.assertEqual(m.selftest()["trials_gated"], 1)


if __name__ == "__main__":
    unittest.main()
