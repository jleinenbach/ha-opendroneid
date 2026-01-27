"""Test fixtures for OpenDroneID."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.opendroneid.const import (
    CONF_INACTIVE_TIMEOUT,
    DEFAULT_INACTIVE_TIMEOUT,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None, None, None]:
    """Enable custom integrations."""
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Create mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={CONF_INACTIVE_TIMEOUT: DEFAULT_INACTIVE_TIMEOUT},
        entry_id="test_entry_id",
        title="OpenDroneID BLE Receiver",
    )


@pytest.fixture
def mock_bluetooth() -> Generator[None, None, None]:
    """Mock bluetooth integration."""
    with patch(
        "homeassistant.components.bluetooth.async_register_callback"
    ) as mock_register:
        mock_register.return_value = lambda: None
        yield
