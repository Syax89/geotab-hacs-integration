"""The Geotab integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GeotabApiClient, ApiError, InvalidAuth
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

# List of platforms to support.
PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Geotab from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create the API client
    session = async_get_clientsession(hass)
    client = GeotabApiClient(
        username=entry.data["username"],
        password=entry.data["password"],
        database=entry.data["database"],
        session=session,
    )

    # Create the DataUpdateCoordinator
    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            return await client.async_get_full_device_data()
        except InvalidAuth as err:
            raise UpdateFailed(f"Invalid authentication: {err}") from err
        except ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="geotab_devices",
        update_method=async_update_data,
        update_interval=timedelta(
            seconds=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        ),
    )

    # Fetch initial data so we have our devices ready
    await coordinator.async_config_entry_first_refresh()

    # Add update listener for options
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Store the coordinator in hass.data
    coordinator.config_entry = entry
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
