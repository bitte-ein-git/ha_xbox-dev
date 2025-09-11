# camera.py

"""Camera platform for the Xbox Dev Mode integration."""
import logging
from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import XboxDevUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the camera platform."""
    coordinator: XboxDevUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([XboxDevScreenshotCamera(coordinator, entry)])


class XboxDevScreenshotCamera(Camera):
    """Implementation of an Xbox Dev screenshot camera."""

    def __init__(self, coordinator: XboxDevUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the camera."""
        super().__init__()
        self.coordinator = coordinator
        self._attr_name = "Screenshot"
        self._attr_unique_id = f"{entry.entry_id}_screenshot"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Microsoft",
            model="Xbox DevKit",
        )
        self._image: bytes | None = None
        
    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image response."""
        # Fetch initial image if none exists
        if not self._image:
             await self.async_update_screenshot()
        return self._image

    async def async_update_screenshot(self):
        """Fetch a new screenshot from the Xbox."""
        _LOGGER.debug("Fetching new screenshot")
        try:
            image_bytes = await self.hass.async_add_executor_job(
                self.coordinator.api.get_screenshot
            )
            self._image = image_bytes
            # Notify HA that state has changed
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Failed to fetch screenshot: %s", e)
            self._image = None