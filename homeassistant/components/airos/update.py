"""AirOS update_entity."""

from __future__ import annotations

import logging

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import AirOSConfigEntry, AirOSRuntimeData
from .entity import AirOSEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AirOSConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the AirOS update platform."""
    async_add_entities([AirOSUpdateEntity(config_entry.runtime_data)])


class AirOSUpdateEntity(AirOSEntity, UpdateEntity):
    """Firmware update entity for airOS devices."""

    _attr_translation_key = "firmware_update"
    _attr_has_entity_name = True
    _attr_title = "airOS"
    _attr_supported_features = UpdateEntityFeature.INSTALL

    def __init__(
        self,
        runtime_data: AirOSRuntimeData,
    ) -> None:
        """Initialize the update entity."""
        coordinator = runtime_data.update_coordinator

        super().__init__(coordinator, runtime_data)
        self._runtime_data = runtime_data

        mac = self._runtime_data.data_coordinator.data.derived.mac
        self._attr_unique_id = f"{mac}_firmware_update"

    @property
    def installed_version(self) -> str | None:
        """Return current installed version."""
        return str(self._runtime_data.data_coordinator.data.host.fwversion)

    @property
    def latest_version(self) -> str | None:
        """Latest version available for installation."""
        # airOS empties the version field if no update available
        if latest := self.coordinator.data.get("version"):
            return str(latest)
        return self.installed_version

    @property
    def release_url(self) -> str | None:
        """URL to the full release notes page."""
        return str(self.coordinator.data.get("changelog", None))
