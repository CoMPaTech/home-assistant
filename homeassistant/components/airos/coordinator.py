"""DataUpdateCoordinators for AirOS."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta
import logging
from typing import Any, TypeVar, NamedTuple

from airos.airos8 import AirOS, AirOSData
from airos.exceptions import (
    AirOSConnectionAuthenticationError,
    AirOSConnectionSetupError,
    AirOSDataMissingError,
    AirOSDeviceConnectionError,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

AirOSRuntimeData = NamedTuple(
    "AirOSRuntimeData", ["data_coordinator", "update_coordinator"]
)

DataT = TypeVar("DataT")
type AirOSConfigEntry = ConfigEntry[AirOSRuntimeData]


class AirOSBaseCoordinator(DataUpdateCoordinator[DataT], ABC):
    """Base class to manage fetching data from AirOS endpoints."""

    config_entry: AirOSConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: AirOSConfigEntry,
        airos_device: AirOS,
        name: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        self.airos_device = airos_device
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
            config_entry=config_entry,
        )

    async def _async_update_data(self) -> DataT:
        """Fetch data from AirOS."""
        try:
            await self.airos_device.login()
            return await self._async_fetch_data()
        except (AirOSConnectionAuthenticationError,) as err:
            _LOGGER.exception("Error authenticating with airOS device")
            raise ConfigEntryError(
                translation_domain=DOMAIN, translation_key="invalid_auth"
            ) from err
        except (
            AirOSConnectionSetupError,
            AirOSDeviceConnectionError,
            TimeoutError,
        ) as err:
            _LOGGER.error("Error connecting to airOS device: %s", err)
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
            ) from err
        except (AirOSDataMissingError,) as err:
            _LOGGER.error("Expected data not returned by airOS device: %s", err)
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="error_data_missing",
            ) from err

    @abstractmethod
    async def _async_fetch_data(self) -> DataT:
        """Function for subclasses on specific data fetch."""


class AirOSDataCoordinator(AirOSBaseCoordinator[AirOSData]):
    """Class to manage fetching AirOS data from single endpoint."""

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, airos_device: AirOS
    ) -> None:
        """Initialize the data coordinator."""
        super().__init__(
            hass,
            config_entry,
            airos_device,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_fetch_data(self) -> AirOSData:
        """Fetch status-data from AirOS."""
        return await self.airos_device.status()


class AirOSUpdateCoordinator(AirOSBaseCoordinator[dict[str, Any]]):
    """Class to manage fetching AirOS update data."""

    config_entry: AirOSConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: AirOSConfigEntry, airos_device: AirOS
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            config_entry,
            airos_device,
            name=f"{DOMAIN}_update",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_fetch_data(self) -> dict[str, Any]:
        """Fetch status-data from AirOS."""
        return await self.airos_device.update_check()
