"""Config flow for Geotab integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ApiError, GeotabApiClient, InvalidAuth
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Based on Geotab's API, authentication usually requires username, password, and a database/server name.
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Required("database"): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Geotab."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> GeotabOptionsFlowHandler:
        """Get the options flow for this handler."""
        return GeotabOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                # Security: Validate scan interval (min 30s to prevent rate limiting issues)
                if user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL) < 30:
                    errors[CONF_SCAN_INTERVAL] = "min_scan_interval"
                    raise ValueError("Scan interval too short")

                session = async_get_clientsession(self.hass)
                client = GeotabApiClient(
                    username=user_input["username"],
                    password=user_input["password"],
                    database=user_input["database"],
                    session=session,
                )
                await client.async_authenticate()
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except ApiError:
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except-clause
                # Security: Avoid logging the entire user_input dict which contains the password
                _LOGGER.error(
                    "Unexpected exception during config flow: %s", type(err).__name__
                )
                if "base" not in errors:
                    errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input["username"].lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input["username"], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

class GeotabOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Geotab options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize Geotab options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the Geotab options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL,
                            self.config_entry.data.get(
                                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                            ),
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=30)),
                }
            ),
        )
