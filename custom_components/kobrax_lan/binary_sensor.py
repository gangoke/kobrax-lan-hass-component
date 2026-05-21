from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import KobraXEntity


@dataclass(frozen=True, kw_only=True)
class KobraXBinaryDescription(BinarySensorEntityDescription):
    value_key: str


BINARY_SENSORS: tuple[KobraXBinaryDescription, ...] = (
    KobraXBinaryDescription(
        key="online",
        name="Online",
        value_key="kobra_state",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    KobraXBinaryDescription(
        key="printing",
        name="Printing",
        value_key="print_state",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    KobraXBinaryDescription(
        key="light",
        name="Light State",
        value_key="light_on",
        icon="mdi:lightbulb",
    ),
)


class KobraXBinarySensor(KobraXEntity, BinarySensorEntity):
    entity_description: KobraXBinaryDescription

    def __init__(self, coordinator, entry, description: KobraXBinaryDescription) -> None:
        super().__init__(coordinator, entry, description.key, description.name)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        if self.entity_description.value_key == "kobra_state":
            return str(self.state_data.get("kobra_state", "")).lower() != "offline"
        if self.entity_description.value_key == "print_state":
            return str(self.state_data.get("print_state", "")).lower() == "printing"
        return bool(self.state_data.get(self.entity_description.value_key, False))


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [
            KobraXBinarySensor(coordinator, entry, description)
            for description in BINARY_SENSORS
        ]
    )
