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
        translation_key="odometer",
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
        key="odometer_raw",
        translation_key="odometer_raw",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.get("odometer_raw", 0) / 1000 if data.get("odometer_raw") is not None else None
        ),
        entity_registry_enabled_default=False,
    ),


    GeotabSensorEntityDescription(
        key="total_distance",
        translation_key="total_distance",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.get("total_distance", 0) / 1000 if data.get("total_distance") is not None else None
        ),
        entity_registry_enabled_default=False,
    ),

    GeotabSensorEntityDescription(
        key="fuel_level",
        translation_key="fuel_level",
        icon="mdi:gas-station",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("fuel_level"),
    ),
    GeotabSensorEntityDescription(
        key="fuel_level_raw",
        translation_key="fuel_level_raw",
        icon="mdi:gas-station-outline",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("fuel_level_raw"),
        entity_registry_enabled_default=False,
    ),
    # ── Performance & Driving ───────────────────────────────────────────
    GeotabSensorEntityDescription(
        key="speed",
        translation_key="speed",
        icon="mdi:speedometer",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("speed"),
    ),
    GeotabSensorEntityDescription(
        key="fuel_rate",
        translation_key="fuel_rate",
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
        translation_key="voltage",
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
        translation_key="rpm",
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
        translation_key="engine_hours",
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
        translation_key="engine_load",
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
        translation_key="coolant_temp",
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
        translation_key="oil_temp",
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
        translation_key="oil_pressure",
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
        translation_key="ambient_temp",
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
        translation_key="transmission_temp",
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
        translation_key="tire_pressure_front_left",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.get("tire_pressure_front_left") * PA_TO_PSI
            if data.get("tire_pressure_front_left") is not None
            else None
        ),
    ),
    GeotabSensorEntityDescription(
        key="tire_pressure_front_right",
        translation_key="tire_pressure_front_right",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.get("tire_pressure_front_right") * PA_TO_PSI
            if data.get("tire_pressure_front_right") is not None
            else None
        ),
    ),
    GeotabSensorEntityDescription(
        key="tire_pressure_rear_left",
        translation_key="tire_pressure_rear_left",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.get("tire_pressure_rear_left") * PA_TO_PSI
            if data.get("tire_pressure_rear_left") is not None
            else None
        ),
    ),
    GeotabSensorEntityDescription(
        key="tire_pressure_rear_right",
        translation_key="tire_pressure_rear_right",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.get("tire_pressure_rear_right") * PA_TO_PSI
            if data.get("tire_pressure_rear_right") is not None
            else None
        ),
    ),
    GeotabSensorEntityDescription(
        key="accelerator_pos",
        translation_key="accelerator_pos",
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
        translation_key="throttle_pos",
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
        translation_key="last_trip_distance",
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
        translation_key="daily_distance",
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
        translation_key="weekly_distance",
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
        translation_key="monthly_distance",
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
        translation_key="daily_trip_count",
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
        translation_key="weekly_trip_count",
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
        translation_key="average_trip_speed",
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
        translation_key="weekly_idle_time",
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
        translation_key="last_update",
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
