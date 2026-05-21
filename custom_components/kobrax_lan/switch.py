from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import ServiceValidationError

from .api import KobraXApiError
from .const import DOMAIN
from .entity import KobraXEntity


class KobraXAceAutoFeedSwitch(KobraXEntity, SwitchEntity):
    def __init__(self, coordinator, entry, ace_id: int) -> None:
        super().__init__(coordinator, entry, f"ace_{ace_id}_auto_feed", f"ACE {ace_id + 1} Auto Fill")
        self._ace_id = ace_id
        self._attr_icon = "mdi:autorenew"

    @property
    def is_on(self) -> bool:
        auto_feed = self.state_data.get("ace_auto_feed") or {}
        if not isinstance(auto_feed, dict):
            return False
        value = auto_feed.get(self._ace_id)
        if value is None:
            value = auto_feed.get(str(self._ace_id))
        return bool(value)

    async def async_turn_on(self, **kwargs) -> None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            await api.async_set_ace_auto_feed(self._ace_id, True)
            await self.coordinator.async_request_refresh()
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err


class KobraXAceDryerSwitch(KobraXEntity, SwitchEntity):
    def __init__(self, coordinator, entry, ace_id: int) -> None:
        super().__init__(coordinator, entry, f"ace_{ace_id}_dryer", f"ACE {ace_id + 1} Dryer")
        self._ace_id = ace_id
        self._attr_icon = "mdi:tumble-dryer"

    @property
    def is_on(self) -> bool:
        drying = self.state_data.get("ace_drying") or {}
        if not isinstance(drying, dict):
            return False

        unit_data = drying.get(self._ace_id)
        if unit_data is None:
            unit_data = drying.get(str(self._ace_id))

        if isinstance(unit_data, dict):
            status = unit_data.get("status")
        elif self._ace_id == 0:
            # Backward-compatible fallback: older bridge payloads may expose unit 0 as a flat object.
            status = drying.get("status")
        else:
            status = None

        try:
            return int(status) > 0 if status is not None else False
        except (TypeError, ValueError):
            return False

    async def async_turn_on(self, **kwargs) -> None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            cfg = self.hass.data[DOMAIN][self._entry.entry_id]["ace_dry_config"]
            ace_cfg = cfg.get(self._ace_id) or {}
            await api.async_set_ace_dry(
                "start",
                target_temp=int(ace_cfg.get("target_temp", 45)),
                duration=int(ace_cfg.get("duration", 240)),
                ace_id=self._ace_id,
            )
            await self.coordinator.async_request_refresh()
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err

    async def async_turn_off(self, **kwargs) -> None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            await api.async_set_ace_dry("stop", ace_id=self._ace_id)
            await self.coordinator.async_request_refresh()
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []

    # Pre-create switches for all 4 possible ACE units
    entities.extend(KobraXAceAutoFeedSwitch(coordinator, entry, ace_id) for ace_id in range(4))
    entities.extend(KobraXAceDryerSwitch(coordinator, entry, ace_id) for ace_id in range(4))

    async_add_entities(entities)
