"""Config flow for envelope-budget integration."""
from __future__ import annotations

import logging
from os.path import exists, join
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_FILE_PATH, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_NAME,
            default="Budget Envelopes",
            description="Define a name for your budget envelope(s) states",
            msg="msg",
        ): str,
        vol.Required(
            CONF_FILE_PATH,
            default="path/to/envelope-stats.json",
            description="Path to the envelope-stats.json in a folder where home assistant is allowed to access (see allowlist_external_dirs)",
            msg="msg",
        ): str,
    }
)


class Validator:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self) -> None:
        """Initialize."""

    async def check_forfile(self, file_path: str) -> bool:
        """Test if we can authenticate with the host."""
        return exists(file_path)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    if not exists(data[CONF_FILE_PATH]):
        raise InvalidFilePath

    if CONF_NAME not in data or data[CONF_NAME] == "":
        data[CONF_NAME] = "Budget Envelopes"

    _LOGGER.log(logging.DEBUG, data)

    return {"title": data[CONF_NAME], CONF_FILE_PATH: data[CONF_FILE_PATH]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for envelope-budget."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidFilePath:
                errors[
                    "base"
                ] = "No such file found\nplease list at least a folder under allowlist_external_dirs in configuration.yaml"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidFilePath(HomeAssistantError):
    """Error to indicate there is invalid auth."""
