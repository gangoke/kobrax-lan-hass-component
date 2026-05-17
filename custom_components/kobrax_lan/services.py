from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .api import KobraXApiError
from .const import DOMAIN

SERVICE_CHANGE_PRINT_SPEED_MODE = "change_print_speed_mode"
SERVICE_CHANGE_PRINT_TARGET_NOZZLE_TEMPERATURE = "change_print_target_nozzle_temperature"
SERVICE_CHANGE_PRINT_TARGET_HOTBED_TEMPERATURE = "change_print_target_hotbed_temperature"

ATTR_CONFIG_ENTRY = "config_entry"
ATTR_DEVICE_ID = "device_id"
ATTR_PRINTER_ID = "printer_id"
ATTR_SPEED_MODE = "speed_mode"
ATTR_TEMPERATURE = "temperature"

SERVICE_SCHEMAS: dict[str, vol.Schema] = {
    SERVICE_CHANGE_PRINT_SPEED_MODE: vol.Schema(
        {
            vol.Optional(ATTR_CONFIG_ENTRY): cv.string,
            vol.Optional(ATTR_DEVICE_ID): cv.string,
            vol.Optional(ATTR_PRINTER_ID): vol.Any(cv.positive_int, cv.string),
            vol.Required(ATTR_SPEED_MODE): vol.All(vol.Coerce(int), vol.Range(min=1, max=3)),
        }
    ),
    SERVICE_CHANGE_PRINT_TARGET_NOZZLE_TEMPERATURE: vol.Schema(
        {
            vol.Optional(ATTR_CONFIG_ENTRY): cv.string,
            vol.Optional(ATTR_DEVICE_ID): cv.string,
            vol.Optional(ATTR_PRINTER_ID): vol.Any(cv.positive_int, cv.string),
            vol.Required(ATTR_TEMPERATURE): vol.All(vol.Coerce(float), vol.Range(min=0, max=400)),
        }
    ),
    SERVICE_CHANGE_PRINT_TARGET_HOTBED_TEMPERATURE: vol.Schema(
        {
            vol.Optional(ATTR_CONFIG_ENTRY): cv.string,
            vol.Optional(ATTR_DEVICE_ID): cv.string,
            vol.Optional(ATTR_PRINTER_ID): vol.Any(cv.positive_int, cv.string),
            vol.Required(ATTR_TEMPERATURE): vol.All(vol.Coerce(float), vol.Range(min=0, max=200)),
        }
    ),
}


def _resolve_entry_id(hass: HomeAssistant, call: ServiceCall) -> str:
    requested = call.data.get(ATTR_CONFIG_ENTRY)
    domain_data = hass.data.get(DOMAIN, {})

    if requested:
        if requested in domain_data:
            return requested
        raise ServiceValidationError(f"Unknown config_entry for {DOMAIN}: {requested}")

    entry_ids = [entry_id for entry_id, value in domain_data.items() if isinstance(value, dict) and "api" in value]
    if len(entry_ids) == 1:
        return entry_ids[0]

    raise ServiceValidationError(
        "Multiple Kobra X LAN entries loaded. Include config_entry in the service call."
    )


async def _handle_change_print_speed_mode(hass: HomeAssistant, call: ServiceCall) -> None:
    entry_id = _resolve_entry_id(hass, call)
    api = hass.data[DOMAIN][entry_id]["api"]
    coordinator = hass.data[DOMAIN][entry_id]["coordinator"]

    mode = int(call.data[ATTR_SPEED_MODE])

    try:
        await api.async_set_speed_mode(mode)
        await coordinator.async_request_refresh()
    except KobraXApiError as err:
        raise HomeAssistantError(str(err)) from err


async def _handle_change_print_target_nozzle_temperature(hass: HomeAssistant, call: ServiceCall) -> None:
    entry_id = _resolve_entry_id(hass, call)
    api = hass.data[DOMAIN][entry_id]["api"]
    coordinator = hass.data[DOMAIN][entry_id]["coordinator"]

    temperature = float(call.data[ATTR_TEMPERATURE])

    try:
        await api.async_set_temperature(nozzle=temperature, bed=None)
        await coordinator.async_request_refresh()
    except KobraXApiError as err:
        raise HomeAssistantError(str(err)) from err


async def _handle_change_print_target_hotbed_temperature(hass: HomeAssistant, call: ServiceCall) -> None:
    entry_id = _resolve_entry_id(hass, call)
    api = hass.data[DOMAIN][entry_id]["api"]
    coordinator = hass.data[DOMAIN][entry_id]["coordinator"]

    temperature = float(call.data[ATTR_TEMPERATURE])

    try:
        await api.async_set_temperature(nozzle=None, bed=temperature)
        await coordinator.async_request_refresh()
    except KobraXApiError as err:
        raise HomeAssistantError(str(err)) from err


def async_register_services(hass: HomeAssistant) -> None:
    async def _service_change_print_speed_mode(call: ServiceCall) -> None:
        await _handle_change_print_speed_mode(hass, call)

    async def _service_change_print_target_nozzle_temperature(call: ServiceCall) -> None:
        await _handle_change_print_target_nozzle_temperature(hass, call)

    async def _service_change_print_target_hotbed_temperature(call: ServiceCall) -> None:
        await _handle_change_print_target_hotbed_temperature(hass, call)

    if not hass.services.has_service(DOMAIN, SERVICE_CHANGE_PRINT_SPEED_MODE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CHANGE_PRINT_SPEED_MODE,
            _service_change_print_speed_mode,
            schema=SERVICE_SCHEMAS[SERVICE_CHANGE_PRINT_SPEED_MODE],
        )

    if not hass.services.has_service(DOMAIN, SERVICE_CHANGE_PRINT_TARGET_NOZZLE_TEMPERATURE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CHANGE_PRINT_TARGET_NOZZLE_TEMPERATURE,
            _service_change_print_target_nozzle_temperature,
            schema=SERVICE_SCHEMAS[SERVICE_CHANGE_PRINT_TARGET_NOZZLE_TEMPERATURE],
        )

    if not hass.services.has_service(DOMAIN, SERVICE_CHANGE_PRINT_TARGET_HOTBED_TEMPERATURE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CHANGE_PRINT_TARGET_HOTBED_TEMPERATURE,
            _service_change_print_target_hotbed_temperature,
            schema=SERVICE_SCHEMAS[SERVICE_CHANGE_PRINT_TARGET_HOTBED_TEMPERATURE],
        )


def async_unregister_services(hass: HomeAssistant) -> None:
    for service_name in (
        SERVICE_CHANGE_PRINT_SPEED_MODE,
        SERVICE_CHANGE_PRINT_TARGET_NOZZLE_TEMPERATURE,
        SERVICE_CHANGE_PRINT_TARGET_HOTBED_TEMPERATURE,
    ):
        if hass.services.has_service(DOMAIN, service_name):
            hass.services.async_remove(DOMAIN, service_name)
