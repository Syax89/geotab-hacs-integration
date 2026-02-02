"""Sensor platform for Geotab."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength, UnitOfSpeed
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
class GeotabSensorEntityDescription(SensorEntityDescription):
    """Describes a Geotab sensor entity."""

    value_fn: Callable[[dict], StateType]


SENSORS: tuple[GeotabSensorEntityDescription, ...] = (
    GeotabSensorEntityDescription(
        key="speed",
        name="Speed",
        icon="mdi:speedometer",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("speed"),
    ),
    GeotabSensorEntityDescription(
        key="odometer",
        name="Odometer",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        # Odometer data from the API is in meters, convert to km
        value_fn=lambda data: data.get("odometer", 0) / 1000
        if data.get("odometer") is not None
        else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Geotab sensor platform."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        GeotabSensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in SENSORS
        # Don't create a sensor if the data isn't available
        if description.value_fn(coordinator.data[device_id]) is not None
    ]
    async_add_entities(entities)


class GeotabSensor(CoordinatorEntity, SensorEntity):
    """A Geotab sensor."""

    entity_description: GeotabSensorEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_id: str,
        description: GeotabSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
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
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.device_data)
