"""Tests for OpenDroneID diagnostics."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.opendroneid.decoder import DroneData


@pytest.mark.asyncio
async def test_async_get_config_entry_diagnostics(mock_hass, mock_config_entry):
    """Test diagnostics."""
    from custom_components.opendroneid.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    mock_coordinator = MagicMock()
    drone_data = DroneData(source_address="AA:BB:CC:DD:EE:FF", uas_id="TEST123")
    mock_coordinator.data = {"test": drone_data}

    mock_config_entry.runtime_data = MagicMock()
    mock_config_entry.runtime_data.coordinator = mock_coordinator

    result = await async_get_config_entry_diagnostics(mock_hass, mock_config_entry)

    assert result["entry_id"] == "test_entry_id"
    assert result["drone_count"] == 1
    assert "drones" in result
