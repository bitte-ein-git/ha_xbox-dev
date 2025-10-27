# config_flow.py

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import requests
import logging

from .const import DOMAIN
from .api import XboxOneDevmodeApi

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validate the user input allows us to connect."""
    api = XboxOneDevmodeApi(data[CONF_IP_ADDRESS], data[CONF_USERNAME], data[CONF_PASSWORD])
    
    try:
        await hass.async_add_executor_job(api.test_connection)
        machine_name = await hass.async_add_executor_job(api.get_machinename)
        # set title to machine_name only
        return {"title": machine_name}
    except requests.exceptions.HTTPError as err:
        _LOGGER.error("Authentication failed: %s", err)
        raise ConnectionError("Authentication failed") from err
    except requests.exceptions.RequestException as err:
        _LOGGER.error("Connection failed: %s", err)
        raise ConnectionError("Cannot connect to device") from err


class XboxDevConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Xbox Dev Mode."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                # use IP address for unique ID
                await self.async_set_unique_id(user_input[CONF_IP_ADDRESS])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )