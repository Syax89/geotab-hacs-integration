"""Config flow for Geotab integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
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
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.Coerce(int),
    }
)

STEP_REAUTH_DATA_SCHEMA = vol.Schema({vol.Required("password"): str})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Geotab."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> GeotabOptionsFlowHandler:
        """Get the options flow for this handler."""
        return GeotabOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Validate scan interval before attempting API calls to avoid
            # the ValueError falling into the generic except block.
            if user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL) < 30:
                errors[CONF_SCAN_INTERVAL] = "min_scan_interval"
            else:
                try:
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
                    errors["base"] = "unknown"
                else:
                    unique_id = f"{user_input['username'].lower()}_{user_input['database'].lower()}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"{user_input['username']} ({user_input['database']})",
                        data=user_input,
                    )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> FlowResult:
        """Start re-authentication when the stored credentials stop working."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask for a new password and validate it."""
        reauth_entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                client = GeotabApiClient(
                    username=reauth_entry.data["username"],
                    password=user_input["password"],
                    database=reauth_entry.data["database"],
                    session=async_get_clientsession(self.hass),
                )
                await client.async_authenticate()
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except ApiError:
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except-clause
                _LOGGER.error(
                    "Unexpected exception during re-authentication: %s",
                    type(err).__name__,
                )
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={"password": user_input["password"]},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "username": reauth_entry.data["username"],
                "database": reauth_entry.data["database"],
            },
        )

class GeotabOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Geotab options."""

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
