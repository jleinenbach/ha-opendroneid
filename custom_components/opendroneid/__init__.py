"""OpenDroneID BLE Receiver Integration for Home Assistant.

Detects drones via BLE Remote ID broadcasts using ESPHome Bluetooth Proxies.
Standards: ASTM F3411-22a / ASD-STAN prEN 4709-002

This integration targets Platinum Quality Scale standards.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval

from .const import CONF_INACTIVE_TIMEOUT, DEFAULT_INACTIVE_TIMEOUT, DOMAIN as DOMAIN
from .coordinator import OpenDroneIDCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Platforms to set up
PLATFORMS: list[Platform] = [
    Platform.DEVICE_TRACKER,
]


@dataclass
class OpenDroneIDData:
    """Runtime data for the integration (Bronze: runtime-data)."""

    coordinator: OpenDroneIDCoordinator


# Type alias for config entry (Platinum: strict-typing)
type OpenDroneIDConfigEntry = ConfigEntry[OpenDroneIDData]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OpenDroneIDConfigEntry,
) -> bool:
    """Set up OpenDroneID from a config entry.

    This integration uses Home Assistant's Bluetooth integration to receive
    BLE advertisements from ESPHome proxies. No additional configuration needed.
    """
    _LOGGER.debug("Setting up OpenDroneID integration")

    # Create coordinator
    coordinator = OpenDroneIDCoordinator(hass, entry)

    # Set up BLE scanning
    await coordinator.async_setup()

    # Bronze: runtime-data - Store in runtime_data, NOT hass.data
    entry.runtime_data = OpenDroneIDData(
        coordinator=coordinator,
    )

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up periodic cleanup of inactive drones
    inactive_timeout = entry.options.get(
        CONF_INACTIVE_TIMEOUT, DEFAULT_INACTIVE_TIMEOUT
    )

    @callback
    def _async_cleanup_inactive(_now: datetime) -> None:
        """Remove drones that haven't been seen recently."""
        coordinator.async_remove_inactive_drones()

    # Run cleanup every minute
    entry.async_on_unload(
        async_track_time_interval(
            hass,
            _async_cleanup_inactive,
            timedelta(seconds=60),
        )
    )

    # Handle options updates
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    _LOGGER.info(
        "OpenDroneID integration ready (inactive timeout: %ds)",
        inactive_timeout,
    )

    return True


async def _async_options_updated(
    hass: HomeAssistant,
    entry: OpenDroneIDConfigEntry,
) -> None:
    """Handle options update."""
    # Reload the integration to apply new options
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant,
    entry: OpenDroneIDConfigEntry,
) -> bool:
    """Unload a config entry.

    Silver: config-entry-unloading - Support unloading.
    """
    # Shut down BLE scanning
    await entry.runtime_data.coordinator.async_shutdown()

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
