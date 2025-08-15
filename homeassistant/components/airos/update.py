"""AirOS update_entity."""

from __future__ import annotations

import logging

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import AirOSRuntimeData, AirOSUpdateCoordinator
from .entity import AirOSEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry[AirOSRuntimeData],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the AirOS update platform."""
    runtime_data = config_entry.runtime_data
    update_coordinator = runtime_data.update_coordinator

    async_add_entities(
        [
            AirOSUpdateEntity(
                update_coordinator,
                runtime_data,
            )
        ]
    )


class AirOSUpdateEntity(AirOSEntity, UpdateEntity):
    """Firmware update entity for airOS devices."""

    _attr_translation_key = "firmware_update"
    _attr_has_entity_name = True
    _attr_title = "airOS"
    _attr_supported_features = (UpdateEntityFeature.INSTALL,)

    def __init__(
        self,
        coordinator: AirOSUpdateCoordinator,
        runtime_data: AirOSRuntimeData,
    ) -> None:
        """Initialize the update entity."""
        super().__init__(coordinator, runtime_data)
        self._runtime_data = runtime_data
        if runtime_data.data_coordinator.data:
            mac = runtime_data.data_coordinator.data.derived.mac
            self._attr_unique_id = f"{mac}_firmware_update"
        else:
            self._attr_unique_id = (
                f"{runtime_data.config_entry.entry_id}_firmware_update"
            )

    @property
    def installed_version(self) -> str | None:
        """Return current installed version."""
        return self._runtime_data.data_coordinator.data.host.fwversion

    @property
    def latest_version(self) -> str | None:
        """Latest version available for installation."""
        # airOS empties the version field if no update available
        if self.coordinator.data:
            return self.coordinator.data.get("version", self.installed_version)
        return None

    #    @property
    #    def release_summary(self) -> str | None:
    #        """Summary of the release notes for the new version."""
    #        if self.coordinator.data:
    #            return self.coordinator.data.get("changelog", None)
    #        return None

    @property
    def release_url(self) -> str | None:
        """URL to the full release notes page."""
        if self.coordinator.data:
            return self.coordinator.data.get("changelog", None)
        return None
