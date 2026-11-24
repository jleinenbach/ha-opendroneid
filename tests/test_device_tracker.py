"""Tests for OpenDroneID device_tracker."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.opendroneid.decoder import DroneData, IDType, UAType


@pytest.mark.asyncio
async def test_device_tracker_setup(mock_hass, mock_config_entry, mock_bluetooth):
    """Test device tracker setup."""
    from custom_components.opendroneid.device_tracker import async_setup_entry

    mock_coordinator = MagicMock()
    mock_coordinator.data = {}
    mock_coordinator.async_add_listener = MagicMock()
    mock_config_entry.runtime_data = MagicMock()
    mock_config_entry.runtime_data.coordinator = mock_coordinator

    mock_add_entities = AsyncMock()

    await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

    # Verify listener was added
    mock_coordinator.async_add_listener.assert_called_once()


@pytest.mark.asyncio
async def test_device_tracker_entity_creation(mock_hass, mock_config_entry):
    """Test device tracker entity creation."""
    from custom_components.opendroneid.device_tracker import DroneDeviceTracker

    mock_coordinator = MagicMock()
    drone_id = "testdrone"
    drone_data = DroneData(
        source_address="AA:BB:CC:DD:EE:FF",
        uas_id="TEST123",
        id_type=IDType.SERIAL_NUMBER,
        ua_type=UAType.HELICOPTER,
        latitude=49.86625,
        longitude=10.83948,
        altitude_geo=283.0,
        rssi=-50,
    )
    mock_coordinator.data = {drone_id: drone_data}

    tracker = DroneDeviceTracker(mock_coordinator, drone_id, drone_data)

    assert tracker.name == "Drone TEST123"
    assert tracker.unique_id == "opendroneid_testdrone"
    assert tracker.latitude == 49.86625
    assert tracker.longitude == 10.83948


@pytest.mark.asyncio
async def test_device_tracker_trust_attributes(mock_hass, mock_config_entry):
    """Test trust assessment attributes are exposed."""
    from custom_components.opendroneid.device_tracker import DroneDeviceTracker

    mock_coordinator = MagicMock()
    drone_id = "testdrone"
    drone_data = DroneData(
        source_address="AA:BB:CC:DD:EE:FF",
        uas_id="TEST123",
        id_type=IDType.SERIAL_NUMBER,
        ua_type=UAType.HELICOPTER,
    )
    drone_data.trust_verdict = "suspicious"
    drone_data.trust_reasons = ["teleport"]
    drone_data.trust_score = 0.25
    drone_data.trust_alert = True
    mock_coordinator.data = {drone_id: drone_data}

    tracker = DroneDeviceTracker(mock_coordinator, drone_id, drone_data)
    attrs = tracker.extra_state_attributes

    assert attrs["trust_verdict"] == "suspicious"
    assert attrs["trust_reasons"] == ["teleport"]
    assert attrs["trust_score"] == 0.25
    assert attrs["trust_alert"] is True


@pytest.mark.asyncio
async def test_device_tracker_no_trust_attributes_before_assessment(
    mock_hass, mock_config_entry
):
    """Test trust attributes are absent until a verdict exists."""
    from custom_components.opendroneid.device_tracker import DroneDeviceTracker

    mock_coordinator = MagicMock()
    drone_id = "testdrone"
    drone_data = DroneData(source_address="AA:BB:CC:DD:EE:FF")
    mock_coordinator.data = {drone_id: drone_data}

    tracker = DroneDeviceTracker(mock_coordinator, drone_id, drone_data)
    attrs = tracker.extra_state_attributes

    assert "trust_verdict" not in attrs
    assert "trust_reasons" not in attrs
    assert "trust_score" not in attrs
    assert "trust_alert" not in attrs
