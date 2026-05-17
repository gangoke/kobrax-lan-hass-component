from __future__ import annotations

import base64
import binascii

from homeassistant.components.image import ImageEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .entity import KobraXEntity


class KobraXGCodeImage(KobraXEntity, ImageEntity):
    def __init__(self, coordinator, entry, key: str, name: str) -> None:
        KobraXEntity.__init__(self, coordinator, entry, key, name)
        ImageEntity.__init__(self, coordinator.hass)
        self._attr_content_type = "image/png"

    async def async_image(self) -> bytes | None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        files = await api.async_get_files()
        if not files:
            return None

        active_filename = self.state_data.get("filename")
        selected = None
        if active_filename:
            selected = next((f for f in files if f.get("filename") == active_filename), None)
        if selected is None:
            selected = files[0]

        thumb_b64 = selected.get("thumbnail_b64")
        if not thumb_b64:
            return None

        try:
            image = base64.b64decode(thumb_b64, validate=True)
        except (ValueError, binascii.Error):
            return None

        self._attr_image_last_updated = dt_util.utcnow()
        return image


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([KobraXGCodeImage(coordinator, entry, "gcode_thumbnail", "GCode Thumbnail")])