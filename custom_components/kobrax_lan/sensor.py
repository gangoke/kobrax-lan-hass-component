from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfTemperature

from .const import DOMAIN
from .entity import KobraXEntity


@dataclass(frozen=True, kw_only=True)
class KobraXSensorDescription(SensorEntityDescription):
    value_key: str


SENSORS: tuple[KobraXSensorDescription, ...] = (
    KobraXSensorDescription(
        key="state",
        name="State",
        value_key="kobra_state",
        icon="mdi:printer-3d",
    ),
    KobraXSensorDescription(
        key="print_state",
        name="Print State",
        value_key="print_state",
        icon="mdi:state-machine",
    ),
    KobraXSensorDescription(
        key="progress",
        name="Progress",
        value_key="progress",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:percent",
    ),
    KobraXSensorDescription(
        key="hotend_temp",
        name="Hotend Temperature",
        value_key="nozzle_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    KobraXSensorDescription(
        key="target_hotend_temp",
        name="Target Hotend Temperature",
        value_key="nozzle_target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    KobraXSensorDescription(
        key="bed_temp",
        name="Bed Temperature",
        value_key="bed_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    KobraXSensorDescription(
        key="target_bed_temp",
        name="Target Bed Temperature",
        value_key="bed_target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    KobraXSensorDescription(
        key="filename",
        name="Filename",
        value_key="filename",
        icon="mdi:file",
    ),
    KobraXSensorDescription(
        key="current_layer",
        name="Current Layer",
        value_key="curr_layer",
        icon="mdi:layers-triple",
    ),
    KobraXSensorDescription(
        key="total_layers",
        name="Total Layers",
        value_key="total_layers",
        icon="mdi:layers",
    ),
    KobraXSensorDescription(
        key="remaining_time",
        name="Remaining Time",
        value_key="remain_time",
        icon="mdi:timer-sand",
    ),
    KobraXSensorDescription(
        key="print_duration",
        name="Print Duration",
        value_key="print_duration",
        icon="mdi:timer-outline",
    ),
)


class KobraXSensor(KobraXEntity, SensorEntity):
    entity_description: KobraXSensorDescription

    def __init__(self, coordinator, entry, description: KobraXSensorDescription) -> None:
        super().__init__(coordinator, entry, description.key, description.name)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        value = self.state_data.get(self.entity_description.value_key)
        if self.entity_description.value_key == "progress" and value is not None:
            return round(float(value) * 100, 1)
        return value


class KobraXFilamentSlotSensor(KobraXEntity, SensorEntity):
    def __init__(self, coordinator, entry, slot_index: int, field: str) -> None:
        name_suffix = {
            "color": f"Filament Slot {slot_index + 1} Color",
            "type": f"Filament Slot {slot_index + 1} Type",
        }[field]
        super().__init__(coordinator, entry, f"filament_slot_{slot_index + 1}_{field}", name_suffix)
        self._slot_index = slot_index
        self._field = field

        if field == "color":
            self._attr_icon = "mdi:palette"
        elif field == "type":
            self._attr_icon = "mdi:label"
        else:
            self._attr_icon = "mdi:numeric"

    def _slot(self) -> dict[str, Any]:
        slots = self.state_data.get("ams_slots") or []
        if not isinstance(slots, list) or self._slot_index >= len(slots):
            return {}
        slot = slots[self._slot_index]
        return slot if isinstance(slot, dict) else {}

    @staticmethod
    def _to_color_hex(color: Any) -> str | None:
        if isinstance(color, list) and len(color) >= 3:
            try:
                return "#{:02X}{:02X}{:02X}".format(int(color[0]), int(color[1]), int(color[2]))
            except (TypeError, ValueError):
                return None
        if isinstance(color, str):
            cleaned = color.strip().lstrip("#")
            if len(cleaned) >= 6:
                return f"#{cleaned[:6].upper()}"
        return None

    @property
    def available(self) -> bool:
        return bool(self._slot()) and super().available

    @property
    def native_value(self) -> Any:
        slot = self._slot()
        if not slot:
            return None
        if self._field == "color":
            return self._to_color_hex(slot.get("color"))
        if self._field == "type":
            material = slot.get("type")
            return str(material).upper() if material else None
        return None


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    slots = coordinator.data.get("ams_slots") if coordinator.data else []
    slot_count = len(slots) if isinstance(slots, list) and len(slots) > 0 else 4

    filament_entities: list[SensorEntity] = []
    for slot_index in range(slot_count):
        for field in ("color", "type"):
            filament_entities.append(KobraXFilamentSlotSensor(coordinator, entry, slot_index, field))

    async_add_entities(
        [
            KobraXSensor(coordinator, entry, description)
            for description in SENSORS
        ]
        + filament_entities
    )
