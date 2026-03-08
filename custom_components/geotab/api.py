"""API Client for Geotab."""

from __future__ import annotations

import asyncio
import logging
import socket
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import aiohttp
import mygeotab
from mygeotab.exceptions import AuthenticationException

from .const import DIAGNOSTICS_TO_FETCH, AUTO_PRUNE_REPROBE_INTERVAL

_LOGGER = logging.getLogger(__name__)


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
        # Auto-pruning state: diagnostic keys that returned empty for ALL devices
        self._pruned_diagnostics: set[str] = set()
        self._poll_count: int = 0

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

    def _blocking_fetch_all(self, include_trips: bool = True) -> tuple[list, list, list]:
        """Fetch device list and all multi-call data synchronously.

        Intended to run inside a single executor call so the event loop
        is only blocked once per coordinator update (one thread, one round-trip).
        Returns (devices, results, call_map).
        """
        devices = self.client.get("Device")
        if not devices:
            return [], [], []

        self._poll_count += 1

        # Determine which diagnostics to fetch (auto-pruning)
        reprobe = self._poll_count % AUTO_PRUNE_REPROBE_INTERVAL == 0
        if reprobe and self._pruned_diagnostics:
            _LOGGER.debug(
                "Re-probing %d pruned diagnostics at poll #%d",
                len(self._pruned_diagnostics),
                self._poll_count,
            )
        active_diagnostics = {
            key: diag_id
            for key, diag_id in DIAGNOSTICS_TO_FETCH.items()
            if key not in self._pruned_diagnostics or reprobe
        }

        calls: list = []
        call_map: list[str] = []

        # Device real-time status
        calls.append(("Get", {"typeName": "DeviceStatusInfo"}))
        call_map.append("status")

        # Diagnostics (latest per device for each diagnostic type)
        for key, diagnostic_id in active_diagnostics.items():
            calls.append(
                (
                    "Get",
                    {
                        "typeName": "StatusData",
                        "search": {"diagnosticSearch": {"id": diagnostic_id}},
                        "resultsLimit": len(devices) * 10,
                    },
                )
            )
            call_map.append(f"diag_{key}")

        # Active faults
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

        # Diagnostic lookup for Go device faults (resolves opaque IDs to names)
        calls.append(
            (
                "Get",
                {
                    "typeName": "Diagnostic",
                    "search": {"diagnosticType": "GoFault"},
                },
            )
        )
        call_map.append("diagnostics_lookup")

        # Trips (only when include_trips=True)
        if include_trips:
            from_date = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
            for device in devices:
                device_id = device["id"]
                calls.append(
                    (
                        "Get",
                        {
                            "typeName": "Trip",
                            "search": {
                                "deviceSearch": {"id": device_id},
                                "fromDate": from_date,
                            },
                            "resultsLimit": 200,
                        },
                    )
                )
                call_map.append(f"trip_{device_id}")

        results = self.client.multi_call(calls)

        # Auto-pruning: after first poll, detect diagnostics that returned empty for ALL devices
        if self._poll_count == 1 or reprobe:
            self._update_pruned_diagnostics(results, call_map, len(devices))

        return devices, results, call_map

    def _update_pruned_diagnostics(
        self, results: list, call_map: list[str], device_count: int
    ) -> None:
        """Detect diagnostic keys that returned empty data for all devices."""
        new_pruned: set[str] = set()
        for i, key in enumerate(call_map):
            if not key.startswith("diag_"):
                continue
            diag_key = key[5:]
            result = results[i]
            if not isinstance(result, list) or len(result) == 0:
                new_pruned.add(diag_key)

        if new_pruned != self._pruned_diagnostics:
            added = new_pruned - self._pruned_diagnostics
            removed = self._pruned_diagnostics - new_pruned
            if added:
                _LOGGER.info(
                    "Auto-pruning %d diagnostics (empty for all %d devices): %s",
                    len(added),
                    device_count,
                    sorted(added),
                )
            if removed:
                _LOGGER.info(
                    "Re-enabled %d diagnostics after re-probe: %s",
                    len(removed),
                    sorted(removed),
                )
        self._pruned_diagnostics = new_pruned

    async def async_get_full_device_data(
        self, include_trips: bool = True
    ) -> dict[str, dict]:
        """Get combined device and status info from the API using multi-calls."""
        try:
            loop = asyncio.get_running_loop()

            # Single executor call: device list + multi_call in one blocking thread
            async with asyncio.timeout(45):
                devices, results, call_map = await loop.run_in_executor(
                    None, lambda: self._blocking_fetch_all(include_trips)
                )

            if not devices:
                return {}

            # --- Process the results ---
            status_results = []
            diagnostic_results_dict = {}
            fault_results = []
            trip_results_dict: dict[str, list[dict]] = {}
            diagnostics_lookup = {}

            for i, result in enumerate(results):
                key = call_map[i]
                if key == "status":
                    status_results = result
                elif key == "diagnostics_lookup":
                    # Build map: diagnostic ID → human-readable name
                    if isinstance(result, list):
                        for diag in result:
                            diag_id = diag.get("id")
                            diag_name = diag.get("name")
                            if diag_id and diag_name:
                                diagnostics_lookup[diag_id] = diag_name
                elif key.startswith("diag_"):
                    diag_key = key[5:]
                    diagnostic_results_dict[diag_key] = result
                elif key == "faults":
                    fault_results = result
                elif key.startswith("trip_"):
                    trip_device_id = key[5:]
                    if isinstance(result, list) and result:
                        # Filter trips with distance > 0 to avoid empty trips
                        real_trips = [t for t in result if t.get("distance", 0) > 0]
                        if real_trips:
                            # Sort by start dateTime descending
                            sorted_trips = sorted(
                                real_trips, key=lambda x: x.get("start", ""), reverse=True
                            )
                            trip_results_dict[trip_device_id] = sorted_trips

            # Map status info by device ID
            status_map = {
                status["device"]["id"]: status
                for status in status_results
                if "device" in status
            }

            # Map diagnostic data by device ID and key
            diagnostics_map = defaultdict(dict)
            for diag_key, items in diagnostic_results_dict.items():
                if not isinstance(items, list):
                    continue
                sorted_items = sorted(
                    items, key=lambda x: x.get("dateTime", ""), reverse=True
                )
                for item in sorted_items:
                    if "data" in item and "device" in item:
                        device_id = item["device"]["id"]
                        if diag_key not in diagnostics_map[device_id]:
                            diagnostics_map[device_id][diag_key] = item["data"]

            # Map faults by device ID
            fault_map = defaultdict(list)
            sorted_faults = sorted(
                fault_results,
                key=lambda x: x.get("dateTime", ""),
                reverse=True
            )
            for fault in sorted_faults:
                if "device" in fault:
                    fault_map[fault["device"]["id"]].append(fault)

            # Log summary
            _LOGGER.debug(
                "Fetched data for %d device(s), %d active diagnostics, trips=%s",
                len(devices),
                len(diagnostic_results_dict),
                "included" if include_trips else "cached",
            )

            # Combine all data, keyed by device ID
            combined_data = {}
            for device in devices:
                device_id = device.get("id")
                if not device_id:
                    continue

                device_name = device.get("name", device_id)

                # Merge device info, diagnostics, and trip data
                data = device.copy()

                # 1. Update with diagnostics (might be slightly delayed)
                if device_id in diagnostics_map:
                    diag_data = diagnostics_map[device_id]
                    data.update(diag_data)

                    # Fallback for odometer (if adjustment is None/0 but raw exists)
                    if diag_data.get("odometer") is None and "odometer_raw" in diag_data:
                        data["odometer"] = diag_data["odometer_raw"]

                    # Fallback for engine_hours
                    if diag_data.get("engine_hours") is None and "engine_hours_raw" in diag_data:
                        data["engine_hours"] = diag_data["engine_hours_raw"]

                    _LOGGER.debug(
                        "[%s] %d diagnostic values available",
                        device_name,
                        len(diag_data),
                    )

                # 2. Add fault data and diagnostic name lookup
                data["_diagnostics_lookup"] = diagnostics_lookup
                if device_id in fault_map:
                    data["active_faults"] = fault_map[device_id]

                # 3. Add trip data
                if trip_list := trip_results_dict.get(device_id):
                    data["last_trip"] = trip_list[0]  # backward compatibility
                    data["trip_history"] = trip_list  # full history

                    # Final fallback for engine_hours from last trip data
                    if data.get("engine_hours") is None and "engineHours" in trip_list[0]:
                        data["engine_hours"] = trip_list[0]["engineHours"]

                    _LOGGER.debug(
                        "[%s] %d valid trips loaded",
                        device_name,
                        len(trip_list),
                    )

                # 4. Final update with status info (DeviceStatusInfo), the most real-time state
                if status_info := status_map.get(device_id):
                    # Cache ignition from StatusData as fallback if isIgnitionOn is None
                    status_data_ignition = data.get("ignition")

                    data.update(status_info)

                    # Ignition logic (priority order):
                    # 1. isIgnitionOn from DeviceStatusInfo (most reliable when present)
                    # 2. isDriving=False + speed=0 → ignition OFF (real-time, reliable)
                    # 3. Fallback to DiagnosticIgnitionId (may be stale)
                    if status_info.get("isIgnitionOn") is not None:
                        data["ignition"] = 1 if status_info["isIgnitionOn"] else 0
                    elif status_info.get("isDriving") is False and status_info.get("speed", 0) == 0:
                        data["ignition"] = 0
                    elif status_data_ignition is not None:
                        data["ignition"] = status_data_ignition

                combined_data[device_id] = data

            return combined_data

        except asyncio.TimeoutError as e:
            raise ApiError("Data fetch timed out after 45 seconds") from e
        except Exception as e:
            raise ApiError(f"Failed to get device data: {e}") from e
