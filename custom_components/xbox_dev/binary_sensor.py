# binary_sensor.py

"""Binary sensor platform for the Xbox Dev Mode integration."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XboxDevUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator: XboxDevUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([XboxDevStatusSensor(coordinator, entry)])


class XboxDevStatusSensor(CoordinatorEntity[XboxDevUpdateCoordinator], BinarySensorEntity):
    """Implementation of an Xbox Dev Mode status sensor."""

    def __init__(self, coordinator: XboxDevUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Status"
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Microsoft",
            model="Xbox DevKit",
        )

    @property
    def is_on(self) -> bool:
        """Return true if the device is online."""
        return self.coordinator.last_update_success