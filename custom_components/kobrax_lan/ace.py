from __future__ import annotations

from typing import Any


def ace_unit_dryer_data(state_data: dict[str, Any], ace_id: int) -> dict[str, Any] | None:
    """Return the dryer payload for one ACE unit.

    Bridge >= 0.9.28 reports ``ace_drying`` as a flat object (the "primary" unit)
    plus ``units: [{id, ...}]`` with one entry per ACE. Older bridges used a dict
    keyed by unit id (int or str) or only the flat object for unit 0.
    """
    drying = state_data.get("ace_drying")
    if not isinstance(drying, dict):
        return None

    units = drying.get("units")
    if isinstance(units, list):
        for unit in units:
            if not isinstance(unit, dict):
                continue
            try:
                if int(unit.get("id", -1)) == ace_id:
                    return unit
            except (TypeError, ValueError):
                continue
        # A per-unit list is authoritative: no entry means no data for this unit.
        return None

    unit_data = drying.get(ace_id)
    if unit_data is None:
        unit_data = drying.get(str(ace_id))
    if isinstance(unit_data, dict):
        return unit_data
    if ace_id == 0:
        return drying
    return None
