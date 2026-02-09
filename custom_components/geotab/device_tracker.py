"""Device tracker for Geotab."""

from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Geotab device tracker."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        GeotabDeviceTracker(coordinator, device_id) for device_id in coordinator.data
    )


class GeotabDeviceTracker(CoordinatorEntity, TrackerEntity):
    """A Geotab device tracker."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_tracker"
        self._attr_name = "Location"

    @property
    def device_data(self) -> dict:
        """Return the device data for this entity."""
        return self.coordinator.data[self._device_id]

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
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        # Retrieve database from the config entry stored in the coordinator
        database = self.coordinator.config_entry.data.get("database", "Unknown")

        # Build a configuration URL. Usually it's my.geotab.com/database
        # If the database looks like a domain (has a dot), use it directly, otherwise assume my.geotab.com
        if "." in database:
            config_url = f"https://{database}"
        else:
            config_url = f"https://my.geotab.com/{database}"

        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self.device_data.get("name"),
            manufacturer="Geotab",
            model=f"{self.device_data.get('deviceType')} ({database})",
            hw_version=self.device_data.get("deviceType"),
            sw_version=self.device_data.get("version"),
            serial_number=self.device_data.get("serialNumber"),
            configuration_url=config_url,
        )

    @property
    def extra_state_attributes(self) -> dict[str, any] | None:
        """Return extra state attributes."""
        return {
            "speed": self.device_data.get("speed"),
            "is_driving": self.device_data.get("isDriving"),
            "last_updated": self.device_data.get("dateTime"),
        }
