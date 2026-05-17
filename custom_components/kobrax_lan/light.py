from __future__ import annotations

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.exceptions import ServiceValidationError

from .api import KobraXApiError
from .const import DOMAIN
from .entity import KobraXEntity


class KobraXLight(KobraXEntity, LightEntity):
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    @property
    def is_on(self) -> bool:
        return bool(self.state_data.get("light_on", False))

    async def async_turn_on(self, **kwargs) -> None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            await api.async_set_light(True)
            await self.coordinator.async_request_refresh()
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err

    async def async_turn_off(self, **kwargs) -> None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            await api.async_set_light(False)
            await self.coordinator.async_request_refresh()
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([KobraXLight(coordinator, entry, "light", "Light")])
