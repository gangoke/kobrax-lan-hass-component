from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KobraXApiClient
from .const import CONF_HOST, DOMAIN, PLATFORMS
from .coordinator import KobraXCoordinator
from .services import async_register_services, async_unregister_services

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]
    base_url = host if host.startswith("http") else f"http://{host}"

    session = async_get_clientsession(hass)
    api = KobraXApiClient(session, base_url)

    hass.data[DOMAIN]["logger"] = _LOGGER
    coordinator = KobraXCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
        "entry": entry,
    }

    async_register_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not any(isinstance(value, dict) and "api" in value for value in hass.data[DOMAIN].values()):
            async_unregister_services(hass)
    return unload_ok
