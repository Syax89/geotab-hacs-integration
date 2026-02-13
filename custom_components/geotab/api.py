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
    "engine_hours": "DiagnosticEngineHoursId",
    "ignition": "DiagnosticIgnitionId",
    "door_status": "DiagnosticDoorAjarId",  # Common ID for any door being ajar
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
        self._session = session
        self.client = mygeotab.API(
            username=self._username,
            password=self._password,
            database=self._database,
        )

    async def async_authenticate(self) -> None:
        """Authenticate with the Geotab API."""
        try:
            loop = asyncio.get_running_loop()
            async with asyncio.timeout(10):
                await loop.run_in_executor(None, self.client.authenticate)
        except AuthenticationException as e:
            raise InvalidAuth("Invalid username, password, or database") from e
        except asyncio.TimeoutError as e:
            raise ApiError("Authentication timed out") from e
        except (socket.gaierror, aiohttp.ClientError) as e:
            raise ApiError(f"API connection error: {e}") from e
        except Exception as e:
            raise ApiError(f"An unexpected error occurred: {e}") from e

    async def async_get_full_device_data(self) -> dict[str, dict]:
        """Get combined device and status info from the API using multi-calls."""
        try:
            loop = asyncio.get_running_loop()

            # 1. First, get the list of devices to know what to query for
            def _get_devices():
                return self.client.get("Device")

            async with asyncio.timeout(10):
                devices = await loop.run_in_executor(None, _get_devices)

            if not devices:
                return {}

            # 2. Build a multi-call for status, diagnostics, faults and the latest trip per device
            calls = [("Get", {"typeName": "DeviceStatusInfo"})]
            
            # Diagnostics (Latest per device for each diagnostic)
            for diagnostic_id in DIAGNOSTICS_TO_FETCH.values():
                calls.append(
                    (
                        "Get",
                        {
                            "typeName": "StatusData",
                            "search": {"diagnosticSearch": {"id": diagnostic_id}},
                            "resultsLimit": len(devices), # Fetch latest for all devices
                        },
                    )
                )
            
            # Active Faults
            calls.append(
                (
                    "Get",
                    {
                        "typeName": "FaultData",
                        "search": {"excludeDismissed": True},
                        "resultsLimit": len(devices) * 5,
                    },
                )
            )
            
            # Latest Trip for each device
            for device in devices:
                calls.append(
                    (
                        "Get",
                        {
                            "typeName": "Trip",
                            "search": {"deviceSearch": {"id": device["id"]}},
                            "resultsLimit": 1,
                        },
                    )
                )

            def _multi_call():
                return self.client.multi_call(calls)

            async with asyncio.timeout(30):
                results = await loop.run_in_executor(None, _multi_call)

            # --- Process the results ---
            device_statuses = results[0]
            
            # Diagnostics indexing
            diag_count = len(DIAGNOSTICS_TO_FETCH)
            diagnostic_results = results[1 : 1 + diag_count]
            
            # Faults indexing
            fault_results = results[1 + diag_count]
            
            # Trip indexing
            trip_results = results[2 + diag_count :]

            # Map status info by device ID
            status_map = {
                status["device"]["id"]: status
                for status in device_statuses
                if "device" in status
            }

            # Map diagnostic data by device ID and key
            diagnostics_map = defaultdict(dict)
            diagnostic_keys = list(DIAGNOSTICS_TO_FETCH.keys())

            for i, key in enumerate(diagnostic_keys):
                for item in diagnostic_results[i]:
                    if "data" in item and "device" in item:
                        device_id = item["device"]["id"]
                        # We only keep the latest one (multi_call returns them in order)
                        if key not in diagnostics_map[device_id]:
                            diagnostics_map[device_id][key] = item["data"]
            
            # Map faults by device ID
            fault_map = defaultdict(list)
            for fault in fault_results:
                if "device" in fault:
                    fault_map[fault["device"]["id"]].append(fault)
            
            # Map latest trip by device ID
            trip_map = {}
            for i, device in enumerate(devices):
                if trip_results[i]:
                    trip_map[device["id"]] = trip_results[i][0]

            # Combine all data, keyed by device ID
            combined_data = {}
            for device in devices:
                device_id = device.get("id")
                if not device_id:
                    continue

                # Merge device info, status, diagnostics, and trip
                data = device.copy()
                if status_info := status_map.get(device_id):
                    data.update(status_info)

                if device_id in diagnostics_map:
                    data.update(diagnostics_map[device_id])
                
                if device_id in fault_map:
                    data["active_faults"] = fault_map[device_id]
                
                if device_id in trip_map:
                    data["last_trip"] = trip_map[device_id]

                combined_data[device_id] = data

            return combined_data

        except Exception as e:
            raise ApiError(f"Failed to get device data: {e}") from e
