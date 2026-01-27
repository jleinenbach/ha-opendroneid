"""Tests for OpenDroneID __init__.py."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.opendroneid import (
    OpenDroneIDData,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.opendroneid.const import CONF_INACTIVE_TIMEOUT


@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass, mock_config_entry, mock_bluetooth):
    """Test async_setup_entry."""
    with patch(
        "custom_components.opendroneid.OpenDroneIDCoordinator"
    ) as mock_coordinator_class, patch(
        "custom_components.opendroneid.async_track_time_interval"
    ) as mock_track_time:
        mock_coordinator = MagicMock()
        mock_coordinator.async_setup = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        mock_track_time.return_value = lambda: None

        result = await async_setup_entry(mock_hass, mock_config_entry)

        assert result is True
        assert mock_config_entry.runtime_data is not None
        assert isinstance(mock_config_entry.runtime_data, OpenDroneIDData)
        assert mock_config_entry.runtime_data.coordinator == mock_coordinator

        # Verify coordinator was set up
        mock_coordinator.async_setup.assert_called_once()

        # Verify platforms were set up
        mock_hass.config_entries.async_forward_entry_setups.assert_called_once()

        # Verify time interval tracking was set up
        mock_track_time.assert_called_once()


@pytest.mark.asyncio
async def test_async_unload_entry(mock_hass, mock_config_entry, mock_bluetooth):
    """Test async_unload_entry."""
    # Set up runtime data
    mock_coordinator = MagicMock()
    mock_coordinator.async_shutdown = AsyncMock()
    mock_config_entry.runtime_data = OpenDroneIDData(coordinator=mock_coordinator)

    result = await async_unload_entry(mock_hass, mock_config_entry)

    assert result is True
    mock_coordinator.async_shutdown.assert_called_once()
    mock_hass.config_entries.async_unload_platforms.assert_called_once()


@pytest.mark.asyncio
async def test_options_update(mock_hass, mock_config_entry):
    """Test options update listener."""
    with patch(
        "custom_components.opendroneid._async_options_updated"
    ) as mock_options_updated:
        await mock_options_updated(mock_hass, mock_config_entry)
        mock_hass.config_entries.async_reload.assert_called_once_with(
            mock_config_entry.entry_id
        )


@pytest.mark.asyncio
async def test_cleanup_inactive_drones(mock_hass, mock_config_entry, mock_bluetooth):
    """Test that inactive drone cleanup is scheduled."""
    with patch(
        "custom_components.opendroneid.OpenDroneIDCoordinator"
    ) as mock_coordinator_class, patch(
        "custom_components.opendroneid.async_track_time_interval"
    ) as mock_track_time:
        mock_coordinator = MagicMock()
        mock_coordinator.async_setup = AsyncMock()
        mock_coordinator.async_remove_inactive_drones = MagicMock()
        mock_coordinator_class.return_value = mock_coordinator

        # Capture the cleanup callback
        cleanup_callback = None

        def capture_callback(hass, callback, interval):
            nonlocal cleanup_callback
            cleanup_callback = callback
            return lambda: None

        mock_track_time.side_effect = capture_callback

        await async_setup_entry(mock_hass, mock_config_entry)

        assert cleanup_callback is not None

        # Call the cleanup callback
        from datetime import datetime

        cleanup_callback(datetime.now())

        # Verify cleanup was called
        mock_coordinator.async_remove_inactive_drones.assert_called_once()
