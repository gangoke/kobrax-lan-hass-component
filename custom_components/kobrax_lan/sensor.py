from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_registry import RegistryEntryDisabler

from .const import DOMAIN
from .entity import KobraXEntity


MAX_FILAMENT_SLOTS = 19
TOOLHEAD_SLOT_LIMIT = 4
ACE_DIRECT_SLOT_LIMIT = 4
MAX_ACE_UNITS = 4


def _detected_slot_limit(state_data: dict[str, Any]) -> int:
    mode = str(state_data.get("filament_mode") or "toolhead").lower()
    if mode == "toolhead":
        return TOOLHEAD_SLOT_LIMIT
    if mode == "ace_direct":
        return ACE_DIRECT_SLOT_LIMIT

    slots = state_data.get("ams_slots") or []
    if isinstance(slots, list) and slots:
        return min(len(slots), MAX_FILAMENT_SLOTS)
    return MAX_FILAMENT_SLOTS


def _detected_ace_unit_count(state_data: dict[str, Any]) -> int:
    units = state_data.get("ace_units") or []
    if isinstance(units, list):
        return min(len(units), MAX_ACE_UNITS)
    return 0


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
    KobraXSensorDescription(
        key="skip_object_count",
        name="Skip Object Count",
        value_key="skip_object_count",
        icon="mdi:vector-polygon",
    ),
    KobraXSensorDescription(
        key="skipped_object_count",
        name="Skipped Object Count",
        value_key="skipped_object_count",
        icon="mdi:content-cut",
    ),
    KobraXSensorDescription(
        key="filament_mode",
        name="Filament Mode",
        value_key="filament_mode",
        icon="mdi:shape-outline",
    ),
    KobraXSensorDescription(
        key="ace_unit_count",
        name="ACE Unit Count",
        value_key="ace_unit_count",
        icon="mdi:package-variant",
    ),
    KobraXSensorDescription(
        key="bridge_version",
        name="Bridge Version",
        value_key="version",
        icon="mdi:source-branch",
    ),
    KobraXSensorDescription(
        key="latest_available_version",
        name="Latest Available Version",
        value_key="latest_available_version",
        icon="mdi:cloud-download-outline",
    ),
)


class KobraXSensor(KobraXEntity, SensorEntity):
    entity_description: KobraXSensorDescription

    def __init__(self, coordinator, entry, description: KobraXSensorDescription) -> None:
        super().__init__(coordinator, entry, description.key, description.name)
        self.entity_description = description
        if description.value_key in ("version", "latest_available_version"):
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @staticmethod
    def _seconds_to_hhmmss(seconds: int) -> str:
        hours = seconds // 3600
        remaining_seconds = seconds % 3600
        minutes = remaining_seconds // 60
        secs = remaining_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    @property
    def native_value(self) -> Any:
        if self.entity_description.value_key == "filament_mode":
            return self.state_data.get("filament_mode")
        if self.entity_description.value_key == "ace_unit_count":
            units = self.state_data.get("ace_units")
            return len(units) if isinstance(units, list) else 0
        if self.entity_description.value_key == "latest_available_version":
            update_info = self.state_data.get("update_info") or {}
            if isinstance(update_info, dict):
                return update_info.get("latest")
            return None
        if self.entity_description.value_key == "skip_object_count":
            skip_state = self.state_data.get("skip_state") or {}
            objects = skip_state.get("objects") if isinstance(skip_state, dict) else []
            return len(objects) if isinstance(objects, list) else 0
        if self.entity_description.value_key == "skipped_object_count":
            skip_state = self.state_data.get("skip_state") or {}
            skipped = skip_state.get("skipped") if isinstance(skip_state, dict) else []
            return len(skipped) if isinstance(skipped, list) else 0

        value = self.state_data.get(self.entity_description.value_key)
        if self.entity_description.value_key == "progress" and value is not None:
            return round(float(value) * 100, 1)
        if self.entity_description.value_key in ("remain_time", "print_duration") and value is not None:
            try:
                return self._seconds_to_hhmmss(int(float(value)))
            except (TypeError, ValueError):
                return None
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.value_key == "latest_available_version":
            update_info = self.state_data.get("update_info")
            if isinstance(update_info, dict):
                return {
                    "current": update_info.get("current"),
                    "tag": update_info.get("tag"),
                    "update_available": update_info.get("update_available"),
                    "download_url": update_info.get("download_url"),
                }
            return None

        if self.entity_description.value_key not in ("skip_object_count", "skipped_object_count"):
            return None

        skip_state = self.state_data.get("skip_state")
        if not isinstance(skip_state, dict):
            return None

        objects = skip_state.get("objects")
        skipped = skip_state.get("skipped")
        return {
            "objects": objects if isinstance(objects, list) else [],
            "skipped": skipped if isinstance(skipped, list) else [],
            "filename": skip_state.get("filename"),
            "ts": skip_state.get("ts"),
        }


