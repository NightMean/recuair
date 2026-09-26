"""Config flow for Recuair."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import RecuairApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class RecuairConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Recuair config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            if user_input.get(CONF_SCAN_INTERVAL, 60) < 60:
                errors["base"] = "min_scan_interval"
            else:
                try:
                    session = async_create_clientsession(self.hass)
                    api = RecuairApi(user_input[CONF_HOST], session)
                    data = await api.get_data()
                    if data and data.get("device_name"):
                        await self.async_set_unique_id(data["device_name"])
                        self._abort_if_unique_id_configured()
                        return self.async_create_entry(
                            title=data["device_name"], data=user_input
                        )
                    else:
                        errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=60): int,
            }),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return RecuairOptionsFlowHandler()


class RecuairOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Recuair options."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}

        if user_input is not None:
            if user_input.get(CONF_SCAN_INTERVAL, 60) < 60:
                errors["base"] = "min_scan_interval"
            else:
                try:
                    session = async_create_clientsession(self.hass)
                    api = RecuairApi(user_input[CONF_HOST], session)
                    data = await api.get_data()
                    if data and data.get("device_name"):
                        return self.async_create_entry(title="", data=user_input)
                    else:
                        errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

        current_host = self.config_entry.options.get(
            CONF_HOST, self.config_entry.data.get(CONF_HOST, "")
        )
        current_scan = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, self.config_entry.data.get(CONF_SCAN_INTERVAL, 60)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=current_host): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=current_scan): int,
            }),
            errors=errors,
        )
