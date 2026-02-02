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
                ("Get", {"typeName": "FaultData", "search": {"state": "Active"}}),
                ("Get", {"typeName": "Diagnostic"}), # For fault descriptions
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
            active_faults = results[2]
            all_diagnostics = {diag["id"]: diag for diag in results[3]}
            diagnostic_results = results[4:]

            status_map = {
                status["device"]["id"]: status for status in device_statuses
            }

            diagnostics_map = defaultdict(dict)
            for i, key in enumerate(DIAGNOSTICS_TO_FETCH.keys()):
                for item in diagnostic_results[i]:
                    if "data" in item and "device" in item:
                        device_id = item["device"]["id"]
                        diagnostics_map[device_id][key] = item["data"]

            faults_map = defaultdict(list)
            for fault in active_faults:
                device_id = fault["device"]["id"]
                diagnostic_id = fault.get("diagnostic", {}).get("id")
                diagnostic_details = all_diagnostics.get(diagnostic_id)
                fault_info = {
                    "id": fault["id"],
                    "code": diagnostic_details.get("code") if diagnostic_details else "Unknown",
                    "description": diagnostic_details.get("description") if diagnostic_details else "Unknown",
                    "timestamp": fault.get("timestamp"),
                }
                faults_map[device_id].append(fault_info)

            # Combine all data, keyed by device ID
            combined_data = {}
            for device in devices:
                device_id = device["id"]
                if status_info := status_map.get(device_id):
                    data = device | status_info
                    if device_id in diagnostics_map:
                        data.update(diagnostics_map[device_id])
                    data["active_faults"] = faults_map.get(device_id, [])
                    combined_data[device_id] = data

            return combined_data

        except Exception as e:
            raise ApiError(f"Failed to get device data: {e}") from e
