"""Device tracker for Geotab."""

from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .entity import GeotabEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Geotab device tracker."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Track which devices we've already added entities for
    known_devices = set()

    @callback
    def async_add_new_entities():
        """Add new entities when a new device is discovered."""
        new_entities = []
        for device_id in coordinator.data:
            if device_id not in known_devices:
                new_entities.append(GeotabDeviceTracker(coordinator, device_id))
                known_devices.add(device_id)
        
        if new_entities:
            async_add_entities(new_entities)

    # Add initial entities
    async_add_new_entities()
    
    # Listen for coordinator updates to add new devices dynamically
    entry.async_on_unload(coordinator.async_add_listener(async_add_new_entities))


class GeotabDeviceTracker(GeotabEntity, TrackerEntity):
    """A Geotab device tracker."""

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_tracker"
        self._attr_name = "Location"

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self.device_data.get("latitude")

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self.device_data.get("longitude")

    @property
    def source_type(self) -> SourceType:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        return {
            "speed": self.device_data.get("speed"),
            "is_driving": self.device_data.get("isDriving"),
            "last_updated": self.device_data.get("dateTime"),
        }
