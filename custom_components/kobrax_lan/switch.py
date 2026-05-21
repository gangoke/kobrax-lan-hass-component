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

    async def async_turn_off(self, **kwargs) -> None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            await api.async_set_ace_auto_feed(self._ace_id, False)
            await self.coordinator.async_request_refresh()
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Pre-create switches for all 4 possible ACE units
    async_add_entities(
        [KobraXAceAutoFeedSwitch(coordinator, entry, ace_id) for ace_id in range(4)]
    )
