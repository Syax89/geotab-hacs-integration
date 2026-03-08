"""Sensor platform for Geotab."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from homeassistant.util import dt as dt_util

from .const import DOMAIN, PA_TO_PSI
from .entity import GeotabEntity
from . import trip_stats


@dataclass(frozen=True, kw_only=True)
class GeotabSensorEntityDescription(SensorEntityDescription):
    """Describes a Geotab sensor entity."""

    value_fn: Callable[[dict], StateType]


SENSORS: tuple[GeotabSensorEntityDescription, ...] = (
    # ── Primary Status ──────────────────────────────────────────────────
    GeotabSensorEntityDescription(
        key="odometer",
        name="Odometer",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.get("odometer", 0) / 1000 if data.get("odometer") is not None else None
        ),
    ),
    GeotabSensorEntityDescription(
        key="fuel_level",
        name="Fuel Level",
        icon="mdi:gas-station",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("fuel_level"),
    ),
    # ── Performance & Driving ───────────────────────────────────────────
    GeotabSensorEntityDescription(
        key="speed",
        name="Speed",
        icon="mdi:speedometer",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("speed"),
    ),
    GeotabSensorEntityDescription(
        key="fuel_rate",
        name="Fuel Rate",
        icon="mdi:fuel",
        native_unit_of_measurement="L/h",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.get("fuel_rate", 0) if data.get("ignition") == 1 else 0
        ),
        entity_registry_enabled_default=False,
    ),
    # ── Engine & Health (Diagnostics) ──────────────────────────────────
    GeotabSensorEntityDescription(
        key="voltage",
        name="Battery Voltage",
        icon="mdi:car-battery",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        value_fn=lambda data: data.get("voltage"),
    ),
    GeotabSensorEntityDescription(
        key="rpm",
        name="Engine Speed",
        icon="mdi:engine-outline",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        value_fn=lambda data: (
            data.get("rpm", 0) if data.get("ignition") == 1 else 0
        ),
        entity_registry_enabled_default=False,
    ),
    GeotabSensorEntityDescription(
        key="engine_hours",
        name="Engine Hours",
        icon="mdi:timer-outline",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.get("engine_hours", 0) / 3600
            if data.get("engine_hours") is not None
            else None
        ),
    ),
    GeotabSensorEntityDescription(
        key="engine_load",
        name="Engine Load",
        icon="mdi:engine",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("engine_load"),
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
        suggested_display_precision=1,
        value_fn=lambda data: data.get("coolant_temp"),
        entity_registry_enabled_default=False,
    ),
    GeotabSensorEntityDescription(
        key="oil_temp",
        name="Engine Oil Temperature",
        icon="mdi:oil-temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("oil_temp"),
        entity_registry_enabled_default=False,
    ),
    GeotabSensorEntityDescription(
        key="oil_pressure",
        name="Engine Oil Pressure",
        icon="mdi:gauge",
        native_unit_of_measurement=UnitOfPressure.KPA,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.get("oil_pressure") / 1000
            if data.get("oil_pressure") is not None
            else None
        ),
        entity_registry_enabled_default=False,
    ),
    # ── Environmental & Chassis (Diagnostics) ───────────────────────────
    GeotabSensorEntityDescription(
        key="ambient_temp",
        name="Ambient Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("ambient_temp"),
        entity_registry_enabled_default=False,
    ),
    GeotabSensorEntityDescription(
        key="transmission_temp",
        name="Transmission Temperature",
        icon="mdi:car-cog",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("transmission_temp"),
        entity_registry_enabled_default=False,
    ),
    GeotabSensorEntityDescription(
        key="tire_pressure_front_left",
        name="Tire Pressure Front Left",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: (data.get("tire_pressure_front_left") or 0) * PA_TO_PSI,
    ),
    GeotabSensorEntityDescription(
        key="tire_pressure_front_right",
        name="Tire Pressure Front Right",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: (data.get("tire_pressure_front_right") or 0) * PA_TO_PSI,
    ),
    GeotabSensorEntityDescription(
        key="tire_pressure_rear_left",
        name="Tire Pressure Rear Left",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: (data.get("tire_pressure_rear_left") or 0) * PA_TO_PSI,
    ),
    GeotabSensorEntityDescription(
        key="tire_pressure_rear_right",
        name="Tire Pressure Rear Right",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: (data.get("tire_pressure_rear_right") or 0) * PA_TO_PSI,
    ),
    GeotabSensorEntityDescription(
        key="accelerator_pos",
        name="Accelerator Position",
        icon="mdi:car-speed-limiter",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.get("accelerator_pos", 0) if data.get("ignition") == 1 else 0
        ),
        entity_registry_enabled_default=False,
    ),
    GeotabSensorEntityDescription(
        key="throttle_pos",
        name="Throttle Position",
        icon="mdi:circle-slice-8",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.get("throttle_pos", 0) if data.get("ignition") == 1 else 0
        ),
        entity_registry_enabled_default=False,
    ),
    # ── Trip Statistics ─────────────────────────────────────────────────
    GeotabSensorEntityDescription(
        key="last_trip_distance",
        name="Last Trip Distance",
        icon="mdi:map-marker-distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: (
            data.get("last_trip", {}).get("distance")
            if data.get("last_trip")
            else None
        ),
    ),
    GeotabSensorEntityDescription(
        key="daily_distance",
        name="Daily Distance",
        icon="mdi:map-marker-path",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: trip_stats.daily_distance(
            data.get("trip_history", [])
        ),
        entity_registry_enabled_default=False,
    ),
    GeotabSensorEntityDescription(
        key="weekly_distance",
        name="Weekly Distance",
        icon="mdi:map-marker-path",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: trip_stats.weekly_distance(
            data.get("trip_history", [])
        ),
        entity_registry_enabled_default=False,
    ),
    GeotabSensorEntityDescription(
        key="monthly_distance",
        name="Monthly Distance",
        icon="mdi:map-marker-path",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: trip_stats.monthly_distance(
            data.get("trip_history", [])
        ),
        entity_registry_enabled_default=False,
    ),
    GeotabSensorEntityDescription(
        key="daily_trip_count",
        name="Daily Trip Count",
        icon="mdi:counter",
        native_unit_of_measurement="trips",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: trip_stats.daily_trip_count(
            data.get("trip_history", [])
        ),
        entity_registry_enabled_default=False,
    ),
    GeotabSensorEntityDescription(
        key="weekly_trip_count",
        name="Weekly Trip Count",
        icon="mdi:counter",
        native_unit_of_measurement="trips",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: trip_stats.weekly_trip_count(
            data.get("trip_history", [])
        ),
        entity_registry_enabled_default=False,
    ),
    GeotabSensorEntityDescription(
        key="average_trip_speed",
        name="Avg Trip Speed (7d)",
        icon="mdi:speedometer",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: trip_stats.average_trip_speed(
            data.get("trip_history", [])
        ),
        entity_registry_enabled_default=False,
    ),
    GeotabSensorEntityDescription(
        key="weekly_idle_time",
        name="Weekly Idle Time",
        icon="mdi:timer-sand",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: trip_stats.total_idle_time_weekly(
            data.get("trip_history", [])
        ),
        entity_registry_enabled_default=False,
    ),
    # ── System (Diagnostics) ────────────────────────────────────────────
    GeotabSensorEntityDescription(
        key="last_update",
        name="Last Update",
        icon="mdi:clock-check",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: (
            dt_util.parse_datetime(data.get("dateTime"))
            if isinstance(data.get("dateTime"), str)
            else data.get("dateTime")
        ),
    ),
)



async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Geotab sensor platform."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Track which devices we've already added entities for
    known_devices = set()

    @callback
    def async_add_new_entities():
        """Add new entities when a new device is discovered."""
        new_entities = []
        for device_id in coordinator.data:
            if device_id not in known_devices:
                for description in SENSORS:
                    new_entities.append(GeotabSensor(coordinator, device_id, description))
                known_devices.add(device_id)

        if new_entities:
            async_add_entities(new_entities)

    # Add initial entities
    async_add_new_entities()

    # Listen for coordinator updates to add new devices dynamically
    entry.async_on_unload(coordinator.async_add_listener(async_add_new_entities))


class GeotabSensor(GeotabEntity, SensorEntity):
    """A Geotab sensor."""

    entity_description: GeotabSensorEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_id: str,
        description: GeotabSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.device_data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.entity_description.key == "last_trip_distance":
            if trip := self.device_data.get("last_trip"):
                return {
                    "start": trip.get("start"),
                    "stop": trip.get("stop"),
                    "maximum_speed": trip.get("maximumSpeed"),
                    "driving_duration": trip.get("drivingDuration"),
                    "idling_duration": trip.get("idlingDuration"),
                }
        return None
