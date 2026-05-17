from __future__ import annotations

from homeassistant.components.camera import Camera

from .api import KobraXApiError
from .const import DOMAIN
from .entity import KobraXEntity


class KobraXCamera(KobraXEntity, Camera):
    def __init__(self, coordinator, entry, key: str, name: str) -> None:
        KobraXEntity.__init__(self, coordinator, entry, key, name)
        Camera.__init__(self)

    @property
    def is_streaming(self) -> bool:
        return bool(self.state_data.get("camera_url"))

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            return await api.async_get_camera_snapshot()
        except KobraXApiError:
            return None


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([KobraXCamera(coordinator, entry, "camera", "Camera")])
