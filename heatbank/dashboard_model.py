"""C8 supervisor aggregation with a minimum group size k (plan R5, R3, C8).

Design decisions (see docs/AUDIT.md, A5 and A6):
* The supervisor view is built from CREW GROUPS in the task roster (zone x worker type x headcount), not from reports sent by
  individual phones. There is therefore no per-device upload channel at all, and nothing to re-identify.
* A zone with fewer than k people is never shown alone. Small zones are pooled; a pool that is still below k is dropped from
  the table and only feeds the site status.
* SAFETY OVERRIDE: suppression never hides a hazard. The site status is the highest level of ANY crew group, shown as a
  level and an action with no count and no zone, so a single Red group cannot disappear into a '<k' cell.
Levels here are model outputs for task groups (weather + task + PPE + acclimatisation), not measurements of people."""
from typing import Dict, List
from . import config

ZONE_POOLED = "_pooled"


def aggregate(roster: Dict[str, Dict[str, int]], zone_names: Dict[str, str], per_arch: Dict[str, List[dict]],
              k: int = None) -> dict:
    """roster: zone_id -> {archetype_id: headcount}. per_arch: archetype_id -> hourly rows (from simulate_worker).
    Returns {'k', 'hours', 'site': [...], 'zones': [...], 'pooled_groups': int}. No names anywhere."""
    k = config.DASH_MIN_GROUP_K if k is None else k
    n_hours = len(next(iter(per_arch.values())))
    hours = [r["hour"] for r in next(iter(per_arch.values()))]
    names = {"Green": 0, "Yellow": 1, "Orange": 2, "Red": 3}

    def zone_hours(members: Dict[str, int]):
        out = []
        for i in range(n_hours):
            counts, worst, brk, rot = [0, 0, 0, 0], 0, 60, False
            for aid, n in members.items():
                if n <= 0: continue
                row = per_arch[aid][i]
                lvl = names[row["level_max"]]
                counts[lvl] += n; worst = max(worst, lvl)
                brk = min(brk, row["work_planned_min"]); rot = rot or bool(row.get("rotate"))
            out.append({"hour": hours[i], "counts": counts, "worst": worst,
                        "first_break_min": None if brk >= 60 else brk, "rotate": rot})
        return out

    sizes = {z: sum(m.values()) for z, m in roster.items()}
    listed = {z: m for z, m in roster.items() if sizes[z] >= k}
    small = {z: m for z, m in roster.items() if 0 < sizes[z] < k}
    pooled: Dict[str, int] = {}
    for m in small.values():
        for aid, n in m.items(): pooled[aid] = pooled.get(aid, 0) + n
    zones = [{"id": z, "name": zone_names.get(z, z), "n": sizes[z], "hours": zone_hours(m)} for z, m in listed.items()]
    pool_n = sum(pooled.values())
    if pool_n >= k:
        zones.append({"id": ZONE_POOLED, "name": None, "n": pool_n, "hours": zone_hours(pooled)})
    # site status: worst level of ANY group, including pooled-away ones. No counts.
    everyone: Dict[str, int] = {}
    for m in roster.values():
        for aid, n in m.items(): everyone[aid] = everyone.get(aid, 0) + n
    site = [{"hour": h["hour"], "worst": h["worst"], "rotate": h["rotate"]} for h in zone_hours(everyone)]
    return {"k": k, "hours": hours, "site": site, "zones": zones, "pooled_groups": len(small)}


def leaks_small_group(agg: dict) -> bool:
    """Self-check used by tests: True if any listed zone is smaller than k (it must never happen)."""
    return any(z["n"] < agg["k"] for z in agg["zones"])
