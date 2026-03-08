"""The Geotab integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, ServiceCall
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
    TRIP_FETCH_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# List of platforms to support.
PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
]

SERVICE_REFRESH = "refresh"


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

    # Trip fetch caching state
    last_trip_fetch: float = 0.0
    cached_trip_data: dict[str, dict] = {}

    # Create the DataUpdateCoordinator
    async def async_update_data():
        """Fetch data from API endpoint."""
        nonlocal consecutive_failures, circuit_open_since
        nonlocal last_trip_fetch, cached_trip_data

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

        # Determine if we should fetch trips this cycle
        now = dt_util.utcnow().timestamp()
        include_trips = (now - last_trip_fetch) >= TRIP_FETCH_INTERVAL

        try:
            data = await client.async_get_full_device_data(include_trips=include_trips)

            if include_trips:
                last_trip_fetch = now
                # Cache trip data for cycles where trips are skipped
                cached_trip_data = {}
                for device_id, device_data in data.items():
                    if "last_trip" in device_data:
                        cached_trip_data[device_id] = {
                            "last_trip": device_data["last_trip"],
                            "trip_history": device_data.get("trip_history", []),
                        }
            else:
                # Inject cached trip data
                for device_id, trip_cache in cached_trip_data.items():
                    if device_id in data:
                        data[device_id].update(trip_cache)

            if consecutive_failures:
                _LOGGER.info(
                    "Geotab API recovered after %d failure(s).", consecutive_failures
                )
            consecutive_failures = 0

            device_count = len(data)
            _LOGGER.debug(
                "Geotab update: %d device(s), trips=%s",
                device_count,
                "fetched" if include_trips else "cached",
            )

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

    # Register the refresh service (once per domain)
    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):

        async def handle_refresh(call: ServiceCall) -> None:
            """Handle the geotab.refresh service call."""
            _LOGGER.info("Geotab manual refresh requested via service call")
            for coord in hass.data.get(DOMAIN, {}).values():
                if isinstance(coord, DataUpdateCoordinator):
                    await coord.async_request_refresh()

        hass.services.async_register(DOMAIN, SERVICE_REFRESH, handle_refresh)

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
