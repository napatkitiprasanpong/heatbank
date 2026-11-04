"""Every output file gets a sidecar <file>.meta.json declaring where it came from (plan P4: transparency)."""
import json, datetime
from . import __version__

DISCLAIMER = ("Planning-stage prototype. Not a medical device. Thresholds are PROPOSED design parameters, "
              "not clinical guidance. Simulated results are not real-world validation.")


def write_meta(path: str, *, source: str, licence_note: str, synthetic: bool, model: str, extra: dict = None):
    meta = {"file": path, "heatbank_version": __version__, "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "weather_source": source, "licence_note": licence_note, "synthetic_data": synthetic, "strain_model": model,
            "disclaimer": DISCLAIMER}
    meta.update(extra or {})
    with open(path + ".meta.json", "w") as fh:
        json.dump(meta, fh, indent=2)
