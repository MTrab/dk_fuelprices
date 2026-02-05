"""Sensor platform for Braendstofpriser integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify as util_slugify

from .api import APIClient
from .const import ATTR_COORDINATOR, DOMAIN

SENSORS = [
    SensorEntityDescription(
        key="price",
        name="Fuel Price",
        native_unit_of_measurement="DKK/L",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:gas-station",
    ),
    SensorEntityDescription(
        key="last_updated",
        name="Last Updated",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline",
    ),
]


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up sensor platform for Braendstofpriser integration."""

    subentries = hass.data[DOMAIN][entry.entry_id]["subentries"]

    sensors = []
    for subentry_data in subentries.values():
        coordinator = subentry_data[ATTR_COORDINATOR]
        subentry_sensors = []
        for sensor in SENSORS:
            if sensor.key == "last_updated":
                subentry_sensors.append(
                    BraendstofpriserSensor(
                        coordinator,
                        "last_updated",
                        "last_updated",
                        sensor,
                    )
                )
            else:
                for product_key, product_info in coordinator.products.items():
                    subentry_sensors.append(
                        BraendstofpriserSensor(
                            coordinator,
                            product_key,
                            product_info["name"],
                            sensor,
                        )
                    )

        async_add_devices(
            subentry_sensors,
            True,
            config_subentry_id=coordinator.subentry_id,
        )


class BraendstofpriserSensor(CoordinatorEntity[APIClient], RestoreSensor):
    """Sensor for Braendstofpriser integration."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, product_key, product_name, description):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description

        self._product_key = product_key
        self._product_name = product_name

        if description.key == "last_updated":
            self._attr_name = "Last Updated"
        else:
            self._attr_name = f"{product_name}"

        self._attr_unique_id = util_slugify(
            f"{self.coordinator.subentry_id}_{self.entity_description.key}_{product_key}"
        )
        self._attr_config_subentry_id = self.coordinator.subentry_id

        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    self.coordinator.subentry_id,
                )
            },
            name=self.coordinator.station_name,
            manufacturer=self.coordinator.company,
            model=self.coordinator.station_name,
        )

        self._attr_native_value = self.get_value()

    def get_value(self):
        """Get the current value of the sensor."""
        if self.entity_description.key == "last_updated":
            return self.coordinator.updated_at

        return self.coordinator.products[self._product_key]["price"]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        value = self.get_value()

        if value is not None:
            self._attr_native_value = self.get_value()

        self.schedule_update_ha_state()
