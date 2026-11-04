import json, os, tempfile, unittest
from heatbank import cli
from heatbank.planner.planner import suggest_shift_windows


class CliSmoke(unittest.TestCase):
    def test_plan_toy_writes_files_with_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            cli.main(["plan", "--scenario", "hot_humid", "--toy", "--archetype", "A09", "--out", d, "--cache", os.path.join(d, "c.json")])
            self.assertTrue(os.path.exists(os.path.join(d, "shift_plan.md")))
            meta = json.load(open(os.path.join(d, "shift_plan.csv.meta.json")))
            self.assertTrue(meta["synthetic_data"]); self.assertIn("TOY", meta["strain_model"]); self.assertIn("Not a medical device", meta["disclaimer"])

    def test_safe_minutes_toy(self):
        with tempfile.TemporaryDirectory() as d:
            cli.main(["safe-minutes", "--scenario", "cool", "--toy", "--out", d, "--cache", os.path.join(d, "c.json")])
            self.assertGreater(len(open(os.path.join(d, "safe_minutes.csv")).read().splitlines()), 24 * 12)

    def test_open_meteo_refused_without_opt_in(self):
        from heatbank.weather.open_meteo import LicenceGuardError
        with self.assertRaises(LicenceGuardError):
            cli.main(["safe-minutes", "--open-meteo", "13.7", "100.5", "--toy"])

    def test_faults_command_passes(self):
        with self.assertRaises(SystemExit) as cm: cli.main(["faults"])
        self.assertEqual(cm.exception.code, 0)

    def test_windows_helper(self):
        self.assertEqual(suggest_shift_windows([60, 20, 50]), [(0, 0), (2, 2)])


if __name__ == "__main__":
    unittest.main()
