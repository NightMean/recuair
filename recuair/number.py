"""Number platform for Recuair controls."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import RecuairApi, RecuairApiError
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Recuair number entities from config entry."""
    api: RecuairApi = hass.data[DOMAIN][entry.entry_id]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.unique_id)},
        name=entry.title,
        manufacturer="Recuair",
        model="DC40",
        configuration_url=f"http://{entry.data[CONF_HOST]}",
    )
    async_add_entities([RecuairLightIntensityNumber(api, entry, device_info)])


class RecuairLightIntensityNumber(NumberEntity):
    """Number entity for Recuair light intensity."""

    _attr_has_entity_name = True
    _attr_name = "Light Intensity"
    _attr_native_min_value = 0
    _attr_native_max_value = 5
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_should_poll = True

    def __init__(self, api: RecuairApi, entry: ConfigEntry, device_info: DeviceInfo) -> None:
        """Initialize light intensity number."""
        self._api = api
        self._entry = entry
        self._attr_device_info = device_info
        self._attr_unique_id = f"{entry.entry_id}_light_intensity_control"
        self._attr_native_value = 0

    async def async_added_to_hass(self) -> None:
        """Update initial state when entity is added."""
        await super().async_added_to_hass()
        await self.async_update()

    async def async_update(self) -> None:
        """Fetch current light intensity from device state."""
        data = await self._api.get_data()
        value = (data or {}).get("light_intensity")
        if isinstance(value, int):
            self._attr_native_value = value

    async def async_set_native_value(self, value: float) -> None:
        """Set device light intensity.

        Recuair expects full RGB payload for light updates.
        """
        intensity = int(value)
        try:
            await self._api.async_set_light(intensity=intensity, red=255, green=255, blue=255)
        except RecuairApiError as err:
            raise HomeAssistantError(str(err)) from err
        self._attr_native_value = intensity
        self.async_write_ha_state()
