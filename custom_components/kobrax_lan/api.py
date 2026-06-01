from __future__ import annotations

import logging
from typing import Any

import aiohttp


_LOGGER = logging.getLogger(__name__)


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

    def camera_h264_proxy_url(self) -> str:
        return self._url("/api/camera/h264")

    async def async_h264_stream_available(self, timeout_seconds: float = 1.5) -> bool:
        """Probe whether the bridge h264 endpoint is reachable now."""
        try:
            timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            async with self._session.get(self.camera_h264_proxy_url(), timeout=timeout) as response:
                if response.status != 200:
                    return False
                chunk = await response.content.read(1)
                return bool(chunk)
        except Exception:
            return False

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

    async def async_get_settings(self) -> dict[str, Any]:
        data = await self._get_json("/api/settings")
        if isinstance(data, dict):
            return data
        raise KobraXApiError("Unexpected response for /api/settings")

    async def async_set_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = await self._post_json("/api/settings", payload)
        if isinstance(data, dict):
            return data
        raise KobraXApiError("Unexpected response for /api/settings")

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

    async def async_get_filament_slots(self) -> list[dict[str, Any]]:
        data = await self._get_json("/kx/filament/slots")
        result = data.get("result", [])
        if isinstance(result, list):
            return [slot for slot in result if isinstance(slot, dict)]
        raise KobraXApiError("Unexpected response for /kx/filament/slots")

    async def async_get_filament_profiles(self, material_type: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if material_type:
            params["type"] = material_type

        try:
            async with self._session.get(self._url("/kx/filament/profiles"), params=params or None) as response:
                response.raise_for_status()
                data = await response.json()
        except Exception as err:
            raise KobraXApiError(err) from err

        result = data.get("result", []) if isinstance(data, dict) else []
        if isinstance(result, list):
            return [profile for profile in result if isinstance(profile, dict)]
        raise KobraXApiError("Unexpected response for /kx/filament/profiles")

    async def async_set_filament_slot_profile(
        self,
        slot_index: int,
        filament_id: str,
        vendor: str = "",
        name: str = "",
    ) -> dict[str, Any]:
        data = await self._post_json(
            f"/kx/filament/slots/{int(slot_index)}/profile",
            {"id": filament_id, "vendor": vendor, "name": name},
        )
        if isinstance(data, dict):
            return data
        raise KobraXApiError("Unexpected response for /kx/filament/slots/{idx}/profile")

    async def async_set_ace_auto_feed(self, ace_id: int, on: bool) -> dict[str, Any]:
        data = await self._post_json("/api/ace/auto_feed", {"ace_id": ace_id, "on": on})
        if data.get("error") not in (None, ""):
            raise KobraXApiError(str(data["error"]))
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

        try:
            data = await self._post_json("/api/ace/dry", payload)
        except KobraXApiError as err:
            # Some bridge versions can return a false 502 while setDry is
            # still applied successfully on the printer.
            msg = str(err)
            if "502" in msg and "/api/ace/dry" in msg:
                _LOGGER.warning("Ignoring bridge 502 for /api/ace/dry because command may already be applied: %s", msg)
                return {"result": "ok", "warning": "ignored_502"}
            raise

        if data.get("error") not in (None, ""):
            raise KobraXApiError(str(data["error"]))
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
