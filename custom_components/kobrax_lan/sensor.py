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
    # Compatibility aliases used by the kobrax-lan-card (ported from anycubic card)
    KobraXSensorDescription(
        key="job_state",
        name="Job State",
        value_key="print_state",
        icon="mdi:state-machine",
    ),
    KobraXSensorDescription(
        key="current_status",
        name="Current Status",
        value_key="print_state",
        icon="mdi:information-outline",
    ),
    KobraXSensorDescription(
        key="job_progress",
        name="Job Progress",
        value_key="progress",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:percent",
    ),
    KobraXSensorDescription(
        key="job_time_elapsed",
        name="Job Time Elapsed",
        value_key="print_duration",
        icon="mdi:timer-outline",
    ),
    KobraXSensorDescription(
        key="job_time_remaining",
        name="Job Time Remaining",
        value_key="remain_time",
        icon="mdi:timer-sand",
    ),
    KobraXSensorDescription(
        key="hotbed_temperature",
        name="Hotbed Temperature",
        value_key="bed_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    KobraXSensorDescription(
        key="nozzle_temperature",
        name="Nozzle Temperature",
        value_key="nozzle_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    KobraXSensorDescription(
        key="target_hotbed_temperature",
        name="Target Hotbed Temperature",
        value_key="bed_target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    KobraXSensorDescription(
        key="target_nozzle_temperature",
        name="Target Nozzle Temperature",
        value_key="nozzle_target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    KobraXSensorDescription(
        key="job_name",
        name="Job Name",
        value_key="filename",
        icon="mdi:file",
    ),
    KobraXSensorDescription(
        key="job_current_layer",
        name="Job Current Layer",
        value_key="curr_layer",
        icon="mdi:layers-triple",
    ),
    KobraXSensorDescription(
        key="job_total_layers",
        name="Job Total Layers",
        value_key="total_layers",
        icon="mdi:layers",
    ),
    KobraXSensorDescription(
        key="job_speed_mode",
        name="Job Speed Mode",
        value_key="print_speed_mode",
        icon="mdi:speedometer",
    ),
    KobraXSensorDescription(
        key="fan_speed",
        name="Fan Speed",
        value_key="fan_speed",
        icon="mdi:fan",
    ),
    KobraXSensorDescription(
        key="ace_spools",
        name="ACE Spools",
        value_key="ams_slots",
        icon="mdi:palette-swatch",
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
        if self.entity_description.key in {"progress", "job_progress"} and value is not None:
            return round(float(value) * 100, 1)
        if self.entity_description.key == "job_speed_mode":
            mode = int(value) if value is not None else 2
            mapping = {1: "Slow", 2: "Normal", 3: "Fast"}
            return mapping.get(mode, "Normal")
        if self.entity_description.key == "ace_spools":
            return "active" if isinstance(value, list) and len(value) > 0 else "inactive"
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key == "current_status":
            material_type = self.state_data.get("material_type") or "Filament"
            return {"material_type": material_type}

        if self.entity_description.key == "job_speed_mode":
            mode = int(self.state_data.get("print_speed_mode") or 2)
            return {
                "available_modes": [
                    {"mode": 1, "description": "Slow"},
                    {"mode": 2, "description": "Normal"},
                    {"mode": 3, "description": "Fast"},
                ],
                "print_speed_mode_code": mode,
            }

        if self.entity_description.key in {"target_nozzle_temperature", "target_hotbed_temperature"}:
            return {
                "limit_min": 0,
                "limit_max": 400 if self.entity_description.key == "target_nozzle_temperature" else 200,
            }

        if self.entity_description.key == "ace_spools":
            slots = self.state_data.get("ams_slots")
            return {"slots": slots if isinstance(slots, list) else []}

        return None


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
