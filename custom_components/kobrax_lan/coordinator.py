from __future__ import annotations

import time
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KobraXApiClient, KobraXApiError
from .const import DOMAIN, UPDATE_CHECK_INTERVAL, UPDATE_INTERVAL


class KobraXCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, api: KobraXApiClient) -> None:
        super().__init__(
            hass,
            logger=hass.data[DOMAIN]["logger"],
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self._update_info: dict[str, Any] = {}
        self._restart_supported: bool | None = None
        self._next_update_check_monotonic = 0.0

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            # Probe restart endpoint once if not checked
            if self._restart_supported is None:
                try:
                    await self.api.async_restart_bridge()
                    self._restart_supported = True
                except Exception as err:
                    # Only disable if 404/501, otherwise treat as available
                    msg = str(err)
                    if "404" in msg or "501" in msg:
                        self._restart_supported = False
                    else:
                        self._restart_supported = True
            state = await self.api.async_get_state()

            now = time.monotonic()
            if now >= self._next_update_check_monotonic:
                try:
                    self._update_info = await self.api.async_check_updates()
                except KobraXApiError:
                    # Keep integration polling resilient if update service is temporarily unavailable.
                    pass
                self._next_update_check_monotonic = now + UPDATE_CHECK_INTERVAL.total_seconds()

            if self._update_info:
                state["update_info"] = self._update_info
            try:
                skip_state = await self.api.async_get_skip_state()
                state["skip_state"] = skip_state
            except KobraXApiError:
                # Skip endpoints are only available on newer bridge versions.
                pass
            return state
        except KobraXApiError as err:
            raise UpdateFailed(str(err)) from err

    async def async_check_updates(self) -> dict[str, Any]:
        try:
            update_info = await self.api.async_check_updates()
        except KobraXApiError as err:
            raise UpdateFailed(str(err)) from err

        self._update_info = update_info
        merged = dict(self.data or {})
        merged["update_info"] = update_info
        self.async_set_updated_data(merged)
        return update_info

    async def async_apply_update(self) -> dict[str, Any]:
        update_info = self._update_info or await self.async_check_updates()
        tag = str(update_info.get("tag") or "").strip()
        download_url = str(update_info.get("download_url") or "").strip()
        if not tag or not download_url:
            raise UpdateFailed("Missing tag or download URL from update check")

        try:
            result = await self.api.async_apply_update(tag=tag, download_url=download_url)
        except KobraXApiError as err:
            raise UpdateFailed(str(err)) from err

        self._update_info = {**update_info, "last_apply_result": result}
        merged = dict(self.data or {})
        merged["update_info"] = self._update_info
        self.async_set_updated_data(merged)
        return result
