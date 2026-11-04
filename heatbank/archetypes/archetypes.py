"""C4 worker archetypes: SIMULATED, team-generated, no identifiers, no real people (P3, D4).

Plan rule: archetype values must cite published sources. They do NOT yet. Every row carries
source_status='UNVERIFIED' and the 'basis' text says where the number should come from. Do not
present these as validated until each is checked (see unverified())."""
from dataclasses import dataclass
from typing import List

# PROPOSED metabolic classes, W/m2: from memory of ISO 8996 / ISO 7243 work classes (low, moderate, high). VERIFY.
MET = {"light": 100.0, "moderate": 165.0, "heavy": 230.0}
# PROPOSED clothing insulation, clo: typical light work clothing vs coverall/PPE. VERIFY against ISO 9920.
CLO = {"light_clothing": 0.5, "coverall_ppe": 0.9}
POSTURE_STANDING = 2   # pythermalcomfort posture code (UNVERIFIED mapping, U6)


@dataclass(frozen=True)
class Archetype:
    id: str
    task: str
    clothing: str
    acclimatized: bool
    met_wm2: float
    clo: float
    posture: int
    drink: int
    source_status: str
    basis: str

    @property
    def label(self) -> str:
        return f"{self.task} work, {self.clothing.replace('_', ' ')}, {'acclimatised' if self.acclimatized else 'not acclimatised'}"


def build_archetypes() -> List[Archetype]:
    out, n = [], 1
    for task in ("light", "moderate", "heavy"):
        for clothing in ("light_clothing", "coverall_ppe"):
            for acc in (True, False):
                out.append(Archetype(
                    id=f"A{n:02d}", task=task, clothing=clothing, acclimatized=acc, met_wm2=MET[task],
                    clo=CLO[clothing], posture=POSTURE_STANDING, drink=1, source_status="UNVERIFIED",
                    basis="met: ISO 8996/7243 class (check); clo: ISO 9920 (check); acclimatisation: PHS input"))
                n += 1
    return out


def unverified(archetypes: List[Archetype]) -> List[str]:
    return [a.id for a in archetypes if a.source_status != "VERIFIED"]
