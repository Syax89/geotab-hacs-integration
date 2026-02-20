"""The Geotab integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import GeotabApiClient, ApiError, InvalidAuth
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    CIRCUIT_BREAKER_MAX_FAILURES,
    CIRCUIT_BREAKER_RESET_DELAY,
)

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

    # Circuit breaker state
    consecutive_failures = 0
    circuit_open_since = None

    # Create the DataUpdateCoordinator
    async def async_update_data():
        """Fetch data from API endpoint."""
        nonlocal consecutive_failures, circuit_open_since

        # If the circuit is open, skip the update until the reset delay has elapsed
        if circuit_open_since is not None:
            elapsed = (dt_util.utcnow() - circuit_open_since).total_seconds()
            if elapsed < CIRCUIT_BREAKER_RESET_DELAY:
                remaining = int(CIRCUIT_BREAKER_RESET_DELAY - elapsed)
                _LOGGER.warning(
                    "Geotab circuit breaker open, skipping update. Retrying in %ds.",
                    remaining,
                )
                raise UpdateFailed(f"Circuit breaker open, retrying in {remaining}s")
            _LOGGER.info("Geotab circuit breaker: attempting reset.")
            circuit_open_since = None

        try:
            data = await client.async_get_full_device_data()
            if consecutive_failures:
                _LOGGER.info(
                    "Geotab API recovered after %d failure(s).", consecutive_failures
                )
            consecutive_failures = 0
            return data
        except InvalidAuth as err:
            # Auth errors won't fix themselves; notify HA to prompt re-auth
            raise ConfigEntryAuthFailed(f"Invalid authentication: {err}") from err
        except (ApiError, Exception) as err:
            consecutive_failures += 1
            if consecutive_failures >= CIRCUIT_BREAKER_MAX_FAILURES:
                circuit_open_since = dt_util.utcnow()
                _LOGGER.error(
                    "Geotab circuit breaker opened after %d consecutive failures. "
                    "Pausing updates for %ds.",
                    consecutive_failures,
                    CIRCUIT_BREAKER_RESET_DELAY,
                )
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="geotab_devices",
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
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
        if DOMAIN in hass.data:
            hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
