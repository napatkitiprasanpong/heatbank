"""Part 6: plain-language 'Why this level?' reasons (explainability). The pure functions live in dashboard/core.js, so they are
run through node like the other front-end parity tests. Reasons must be TRUE for the shown state and never mention a raise that
did not happen."""
import json, os, shutil, subprocess, unittest
from heatbank.i18n import strings

DASH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard")


def run(expr):
    script = "const C=require(process.argv[1]); const n=l=>['G','Y','O','R'][l]; console.log(JSON.stringify(" + expr + "))"
    return json.loads(subprocess.run(["node", "-e", script, os.path.join(DASH, "core.js")], capture_output=True, text=True, check=True).stdout)


@unittest.skipUnless(shutil.which("node"), "node not installed")
class Explain(unittest.TestCase):
    base = dict(haveForecast=True, planned=2, work=10, gate=False, stale=False, degraded=2, ageMin=20, maxAge=180, overdue=False, worked=0)

    def keys(self, **kw):
        o = dict(self.base, **kw)
        return [x["key"] for x in run("C.explainWorker(%s, n)" % json.dumps(o))]

    def test_each_band_has_its_own_reason(self):
        for lv in range(4): self.assertEqual(self.keys(planned=lv, degraded=lv), ["why_band_%d" % lv])

    def test_no_forecast_is_only_the_missing_data_reason(self):
        self.assertEqual(self.keys(haveForecast=False), ["why_no_data"])

    def test_stale_reason_only_when_it_actually_raised_the_level(self):
        self.assertEqual(self.keys(stale=True, planned=1, degraded=2), ["why_band_1", "why_stale"])
        self.assertEqual(self.keys(stale=True, planned=3, degraded=3), ["why_band_3"])

    def test_overdue_and_gate_reasons(self):
        self.assertIn("why_overdue", self.keys(overdue=True, worked=25))
        self.assertIn("why_gate", self.keys(gate=True, planned=3, degraded=3))

    def test_stale_reason_names_levels_and_ages(self):
        o = dict(self.base, stale=True, planned=1, degraded=2, ageMin=300)
        v = run("C.explainWorker(%s, n)" % json.dumps(o))[1]["vars"]
        self.assertEqual((v["from"], v["to"], v["age"], v["max"]), ("Y", "O", 300, 180))

    def test_zone_lists_counts_hottest_first_and_first_break(self):
        r = run("C.explainZone({haveForecast:true,counts:[2,3,4,0],worst:2,level:2,firstBreak:25,stale:false,ageMin:5,maxAge:180}, n)")
        self.assertEqual([x["key"] for x in r], ["why_zone", "why_zone_break"])
        self.assertEqual(r[0]["vars"]["list"], "4 O, 3 Y, 2 G")
        self.assertEqual(r[1]["vars"]["n"], 25)

    def test_site_reason_and_missing_data(self):
        self.assertEqual([x["key"] for x in run("C.explainSite({haveForecast:true,worst:1,level:1}, n)")], ["why_site"])
        self.assertEqual([x["key"] for x in run("C.explainSite({haveForecast:false}, n)")], ["why_no_data"])


class Strings(unittest.TestCase):
    def test_every_reason_key_exists_in_every_language(self):
        keys = ["why_title", "why_gate", "why_stale", "why_overdue", "why_no_data", "why_zone", "why_zone_break", "why_site"] + ["why_band_%d" % i for i in range(4)]
        for lang in strings.LANGS:
            for k in keys: self.assertTrue(strings.get(lang, k), (lang, k))

    def test_placeholders_match_between_languages(self):
        import re
        for k in ["why_band_2", "why_stale", "why_overdue", "why_zone", "why_zone_break"]:
            self.assertEqual(set(re.findall(r"\{(\w+)\}", strings.get("en", k))), set(re.findall(r"\{(\w+)\}", strings.get("th", k))), k)


if __name__ == "__main__":
    unittest.main()
