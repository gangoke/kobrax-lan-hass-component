from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity import EntityCategory

from .api import KobraXApiError
from .const import DOMAIN
from .entity import KobraXEntity


class KobraXAceAutoFeedSwitch(KobraXEntity, SwitchEntity):
    def __init__(self, coordinator, entry, ace_id: int) -> None:
        super().__init__(coordinator, entry, f"ace_{ace_id}_auto_feed", f"ACE {ace_id + 1} Auto Fill")
        self._ace_id = ace_id
        self._attr_icon = "mdi:autorenew"

    @property
    def is_on(self) -> bool:
        auto_feed = self.state_data.get("ace_auto_feed") or {}
        if not isinstance(auto_feed, dict):
            return False
        value = auto_feed.get(self._ace_id)
        if value is None:
            value = auto_feed.get(str(self._ace_id))
        return bool(value)

    def _apply_optimistic_state(self, is_on: bool) -> None:
        merged: dict[str, Any] = dict(self.coordinator.data or {})
        auto_feed = merged.get("ace_auto_feed")
        if not isinstance(auto_feed, dict):
            auto_feed = {}
        else:
            auto_feed = dict(auto_feed)

        key: int | str = self._ace_id
        if key not in auto_feed and str(self._ace_id) in auto_feed:
            key = str(self._ace_id)
        auto_feed[key] = 1 if is_on else 0

        merged["ace_auto_feed"] = auto_feed
        self.coordinator.async_set_updated_data(merged)

    async def async_turn_on(self, **kwargs) -> None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            await api.async_set_ace_auto_feed(self._ace_id, True)
            self._apply_optimistic_state(True)
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err


class KobraXBridgeSettingSwitch(KobraXEntity, SwitchEntity):
    def __init__(self, coordinator, entry, key: str, name: str, setting_key: str, icon: str) -> None:
        super().__init__(coordinator, entry, key, name)
        self._setting_key = setting_key
        self._attr_icon = icon
        self._attr_entity_category = EntityCategory.CONFIG

    def _current_settings(self) -> dict[str, Any]:
        settings = self.state_data.get("settings")
        return settings if isinstance(settings, dict) else {}

    @property
    def available(self) -> bool:
        return bool(self._current_settings()) and super().available

    @property
    def is_on(self) -> bool:
        value = self._current_settings().get(self._setting_key)
        try:
            return bool(int(value))
        except (TypeError, ValueError):
            return bool(value)

    def _apply_optimistic_state(self, is_on: bool) -> None:
        merged: dict[str, Any] = dict(self.coordinator.data or {})
        settings = merged.get("settings")
        if not isinstance(settings, dict):
            settings = {}
        else:
            settings = dict(settings)

        settings[self._setting_key] = 1 if is_on else 0
        merged["settings"] = settings
        self.coordinator.async_set_updated_data(merged)

    async def _set_state(self, is_on: bool) -> None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            settings = await api.async_get_settings()
            settings[self._setting_key] = 1 if is_on else 0
            await api.async_set_settings(settings)
            self._apply_optimistic_state(is_on)
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err

    async def async_turn_on(self, **kwargs) -> None:
        await self._set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set_state(False)

    async def async_turn_off(self, **kwargs) -> None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            await api.async_set_ace_auto_feed(self._ace_id, False)
            self._apply_optimistic_state(False)
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err


class KobraXAceDryerSwitch(KobraXEntity, SwitchEntity):
    def __init__(self, coordinator, entry, ace_id: int) -> None:
        super().__init__(coordinator, entry, f"ace_{ace_id}_dryer", f"ACE {ace_id + 1} Dryer")
        self._ace_id = ace_id
        self._attr_icon = "mdi:tumble-dryer"

    @property
    def is_on(self) -> bool:
        drying = self.state_data.get("ace_drying") or {}
        if not isinstance(drying, dict):
            return False

        unit_data = drying.get(self._ace_id)
        if unit_data is None:
            unit_data = drying.get(str(self._ace_id))

        if isinstance(unit_data, dict):
            status = unit_data.get("status")
        elif self._ace_id == 0:
            # Backward-compatible fallback: older bridge payloads may expose unit 0 as a flat object.
            status = drying.get("status")
        else:
            status = None

        try:
            return int(status) > 0 if status is not None else False
        except (TypeError, ValueError):
            return False

    def _apply_optimistic_state(self, is_on: bool) -> None:
        merged: dict[str, Any] = dict(self.coordinator.data or {})
        drying = merged.get("ace_drying")
        if not isinstance(drying, dict):
            drying = {}
        else:
            drying = dict(drying)

        unit_data = drying.get(self._ace_id)
        unit_key: int | str = self._ace_id
        if unit_data is None:
            unit_data = drying.get(str(self._ace_id))
            if unit_data is not None:
                unit_key = str(self._ace_id)

        if isinstance(unit_data, dict):
            next_unit_data = dict(unit_data)
        else:
            next_unit_data = {}

        next_unit_data["status"] = 1 if is_on else 0
        drying[unit_key] = next_unit_data

        # Keep backward-compatible flat status for unit 0 payload variants.
        if self._ace_id == 0:
            drying["status"] = 1 if is_on else 0

        merged["ace_drying"] = drying
        self.coordinator.async_set_updated_data(merged)

    async def async_turn_on(self, **kwargs) -> None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            cfg = self.hass.data[DOMAIN][self._entry.entry_id]["ace_dry_config"]
            ace_cfg = cfg.get(self._ace_id) or {}
            await api.async_set_ace_dry(
                "start",
                target_temp=int(ace_cfg.get("target_temp", 45)),
                duration=int(ace_cfg.get("duration", 240)),
                ace_id=self._ace_id,
            )
            self._apply_optimistic_state(True)
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err

    async def async_turn_off(self, **kwargs) -> None:
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            await api.async_set_ace_dry("stop", ace_id=self._ace_id)
            self._apply_optimistic_state(False)
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        KobraXBridgeSettingSwitch(
            coordinator,
            entry,
            "camera_on_print",
            "Camera On Print",
            "camera_on_print",
            "mdi:camera-wireless",
        ),
        KobraXBridgeSettingSwitch(
            coordinator,
            entry,
            "web_upload_warning",
            "Web Upload Warning",
            "web_upload_warning",
            "mdi:alert-outline",
        ),
    ]

    # Pre-create switches for all 4 possible ACE units
    entities.extend(KobraXAceAutoFeedSwitch(coordinator, entry, ace_id) for ace_id in range(4))
    entities.extend(KobraXAceDryerSwitch(coordinator, entry, ace_id) for ace_id in range(4))

    async_add_entities(entities)
