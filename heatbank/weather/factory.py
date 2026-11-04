"""Pick a weather provider from CLI-style arguments (one place, so every command behaves the same)."""
from .csv_provider import CsvProvider
from .open_meteo import OpenMeteoProvider
from .scenarios import SyntheticScenario


def make_provider(scenario=None, csv=None, csv_licence="", open_meteo=None, allow_noncommercial=False):
    if scenario: return SyntheticScenario(scenario)
    if csv: return CsvProvider(csv, csv_licence)
    if open_meteo: return OpenMeteoProvider(*open_meteo, allow_noncommercial=allow_noncommercial)
    raise ValueError("choose a weather source: --scenario, --csv or --open-meteo")
