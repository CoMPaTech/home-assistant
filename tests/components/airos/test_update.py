"""Test the Ubiquiti airOS update."""

import logging
from unittest.mock import AsyncMock

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import setup_integration

from tests.common import MockConfigEntry, patch, snapshot_platform

_LOGGER = logging.getLogger("bla")


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_all_entities(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    mock_airos_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    update_fixture,
) -> None:
    """Test all entities."""
    with patch(
        "homeassistant.components.airos.coordinator.AirOSUpdateCoordinator._async_fetch_data",
        return_value=update_fixture,
    ):
        await setup_integration(hass, mock_config_entry, [Platform.UPDATE])
    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


async def test_no_update(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    mock_airos_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    update_fixture,
    ap_fixture,
) -> None:
    """Test no version present."""
    update_fixture["version"] = None
    with patch(
        "homeassistant.components.airos.coordinator.AirOSUpdateCoordinator._async_fetch_data",
        return_value=update_fixture,
    ):
        await setup_integration(hass, mock_config_entry, [Platform.UPDATE])

    expected_entity_id = "update.nanostation_5ac_ap_name_none"
    entity_state = hass.states.get(expected_entity_id)

    assert entity_state.attributes["latest_version"] == ap_fixture.host.fwversion
    assert entity_state.attributes["installed_version"] == ap_fixture.host.fwversion
