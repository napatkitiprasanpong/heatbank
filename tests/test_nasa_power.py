"""D8 NASA POWER adapter tests.

IMPORTANT: the build sandbox could not reach NASA. Every payload below is a FIXTURE that mimics the documented layout of the
POWER hourly JSON response ({"properties": {"parameter": {NAME: {"YYYYMMDDHH": value}}}}, fill value -999). It is not real
data and proves nothing about real weather. It proves the parsing, unit, time-zone, fill-value, caching and labelling logic.
The first real download on the owner's machine is the real test of the layout assumption."""
import io, json, math, os, shutil, subprocess, tempfile, unittest, urllib.error, urllib.request
from unittest import mock

from heatbank.weather import nasa_power as npw
from heatbank.weather.factory import make_provider


def fixture_payload(days=("20250714", "20250715", "20250716"), ps_units="kPa", sw_units="W/m^2", hole=None, fill=-999.0):
    """3 UTC days of smooth diurnal values. hole = (param, 'YYYYMMDDHH') puts a fill value there."""
    par = {k: {} for k in npw.PARAMS}
    for d in days:
        for hh in range(24):
            s = f"{d}{hh:02d}"
            loc = (hh + 4) % 24                                   # local solar-ish clock for a +4 h place
            par["T2M"][s] = round(33 + 9 * math.sin(math.pi * (loc - 6) / 12) if 6 <= loc <= 18 else 30.0, 2)
            par["RH2M"][s] = 40.0
            par["WS10M"][s] = 3.0
            par["PS"][s] = 100.2                                  # kPa
            par["ALLSKY_SFC_SW_DWN"][s] = round(max(0.0, 900 * math.sin(math.pi * (loc - 6) / 12)), 1) if 6 <= loc <= 18 else 0.0
    if hole: par[hole[0]][hole[1]] = fill
    return {"type": "Feature", "properties": {"parameter": par}, "header": {"fill_value": fill},
            "parameters": {"T2M": {"units": "C"}, "RH2M": {"units": "%"}, "WS10M": {"units": "m/s"},
                           "PS": {"units": ps_units}, "ALLSKY_SFC_SW_DWN": {"units": sw_units}}}


