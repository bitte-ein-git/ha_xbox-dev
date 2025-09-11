# button.py

"""Button platform for the Xbox Dev Mode integration."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Awaitable, Callable
import logging

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import XboxDevUpdateCoordinator
from .camera import XboxDevScreenshotCamera

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True)
class XboxDevButtonEntityDescription(ButtonEntityDescription):
    """Describes an Xbox Dev button entity."""
    press_action: Callable[[XboxDevUpdateCoordinator], Awaitable] | None = None

async def reboot_action(coordinator: XboxDevUpdateCoordinator):
    """Reboot the Xbox."""
    await coordinator.hass.async_add_executor_job(coordinator.api.reboot)

async def shutdown_action(coordinator: XboxDevUpdateCoordinator):
    """Shutdown the Xbox."""
    await coordinator.hass.async_add_executor_job(coordinator.api.shutdown)

async def disconnect_controllers_action(coordinator: XboxDevUpdateCoordinator):
    """Disconnect controllers."""
    await coordinator.hass.async_add_executor_job(coordinator.api.disconnect_controllers)

async def update_screenshot_action(coordinator: XboxDevUpdateCoordinator):
    """Trigger screenshot update by finding the camera entity and calling its method."""
    registry = er.async_get(coordinator.hass)
    entity_id = registry.async_get_entity_id(
        "camera", DOMAIN, f"{coordinator.entry.entry_id}_screenshot"
    )

    if entity_id:
        camera_entity: XboxDevScreenshotCamera | None = None
        if (platform := coordinator.hass.data.get("camera")):
             camera_entity = platform.get_entity(entity_id)
        
        if camera_entity and isinstance(camera_entity, XboxDevScreenshotCamera):
            _LOGGER.debug("Calling async_update_screenshot on %s", entity_id)
            await camera_entity.async_update_screenshot()
        else:
            _LOGGER.warning("Could not find camera entity object to update screenshot.")
    else:
        _LOGGER.warning("Could not find camera entity_id in registry.")


BUTTONS: tuple[XboxDevButtonEntityDescription, ...] = (
    XboxDevButtonEntityDescription(
        key="reboot",
        name="Reboot",
        icon="mdi:restart",
        press_action=reboot_action,
    ),
    XboxDevButtonEntityDescription(
        key="shutdown",
        name="Shutdown",
        icon="mdi:power",
        press_action=shutdown_action,
    ),
    XboxDevButtonEntityDescription(
        key="disconnect_controllers",
        name="Disconnect Controllers",
        icon="mdi:microsoft-xbox-controller-off",
        press_action=disconnect_controllers_action,
    ),
    XboxDevButtonEntityDescription(
        key="update_screenshot",
        name="Update Screenshot",
        icon="mdi:camera-refresh",
        press_action=update_screenshot_action,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    coordinator: XboxDevUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        XboxDevButton(coordinator, entry, description)
        for description in BUTTONS
    ]
    async_add_entities(entities)


class XboxDevButton(ButtonEntity):
    """Implementation of an Xbox Dev button."""

    entity_description: XboxDevButtonEntityDescription

    def __init__(
        self,
        coordinator: XboxDevUpdateCoordinator,
        entry: ConfigEntry,
        description: XboxDevButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        self.coordinator = coordinator
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Microsoft",
            model="Xbox DevKit",
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        if self.entity_description.press_action:
            await self.entity_description.press_action(self.coordinator)