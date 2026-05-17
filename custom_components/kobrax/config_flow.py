from __future__ import annotations

import re

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KobraXApiClient, KobraXApiError
from .const import CONF_HOST, CONF_PRINTER_NAME, DEFAULT_HOST, DEFAULT_PRINTER_NAME, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PRINTER_NAME, default=DEFAULT_PRINTER_NAME): str,
    }
)


def _normalize_host(host: str) -> str:
    cleaned = host.strip()
    if not re.match(r"https?://", cleaned):
        cleaned = f"http://{cleaned}"
    cleaned = re.sub(r"/+$", "", cleaned)
    return cleaned


class KobraXConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            host = _normalize_host(user_input[CONF_HOST])
            printer_name = user_input[CONF_PRINTER_NAME].strip() or DEFAULT_PRINTER_NAME

            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            api = KobraXApiClient(session, host)
            try:
                await api.async_check_version()
            except KobraXApiError:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=printer_name,
                    data={
                        CONF_HOST: host,
                        CONF_PRINTER_NAME: printer_name,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return KobraXOptionsFlow(config_entry)


class KobraXOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            host = _normalize_host(user_input[CONF_HOST])
            printer_name = user_input[CONF_PRINTER_NAME].strip() or DEFAULT_PRINTER_NAME
            return self.async_create_entry(
                title="",
                data={
                    CONF_HOST: host,
                    CONF_PRINTER_NAME: printer_name,
                },
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=self.config_entry.data.get(CONF_HOST, DEFAULT_HOST),
                    ): str,
                    vol.Required(
                        CONF_PRINTER_NAME,
                        default=self.config_entry.data.get(
                            CONF_PRINTER_NAME, DEFAULT_PRINTER_NAME
                        ),
                    ): str,
                }
            ),
        )
