from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import ServiceValidationError

from .api import KobraXApiError
from .const import DOMAIN
from .entity import KobraXEntity


class KobraXPrintSpeedSelect(KobraXEntity, SelectEntity):
    _attr_options = ["Slow (1)", "Normal (2)", "Fast (3)"]

    def _mode_to_option(self, mode: int | None) -> str:
        mapping = {
            1: "Slow (1)",
            2: "Normal (2)",
            3: "Fast (3)",
        }
        return mapping.get(mode or 2, "Normal (2)")

    @property
    def current_option(self) -> str:
        mode = self.state_data.get("print_speed_mode")
        return self._mode_to_option(int(mode) if mode is not None else None)

    async def async_select_option(self, option: str) -> None:
        mode = int(option.split("(")[-1].replace(")", ""))
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            await api.async_set_speed_mode(mode)
            await self.coordinator.async_request_refresh()
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [KobraXPrintSpeedSelect(coordinator, entry, "print_speed_mode", "Print Speed")]
    )
