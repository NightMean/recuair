"""Select platform for Recuair controls."""
from __future__ import annotations

import re

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import RecuairApi, RecuairApiError
from .const import DOMAIN, MODEL, MODE_AUTO, MODE_OPTIONS


def _normalize_mode(mode: str) -> str | None:
    """Normalize mode value from Recuair UI to integration option values."""
    normalized = mode.strip().lower()
    if normalized in MODE_OPTIONS:
        return normalized

    if "auto" in normalized:
        return "auto"
    if "off" in normalized:
        return "off"
    if "holiday" in normalized:
        return "holiday"
    if "bypass" in normalized:
        return "bypass"

    match = re.search(r"\b([1-4])\b", normalized)
    if match:
        return match.group(1)
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Recuair select entities from config entry."""
    api: RecuairApi = hass.data[DOMAIN][entry.entry_id]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.unique_id)},
        name=entry.title,
        manufacturer="Recuair",
        model=MODEL,
        configuration_url=api.configuration_url,
    )
    async_add_entities([RecuairModeSelect(api, entry, device_info)])


class RecuairModeSelect(SelectEntity):
    """Select entity for Recuair operating mode."""

    _attr_has_entity_name = True
    _attr_name = "Mode"
    _attr_options = MODE_OPTIONS
    _attr_should_poll = True

    def __init__(self, api: RecuairApi, entry: ConfigEntry, device_info: DeviceInfo) -> None:
        """Initialize the mode select entity."""
        self._api = api
        self._entry = entry
        self._attr_device_info = device_info
        self._attr_unique_id = f"{entry.entry_id}_mode"
        self._attr_current_option = MODE_AUTO

    async def async_added_to_hass(self) -> None:
        """Update initial state when entity is added."""
        await super().async_added_to_hass()
        await self.async_update()

    async def async_update(self) -> None:
        """Fetch current mode from device state."""
        data = await self._api.get_data()
        mode = (data or {}).get("mode")
        if isinstance(mode, str):
            normalized = _normalize_mode(mode)
            if normalized is not None:
                self._attr_current_option = normalized

    async def async_select_option(self, option: str) -> None:
        """Select a new device mode."""
        try:
            await self._api.async_set_mode(option)
        except RecuairApiError as err:
            raise HomeAssistantError(str(err)) from err
        self._attr_current_option = option
        self.async_write_ha_state()
