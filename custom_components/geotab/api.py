"""API Client for Geotab."""
from __future__ import annotations

import asyncio
import socket
from collections import defaultdict

import aiohttp
import mygeotab
from mygeotab.exceptions import AuthenticationException


class GeotabApiClientError(Exception):
    """Base exception for API client errors."""


class InvalidAuth(GeotabApiClientError):
    """Exception for invalid authentication."""


class ApiError(GeotabApiClientError):
    """Exception for API errors."""

# Define the diagnostics we want to fetch
DIAGNOSTICS_TO_FETCH = {
    "odometer": "DiagnosticOdometerId",
    "voltage": "DiagnosticGoDeviceVoltageId",
    "fuel_level": "DiagnosticFuelLevelId",
    "tire_pressure_front_left": "DiagnosticTirePressureFrontLeftId",
    "tire_pressure_front_right": "DiagnosticTirePressureFrontRightId",
    "tire_pressure_rear_left": "DiagnosticTirePressureRearLeftId",
    "tire_pressure_rear_right": "DiagnosticTirePressureRearRightId",
    "rpm": "DiagnosticEngineSpeedId",
    "coolant_temp": "DiagnosticEngineCoolantTemperatureId",
    "accelerator_pos": "DiagnosticAcceleratorPedalPositionId",
    "door_status": "DiagnosticDoorAjarId", # Common ID for any door being ajar
    "seatbelt_status": "DiagnosticDriverSeatbeltId",
}


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
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.client.authenticate)
        except AuthenticationException as e:
            raise InvalidAuth("Invalid username, password, or database") from e
        except (socket.gaierror, aiohttp.ClientError) as e:
            raise ApiError(f"API connection error: {e}") from e
        except Exception as e:
            raise ApiError(f"An unexpected error occurred: {e}") from e

    async def async_get_full_device_data(self) -> dict[str, dict]:
        """Get combined device and status info from the API using a multi-call."""
        try:
            loop = asyncio.get_running_loop()

            # Build the list of calls for the multi-call
            calls = [
                ("Get", {"typeName": "Device"}),
                ("Get", {"typeName": "DeviceStatusInfo"}),
            ]
            for diagnostic_id in DIAGNOSTICS_TO_FETCH.values():
                calls.append(
                    (
                        "Get",
                        {
                            "typeName": "StatusData",
                            "search": {"diagnosticSearch": {"id": diagnostic_id}},
                        },
                    )
                )

            # --- Run the multi-call in the executor ---
            def _multi_call():
                return self.client.multi_call(calls)

            results = await loop.run_in_executor(None, _multi_call)

            # --- Process the results ---
            devices = results[0]
            device_statuses = results[1]
            diagnostic_results = results[2:]

            # Map status info by device ID
            status_map = {
                status["device"]["id"]: status for status in device_statuses if "device" in status
            }

            # Map diagnostic data by device ID and key
            diagnostics_map = defaultdict(dict)
            diagnostic_keys = list(DIAGNOSTICS_TO_FETCH.keys())
            
            for i, key in enumerate(diagnostic_keys):
                for item in diagnostic_results[i]:
                    if "data" in item and "device" in item:
                        device_id = item["device"]["id"]
                        diagnostics_map[device_id][key] = item["data"]
            
            # Combine all data, keyed by device ID
            combined_data = {}
            for device in devices:
                device_id = device.get("id")
                if not device_id:
                    continue
                
                # Merge device info, status, and diagnostics
                data = device.copy()
                if status_info := status_map.get(device_id):
                    data.update(status_info)
                
                if device_id in diagnostics_map:
                    data.update(diagnostics_map[device_id])
                
                combined_data[device_id] = data

            return combined_data

        except Exception as e:
            raise ApiError(f"Failed to get device data: {e}") from e
