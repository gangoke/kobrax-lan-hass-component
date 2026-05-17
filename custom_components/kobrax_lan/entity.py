from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER


class KobraXEntity(CoordinatorEntity):
    def __init__(self, coordinator, entry, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = f"{entry.data['printer_name']} {name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=MANUFACTURER,
            model="Kobra X",
            name=entry.data["printer_name"],
            configuration_url=entry.data.get("host"),
        )

    @property
    def state_data(self) -> dict:
        return self.coordinator.data or {}
