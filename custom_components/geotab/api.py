"""API Client for Geotab."""

from __future__ import annotations

import asyncio
import logging
import socket
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp

from .const import DIAGNOSTICS_TO_FETCH

_LOGGER = logging.getLogger(__name__)

TRIP_HISTORY_DAYS = 30
TRIP_RESULTS_LIMIT = 250
FAULT_RESULTS_PER_DEVICE = 10


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
        import mygeotab

        self._username = username
        self._password = password
        self._database = database
        self._session = session
        self.client = mygeotab.API(
            username=self._username,
            password=self._password,
            database=self._database,
        )
        self._diagnostic_keys_by_id = {
            diagnostic_id: key for key, diagnostic_id in DIAGNOSTICS_TO_FETCH.items()
        }
        self._diagnostics_lookup_cache: dict[str, str] = {}

    async def async_authenticate(self) -> None:
        """Authenticate with the Geotab API."""
        from mygeotab.exceptions import AuthenticationException

        try:
            loop = asyncio.get_running_loop()
            await asyncio.wait_for(
                loop.run_in_executor(None, self.client.authenticate), timeout=10
            )
        except AuthenticationException as err:
            raise InvalidAuth("Invalid username, password, or database") from err
        except asyncio.TimeoutError as err:
            raise ApiError("Authentication timed out") from err
        except (socket.gaierror, aiohttp.ClientError) as err:
            raise ApiError(f"API connection error: {err}") from err
        except Exception as err:
            raise ApiError(f"An unexpected error occurred: {err}") from err

    def _blocking_fetch_all(self, include_trips: bool = True) -> tuple[list, list, list]:
        """Fetch devices and supporting data synchronously."""
        devices = self.client.get("Device")
        if not devices:
            return [], [], []

        device_ids = [device["id"] for device in devices if device.get("id")]
        diagnostics = [{"id": diagnostic_id} for diagnostic_id in DIAGNOSTICS_TO_FETCH.values()]

        calls: list[tuple[str, dict[str, Any]]] = [
            (
                "Get",
                {
                    "typeName": "DeviceStatusInfo",
                    "search": {"diagnostics": diagnostics},
                },
            ),
            (
                "Get",
                {
                    "typeName": "FaultData",
                    "search": {
                        "deviceSearch": {"deviceIds": device_ids},
                        "state": "Active",
                    },
                    "resultsLimit": max(len(device_ids) * FAULT_RESULTS_PER_DEVICE, 20),
                },
            ),
        ]
        call_map = ["status", "faults"]

        if include_trips:
            from_date = (
                datetime.now(timezone.utc) - timedelta(days=TRIP_HISTORY_DAYS)
            ).isoformat()
            for device_id in device_ids:
                calls.append(
                    (
                        "Get",
                        {
                            "typeName": "Trip",
                            "search": {
                                "deviceSearch": {"id": device_id},
                                "fromDate": from_date,
                            },
                            "resultsLimit": TRIP_RESULTS_LIMIT,
                        },
                    )
                )
                call_map.append(f"trip_{device_id}")

        results = self.client.multi_call(calls)
        return devices, results, call_map

    def _blocking_load_fault_diagnostics(self) -> dict[str, str]:
        """Load diagnostic names for Geotab Go faults on demand."""
        result = self.client.get("Diagnostic", search={"diagnosticType": "GoFault"})
        lookup: dict[str, str] = {}
        for diagnostic in result:
            if not isinstance(diagnostic, dict):
                continue
            diagnostic_id = diagnostic.get("id")
            diagnostic_name = diagnostic.get("name")
            if diagnostic_id and diagnostic_name:
                lookup[diagnostic_id] = diagnostic_name
        return lookup

    def _extract_status_diagnostics(self, status_info: dict[str, Any]) -> dict[str, Any]:
        """Extract latest diagnostics already embedded in DeviceStatusInfo."""
        diagnostics: dict[str, Any] = {}
        for item in status_info.get("statusData", []):
            if not isinstance(item, dict):
                continue
            diagnostic = item.get("diagnostic")
            if not isinstance(diagnostic, dict):
                continue
            diagnostic_id = diagnostic.get("id")
            diagnostic_key = self._diagnostic_keys_by_id.get(diagnostic_id)
            if diagnostic_key is None or item.get("data") is None:
                continue
            diagnostics[diagnostic_key] = item["data"]
        return diagnostics

    async def async_get_full_device_data(
        self, include_trips: bool = True
    ) -> dict[str, dict[str, Any]]:
        """Get combined device and status info from the API using multi-calls."""
        try:
            loop = asyncio.get_running_loop()
            devices, results, call_map = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: self._blocking_fetch_all(include_trips)),
                timeout=45,
            )

            if not devices:
                return {}

            status_map: dict[str, dict[str, Any]] = {}
            diagnostics_map: defaultdict[str, dict[str, Any]] = defaultdict(dict)
            fault_map: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
            trip_results_dict: dict[str, list[dict[str, Any]]] = {}
            diagnostics_lookup = dict(self._diagnostics_lookup_cache)
            unknown_fault_diagnostic_ids: set[str] = set()

            for index, key in enumerate(call_map):
                result = results[index]

                if key == "status" and isinstance(result, list):
                    for status in result:
                        if not isinstance(status, dict):
                            continue
                        device = status.get("device")
                        if not isinstance(device, dict) or not device.get("id"):
                            continue
                        device_id = device["id"]
                        status_map[device_id] = status
                        diagnostics_map[device_id].update(
                            self._extract_status_diagnostics(status)
                        )

                elif key == "faults" and isinstance(result, list):
                    sorted_faults = sorted(
                        (fault for fault in result if isinstance(fault, dict)),
                        key=lambda item: item.get("dateTime", ""),
                        reverse=True,
                    )
                    for fault in sorted_faults:
                        device = fault.get("device")
                        if isinstance(device, dict) and device.get("id"):
                            fault_map[device["id"]].append(fault)
                            diagnostic = fault.get("diagnostic")
                            if isinstance(diagnostic, dict):
                                diagnostic_id = diagnostic.get("id")
                                if diagnostic_id and diagnostic_id not in diagnostics_lookup:
                                    unknown_fault_diagnostic_ids.add(diagnostic_id)

                elif key.startswith("trip_") and isinstance(result, list):
                    device_id = key[5:]
                    real_trips = [
                        trip
                        for trip in result
                        if isinstance(trip, dict) and trip.get("distance", 0) > 0
                    ]
                    if real_trips:
                        trip_results_dict[device_id] = sorted(
                            real_trips,
                            key=lambda trip: trip.get("start", ""),
                            reverse=True,
                        )

            if unknown_fault_diagnostic_ids:
                diagnostics_lookup.update(
                    await asyncio.wait_for(
                        loop.run_in_executor(None, self._blocking_load_fault_diagnostics),
                        timeout=20,
                    )
                )

            self._diagnostics_lookup_cache = diagnostics_lookup

            total_diagnostics = sum(len(values) for values in diagnostics_map.values())
            _LOGGER.debug(
                "Fetched data for %d device(s), %d diagnostic values, trips=%s",
                len(devices),
                total_diagnostics,
                "included" if include_trips else "cached",
            )

            combined_data: dict[str, dict[str, Any]] = {}
            for device in devices:
                device_id = device.get("id")
                if not device_id:
                    continue

                device_name = device.get("name", device_id)
                data: dict[str, Any] = device.copy()
                diag_data = diagnostics_map.get(device_id, {})
                data.update(diag_data)

                if data.get("odometer") is None:
                    if diag_data.get("odometer") is not None:
                        data["odometer"] = diag_data["odometer"]
                    elif diag_data.get("odometer_raw") is not None:
                        data["odometer"] = diag_data["odometer_raw"]
                    elif diag_data.get("total_distance") is not None:
                        data["odometer"] = diag_data["total_distance"]

                if data.get("engine_hours") is None and diag_data.get("engine_hours_raw") is not None:
                    data["engine_hours"] = diag_data["engine_hours_raw"]

                if diag_data:
                    _LOGGER.debug("[%s] %d diagnostic values available", device_name, len(diag_data))

                data["_diagnostics_lookup"] = diagnostics_lookup
                if device_id in fault_map:
                    data["active_faults"] = fault_map[device_id]

                if trip_list := trip_results_dict.get(device_id):
                    data["last_trip"] = trip_list[0]
                    data["trip_history"] = trip_list
                    if data.get("engine_hours") is None and "engineHours" in trip_list[0]:
                        data["engine_hours"] = trip_list[0]["engineHours"]
                    _LOGGER.debug("[%s] %d valid trips loaded", device_name, len(trip_list))

                if status_info := status_map.get(device_id):
                    status_data_ignition = data.get("ignition")
                    status_payload = dict(status_info)
                    status_payload.pop("statusData", None)
                    data.update(status_payload)

                    if data.get("rpm", 0) > 0:
                        data["ignition"] = 1
                    elif status_info.get("isIgnitionOn") is not None:
                        data["ignition"] = 1 if status_info["isIgnitionOn"] else 0
                    elif status_info.get("isDriving") is False and status_info.get("speed", 0) == 0:
                        data["ignition"] = 0
                    elif status_data_ignition is not None:
                        data["ignition"] = status_data_ignition

                combined_data[device_id] = data

            return combined_data

        except asyncio.TimeoutError as err:
            raise ApiError("Data fetch timed out after 45 seconds") from err
        except Exception as err:
            raise ApiError(f"Failed to get device data: {err}") from err
