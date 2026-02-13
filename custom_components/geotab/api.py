"""API Client for Geotab."""

from __future__ import annotations

import asyncio
import socket
from collections import defaultdict

import aiohttp
import mygeotab
from mygeotab.exceptions import AuthenticationException

from .const import DIAGNOSTICS_TO_FETCH


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
            calls = []
            call_map = []

            # Device Status
            calls.append(("Get", {"typeName": "DeviceStatusInfo"}))
            call_map.append("status")
            
            # Diagnostics (Latest per device for each diagnostic)
            for key, diagnostic_id in DIAGNOSTICS_TO_FETCH.items():
                calls.append(
                    (
                        "Get",
                        {
                            "typeName": "StatusData",
                            "search": {"diagnosticSearch": {"id": diagnostic_id}},
                            "resultsLimit": len(devices),
                        },
                    )
                )
                call_map.append(f"diag_{key}")
            
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
            call_map.append("faults")
            
            # Latest Trip for each device
            for device in devices:
                device_id = device["id"]
                calls.append(
                    (
                        "Get",
                        {
                            "typeName": "Trip",
                            "search": {"deviceSearch": {"id": device_id}},
                            "resultsLimit": 1,
                        },
                    )
                )
                call_map.append(f"trip_{device_id}")

            def _multi_call():
                return self.client.multi_call(calls)

            async with asyncio.timeout(30):
                results = await loop.run_in_executor(None, _multi_call)

            # --- Process the results ---
            status_results = []
            diagnostic_results_dict = {}
            fault_results = []
            trip_results_dict = {}

            for i, result in enumerate(results):
                key = call_map[i]
                if key == "status":
                    status_results = result
                elif key.startswith("diag_"):
                    diag_key = key[5:]
                    diagnostic_results_dict[diag_key] = result
                elif key == "faults":
                    fault_results = result
                elif key.startswith("trip_"):
                    trip_device_id = key[5:]
                    if result:
                        trip_results_dict[trip_device_id] = result[0]

            # Map status info by device ID
            status_map = {
                status["device"]["id"]: status
                for status in status_results
                if "device" in status
            }

            # Map diagnostic data by device ID and key
            diagnostics_map = defaultdict(dict)
            for diag_key, items in diagnostic_results_dict.items():
                for item in items:
                    if "data" in item and "device" in item:
                        device_id = item["device"]["id"]
                        if diag_key not in diagnostics_map[device_id]:
                            diagnostics_map[device_id][diag_key] = item["data"]
            
            # Map faults by device ID
            fault_map = defaultdict(list)
            for fault in fault_results:
                if "device" in fault:
                    fault_map[fault["device"]["id"]].append(fault)

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
                
                if trip_data := trip_results_dict.get(device_id):
                    data["last_trip"] = trip_data

                combined_data[device_id] = data

            return combined_data

        except Exception as e:
            raise ApiError(f"Failed to get device data: {e}") from e