class KobraXAceDryerSensor(KobraXEntity, SensorEntity):
    """Per-ACE-unit dryer sensor."""
    
    def __init__(
        self,
        coordinator,
        entry,
        ace_id: int,
        sensor_type: str,  # "status", "humidity", "current_temp", "target_temp", "remaining_time"
    ) -> None:
        if sensor_type == "status":
            unique_key = f"ace_{ace_id}_dryer_status"
            name = f"ACE {ace_id + 1} Dryer Status"
            icon = "mdi:tumble-dryer"
        elif sensor_type == "humidity":
            unique_key = f"ace_{ace_id}_dryer_humidity"
            name = f"ACE {ace_id + 1} Dryer Humidity"
            icon = "mdi:water-percent"
        elif sensor_type == "current_temp":
            unique_key = f"ace_{ace_id}_dryer_current_temp"
            name = f"ACE {ace_id + 1} Dryer Current Temperature"
            icon = None
        elif sensor_type == "target_temp":
            unique_key = f"ace_{ace_id}_dryer_target_temp"
            name = f"ACE {ace_id + 1} Dryer Target Temperature"
            icon = None
        else:  # remaining_time
            unique_key = f"ace_{ace_id}_dryer_remaining_time"
            name = f"ACE {ace_id + 1} Dryer Remaining Time"
            icon = "mdi:timer-sand"

        super().__init__(coordinator, entry, unique_key, name)
        self._ace_id = ace_id
        self._sensor_type = sensor_type
        if icon:
            self._attr_icon = icon
        
        if sensor_type == "humidity":
            self._attr_native_unit_of_measurement = PERCENTAGE
        elif sensor_type in ("current_temp", "target_temp"):
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_suggested_unit_of_measurement = UnitOfTemperature.CELSIUS
        elif sensor_type == "remaining_time":
            pass  # HH:mm:ss format, no unit needed

    @staticmethod
    def _minutes_to_hhmmss(minutes: int) -> str:
        """Convert minutes to HH:mm:ss format."""
        total_seconds = minutes * 60
        hours = total_seconds // 3600
        remaining_seconds = total_seconds % 3600
        mins = remaining_seconds // 60
        secs = remaining_seconds % 60
        return f"{hours:02d}:{mins:02d}:{secs:02d}"

    @property
    def native_value(self) -> Any:
        drying = self.state_data.get("ace_drying") or {}
        
        # Handle per-unit structure: ace_drying[ace_id] or global structure
        if isinstance(drying, dict):
            # Try per-unit key first
            unit_data = drying.get(self._ace_id)
            if isinstance(unit_data, dict):
                drying = unit_data
            elif self._ace_id == 0 and not unit_data:
                # Fall back to global structure for unit 0
                pass
            else:
                # No data for this unit
                return None
        else:
            return None

        if self._sensor_type == "status":
            status = int(drying.get("status", 0)) if drying.get("status") is not None else 0
            return "running" if status else "idle"
        elif self._sensor_type == "humidity":
            humidity = drying.get("humidity")
            return round(float(humidity), 1) if humidity is not None else None
        elif self._sensor_type == "current_temp":
            current_temp = drying.get("current_temp")
            return round(float(current_temp), 1) if current_temp is not None else None
        elif self._sensor_type == "target_temp":
            target_temp = drying.get("target_temp")
            return float(target_temp) if target_temp is not None else None
        elif self._sensor_type == "remaining_time":
            remain = drying.get("remain_time")
            if remain is not None:
                try:
                    minutes = int(remain)
                    return self._minutes_to_hhmmss(minutes)
                except (TypeError, ValueError):
                    return None
            return None
        
        return None


