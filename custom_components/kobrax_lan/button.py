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
# ENABLE ME WHEN API ENDPOINT IS ADDED    
#      KobraXButtonDescription(
#          key="restart_bridge",
#          name="Restart (KX-Bridge)",
#          icon="mdi:restart",
#         action="restart",
#          entity_category=EntityCategory.CONFIG,
#      ), 
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


# ACE dryer buttons are now dynamically created in async_setup_entry


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


class KobraXAceDryButton(KobraXEntity, ButtonEntity):
    def __init__(
        self,
        coordinator,
        entry,
        ace_id: int,
        action: str,  # "dry_start" or "dry_stop"
    ) -> None:
        if action == "dry_start":
            unique_key = f"ace_{ace_id}_dry_start"
            name = f"ACE {ace_id + 1} Dryer Start"
            icon = "mdi:tumble-dryer"
        else:  # dry_stop
            unique_key = f"ace_{ace_id}_dry_stop"
            name = f"ACE {ace_id + 1} Dryer Stop"
            icon = "mdi:tumble-dryer-off"

        super().__init__(coordinator, entry, unique_key, name)
        self._ace_id = ace_id
        self._action = action
        self._attr_icon = icon

    async def async_press(self) -> None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            if self._action == "dry_start":
                cfg = self.hass.data[DOMAIN][self._entry.entry_id]["ace_dry_config"]
                ace_cfg = cfg.get(self._ace_id) or {}
                await api.async_set_ace_dry(
                    "start",
                    target_temp=int(ace_cfg.get("target_temp", 45)),
                    duration=int(ace_cfg.get("duration", 240)),
                    ace_id=self._ace_id,
                )
            elif self._action == "dry_stop":
                await api.async_set_ace_dry("stop", ace_id=self._ace_id)
            await self.coordinator.async_request_refresh()
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    entities = [
        KobraXActionButton(coordinator, entry, description)
        for description in BUTTONS
    ]
    
    # Pre-create all 8 ACE dryer buttons (start + stop for each of 4 ACE units)
    for ace_id in range(4):
        entities.append(KobraXAceDryButton(coordinator, entry, ace_id, "dry_start"))
        entities.append(KobraXAceDryButton(coordinator, entry, ace_id, "dry_stop"))
    
    async_add_entities(entities)
