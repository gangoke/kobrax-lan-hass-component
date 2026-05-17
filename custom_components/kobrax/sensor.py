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
    ),
    KobraXSensorDescription(
        key="target_hotend_temp",
        name="Target Hotend Temperature",
        value_key="nozzle_target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
    ),
    KobraXSensorDescription(
        key="bed_temp",
        name="Bed Temperature",
        value_key="bed_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    KobraXSensorDescription(
        key="target_bed_temp",
        name="Target Bed Temperature",
        value_key="bed_target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
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
        entity_registry_enabled_default=False,
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
        entity_registry_enabled_default=False,
    ),
)


class KobraXSensor(KobraXEntity, SensorEntity):
    entity_description: KobraXSensorDescription

    @property
    def native_value(self) -> Any:
        value = self.state_data.get(self.entity_description.value_key)
        if self.entity_description.value_key == "progress" and value is not None:
            return round(float(value) * 100, 1)
        return value


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [
            KobraXSensor(coordinator, entry, description.key, description.name)
            for description in SENSORS
        ]
    )
