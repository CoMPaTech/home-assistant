"""Test the Ubiquiti airOS update."""

import logging
from unittest.mock import AsyncMock

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import setup_integration

from tests.common import MockConfigEntry, patch

_LOGGER = logging.getLogger("bla")


@pytest.mark.parametrize("update_state", ["available", "latest"])
async def test_no_update(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    mock_airos_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    update_state: str,
    update_fixture,
    ap_fixture,
) -> None:
    """Test no version present."""
    with patch(
        "homeassistant.components.airos.coordinator.AirOSUpdateCoordinator._async_fetch_data",
        return_value=update_fixture,
    ):
        await setup_integration(hass, mock_config_entry, [Platform.UPDATE])

    expected_entity_id = "update.nanostation_5ac_ap_name_none"
    entity_state = hass.states.get(expected_entity_id)

    if update_state == "available":
        assert entity_state.attributes["latest_version"] == "v8.7.19"
    # If latest there is no version in the fixture
    if update_state == "latest":
        assert entity_state.attributes["latest_version"] == ap_fixture.host.fwversion

    assert entity_state.attributes["installed_version"] == ap_fixture.host.fwversion
