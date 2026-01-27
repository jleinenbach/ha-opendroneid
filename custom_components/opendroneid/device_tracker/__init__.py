"""Device tracker platform for OpenDroneID.

Creates device_tracker entities for detected drones with GPS coordinates
for display on Home Assistant maps.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.core import HomeAssistant, callback

from ..const import DOMAIN
from ..decoder import DroneData, OperationalStatus

if TYPE_CHECKING:
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .. import OpenDroneIDConfigEntry
    from ..coordinator import OpenDroneIDCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OpenDroneIDConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenDroneID device tracker from a config entry."""
    coordinator: OpenDroneIDCoordinator = entry.runtime_data.coordinator

    # Track which drones we've already created entities for
    tracked_drones: set[str] = set()

    @callback
    def _async_add_new_drones() -> None:
        """Add device trackers for newly discovered drones."""
        new_entities: list[DroneDeviceTracker] = []

        for drone_id, drone_data in coordinator.data.items():
            if drone_id not in tracked_drones:
                tracked_drones.add(drone_id)
                new_entities.append(
                    DroneDeviceTracker(coordinator, drone_id, drone_data)
                )
                _LOGGER.debug("Adding device tracker for drone: %s", drone_id)

        if new_entities:
            async_add_entities(new_entities)

    # Add entities for any drones already discovered
    _async_add_new_drones()

    # Listen for new drones
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_drones))


class DroneDeviceTracker(TrackerEntity):
    """Device tracker for a detected drone.

    Provides GPS coordinates for map display in Home Assistant.
    """

    _attr_has_entity_name = True
    _attr_name = None  # Use device name

    def __init__(
        self,
        coordinator: OpenDroneIDCoordinator,
        drone_id: str,
        drone_data: DroneData,
    ) -> None:
        """Initialize the drone device tracker."""
        self.coordinator = coordinator
        self._drone_id = drone_id
        self._drone_data = drone_data

        # Entity identifiers
        self._attr_unique_id = f"{DOMAIN}_{drone_id}"

        # Device info - each drone is its own device
        self._attr_device_info = {
            "identifiers": {(DOMAIN, drone_id)},
            "name": f"Drone {drone_data.uas_id or drone_id[:8]}",
            "manufacturer": "Unknown",
            "model": drone_data.ua_type.name if drone_data.ua_type else "Drone",
            "via_device": None,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._drone_id in self.coordinator.data
        )

    @property
    def source_type(self) -> SourceType:
        """Return the source type (GPS) for map display."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return latitude of the drone."""
        if self._drone_id in self.coordinator.data:
            return self.coordinator.data[self._drone_id].latitude
        return None

    @property
    def longitude(self) -> float | None:
        """Return longitude of the drone."""
        if self._drone_id in self.coordinator.data:
            return self.coordinator.data[self._drone_id].longitude
        return None

    @property
    def location_accuracy(self) -> int:
        """Return the GPS accuracy in meters."""
        # Remote ID typically has ~10m accuracy
        return 10

    @property
    def battery_level(self) -> int | None:
        """Return battery level if available (not in standard Remote ID)."""
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:  # noqa: PLR0912
        """Return additional state attributes."""
        if self._drone_id not in self.coordinator.data:
            return None

        drone = self.coordinator.data[self._drone_id]

        attrs = {
            "uas_id": drone.uas_id,
            "id_type": drone.id_type.name if drone.id_type else None,
            "ua_type": drone.ua_type.name if drone.ua_type else None,
            "status": drone.status.name if drone.status else None,
        }

        # Add position data
        if drone.altitude_geo is not None:
            attrs["altitude"] = round(drone.altitude_geo, 1)
        if drone.altitude_baro is not None:
            attrs["altitude_barometric"] = round(drone.altitude_baro, 1)
        if drone.height is not None:
            attrs["height"] = round(drone.height, 1)
            attrs["height_type"] = drone.height_type.name if drone.height_type else None

        # Add velocity data
        if drone.speed_horizontal is not None:
            attrs["speed"] = round(drone.speed_horizontal, 1)
        if drone.speed_vertical is not None:
            attrs["vertical_speed"] = round(drone.speed_vertical, 1)
        if drone.direction is not None:
            attrs["heading"] = round(drone.direction, 1)

        # Add operator/pilot location if available
        if drone.operator_latitude is not None and drone.operator_longitude is not None:
            attrs["operator_latitude"] = drone.operator_latitude
            attrs["operator_longitude"] = drone.operator_longitude
            if drone.operator_altitude is not None:
                attrs["operator_altitude"] = round(drone.operator_altitude, 1)

        # Add operator ID if available
        if drone.operator_id:
            attrs["operator_id"] = drone.operator_id

        # Add signal info
        if drone.rssi:
            attrs["rssi"] = drone.rssi
        if drone.source_address:
            attrs["source_address"] = drone.source_address

        # Add timestamps
        if drone.last_seen:
            attrs["last_seen"] = drone.last_seen

        return attrs

    @property
    def state(self) -> str | None:
        """Return the state of the drone.

        For device_tracker, state is typically 'home' or 'not_home',
        but for drones we use the operational status.
        """
        if self._drone_id not in self.coordinator.data:
            return None

        drone = self.coordinator.data[self._drone_id]

        # Map operational status to meaningful states
        if drone.status == OperationalStatus.GROUND:
            return "ground"
        if drone.status == OperationalStatus.AIRBORNE:
            return "airborne"
        if drone.status == OperationalStatus.EMERGENCY:
            return "emergency"
        if drone.status == OperationalStatus.REMOTE_ID_FAILURE:
            return "malfunction"
        return "unknown"

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
