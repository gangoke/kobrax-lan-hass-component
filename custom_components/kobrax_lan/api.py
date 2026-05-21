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

    def camera_stream_proxy_url(self) -> str:
        return self._url("/api/camera/stream")

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

    async def async_get_files(self) -> list[dict[str, Any]]:
        data = await self._get_json("/kx/files")
        result = data.get("result", [])
        if isinstance(result, list):
            return result
        raise KobraXApiError("Unexpected response for /kx/files")

    async def async_get_file_objects(self, file_id: str) -> dict[str, Any]:
        data = await self._get_json(f"/kx/files/{file_id}/objects")
        result = data.get("result", {})
        if isinstance(result, dict):
            return result
        raise KobraXApiError("Unexpected response for /kx/files/{id}/objects")

    async def async_skip_objects(self, names: list[str]) -> dict[str, Any]:
        data = await self._post_json("/kx/skip", {"names": names})
        result = data.get("result")
        if result is None:
            raise KobraXApiError("Unexpected response for /kx/skip")
        return data

    async def async_skip_query(self) -> dict[str, Any]:
        data = await self._post_json("/kx/skip/query", {})
        result = data.get("result", {})
        if isinstance(result, dict):
            return result
        raise KobraXApiError("Unexpected response for /kx/skip/query")

    async def async_get_skip_state(self) -> dict[str, Any]:
        data = await self._get_json("/kx/skip/state")
        result = data.get("result", {})
        if isinstance(result, dict):
            return result
        raise KobraXApiError("Unexpected response for /kx/skip/state")

    async def async_set_ace_auto_feed(self, ace_id: int, on: bool) -> dict[str, Any]:
        data = await self._post_json("/api/ace/auto_feed", {"ace_id": ace_id, "on": on})
        result = data.get("result")
        if result is None:
            raise KobraXApiError("Unexpected response for /api/ace/auto_feed")
        return data

    async def async_set_ace_dry(
        self,
        action: str,
        target_temp: int | None = None,
        duration: int | None = None,
        ace_id: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"action": action}
        if target_temp is not None:
            payload["target_temp"] = int(target_temp)
        if duration is not None:
            payload["duration"] = int(duration)
        if ace_id is not None:
            payload["ace_id"] = int(ace_id)

        data = await self._post_json("/api/ace/dry", payload)
        result = data.get("result")
        if result is None:
            raise KobraXApiError("Unexpected response for /api/ace/dry")
        return data

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

    async def async_restart_bridge(self) -> None:
        await self._post_json("/api/restart", {})

    async def async_start_camera(self) -> None:
        await self._post_json("/api/camera/start", {})

    async def async_stop_camera(self) -> None:
        await self._post_json("/api/camera/stop", {})

    async def async_check_updates(self) -> dict[str, Any]:
        return await self._get_json("/api/update/check")

    async def async_apply_update(self, tag: str, download_url: str) -> dict[str, Any]:
        return await self._post_json(
            "/api/update/apply",
            {"tag": tag, "download_url": download_url},
        )

    async def async_get_camera_url(self) -> str | None:
        data = await self._get_json("/api/camera")
        url = data.get("url")
        if url is None or isinstance(url, str):
            return url
        raise KobraXApiError("Unexpected response for /api/camera")

    async def async_get_camera_snapshot(self) -> bytes:
        try:
            async with self._session.get(self._url("/api/camera/snapshot")) as response:
                response.raise_for_status()
                return await response.read()
        except Exception as err:
            raise KobraXApiError(err) from err
