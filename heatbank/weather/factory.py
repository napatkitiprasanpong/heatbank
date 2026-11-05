"""Pick a weather provider from CLI-style arguments (one place, so every command behaves the same)."""
from .csv_provider import CsvProvider
from .open_meteo import OpenMeteoProvider
from .scenarios import SyntheticScenario
from .nasa_power import NasaPowerProvider


def make_provider(scenario=None, csv=None, csv_licence="", open_meteo=None, allow_noncommercial=False,
                  nasa_power=None, utc_offset_h=4.0, nasa_refresh=False, nasa_dir="data/real"):
    if scenario: return SyntheticScenario(scenario)
    if nasa_power:      # (lat, lon, "YYYY-MM-DD"): REAL weather replay, D8
        lat, lon, date = nasa_power
        return NasaPowerProvider(float(lat), float(lon), str(date), utc_offset_h, nasa_dir, nasa_refresh)
    if csv: return CsvProvider(csv, csv_licence)
    if open_meteo: return OpenMeteoProvider(*open_meteo, allow_noncommercial=allow_noncommercial)
    raise ValueError("choose a weather source: --scenario, --csv, --nasa-power or --open-meteo")
