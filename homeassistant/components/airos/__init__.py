"""The Ubiquiti airOS integration."""

from __future__ import annotations

import logging

from airos.airos8 import AirOS8

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .binary_sensor import BINARY_SENSORS
from .coordinator import AirOSConfigEntry, AirOSDataUpdateCoordinator

_PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: AirOSConfigEntry) -> bool:
    """Set up Ubiquiti airOS from a config entry."""

    # By default airOS 8 comes with self-signed SSL certificates,
    # with no option in the web UI to change or upload a custom certificate.
    session = async_get_clientsession(hass, verify_ssl=False)

    airos_device = AirOS8(
        host=entry.data[CONF_HOST],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        session=session,
    )

    coordinator = AirOSDataUpdateCoordinator(hass, entry, airos_device)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_migrate_entry(hass: HomeAssistant, entry: AirOSConfigEntry) -> bool:
    """Migrate old config entry."""

    if entry.version > 1:
        # This means the user has downgraded from a future version
        return False

    # Introduce SSL
    # code here

    # As v6 has no device_id use mac_address in binary_sensor
    if entry.version == 1 and entry.minor_version == 2:
        entitiy_registry = er.async_get(hass)

        device_id = entry.data.get("host", {}).get("device_id")
        mac = entry.data.get("derived", {}).get("mac")
        if not mac or not device_id:
            _LOGGER.error(
                "Missing device_id or mac for migration, can't migrate binary sensors"
            )
            return False

        binary_sensor_keys = [desc.key for desc in BINARY_SENSORS]
        for key in binary_sensor_keys:
            old_unique_id = f"{device_id}_{key}"
            new_unique_id = f"{mac}_{key}"
            if (entity_entry := entitiy_registry.async_get(old_unique_id)) is not None:
                entitiy_registry.async_update_entity(
                    entity_entry.entity_id, new_unique_id=new_unique_id
                )

        hass.config_entries.async_update_entry(entry, minor_version=3)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: AirOSConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