class Parse(unittest.TestCase):
    def test_utc_to_local_day_and_units(self):
        hs = npw.parse_response(fixture_payload(), 4.0, "2025-07-15")
        self.assertEqual(len(hs), 24)
        self.assertEqual(hs[0].time_iso, "2025-07-15T00:00"); self.assertEqual(hs[-1].time_iso, "2025-07-15T23:00")
        self.assertAlmostEqual(hs[0].pressure_hpa, 1002.0, places=3)          # kPa -> hPa
        self.assertTrue(all(h.synthetic is False and h.tg_c is None for h in hs))   # real weather, and no globe temperature invented
        self.assertGreater(max(h.solar_wm2 for h in hs), 800)

    def test_local_midnight_crossing_uses_both_utc_days(self):
        # local 00:00 on the 15th is 20:00 UTC on the 14th at +4: it must come from the previous UTC day
        hs = npw.parse_response(fixture_payload(), 4.0, "2025-07-15")
        self.assertEqual([h.time_iso[11:13] for h in hs[:3]], ["00", "01", "02"])

    def test_negative_offset(self):
        hs = npw.parse_response(fixture_payload(), -5.0, "2025-07-15")
        self.assertEqual(len(hs), 24)

    def test_fill_value_is_never_used_or_interpolated(self):
        with self.assertRaises(npw.NasaPowerError) as c:
            npw.parse_response(fixture_payload(hole=("T2M", "2025071506")), 4.0, "2025-07-15")
        self.assertIn("10:00", str(c.exception)); self.assertIn("never invent", str(c.exception))

    def test_missing_solar_hour_also_refuses(self):
        with self.assertRaises(npw.NasaPowerError):
            npw.parse_response(fixture_payload(hole=("ALLSKY_SFC_SW_DWN", "2025071508")), 4.0, "2025-07-15")

    def test_unknown_unit_is_refused_not_guessed(self):
        with self.assertRaises(npw.NasaPowerError) as c:
            npw.parse_response(fixture_payload(sw_units="MJ/m^2/day"), 4.0, "2025-07-15")
        self.assertIn("refusing to guess", str(c.exception))

    def test_pressure_in_hpa_is_not_multiplied(self):
        p = fixture_payload(ps_units="hPa"); p["properties"]["parameter"]["PS"] = {k: 1002.0 for k in p["properties"]["parameter"]["PS"]}
        self.assertAlmostEqual(npw.parse_response(p, 4.0, "2025-07-15")[5].pressure_hpa, 1002.0, places=3)

    def test_unexpected_layout_names_what_was_found(self):
        with self.assertRaises(npw.NasaPowerError) as c: npw.parse_response({"features": []}, 4.0, "2025-07-15")
        self.assertIn("features", str(c.exception))

    def test_missing_parameter_is_reported(self):
        p = fixture_payload(); del p["properties"]["parameter"]["WS10M"]
        with self.assertRaises(npw.NasaPowerError) as c: npw.parse_response(p, 4.0, "2025-07-15")
        self.assertIn("WS10M", str(c.exception))

    def test_date_outside_response_gives_clear_error(self):
        with self.assertRaises(npw.NasaPowerError): npw.parse_response(fixture_payload(), 4.0, "2024-01-01")

    def test_rh_clamped_and_solar_never_negative(self):
        p = fixture_payload(); p["properties"]["parameter"]["RH2M"]["2025071510"] = 101.5; p["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]["2025071510"] = -0.2
        hs = npw.parse_response(p, 4.0, "2025-07-15"); h = [x for x in hs if x.time_iso.endswith("14:00")][0]
        self.assertEqual(h.rh_pct, 100.0); self.assertEqual(h.solar_wm2, 0.0)


class Provider(unittest.TestCase):
    def setUp(self): self.d = tempfile.mkdtemp()
    def tearDown(self): shutil.rmtree(self.d, ignore_errors=True)

    def _prov(self, **kw): return npw.NasaPowerProvider(24.45, 54.38, "2025-07-15", 4.0, self.d, **kw)

    def test_request_url_is_what_the_api_page_documents(self):
        u = self._prov().request_url()
        for s in ("power.larc.nasa.gov/api/temporal/hourly/point", "parameters=T2M%2CRH2M%2CWS10M%2CPS%2CALLSKY_SFC_SW_DWN",
                  "time-standard=UTC", "start=20250714", "end=20250716", "format=JSON", "latitude=24.45", "longitude=54.38"):
            self.assertIn(s, u)

    def test_download_saves_raw_before_parsing_then_works_offline(self):
        class R(io.BytesIO):
            def __enter__(s): return s
            def __exit__(s, *a): return False
        with mock.patch.object(urllib.request, "urlopen", lambda *a, **k: R(json.dumps(fixture_payload()).encode())):
            p = self._prov(); hs = p.hours()
        self.assertEqual(len(hs), 24); self.assertTrue(os.path.exists(p.cache_path)); self.assertIsNotNone(p.retrieved_utc)
        with open(p.cache_path) as fh: saved = json.load(fh)
        self.assertIn("credit", saved); self.assertIn("request_url", saved)
        def boom(*a, **k): raise AssertionError("network used although a saved copy exists")
        with mock.patch.object(urllib.request, "urlopen", boom):
            self.assertEqual(len(self._prov().hours()), 24)                   # offline-first (P5)

    def test_layout_surprise_still_keeps_the_raw_file(self):
        class R(io.BytesIO):
            def __enter__(s): return s
            def __exit__(s, *a): return False
        with mock.patch.object(urllib.request, "urlopen", lambda *a, **k: R(b'{"surprise": 1}')):
            p = self._prov()
            with self.assertRaises(npw.NasaPowerError): p.hours()
        self.assertTrue(os.path.exists(p.cache_path))

    def test_http_error_is_clear_and_not_retried(self):
        calls = []
        def err(*a, **k):
            calls.append(1); raise urllib.error.HTTPError("u", 422, "bad", {}, io.BytesIO(b"parameter not available"))
        with mock.patch.object(urllib.request, "urlopen", err):
            with self.assertRaises(npw.NasaPowerError) as c: self._prov().hours()
        self.assertIn("422", str(c.exception)); self.assertEqual(len(calls), 1)

    def test_no_network_gives_a_helpful_message(self):
        with mock.patch.object(urllib.request, "urlopen", side_effect=urllib.error.URLError("down")), mock.patch("time.sleep"):
            with self.assertRaises(npw.NasaPowerError) as c: self._prov().hours()
        self.assertIn("internet", str(c.exception))

    def test_bad_inputs_fail_early(self):
        with self.assertRaises(ValueError): npw.NasaPowerProvider(95, 0, "2025-07-15")
        with self.assertRaises(ValueError): npw.NasaPowerProvider(0, 0, "15/07/2025")

    def test_factory_and_licence_note_cite_nasa(self):
        p = make_provider(None, nasa_power=("24.45", "54.38", "2025-07-15"), nasa_dir=self.d)
        self.assertIsInstance(p, npw.NasaPowerProvider); self.assertIn("NASA", p.licence_note); self.assertIn("NOT a forecast", p.licence_note)


class Labelling(unittest.TestCase):
    """Real weather must never be presented as live, and the crew/clock must still be labelled simulated."""
    def _pack(self):
        from heatbank.archetypes.archetypes import build_archetypes
        from heatbank.export import build_pack, DEMO_ROSTER, DEMO_ZONES
        from heatbank.sim.toy_model import toy_phs
        from heatbank.strain.phs_wrapper import StrainEngine
        hours = npw.parse_response(fixture_payload(), 4.0, "2025-07-15")
        return build_pack(StrainEngine(toy_phs), hours, build_archetypes(), DEMO_ROSTER, DEMO_ZONES, "TOY", "nasa-power:test", True,
                          weather_real=True, attribution=npw.CREDIT)

    def test_provenance_flags(self):
        p = self._pack()["provenance"]
        self.assertTrue(p["synthetic"])            # crew and clock are still simulated
        self.assertTrue(p["weather_real"]); self.assertIn("NASA", p["attribution"]); self.assertEqual(p["weather_date"], "2025-07-15")

    def test_strings_exist_in_both_languages(self):
        s = self._pack()["strings"]
        for lang in ("en", "th"):
            for k in ("banner_demo_realwx", "simulated_realwx"): self.assertIn("{date}", s[lang][k])

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_pages_boot_with_real_weather_labels(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        d = tempfile.mkdtemp()
        try:
            shutil.copytree(os.path.join(root, "dashboard"), os.path.join(d, "dashboard"))
            from heatbank.export import write_js
            write_js(self._pack(), os.path.join(d, "dashboard", "data.js"))
            p = subprocess.run(["node", os.path.join(root, "tests", "dom_smoke.js"), os.path.join(d, "dashboard")], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        finally: shutil.rmtree(d, ignore_errors=True)

    def test_v2_with_a_real_day_adds_a_labelled_scenario(self):
        import contextlib
        from heatbank.sim import run_v2
        d = tempfile.mkdtemp(); tmp = tempfile.mkdtemp()
        try:
            class Fake:
                name = "nasa-power:test"; licence_note = npw.NasaPowerProvider.licence_note
                def hours(self): return npw.parse_response(fixture_payload(), 4.0, "2025-07-15")
            with contextlib.redirect_stdout(io.StringIO()): run_v2.run(True, [1.0], d, real_provider=Fake())
            with open(os.path.join(d, "v2_summary.md"), encoding="utf-8") as fh: md = fh.read()
            self.assertIn("## real_day", md); self.assertIn("REAL weather", md); self.assertIn("SIMULATED", md)
        finally: shutil.rmtree(d, ignore_errors=True); shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()


class NoSilentSubstitution(unittest.TestCase):
    def test_real_day_never_falls_back_to_another_days_cache(self):
        """Regression: with no saved copy and no network, the CLI used the generic last_forecast cache (another day) under the new date's label."""
        import argparse
        from heatbank import cli
        from heatbank.weather import cache as wcache
        d = tempfile.mkdtemp()
        try:
            other_day = npw.parse_response(fixture_payload(), 4.0, "2025-07-15")
            last = os.path.join(d, "last_forecast.json"); wcache.save(last, "x", "y", other_day)
            a = argparse.Namespace(scenario=None, csv=None, csv_licence="", open_meteo=None, allow_noncommercial=False,
                                   nasa_power=["24.45", "54.38", "2025-07-16"], utc_offset=4.0, nasa_refresh=False, cache=last)
            with mock.patch.object(urllib.request, "urlopen", side_effect=urllib.error.URLError("down")), mock.patch("time.sleep"), \
                 mock.patch("heatbank.weather.nasa_power.NasaPowerProvider.cache_path", new=os.path.join(d, "none.json")):
                with self.assertRaises(SystemExit) as c: cli._hours(a)
            self.assertIn("could not get the real weather", str(c.exception))
        finally: shutil.rmtree(d, ignore_errors=True)
