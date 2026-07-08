from __future__ import annotations

import re

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
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

    def __init__(self) -> None:
        self._primary_data: dict[str, str] = {}
        self._discovered: list[dict[str, str]] = []

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
                self._primary_data = {
                    CONF_HOST: host,
                    CONF_PRINTER_NAME: printer_name,
                }
                self._discovered = await self._async_discover_other_printers(api, host)
                if self._discovered:
                    return await self.async_step_discovered()
                return self.async_create_entry(title=printer_name, data=self._primary_data)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _async_discover_other_printers(self, api: KobraXApiClient, current_host: str) -> list[dict[str, str]]:
        """Find sibling printers on the same KX-Bridge multi-printer instance."""
        try:
            printers = await api.async_get_printers()
        except KobraXApiError:
            return []

        configured_hosts = {
            entry.data.get(CONF_HOST) for entry in self._async_current_entries()
        }

        others: list[dict[str, str]] = []
        seen_hosts: set[str] = set()
        for printer in printers:
            bridge_url = str(printer.get("bridge_url") or "").strip()
            if not bridge_url:
                continue
            host = _normalize_host(bridge_url)
            if host == current_host or host in configured_hosts or host in seen_hosts:
                continue
            seen_hosts.add(host)
            others.append({
                CONF_HOST: host,
                CONF_PRINTER_NAME: str(printer.get("name") or DEFAULT_PRINTER_NAME),
            })
        return others

    async def async_step_discovered(self, user_input=None):
        if user_input is not None:
            selected_hosts = set(user_input.get("printers", []))
            for printer in self._discovered:
                if printer[CONF_HOST] in selected_hosts:
                    self.hass.async_create_task(
                        self.hass.config_entries.flow.async_init(
                            DOMAIN,
                            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
                            data=printer,
                        )
                    )
            return self.async_create_entry(
                title=self._primary_data[CONF_PRINTER_NAME],
                data=self._primary_data,
            )

        options = {
            printer[CONF_HOST]: f"{printer[CONF_PRINTER_NAME]} ({printer[CONF_HOST]})"
            for printer in self._discovered
        }
        return self.async_show_form(
            step_id="discovered",
            data_schema=vol.Schema(
                {
                    vol.Optional("printers", default=list(options)): cv.multi_select(options),
                }
            ),
        )

    async def async_step_integration_discovery(self, discovery_info: dict[str, str]):
        """Silently add a sibling printer discovered via /kx/printers."""
        host = discovery_info[CONF_HOST]
        printer_name = discovery_info.get(CONF_PRINTER_NAME) or DEFAULT_PRINTER_NAME

        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=printer_name,
            data={CONF_HOST: host, CONF_PRINTER_NAME: printer_name},
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