class KobraXFilamentSlotSensor(KobraXEntity, SensorEntity):
    def __init__(self, coordinator, entry, slot_index: int) -> None:
        super().__init__(coordinator, entry, f"slot_{slot_index + 1}", f"Slot {slot_index + 1}")
        self._slot_index = slot_index
        self._attr_icon = "mdi:circle"

    def _slot(self) -> dict[str, Any]:
        slots = self.state_data.get("ams_slots") or []
        if not isinstance(slots, list) or self._slot_index >= len(slots):
            return {}
        slot = slots[self._slot_index]
        return slot if isinstance(slot, dict) else {}

    def _slot_limit_for_mode(self) -> int:
        return _detected_slot_limit(self.state_data)

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
        return self._slot_index < self._slot_limit_for_mode() and bool(self._slot()) and super().available

    @property
    def native_value(self) -> Any:
        slot = self._slot()
        if not slot:
            return "EMPTY"
        status = slot.get("status")
        if status is not None:
            try:
                if int(status) != 5:
                    return "EMPTY"
            except (TypeError, ValueError):
                return "EMPTY"
        material = slot.get("type")
        material_str = str(material).upper() if material else "EMPTY"
        color_hex = self._to_color_hex(slot.get("color"))
        if color_hex and material_str != "EMPTY":
            return f"{material_str} ({color_hex})"
        return material_str

    @property
    def icon_color(self) -> str | None:
        slot = self._slot()
        if not slot:
            return None
        return self._to_color_hex(slot.get("color"))

    @property
    def entity_picture(self) -> str | None:
        """Return a colored circle picture as a frontend fallback when icon tinting is ignored."""
        slot = self._slot()
        empty_svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
            "<circle cx='32' cy='32' r='28' fill='none' stroke='#666' stroke-width='4'/></svg>"
        )
        if not slot:
            return f"data:image/svg+xml;utf8,{quote(empty_svg)}"

        status = slot.get("status")
        if status is not None:
            try:
                if int(status) != 5:
                    return f"data:image/svg+xml;utf8,{quote(empty_svg)}"
            except (TypeError, ValueError):
                return f"data:image/svg+xml;utf8,{quote(empty_svg)}"

        color_hex = self._to_color_hex(slot.get("color"))
        if not color_hex:
            return f"data:image/svg+xml;utf8,{quote(empty_svg)}"

        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
            "<circle cx='32' cy='32' r='28' fill='"
            f"{color_hex}"
            "' stroke='#222' stroke-width='4'/></svg>"
        )
        return f"data:image/svg+xml;utf8,{quote(svg)}"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        slot = self._slot()
        if not slot:
            return None
        return {
            "color_hex": self._to_color_hex(slot.get("color")),
            "status": slot.get("status"),
            "box_id": slot.get("box_id"),
            "global_index": slot.get("global_index"),
            "activity": slot.get("activity"),
        }


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    filament_entities: list[SensorEntity] = []
    for slot_index in range(MAX_FILAMENT_SLOTS):
        filament_entities.append(KobraXFilamentSlotSensor(coordinator, entry, slot_index))

    ace_dryer_entities: list[SensorEntity] = []
    for ace_id in range(MAX_ACE_UNITS):
        for sensor_type in ("status", "humidity", "current_temp", "target_temp", "remaining_time"):
            ace_dryer_entities.append(KobraXAceDryerSensor(coordinator, entry, ace_id, sensor_type))

    entity_registry = er.async_get(hass)

    # Remove legacy single-unit ACE dryer sensors that were replaced by per-unit entities.
    legacy_ace_sensor_keys = (
        "ace_dryer_status",
        "ace_dryer_humidity",
        "ace_dryer_current_temp",
        "ace_dryer_target_temp",
        "ace_dryer_remaining_time",
    )
    for key in legacy_ace_sensor_keys:
        legacy_unique_id = f"{entry.entry_id}_{key}"
        legacy_entity_id = entity_registry.async_get_entity_id("sensor", DOMAIN, legacy_unique_id)
        if legacy_entity_id:
            entity_registry.async_remove(legacy_entity_id)

    @callback
    def _sync_slot_registry_state() -> None:
        state_data = coordinator.data or {}
        enabled_slots = _detected_slot_limit(state_data)

        for slot_index in range(MAX_FILAMENT_SLOTS):
            unique_id = f"{entry.entry_id}_slot_{slot_index + 1}"
            entity_id = entity_registry.async_get_entity_id("sensor", DOMAIN, unique_id)
            if not entity_id:
                continue

            reg_entry = entity_registry.async_get(entity_id)
            if reg_entry is None:
                continue

            should_enable = slot_index < enabled_slots
            if should_enable:
                if reg_entry.disabled_by == RegistryEntryDisabler.INTEGRATION:
                    entity_registry.async_update_entity(entity_id, disabled_by=None)
            else:
                if reg_entry.disabled_by is None:
                    entity_registry.async_update_entity(
                        entity_id,
                        disabled_by=RegistryEntryDisabler.INTEGRATION,
                    )

    async_add_entities(
        [
            KobraXSensor(coordinator, entry, description)
            for description in SENSORS
        ]
        + filament_entities
        + ace_dryer_entities
    )

    @callback
    def _sync_ace_registry_state() -> None:
        state_data = coordinator.data or {}
        enabled_ace_units = _detected_ace_unit_count(state_data)

        # Define all ACE entity patterns: (platform, unique_id_pattern_parts)
        ace_entities: list[tuple[str, str]] = []
        
        for ace_index in range(MAX_ACE_UNITS):
            # Switch entities
            ace_entities.append(("switch", f"{entry.entry_id}_ace_{ace_index}_auto_feed"))
            ace_entities.append(("switch", f"{entry.entry_id}_ace_{ace_index}_dryer"))
            
            # Number entities (temp + duration)
            ace_entities.append(("number", f"{entry.entry_id}_ace_{ace_index}_dry_target_temp"))
            ace_entities.append(("number", f"{entry.entry_id}_ace_{ace_index}_dry_duration"))
            
            # Button entities (start + stop)
            ace_entities.append(("button", f"{entry.entry_id}_ace_{ace_index}_dry_start"))
            ace_entities.append(("button", f"{entry.entry_id}_ace_{ace_index}_dry_stop"))
            
            # Sensor entities (status, humidity, current_temp, target_temp, remaining_time)
            ace_entities.append(("sensor", f"{entry.entry_id}_ace_{ace_index}_dryer_status"))
            ace_entities.append(("sensor", f"{entry.entry_id}_ace_{ace_index}_dryer_humidity"))
            ace_entities.append(("sensor", f"{entry.entry_id}_ace_{ace_index}_dryer_current_temp"))
            ace_entities.append(("sensor", f"{entry.entry_id}_ace_{ace_index}_dryer_target_temp"))
            ace_entities.append(("sensor", f"{entry.entry_id}_ace_{ace_index}_dryer_remaining_time"))

        for platform, unique_id in ace_entities:
            entity_id = entity_registry.async_get_entity_id(platform, DOMAIN, unique_id)
            if not entity_id:
                continue
            
            reg_entry = entity_registry.async_get(entity_id)
            if reg_entry is None:
                continue
            
            # Extract ace_index from unique_id
            parts = unique_id.split("_")
            if len(parts) >= 3:
                try:
                    ace_index = int(parts[2])
                except (ValueError, IndexError):
                    continue
            else:
                continue
            
            should_enable = ace_index < enabled_ace_units
            if should_enable:
                if reg_entry.disabled_by == RegistryEntryDisabler.INTEGRATION:
                    entity_registry.async_update_entity(entity_id, disabled_by=None)
            else:
                if reg_entry.disabled_by is None:
                    entity_registry.async_update_entity(
                        entity_id,
                        disabled_by=RegistryEntryDisabler.INTEGRATION,
                    )

    entry.async_on_unload(coordinator.async_add_listener(_sync_slot_registry_state))
    entry.async_on_unload(coordinator.async_add_listener(_sync_ace_registry_state))
    _sync_slot_registry_state()
    _sync_ace_registry_state()
