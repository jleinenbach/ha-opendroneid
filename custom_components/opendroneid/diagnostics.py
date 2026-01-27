"""Diagnostics support for OpenDroneID (Gold requirement)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from . import OpenDroneIDConfigEntry


async def async_get_config_entry_diagnostics(
    hass: Any,
    entry: OpenDroneIDConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator

    # Convert drone data to serializable format
    drones_data = {}
    for drone_id, drone in coordinator.data.items():
        drones_data[drone_id] = asdict(drone)

    return {
        "entry_id": entry.entry_id,
        "options": dict(entry.options),
        "drone_count": len(coordinator.data),
        "drones": drones_data,
    }
