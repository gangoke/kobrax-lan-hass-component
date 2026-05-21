from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity

from .const import DOMAIN
from .entity import KobraXEntity


def _minutes_to_hhmmss(minutes: int | float) -> str:
    """Convert minutes to HH:mm:ss format."""
    total_seconds = int(minutes * 60)
    hours = total_seconds // 3600
    remaining_seconds = total_seconds % 3600
    mins = remaining_seconds // 60
    secs = remaining_seconds % 60
    return f"{hours:02d}:{mins:02d}:{secs:02d}"


class KobraXAceDryConfigNumber(KobraXEntity, NumberEntity):
    def __init__(
        self,
        coordinator,
        entry,
        ace_id: int,
        config_type: str,  # "target_temp" or "duration"
    ) -> None:
        if config_type == "target_temp":
            unique_key = f"ace_{ace_id}_dry_target_temp"
            name = f"ACE {ace_id + 1} Dryer Target Temperature"
            min_val, max_val, step_val = 30, 80, 1
            unit = "°C"
            icon = "mdi:thermometer"
        else:  # duration
            unique_key = f"ace_{ace_id}_dry_duration"
            name = f"ACE {ace_id + 1} Dryer Duration"
            min_val, max_val, step_val = 10, 1440, 1
            unit = "min"
            icon = "mdi:timer-cog-outline"

        super().__init__(coordinator, entry, unique_key, name)
        self._ace_id = ace_id
        self._config_type = config_type
        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = step_val
        self._attr_native_unit_of_measurement = unit
        self._attr_mode = "box"
        self._attr_icon = icon

    @property
    def native_value(self) -> float:
        cfg = self.hass.data[DOMAIN][self._entry.entry_id]["ace_dry_config"]
        ace_cfg = cfg.get(self._ace_id) or {}
        key = "target_temp" if self._config_type == "target_temp" else "duration"
        if self._config_type == "target_temp":
            return float(ace_cfg.get(key, 45))
        else:
            return float(ace_cfg.get(key, 240))

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self._config_type != "duration":
            return None
        cfg = self.hass.data[DOMAIN][self._entry.entry_id]["ace_dry_config"]
        ace_cfg = cfg.get(self._ace_id) or {}
        duration_minutes = ace_cfg.get("duration", 240)
        return {"formatted_duration": _minutes_to_hhmmss(duration_minutes)}

    async def async_set_native_value(self, value: float) -> None:
        cfg = self.hass.data[DOMAIN][self._entry.entry_id]["ace_dry_config"]
        if self._ace_id not in cfg:
            cfg[self._ace_id] = {}
        key = "target_temp" if self._config_type == "target_temp" else "duration"
        cfg[self._ace_id][key] = int(round(value))
        self.async_write_ha_state()


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    # Initialize ace_dry_config structure if not present
    if "ace_dry_config" not in hass.data[DOMAIN][entry.entry_id]:
        hass.data[DOMAIN][entry.entry_id]["ace_dry_config"] = {}
    
    # Pre-create all 8 numbers (target_temp + duration for each of 4 ACE units)
    entities = []
    for ace_id in range(4):
        entities.append(KobraXAceDryConfigNumber(coordinator, entry, ace_id, "target_temp"))
        entities.append(KobraXAceDryConfigNumber(coordinator, entry, ace_id, "duration"))
    
    async_add_entities(entities)
