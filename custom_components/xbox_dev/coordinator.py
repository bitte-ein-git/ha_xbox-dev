# coordinator.py

"""DataUpdateCoordinator for the Xbox Dev Mode integration."""
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import requests

from .const import DOMAIN, SCAN_INTERVAL_SECONDS, CONF_IP_ADDRESS, CONF_USERNAME, CONF_PASSWORD
from .api import XboxOneDevmodeApi

_LOGGER = logging.getLogger(__name__)


class XboxDevUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Xbox Dev Mode data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.api = XboxOneDevmodeApi(
            entry.data[CONF_IP_ADDRESS],
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD]
        )
        self.entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            data = await self.hass.async_add_executor_job(self._fetch_data)
            return data
        except (requests.RequestException, requests.exceptions.JSONDecodeError, ConnectionError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error during update: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def _fetch_data(self) -> dict[str, Any]:
        """Fetch synchronous data."""
        processes = self.api.get_processes()
        system_perf = self.api.get_system_performance()
        
        running_app_info = self._get_running_app(processes)
        gpu_info = self._get_gpu_info(system_perf)

        return {
            "machine_name": self.api.get_machinename(),
            "connected_controllers": self.api.get_connectedcontrollercount(),
            "device_id": self.api.get_deviceid(),
            "serial_number": self.api.get_serialnumber(),
            "language": self.api.get_language(),
            "running_app": running_app_info.get("app_name_formatted"),
            "cpu_load": system_perf.get("CpuLoad"),
            "io_read_speed": system_perf.get("IOReadSpeed"),
            "io_write_speed": system_perf.get("IOWriteSpeed"),
            "io_other_speed": system_perf.get("IOOtherSpeed"),
            "gpu_memory_used": gpu_info.get("used"),
            "gpu_memory_total": gpu_info.get("total"),
        }

    @staticmethod
    def _get_running_app(processes: list[dict]) -> dict:
        """Parse process list to find the primary running app."""
        running_apps = [p for p in processes if p.get("IsRunning")]
        
        excluded_apps = ["Guide.exe", "RuntimeBroker.exe"]
        filtered_apps = [p for p in running_apps if p.get("ImageName") not in excluded_apps]

        app_to_process = filtered_apps if filtered_apps else running_apps
        
        if not app_to_process:
            return {"app_name_formatted": "None"}

        app = app_to_process[0]
        app_name = app.get("AppName", "Unknown")
        image_name = app.get("ImageName", "unknown.exe")

        return {"app_name_formatted": f"{app_name} ({image_name})"}
    
    @staticmethod
    def _get_gpu_info(system_perf: dict) -> dict:
        """Extract GPU memory info."""
        try:
            gpu_data = system_perf.get("GPUData", {})
            adapter = gpu_data.get("AvailableAdapters", [{}])[0]
            used = adapter.get("DedicatedMemoryUsed", 0)
            total = adapter.get("DedicatedMemory", 0)
            return {"used": used, "total": total}
        except (IndexError, TypeError):
            return {"used": 0, "total": 0}