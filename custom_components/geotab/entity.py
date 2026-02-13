"""Base entity for Geotab integration."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN


class GeotabEntity(CoordinatorEntity):
    """Base Geotab entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id

    @property
    def device_data(self) -> dict:
        """Return the device data for this entity."""
        return self.coordinator.data[self._device_id]

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        database = self.coordinator.config_entry.data.get("database", "Unknown")
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
