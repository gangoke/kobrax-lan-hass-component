from __future__ import annotations

from homeassistant.components.camera import Camera, CameraEntityFeature

from .api import KobraXApiError
from .const import DOMAIN
from .entity import KobraXEntity


class KobraXCamera(KobraXEntity, Camera):
    _attr_supported_features = CameraEntityFeature.STREAM
    _attr_use_stream_for_stills = True

    def __init__(self, coordinator, entry, key: str, name: str) -> None:
        KobraXEntity.__init__(self, coordinator, entry, key, name)
        Camera.__init__(self)

    @property
    def is_streaming(self) -> bool:
        return bool(self.state_data.get("camera_url"))

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        camera_url = self.state_data.get("camera_url")
        attrs = {
            "camera_mjpeg_proxy_url": self.hass.data[DOMAIN][self._entry.entry_id]["api"].camera_stream_proxy_url(),
        }
        if isinstance(camera_url, str) and camera_url:
            attrs["camera_rtsp_url"] = camera_url
        return attrs

    async def stream_source(self) -> str | None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            await api.async_start_camera()
        except KobraXApiError:
            pass

        camera_url = self.state_data.get("camera_url")
        if isinstance(camera_url, str) and camera_url:
            return camera_url

        try:
            camera_url = await api.async_get_camera_url()
        except KobraXApiError:
            return api.camera_stream_proxy_url()

        return camera_url or api.camera_stream_proxy_url()

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            return await api.async_get_camera_snapshot()
        except KobraXApiError:
            return None


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([KobraXCamera(coordinator, entry, "camera", "Camera")])
