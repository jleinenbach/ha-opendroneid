"""Test fixtures for OpenDroneID."""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock homeassistant modules before importing
sys.modules["homeassistant"] = MagicMock()
sys.modules["homeassistant.const"] = MagicMock()
sys.modules["homeassistant.core"] = MagicMock()
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.event"] = MagicMock()
sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()
sys.modules["homeassistant.helpers.entity_platform"] = MagicMock()
sys.modules["homeassistant.components"] = MagicMock()
sys.modules["homeassistant.components.bluetooth"] = MagicMock()
sys.modules["homeassistant.components.device_tracker"] = MagicMock()
sys.modules["homeassistant.components.device_tracker.config_entry"] = MagicMock()
sys.modules["homeassistant.config_entries"] = MagicMock()

from custom_components.opendroneid.const import (
    CONF_DRAGONSYNC_ENABLED,
    CONF_DRAGONSYNC_HOST,
    CONF_DRAGONSYNC_PORT,
    CONF_INACTIVE_TIMEOUT,
    DEFAULT_DRAGONSYNC_PORT,
    DEFAULT_INACTIVE_TIMEOUT,
    DOMAIN,
)


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.config_entries.async_reload = AsyncMock(return_value=True)
    return hass


@pytest.fixture
def mock_config_entry():
    """Create mock config entry."""
    entry = MagicMock()
    entry.domain = DOMAIN
    entry.data = {}
    entry.options = {
        CONF_INACTIVE_TIMEOUT: DEFAULT_INACTIVE_TIMEOUT,
        CONF_DRAGONSYNC_ENABLED: False,
        CONF_DRAGONSYNC_HOST: "",
        CONF_DRAGONSYNC_PORT: DEFAULT_DRAGONSYNC_PORT,
    }
    entry.entry_id = "test_entry_id"
    entry.title = "OpenDroneID BLE Receiver"
    entry.runtime_data = None
    entry.async_on_unload = MagicMock(return_value=None)
    entry.add_update_listener = MagicMock(return_value=lambda: None)
    return entry


@pytest.fixture
def mock_bluetooth():
    """Mock bluetooth integration."""
    with patch(
        "custom_components.opendroneid.coordinator.async_register_callback"
    ) as mock_register:
        mock_register.return_value = lambda: None
        yield mock_register
