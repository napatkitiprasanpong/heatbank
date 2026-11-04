from dataclasses import dataclass, asdict
from typing import Optional, Protocol, List


@dataclass
class WeatherHour:
    """One hour of site weather. All units SI-ish: C, %, m/s, W/m2, hPa."""
    time_iso: str                      # local or UTC ISO string, kept as given
    tdb_c: float
    rh_pct: float
    wind_ms: float
    solar_wm2: Optional[float] = None  # shortwave down, if known
    pressure_hpa: Optional[float] = None
    tg_c: Optional[float] = None       # black-globe temp (own node or synthetic), if known
    synthetic: bool = False            # True => team-generated scenario data (D4)

    def to_dict(self):
        return asdict(self)


class WeatherProvider(Protocol):
    name: str
    licence_note: str

    def hours(self) -> List[WeatherHour]: ...
