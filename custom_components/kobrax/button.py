from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.exceptions import ServiceValidationError

from .api import KobraXApiError
from .const import DOMAIN
from .entity import KobraXEntity


@dataclass(frozen=True, kw_only=True)
class KobraXButtonDescription(ButtonEntityDescription):
    action: str


BUTTONS: tuple[KobraXButtonDescription, ...] = (
    KobraXButtonDescription(
        key="pause_print",
        name="Pause Print",
        icon="mdi:pause",
        action="pause",
    ),
    KobraXButtonDescription(
        key="resume_print",
        name="Resume Print",
        icon="mdi:play",
        action="resume",
    ),
    KobraXButtonDescription(
        key="cancel_print",
        name="Cancel Print",
        icon="mdi:stop",
        action="cancel",
    ),
    KobraXButtonDescription(
        key="connect",
        name="Connect Bridge",
        icon="mdi:lan-connect",
        action="connect",
        entity_registry_enabled_default=False,
    ),
    KobraXButtonDescription(
        key="disconnect",
        name="Disconnect Bridge",
        icon="mdi:lan-disconnect",
        action="disconnect",
        entity_registry_enabled_default=False,
    ),
)


class KobraXActionButton(KobraXEntity, ButtonEntity):
    entity_description: KobraXButtonDescription

    async def async_press(self) -> None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            if self.entity_description.action == "pause":
                await api.async_pause_print()
            elif self.entity_description.action == "resume":
                await api.async_resume_print()
            elif self.entity_description.action == "cancel":
                await api.async_cancel_print()
            elif self.entity_description.action == "connect":
                await api.async_connect()
            elif self.entity_description.action == "disconnect":
                await api.async_disconnect()
            await self.coordinator.async_request_refresh()
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [
            KobraXActionButton(coordinator, entry, description.key, description.name)
            for description in BUTTONS
        ]
    )
