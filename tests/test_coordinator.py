"""Tests for OpenDroneID coordinator."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from custom_components.opendroneid.coordinator import OpenDroneIDCoordinator
from custom_components.opendroneid.decoder import (
    BasicIDMessage,
    DroneData,
    IDType,
    LocationMessage,
    OperationalStatus,
    OperatorIDMessage,
    SystemMessage,
    UAType,
)


@pytest.mark.asyncio
async def test_coordinator_init(mock_hass, mock_config_entry, mock_bluetooth):
    """Test coordinator initialization."""
    coordinator = OpenDroneIDCoordinator(mock_hass, mock_config_entry)

    assert coordinator.hass == mock_hass
    assert coordinator.config_entry == mock_config_entry
    assert coordinator.data == {}
    assert coordinator._cancel_bluetooth_callback is None


@pytest.mark.asyncio
async def test_coordinator_async_setup(mock_hass, mock_config_entry, mock_bluetooth):
    """Test coordinator setup."""
    coordinator = OpenDroneIDCoordinator(mock_hass, mock_config_entry)

    await coordinator.async_setup()

    # Verify BLE callback was registered
    mock_bluetooth.assert_called_once()


@pytest.mark.asyncio
async def test_coordinator_async_shutdown(mock_hass, mock_config_entry, mock_bluetooth):
    """Test coordinator shutdown."""
    coordinator = OpenDroneIDCoordinator(mock_hass, mock_config_entry)
    coordinator._cancel_bluetooth_callback = MagicMock()

    await coordinator.async_shutdown()

    coordinator._cancel_bluetooth_callback.assert_called_once()


@pytest.mark.asyncio
async def test_handle_basic_id_message(mock_hass, mock_config_entry, mock_bluetooth):
    """Test handling Basic ID BLE message."""
    coordinator = OpenDroneIDCoordinator(mock_hass, mock_config_entry)

    # Create mock BLE service info
    service_info = MagicMock()
    service_info.address = "AA:BB:CC:DD:EE:FF"
    service_info.rssi = -50
    service_info.service_data = {
        "0000fffa-0000-1000-8000-00805f9b34fb": bytes([0x0D, 0x42])
        + bytes([0x01, 0x02])
        + b"TESTDRONE"
        + bytes(13)
        + bytes(3)
    }

    with patch.object(coordinator, "async_set_updated_data") as mock_update:
        coordinator._async_handle_bluetooth_event(service_info, None)

        assert "aabbccddeeff" in coordinator.data
        drone = coordinator.data["aabbccddeeff"]
        assert drone.uas_id == "TESTDRONE"
        assert drone.rssi == -50

        mock_update.assert_called_once()


def test_remove_inactive_drones(mock_hass, mock_config_entry):
    """Test removing inactive drones."""
    coordinator = OpenDroneIDCoordinator(mock_hass, mock_config_entry)

    # Add two drones
    now = time.time()
    coordinator.data["drone1"] = DroneData(source_address="AA:BB:CC:DD:EE:01")
    coordinator.data["drone1"].last_seen = now - 400  # Old
    coordinator.data["drone2"] = DroneData(source_address="AA:BB:CC:DD:EE:02")
    coordinator.data["drone2"].last_seen = now - 10  # Recent

    with patch.object(coordinator, "async_set_updated_data"):
        removed = coordinator.async_remove_inactive_drones()

    assert "drone1" in removed
    assert "drone2" not in removed
    assert "drone1" not in coordinator.data
    assert "drone2" in coordinator.data


@pytest.mark.asyncio
async def test_dragonsync_disabled(mock_hass, mock_config_entry, mock_bluetooth):
    """Test DragonSync when disabled."""
    mock_config_entry.options["dragonsync_enabled"] = False

    coordinator = OpenDroneIDCoordinator(mock_hass, mock_config_entry)
    await coordinator.async_setup()

    assert coordinator._zmq_socket is None


@pytest.mark.asyncio
async def test_dragonsync_enabled(mock_hass, mock_config_entry, mock_bluetooth):
    """Test DragonSync when enabled."""
    mock_config_entry.options["dragonsync_enabled"] = True
    mock_config_entry.options["dragonsync_host"] = "localhost"
    mock_config_entry.options["dragonsync_port"] = 4224

    with patch("custom_components.opendroneid.coordinator.zmq") as mock_zmq:
        mock_context = MagicMock()
        mock_socket = MagicMock()
        mock_zmq.Context.return_value = mock_context
        mock_context.socket.return_value = mock_socket

        coordinator = OpenDroneIDCoordinator(mock_hass, mock_config_entry)
        await coordinator.async_setup()

        mock_socket.connect.assert_called_once_with("tcp://localhost:4224")
