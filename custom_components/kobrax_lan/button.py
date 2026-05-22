from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity import EntityCategory

from .api import KobraXApiError
from .const import DOMAIN
from .entity import KobraXEntity


@dataclass(frozen=True, kw_only=True)
class KobraXButtonDescription(ButtonEntityDescription):
    action: str
    ace_id: int | None = None  # None for non-ACE buttons, 0-3 for ACE buttons


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
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
    KobraXButtonDescription(
        key="disconnect",
        name="Disconnect Bridge",
        icon="mdi:lan-disconnect",
        action="disconnect",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),   
     KobraXButtonDescription(
         key="restart_bridge",
         name="Restart (KX-Bridge)",
         icon="mdi:restart",
        action="restart",
         entity_category=EntityCategory.CONFIG,
     ), 
    KobraXButtonDescription(
        key="refresh_skip_state",
        name="Refresh Skip State",
        icon="mdi:refresh",
        action="skip_query",
        entity_registry_enabled_default=False,
    ),
    KobraXButtonDescription(
        key="apply_update",
        name="Apply Update (KX-Bridge)",
        icon="mdi:download-circle-outline",
        action="apply_update",
        entity_category=EntityCategory.CONFIG,
    ),
)


class KobraXActionButton(KobraXEntity, ButtonEntity):
    entity_description: KobraXButtonDescription

    def __init__(self, coordinator, entry, description: KobraXButtonDescription) -> None:
        super().__init__(coordinator, entry, description.key, description.name)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if self.entity_description.action != "apply_update":
            return super().available

        update_info = self.state_data.get("update_info")
        if not isinstance(update_info, dict):
            return False

        current = str(update_info.get("current") or "").strip()
        latest = str(update_info.get("latest") or "").strip()
        if current and latest and current == latest:
            return False

        if update_info.get("update_available") is False:
            return False

        return super().available

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
            elif self.entity_description.action == "restart":
                await api.async_restart_bridge()
            elif self.entity_description.action == "skip_query":
                await api.async_skip_query()
            elif self.entity_description.action == "apply_update":
                await self.coordinator.async_apply_update()
            await self.coordinator.async_request_refresh()
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err
        except Exception as err:
            raise ServiceValidationError(str(err)) from err


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        KobraXActionButton(coordinator, entry, description)
        for description in BUTTONS
    ]

    async_add_entities(entities)
