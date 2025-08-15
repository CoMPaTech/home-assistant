"""Generic AirOS Entity Class."""

from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import AirOSDataCoordinator, AirOSRuntimeData, AirOSUpdateCoordinator


class AirOSEntity(CoordinatorEntity):
    """Represent a AirOS Entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AirOSDataCoordinator | AirOSUpdateCoordinator,
        runtime_data: AirOSRuntimeData,
    ) -> None:
        """Initialise the gateway."""
        super().__init__(coordinator)
        self._runtime_data = runtime_data

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return the device info."""
        data_coordinator = self._runtime_data.data_coordinator
        # Prevent other coordinator(s) updating ahead of data_coordinator
        if not data_coordinator.data:
            return None

        airos_data = data_coordinator.data

        configuration_url: str | None = (
            f"https://{self.coordinator.config_entry.data[CONF_HOST]}"
        )

        return DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, airos_data.derived.mac)},
            configuration_url=configuration_url,
            identifiers={(DOMAIN, str(airos_data.host.device_id))},
            manufacturer=MANUFACTURER,
            model=airos_data.host.devmodel,
            name=airos_data.host.hostname,
            sw_version=airos_data.host.fwversion,
        )
