"""Common fixtures for the Ubiquiti airOS tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from airos.airos6 import AirOS6Data
from airos.airos8 import AirOS8Data
import pytest

from homeassistant.components.airos.config_flow import DetectDeviceData
from homeassistant.components.airos.const import DOMAIN
from homeassistant.components.airos.coordinator import AirOSDataDetect
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry, load_json_object_fixture

AirOSData = AirOS6Data | AirOS8Data


@pytest.fixture
def ap_fixture(request: pytest.FixtureRequest):
    """Load fixture data for AP mode."""
    if hasattr(request, "param"):
        json_data = load_json_object_fixture(request.param, DOMAIN)
    else:
        json_data = load_json_object_fixture("airos_loco5ac_ap-ptp.json", DOMAIN)

    try:
        fw_major = int(
            json_data.get("host").get("fwversion", "0.0.0").lstrip("v").split(".", 1)[0]
        )
    except (ValueError, AttributeError):
        raise ValueError("Invalid firmware version in fixture data")

    match fw_major:
        case 6:
            return AirOS6Data.from_dict(json_data)
        case 8:
            return AirOS8Data.from_dict(json_data)
        case _:
            raise ValueError(f"Unsupported firmware major version: {fw_major}")


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.airos.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_airos_client(ap_fixture: AirOSData):
    """Fixture to mock the AirOS API client."""
    with (
        patch("homeassistant.components.airos.AirOS6", autospec=True) as mock_airos6,
        patch("homeassistant.components.airos.AirOS8", autospec=True) as mock_airos8,
    ):
        client = MagicMock()
        client.login = AsyncMock(return_value=None)
        client.status = AsyncMock(return_value=ap_fixture)

        mock_airos6.return_value = client
        mock_airos8.return_value = client

        yield client


@pytest.fixture(autouse=True)
def mock_async_get_firmware_data(ap_fixture: AirOSDataDetect):
    """Fixture to mock async_get_firmware_data to not do a network call."""
    fw_major = int(ap_fixture.host.fwversion.lstrip("v").split(".", 1)[0])
    return_value = DetectDeviceData(
        fw_major=fw_major,
        mac=ap_fixture.derived.mac,
        hostname=ap_fixture.host.hostname,
    )
    with (
        patch(
            "homeassistant.components.airos.config_flow.async_get_firmware_data",
            new=AsyncMock(return_value=return_value),
        ) as mock_config_flow_firmware,
        patch(
            "homeassistant.components.airos.async_get_firmware_data",
            new=AsyncMock(return_value=return_value),
        ) as mock_init_firmware,
    ):
        yield mock_config_flow_firmware, mock_init_firmware


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the AirOS mocked config entry."""
    return MockConfigEntry(
        title="NanoStation",
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_USERNAME: "ubnt",
        },
        unique_id="01:23:45:67:89:AB",
    )
