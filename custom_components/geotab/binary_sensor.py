"""Binary sensor platform for Geotab."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN


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
        is_on_fn=lambda data: len(data.get("active_faults", [])) > 0,
        attr_fn=lambda data: {
            "fault_count": len(data.get("active_faults", [])),
            "faults": data.get("active_faults", []),
        },
    ),
    # --- Disabled by default sensors ---
    GeotabBinarySensorEntityDescription(
        key="door_status",
        name="Door Ajar",
        device_class=BinarySensorDeviceClass.DOOR,
        is_on_fn=lambda data: data.get("door_status") == 1,
        entity_registry_enabled_by_default=False,
    ),
    GeotabBinarySensorEntityDescription(
        key="seatbelt_status",
        name="Driver Seatbelt",
        device_class=BinarySensorDeviceClass.SAFETY,
        icon="mdi:seatbelt",
        # API returns 1 for unbuckled, so the sensor is "on" (problem state) when unbuckled.
        is_on_fn=lambda data: data.get("seatbelt_status") == 1,
        entity_registry_enabled_by_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Geotab binary sensor platform."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        GeotabBinarySensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in BINARY_SENSORS
        # Create entity if the value_fn would not cause an error
        if coordinator.data.get(device_id, {}).get(description.key) is not None
    ]
    async_add_entities(entities)


class GeotabBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """A Geotab binary sensor."""

    entity_description: GeotabBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_id: str,
        description: GeotabBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"
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
        return self.entity_description.is_on_fn(self.device_data)

    @property
    def extra_state_attributes(self) -> dict[str, any] | None:
        """Return extra state attributes."""
        if self.entity_description.attr_fn:
            return self.entity_description.attr_fn(self.device_data)
        return None
