from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KobraXApiClient
from .const import CONF_HOST, DOMAIN, PLATFORMS
from .coordinator import KobraXCoordinator

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
        "ace_dry_config": {
            0: {
                "target_temp": int((coordinator.data or {}).get("ace_drying", {}).get("target_temp", 45) or 45),
                "duration": int((coordinator.data or {}).get("ace_drying", {}).get("duration", 240) or 240),
            },
            1: {
                "target_temp": 45,
                "duration": 240,
            },
            2: {
                "target_temp": 45,
                "duration": 240,
            },
            3: {
                "target_temp": 45,
                "duration": 240,
            },
        },
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
