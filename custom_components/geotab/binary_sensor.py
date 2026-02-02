"""Binary sensor platform for Geotab."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up the Geotab binary sensor platform."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        GeotabFaultSensor(coordinator, device_id)
        for device_id in coordinator.data
    ]
    async_add_entities(entities)


class GeotabFaultSensor(CoordinatorEntity, BinarySensorEntity):
    """A Geotab binary sensor for active faults."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_active_faults"
        self._attr_name = "Active Faults"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
        )

    @property
    def device_data(self) -> dict:
        """Return the device data for this entity."""
        return self.coordinator.data[self._device_id]

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return len(self.device_data.get("active_faults", [])) > 0

    @property
    def extra_state_attributes(self) -> dict[str, any] | None:
        """Return extra state attributes."""
        faults = self.device_data.get("active_faults", [])
        return {
            "fault_count": len(faults),
            "faults": faults,
        }
