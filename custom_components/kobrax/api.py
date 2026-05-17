from __future__ import annotations

from typing import Any

import aiohttp


class KobraXApiError(Exception):
    """Raised when communication with KX-Bridge fails."""


class KobraXApiClient:
    def __init__(self, session: aiohttp.ClientSession, base_url: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    async def _get_json(self, path: str) -> dict[str, Any]:
        try:
            async with self._session.get(self._url(path)) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as err:
            raise KobraXApiError(err) from err

    async def _post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            async with self._session.post(self._url(path), json=body) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as err:
            raise KobraXApiError(err) from err

    async def async_check_version(self) -> dict[str, Any]:
        return await self._get_json("/api/version")

    async def async_get_state(self) -> dict[str, Any]:
        return await self._get_json("/api/state")

    async def async_pause_print(self) -> None:
        await self._post_json("/printer/print/pause", {})

    async def async_resume_print(self) -> None:
        await self._post_json("/printer/print/resume", {})

    async def async_cancel_print(self) -> None:
        await self._post_json("/printer/print/cancel", {})

    async def async_set_light(self, is_on: bool, brightness: int = 80) -> None:
        await self._post_json("/api/light", {"on": is_on, "brightness": brightness})

    async def async_set_speed_mode(self, mode: int) -> None:
        await self._post_json("/api/speed", {"mode": mode})

    async def async_set_temperature(self, nozzle: float | None, bed: float | None) -> None:
        payload: dict[str, Any] = {}
        if nozzle is not None:
            payload["nozzle"] = nozzle
        if bed is not None:
            payload["bed"] = bed
        if payload:
            await self._post_json("/api/temperature", payload)

    async def async_connect(self) -> None:
        await self._post_json("/api/connect", {})

    async def async_disconnect(self) -> None:
        await self._post_json("/api/disconnect", {})

    async def async_get_camera_snapshot(self) -> bytes:
        try:
            async with self._session.get(self._url("/api/camera/snapshot")) as response:
                response.raise_for_status()
                return await response.read()
        except Exception as err:
            raise KobraXApiError(err) from err
