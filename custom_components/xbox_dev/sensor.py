# sensor.py

"""Sensor platform for the Xbox Dev Mode integration."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfDataRate, PERCENTAGE
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XboxDevUpdateCoordinator

@dataclass(frozen=True)
class XboxDevSensorEntityDescription(SensorEntityDescription):
    """Describes an Xbox Dev sensor entity."""
    value_fn: Callable[[dict], float | int | str | None] | None = None

def _calculate_gpu_usage(data: dict) -> float | None:
    """Calculate GPU memory usage percentage."""
    used = data.get("gpu_memory_used")
    total = data.get("gpu_memory_total")
    if used is not None and total is not None and total > 0:
        return round((used / total) * 100, 2)
    return None

def _bytes_to_megabytes(byte_value: int | None) -> float | None:
    """Convert bytes to megabytes."""
    if byte_value is not None:
        return round(byte_value / (1024 * 1024), 2)
    return None

SENSORS: tuple[XboxDevSensorEntityDescription, ...] = (
    XboxDevSensorEntityDescription(
        key="running_app",
        name="Running App",
        icon="mdi:application-braces-outline",
        value_fn=lambda data: data.get("running_app"),
    ),
    XboxDevSensorEntityDescription(
        key="connected_controllers",
        name="Connected Controllers",
        icon="mdi:controller-classic",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("connected_controllers"),
    ),
    XboxDevSensorEntityDescription(
        key="device_id",
        name="Device ID",
        icon="mdi:card-account-details-outline",
        value_fn=lambda data: data.get("device_id"),
    ),
    XboxDevSensorEntityDescription(
        key="serial_number",
        name="Serial Number",
        icon="mdi:barcode-scan",
        value_fn=lambda data: data.get("serial_number"),
    ),
    XboxDevSensorEntityDescription(
        key="language",
        name="Language",
        icon="mdi:earth",
        value_fn=lambda data: data.get("language"),
    ),
    XboxDevSensorEntityDescription(
        key="cpu_load",
        name="CPU Load",
        icon="mdi:cpu-64-bit",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("cpu_load"),
    ),
    XboxDevSensorEntityDescription(
        key="io_read_speed",
        name="IO Read Speed",
        icon="mdi:file-download-outline",
        native_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: _bytes_to_megabytes(data.get("io_read_speed")),
    ),
    XboxDevSensorEntityDescription(
        key="io_write_speed",
        name="IO Write Speed",
        icon="mdi:file-upload-outline",
        native_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: _bytes_to_megabytes(data.get("io_write_speed")),
    ),
    XboxDevSensorEntityDescription(
        key="io_other_speed",
        name="IO Other Speed",
        icon="mdi:file-sync-outline",
        native_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: _bytes_to_megabytes(data.get("io_other_speed")),
    ),
    XboxDevSensorEntityDescription(
        key="gpu_memory_usage",
        name="GPU Memory",
        icon="mdi:memory",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=_calculate_gpu_usage,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: XboxDevUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        XboxDevSensor(coordinator, entry, description)
        for description in SENSORS
    ]
    async_add_entities(entities)


class XboxDevSensor(CoordinatorEntity[XboxDevUpdateCoordinator], SensorEntity):
    """Implementation of an Xbox Dev sensor."""

    entity_description: XboxDevSensorEntityDescription

    def __init__(
        self,
        coordinator: XboxDevUpdateCoordinator,
        entry: ConfigEntry,
        description: XboxDevSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Microsoft",
            model="Xbox DevKit",
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        # return None if coordinator failed
        if not self.coordinator.last_update_success:
            return None
        
        if self.coordinator.data and self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        
        return None