"""Binary sensor platform for Geotab."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .entity import GeotabEntity

from homeassistant.util import dt as dt_util

def _format_fault_attributes(faults: list) -> dict[str, Any]:
    """Format fault data into readable attributes."""
    if not faults:
        return {
            "fault_count": 0,
            "faults_list": [],
            "faults_details": [],
        }
    
    formatted_faults = []
    details = []
    
    for fault in faults:
        # Extract fault code (DTC)
        fault_code = "Unknown"
        diagnostic_name = "Unknown"
        if "diagnostic" in fault and isinstance(fault["diagnostic"], dict):
            diag = fault["diagnostic"]
            # Try to get a code, then name
            fault_code = diag.get("code") or diag.get("id", "Unknown")
            diagnostic_name = diag.get("name", "Unknown")
        
        # Extract description
        description = fault.get("description", "No description available")
        
        # Extract datetime
        fault_time = fault.get("dateTime", "Unknown")
        if isinstance(fault_time, str) and fault_time != "Unknown":
            parsed = dt_util.parse_datetime(fault_time)
            if parsed:
                fault_time = dt_util.as_local(parsed).strftime("%Y-%m-%d %H:%M:%S")
        
        # Extract state and severity
        fault_state = fault.get("faultState", "Unknown")
        lamp_status = fault.get("malfunctionLampStatus", "None")
        
        # Build formatted string
        fault_str = f"[{fault_code}] {diagnostic_name}"
        if description and description != diagnostic_name:
            fault_str += f" - {description}"
        
        formatted_faults.append(fault_str)
        
        details.append({
            "code": fault_code,
            "name": diagnostic_name,
            "description": description,
            "timestamp": fault_time,
            "state": fault_state,
            "lamp_status": lamp_status,
        })
    
    return {
        "fault_count": len(faults),
        "faults_list": formatted_faults,
        "faults_details": details,
    }


@dataclass(frozen=True, kw_only=True)
class GeotabBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Geotab binary sensor entity."""

    is_on_fn: Callable[[dict], bool]
    attr_fn: Callable[[dict], dict[str, StateType]] | None = None


BINARY_SENSORS: tuple[GeotabBinarySensorEntityDescription, ...] = (
    GeotabBinarySensorEntityDescription(
        key="active_faults",
        name="Active Faults",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: len(data.get("active_faults", [])) > 0,
        attr_fn=lambda data: _format_fault_attributes(data.get("active_faults", [])),
    ),
    GeotabBinarySensorEntityDescription(
        key="is_driving",
        name="Driving",
        device_class=BinarySensorDeviceClass.MOVING,
        is_on_fn=lambda data: data.get("isDriving"),
    ),
    GeotabBinarySensorEntityDescription(
        key="ignition",
        name="Ignition",
        device_class=BinarySensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: data.get("ignition") == 1,
    ),
    # --- Status / Safety ---
    GeotabBinarySensorEntityDescription(
        key="door_status",
        name="Door Ajar",
        device_class=BinarySensorDeviceClass.DOOR,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: data.get("door_status") == 1,
        entity_registry_enabled_default=False,
    ),
    GeotabBinarySensorEntityDescription(
        key="seatbelt_status",
        name="Driver Seatbelt",
        device_class=BinarySensorDeviceClass.SAFETY,
        icon="mdi:seatbelt",
        entity_category=EntityCategory.DIAGNOSTIC,
        # API returns 1 for unbuckled, so the sensor is "on" (problem state) when unbuckled.
        is_on_fn=lambda data: data.get("seatbelt_status") == 1,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Geotab binary sensor platform."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Track which devices we've already added entities for
    known_devices = set()

    @callback
    def async_add_new_entities():
        """Add new entities when a new device is discovered."""
        new_entities = []
        for device_id in coordinator.data:
            if device_id not in known_devices:
                for description in BINARY_SENSORS:
                    new_entities.append(GeotabBinarySensor(coordinator, device_id, description))
                known_devices.add(device_id)
        
        if new_entities:
            async_add_entities(new_entities)

    # Add initial entities
    async_add_new_entities()
    
    # Listen for coordinator updates to add new devices dynamically
    entry.async_on_unload(coordinator.async_add_listener(async_add_new_entities))


class GeotabBinarySensor(GeotabEntity, BinarySensorEntity):
    """A Geotab binary sensor."""

    entity_description: GeotabBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_id: str,
        description: GeotabBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.entity_description.is_on_fn(self.device_data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.entity_description.attr_fn:
            return self.entity_description.attr_fn(self.device_data)
        return None
