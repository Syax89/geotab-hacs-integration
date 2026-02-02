"""API Client for Geotab."""
from __future__ import annotations

import asyncio
import socket

import aiohttp
import mygeotab
from mygeotab.exceptions import AuthenticationException


class GeotabApiClientError(Exception):
    """Base exception for API client errors."""


class InvalidAuth(GeotabApiClientError):
    """Exception for invalid authentication."""


class ApiError(GeotabApiClientError):
    """Exception for API errors."""


class GeotabApiClient:
    """Geotab API Client."""

    def __init__(
        self,
        username: str,
        password: str,
        database: str | None,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._username = username
        self._password = password
        self._database = database
        self.client = mygeotab.API(
            username=self._username,
            password=self._password,
            database=self._database,
        )

    async def async_authenticate(self) -> None:
        """Authenticate with the Geotab API."""
        try:
            # The authenticate method itself is blocking.
            # We run it in an executor to avoid blocking the event loop.
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.client.authenticate)
        except AuthenticationException as e:
            raise InvalidAuth("Invalid username, password, or database") from e
        except (socket.gaierror, aiohttp.ClientError) as e:
            raise ApiError(f"API connection error: {e}") from e
        except Exception as e:
            raise ApiError(f"An unexpected error occurred: {e}") from e

    async def async_get_full_device_data(self) -> dict[str, dict]:
        """Get combined device, status, and odometer info from the API."""
        try:
            # Fetch all data in parallel
            devices, device_statuses, odometer_data = await asyncio.gather(
                self.client.get_async("Device"),
                self.client.get_async("DeviceStatusInfo"),
                self.client.get_async(
                    "StatusData",
                    search={"diagnosticSearch": {"id": "DiagnosticOdometerId"}},
                ),
            )

            # Create lookups for status and odometer info by device id
            status_map = {
                status["device"]["id"]: status for status in device_statuses
            }
            odometer_map = {
                odo["device"]["id"]: odo["data"]
                for odo in odometer_data
                if "data" in odo
            }

            # Combine the data, keyed by device ID
            combined_data = {}
            for device in devices:
                device_id = device["id"]
                if status_info := status_map.get(device_id):
                    # Merge device and status info
                    data = device | status_info
                    # Add odometer if available
                    if odometer_value := odometer_map.get(device_id):
                        data["odometer"] = odometer_value
                    combined_data[device_id] = data

            return combined_data
        except Exception as e:
            raise ApiError(f"Failed to get device data: {e}") from e
