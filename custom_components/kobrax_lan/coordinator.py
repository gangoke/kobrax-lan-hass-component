from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KobraXApiClient, KobraXApiError
from .const import DOMAIN, UPDATE_INTERVAL


class KobraXCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, api: KobraXApiClient) -> None:
        super().__init__(
            hass,
            logger=hass.data[DOMAIN]["logger"],
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_get_state()
        except KobraXApiError as err:
            raise UpdateFailed(str(err)) from err
