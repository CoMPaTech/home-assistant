"""The Ubiquiti airOS integration."""

from __future__ import annotations

from airos.airos6 import AirOS6
from airos.airos8 import AirOS8
from airos.helpers import DetectDeviceData, async_get_firmware_data

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .coordinator import AirOSConfigEntry, AirOSDataUpdateCoordinator

_PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: AirOSConfigEntry) -> bool:
    """Set up Ubiquiti airOS from a config entry."""

    # By default airOS 8 comes with self-signed SSL certificates,
    # with no option in the web UI to change or upload a custom certificate.
    session = async_get_clientsession(hass, verify_ssl=False)

    conn_data = {
        CONF_HOST: entry.data[CONF_HOST],
        CONF_USERNAME: entry.data[CONF_USERNAME],
        CONF_PASSWORD: entry.data[CONF_PASSWORD],
        "session": session,
    }

    # Determine firmware version before creating the device instance
    device_data: DetectDeviceData = await async_get_firmware_data(**conn_data)
    airos_class: type[AirOS8 | AirOS6] = AirOS8
    if device_data["fw_major"] == 6:
        airos_class = AirOS6

    airos_device = airos_class(**conn_data)

    coordinator = AirOSDataUpdateCoordinator(hass, entry, device_data, airos_device)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: AirOSConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
