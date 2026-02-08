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
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
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


# Conversion factor from Pascals (Pa) to PSI
PA_TO_PSI = 0.000145038

SENSORS: tuple[GeotabSensorEntityDescription, ...] = (
    # --- Main Driving Data ---
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
        value_fn=lambda data: (
            data.get("odometer", 0) / 1000 if data.get("odometer") is not None else None
        ),
    ),
    # --- Energy & Fuel ---
    GeotabSensorEntityDescription(
        key="fuel_level",
        name="Fuel Level",
        icon="mdi:gas-station",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("fuel_level"),
    ),
    GeotabSensorEntityDescription(
        key="voltage",
        name="Battery Voltage",
        icon="mdi:car-battery",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("voltage"),
    ),
    # --- Tires ---
    GeotabSensorEntityDescription(
        key="tire_pressure_front_left",
        name="Tire Pressure Front Left",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("tire_pressure_front_left", 0) * PA_TO_PSI,
    ),
    GeotabSensorEntityDescription(
        key="tire_pressure_front_right",
        name="Tire Pressure Front Right",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("tire_pressure_front_right", 0) * PA_TO_PSI,
    ),
    GeotabSensorEntityDescription(
        key="tire_pressure_rear_left",
        name="Tire Pressure Rear Left",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("tire_pressure_rear_left", 0) * PA_TO_PSI,
    ),
    GeotabSensorEntityDescription(
        key="tire_pressure_rear_right",
        name="Tire Pressure Rear Right",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("tire_pressure_rear_right", 0) * PA_TO_PSI,
    ),
    # --- Engine & Technical ---
    GeotabSensorEntityDescription(
        key="engine_hours",
        name="Engine Hours",
        icon="mdi:engine-timer",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("engine_hours"),
    ),
    GeotabSensorEntityDescription(
        key="rpm",
        name="Engine Speed",
        icon="mdi:engine-outline",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("rpm"),
        entity_registry_enabled_default=False,
    ),
    GeotabSensorEntityDescription(
        key="coolant_temp",
        name="Coolant Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("coolant_temp"),
        entity_registry_enabled_default=False,
    ),
    GeotabSensorEntityDescription(
        key="accelerator_pos",
        name="Accelerator Position",
        icon="mdi:pedal",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("accelerator_pos"),
        entity_registry_enabled_default=False,
    ),
    # --- System ---
    GeotabSensorEntityDescription(
        key="dateTime",
        name="Last Update",
        icon="mdi:clock-check",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("dateTime"),
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
        # Round the value if it's a float for cleaner display
        value = self.entity_description.value_fn(self.device_data)
        if isinstance(value, float):
            return round(value, 2)
        return value
