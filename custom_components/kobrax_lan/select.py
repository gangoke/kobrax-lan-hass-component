from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity import EntityCategory

from .api import KobraXApiError
from .const import DOMAIN
from .entity import KobraXEntity


MAX_FILAMENT_SLOTS = 19
TOOLHEAD_SLOT_LIMIT = 4
ACE_DIRECT_SLOT_LIMIT = 4


def _detected_slot_limit(state_data: dict[str, Any]) -> int:
    mode = str(state_data.get("filament_mode") or "toolhead").lower()
    if mode == "toolhead":
        return TOOLHEAD_SLOT_LIMIT
    if mode == "ace_direct":
        return ACE_DIRECT_SLOT_LIMIT

    slots = state_data.get("ams_slots") or []
    if isinstance(slots, list) and slots:
        return min(len(slots), MAX_FILAMENT_SLOTS)
    return MAX_FILAMENT_SLOTS


class KobraXPrintSpeedSelect(KobraXEntity, SelectEntity):
    _attr_options = ["Slow (1)", "Normal (2)", "Fast (3)"]

    def _mode_to_option(self, mode: int | None) -> str:
        mapping = {
            1: "Slow (1)",
            2: "Normal (2)",
            3: "Fast (3)",
        }
        return mapping.get(mode or 2, "Normal (2)")

    @property
    def current_option(self) -> str:
        mode = self.state_data.get("print_speed_mode")
        return self._mode_to_option(int(mode) if mode is not None else None)

    async def async_select_option(self, option: str) -> None:
        mode = int(option.split("(")[-1].replace(")", ""))
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            await api.async_set_speed_mode(mode)
            await self.coordinator.async_request_refresh()
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err


class KobraXFilamentProfileSelect(KobraXEntity, SelectEntity):
    _AUTO_OPTION = "Auto (No Override)"

    def __init__(self, coordinator, entry, slot_index: int) -> None:
        super().__init__(coordinator, entry, f"slot_{slot_index + 1}_filament_profile", f"Slot {slot_index + 1} Filament Profile")
        self._slot_index = slot_index
        self._attr_icon = "mdi:palette"
        self._attr_entity_category = EntityCategory.CONFIG

    def _slot_limit_for_mode(self) -> int:
        return _detected_slot_limit(self.state_data)

    def _slot(self) -> dict[str, Any]:
        slots = self.state_data.get("filament_slots") or []
        if not isinstance(slots, list):
            return {}
        for slot in slots:
            if not isinstance(slot, dict):
                continue
            try:
                if int(slot.get("slot_index", -1)) == self._slot_index:
                    return slot
            except (TypeError, ValueError):
                continue
        return {}

    def _profile_catalog(self) -> list[dict[str, Any]]:
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        profiles = data.get("filament_profiles")
        if isinstance(profiles, list):
            return [item for item in profiles if isinstance(item, dict)]
        return []

    @staticmethod
    def _profile_label(profile: dict[str, Any]) -> str:
        name = str(profile.get("name") or profile.get("id") or "Unknown")
        vendor = str(profile.get("vendor") or "")
        fid = str(profile.get("id") or "")
        vendor_part = f" - {vendor}" if vendor else ""
        return f"{name}{vendor_part} [{fid}]" if fid else f"{name}{vendor_part}"

    def _options_map(self) -> dict[str, tuple[str, str, str]]:
        slot = self._slot()
        material = str(slot.get("material") or "").upper()
        options: dict[str, tuple[str, str, str]] = {self._AUTO_OPTION: ("", "", "")}
        for profile in self._profile_catalog():
            profile_type = str(profile.get("type") or "").upper()
            if material and profile_type and profile_type != material:
                continue
            fid = str(profile.get("id") or "")
            if not fid:
                continue
            vendor = str(profile.get("vendor") or "")
            name = str(profile.get("name") or "")
            options[self._profile_label(profile)] = (fid, vendor, name)
        return options

    @property
    def available(self) -> bool:
        return self._slot_index < self._slot_limit_for_mode() and bool(self._slot()) and super().available

    @property
    def options(self) -> list[str]:
        return list(self._options_map().keys())

    @property
    def current_option(self) -> str:
        slot = self._slot()
        filament_id = str(slot.get("filament_id") or "")
        vendor = str(slot.get("filament_vendor") or "")
        name = str(slot.get("filament_name") or "")
        if not filament_id:
            return self._AUTO_OPTION

        option_map = self._options_map()
        for label, (opt_id, opt_vendor, opt_name) in option_map.items():
            if name and vendor and opt_name == name and opt_vendor == vendor:
                return label
            if opt_id == filament_id and opt_vendor == vendor:
                return label
            if opt_id == filament_id and not vendor:
                return label
        return f"Custom [{filament_id}]"

    def _apply_optimistic_state(self, filament_id: str, vendor: str, name: str) -> None:
        merged: dict[str, Any] = dict(self.coordinator.data or {})
        slots = merged.get("filament_slots")
        if not isinstance(slots, list):
            return

        new_slots: list[dict[str, Any]] = []
        for slot in slots:
            if not isinstance(slot, dict):
                continue
            next_slot = dict(slot)
            try:
                if int(next_slot.get("slot_index", -1)) == self._slot_index:
                    next_slot["filament_id"] = filament_id
                    next_slot["filament_vendor"] = vendor
                    next_slot["filament_name"] = name
            except (TypeError, ValueError):
                pass
            new_slots.append(next_slot)

        merged["filament_slots"] = new_slots
        self.coordinator.async_set_updated_data(merged)

    async def async_select_option(self, option: str) -> None:
        option_map = self._options_map()
        if option not in option_map:
            raise ServiceValidationError(f"Invalid option: {option}")

        filament_id, vendor, name = option_map[option]
        api = self.hass.data[DOMAIN][self._entry.entry_id]["api"]
        try:
            await api.async_set_filament_slot_profile(self._slot_index, filament_id, vendor, name)
            self._apply_optimistic_state(filament_id, vendor, name)
        except KobraXApiError as err:
            raise ServiceValidationError(str(err)) from err


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    try:
        hass.data[DOMAIN][entry.entry_id]["filament_profiles"] = await api.async_get_filament_profiles()
    except KobraXApiError:
        hass.data[DOMAIN][entry.entry_id]["filament_profiles"] = []

    entities: list[SelectEntity] = [KobraXPrintSpeedSelect(coordinator, entry, "print_speed_mode", "Print Speed")]
    entities.extend(KobraXFilamentProfileSelect(coordinator, entry, slot_index) for slot_index in range(MAX_FILAMENT_SLOTS))

    async_add_entities(
        entities
    )
