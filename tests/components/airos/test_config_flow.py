"""Test the Ubiquiti airOS config flow."""

from unittest.mock import AsyncMock, patch

from airos.exceptions import (
    AirOSConnectionAuthenticationError,
    AirOSDeviceConnectionError,
    AirOSKeyDataMissingError,
)
import pytest

from homeassistant.components.airos.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry

MOCK_CONFIG = {
    CONF_HOST: "1.1.1.1",
    CONF_USERNAME: "ubnt",
    CONF_PASSWORD: "test-password",
}


@pytest.mark.parametrize(
    ("ap_fixture", "hostname", "mac", "fw_major"),
    [
        (
            "airos_NanoStation_M5_sta_v6.3.16.json",
            "NanoStation M5",
            "XX:XX:XX:XX:XX:XX",
            6,
        ),
        (
            "airos_loco5ac_ap-ptp.json",
            "NanoStation 5AC ap name",
            "01:23:45:67:89:AB",
            8,
        ),
    ],
    indirect=["ap_fixture"],
)
async def test_form_creates_entry(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_async_get_firmware_data: AsyncMock,
    mock_airos_client: AsyncMock,
    hostname: str,
    mac: str,
    fw_major: int,
) -> None:
    """Test we get the form and create the appropriate entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_CONFIG,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == hostname
    assert result["result"].unique_id == mac
    assert result["data"] == MOCK_CONFIG

    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_duplicate_entry(
    hass: HomeAssistant,
    mock_airos_client: AsyncMock,
    mock_async_get_firmware_data: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the form does not allow duplicate entries."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_CONFIG,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize(
    ("exception", "error"),
    [
        (AirOSConnectionAuthenticationError, "invalid_auth"),
        (AirOSDeviceConnectionError, "cannot_connect"),
        (AirOSKeyDataMissingError, "key_data_missing"),
        (Exception, "unknown"),
    ],
)
async def test_form_exception_handling(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_airos_client: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test we handle exceptions."""
    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        side_effect=exception,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_CONFIG,
        )

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": error}
