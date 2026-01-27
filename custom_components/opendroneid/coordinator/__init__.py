"""DataUpdateCoordinator for OpenDroneID.

Manages drone state from BLE Remote ID broadcasts.
Uses Home Assistant's Bluetooth integration for passive BLE scanning.
Optionally forwards data to DragonSync via ZMQ.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from homeassistant.components.bluetooth import (
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..const import (
    CONF_DRAGONSYNC_ENABLED,
    CONF_DRAGONSYNC_HOST,
    CONF_DRAGONSYNC_PORT,
    CONF_INACTIVE_TIMEOUT,
    DEFAULT_DRAGONSYNC_PORT,
    DEFAULT_INACTIVE_TIMEOUT,
    DOMAIN,
    REMOTE_ID_SERVICE_UUID,
)
from ..decoder import (
    BasicIDMessage,
    DroneData,
    LocationMessage,
    OpenDroneIDDecoder,
    OperatorIDMessage,
    SystemMessage,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# ID type mapping for DragonSync
ID_TYPE_NAMES = {
    0: "None",
    1: "Serial Number (ANSI/CTA-2063-A)",
    2: "CAA Assigned Registration ID",
    3: "UTM Assigned UUID",
    4: "Specific Session ID",
}

# Operational status mapping for DragonSync
OP_STATUS_NAMES = {
    0: "Undeclared",
    1: "Ground",
    2: "Airborne",
    3: "Emergency",
    4: "Remote ID System Failure",
}


class OpenDroneIDCoordinator(DataUpdateCoordinator[dict[str, DroneData]]):
    """Coordinator for OpenDroneID BLE data.

    Unlike typical coordinators, this one doesn't poll - it receives
    BLE advertisements via callbacks from ESPHome proxies.
    """

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            # No update_interval - we're event-driven via BLE callbacks
            update_interval=None,
        )
        self.config_entry = entry
        self._decoder = OpenDroneIDDecoder()

        # Dict of drone_id -> DroneData
        self.data: dict[str, DroneData] = {}

        # Track BLE callback registration
        self._cancel_bluetooth_callback: Callable[[], None] | None = None

        # Inactive timeout from options
        self._inactive_timeout = entry.options.get(
            CONF_INACTIVE_TIMEOUT, DEFAULT_INACTIVE_TIMEOUT
        )

        # DragonSync ZMQ configuration
        self._dragonsync_enabled = entry.options.get(CONF_DRAGONSYNC_ENABLED, False)
        self._dragonsync_host = entry.options.get(CONF_DRAGONSYNC_HOST, "")
        self._dragonsync_port = entry.options.get(
            CONF_DRAGONSYNC_PORT, DEFAULT_DRAGONSYNC_PORT
        )
        self._zmq_socket: Any = None  # zmq.Socket type not available without import
        self._zmq_context: Any = None  # zmq.Context type not available without import

    async def async_setup(self) -> None:
        """Set up the coordinator and register BLE callback."""
        _LOGGER.debug("Setting up OpenDroneID BLE scanning")

        # Register for BLE advertisements with Remote ID service UUID
        # The UUID needs to be in the format expected by HA Bluetooth
        service_uuid = f"0000{REMOTE_ID_SERVICE_UUID:04x}-0000-1000-8000-00805f9b34fb"

        self._cancel_bluetooth_callback = async_register_callback(
            self.hass,
            self._async_handle_bluetooth_event,
            # Match on service UUID
            {"service_uuid": service_uuid},
            BluetoothScanningMode.PASSIVE,
        )

        _LOGGER.info(
            "OpenDroneID BLE scanning active, listening for Remote ID (UUID: 0x%04X)",
            REMOTE_ID_SERVICE_UUID,
        )

        # Set up DragonSync ZMQ if enabled
        if self._dragonsync_enabled and self._dragonsync_host:
            await self._setup_dragonsync()

    async def _setup_dragonsync(self) -> None:
        """Set up ZMQ connection to DragonSync."""
        try:
            import zmq  # noqa: PLC0415

            self._zmq_context = zmq.Context()
            self._zmq_socket = self._zmq_context.socket(zmq.PUB)
            zmq_url = f"tcp://{self._dragonsync_host}:{self._dragonsync_port}"
            self._zmq_socket.connect(zmq_url)
            _LOGGER.info("DragonSync ZMQ connected to %s", zmq_url)
        except ImportError:
            _LOGGER.exception(
                "pyzmq not installed. DragonSync forwarding disabled. "
                "Install with: pip install pyzmq"
            )
            self._dragonsync_enabled = False
        except OSError:
            _LOGGER.exception("Failed to connect to DragonSync")
            self._dragonsync_enabled = False

    async def async_shutdown(self) -> None:
        """Shut down the coordinator."""
        if self._cancel_bluetooth_callback:
            self._cancel_bluetooth_callback()
            self._cancel_bluetooth_callback = None
            _LOGGER.debug("OpenDroneID BLE scanning stopped")

        # Close ZMQ connection
        if self._zmq_socket:
            self._zmq_socket.close()
            self._zmq_socket = None
        if self._zmq_context:
            self._zmq_context.term()
            self._zmq_context = None
            _LOGGER.debug("DragonSync ZMQ connection closed")

    @callback
    def _async_handle_bluetooth_event(
        self,
        service_info: BluetoothServiceInfoBleak,
        change: BluetoothChange,
    ) -> None:
        """Handle a BLE advertisement from an ESPHome proxy.

        This is called for every BLE advertisement matching our service UUID.
        """
        # Get the service data for Remote ID UUID
        service_uuid = f"0000{REMOTE_ID_SERVICE_UUID:04x}-0000-1000-8000-00805f9b34fb"
        service_data = service_info.service_data.get(service_uuid)

        if not service_data:
            # Try short UUID format
            service_data = service_info.service_data.get(
                f"{REMOTE_ID_SERVICE_UUID:04x}"
            )

        if not service_data:
            _LOGGER.debug(
                "No service data for Remote ID UUID in advertisement from %s",
                service_info.address,
            )
            return

        # Decode the service data
        result = self._decoder.decode_service_data(bytes(service_data))
        if not result:
            _LOGGER.debug("Failed to decode service data from %s", service_info.address)
            return

        counter, message_data = result

        # Decode the message
        message = self._decoder.decode_message(message_data)
        if not message:
            _LOGGER.debug("Unknown message type from %s", service_info.address)
            return

        # Use BLE address as drone identifier (until we get Basic ID)
        drone_id = service_info.address.replace(":", "").lower()

        # Get or create drone data
        if drone_id not in self.data:
            self.data[drone_id] = DroneData(
                source_address=service_info.address,
            )
            _LOGGER.info(
                "New drone detected: %s (RSSI: %d dBm)",
                service_info.address,
                service_info.rssi or -100,
            )

        drone = self.data[drone_id]
        drone.rssi = service_info.rssi or -100
        drone.last_seen = time.time()
        drone.message_counter = counter

        # Update drone data based on message type
        self._update_drone_from_message(drone, message)

        # Forward to DragonSync if enabled
        if self._dragonsync_enabled and self._zmq_socket:
            self._send_to_dragonsync(drone, message)

        # Notify listeners of the update
        self.async_set_updated_data(self.data)

    def _update_drone_from_message(
        self,
        drone: DroneData,
        message: BasicIDMessage | LocationMessage | SystemMessage | OperatorIDMessage,
    ) -> None:
        """Update drone data from a decoded message."""
        if isinstance(message, BasicIDMessage):
            drone.uas_id = message.uas_id
            drone.id_type = message.id_type
            drone.ua_type = message.ua_type
            _LOGGER.debug("Basic ID: %s (%s)", message.uas_id, message.id_type.name)

        elif isinstance(message, LocationMessage):
            drone.status = message.status
            drone.height_type = message.height_type
            drone.direction = message.direction
            drone.speed_horizontal = message.speed_horizontal
            drone.speed_vertical = message.speed_vertical
            drone.altitude_baro = message.altitude_baro
            drone.altitude_geo = message.altitude_geo
            drone.height = message.height
            drone.timestamp = message.timestamp

            # Only update lat/lon if valid
            if message.latitude != 0.0:
                drone.latitude = message.latitude
            if message.longitude != 0.0:
                drone.longitude = message.longitude

            _LOGGER.debug(
                "Location: %.6f, %.6f, alt=%.1fm, speed=%.1fm/s",
                drone.latitude or 0,
                drone.longitude or 0,
                drone.altitude_geo or 0,
                drone.speed_horizontal or 0,
            )

        elif isinstance(message, SystemMessage):
            if message.operator_latitude != 0.0:
                drone.operator_latitude = message.operator_latitude
            if message.operator_longitude != 0.0:
                drone.operator_longitude = message.operator_longitude
            if message.operator_altitude_geo != 0.0:
                drone.operator_altitude = message.operator_altitude_geo

            _LOGGER.debug(
                "Operator location: %.6f, %.6f",
                drone.operator_latitude or 0,
                drone.operator_longitude or 0,
            )

        elif isinstance(message, OperatorIDMessage):
            drone.operator_id = message.operator_id
            _LOGGER.debug("Operator ID: %s", message.operator_id)

    def _send_to_dragonsync(
        self,
        drone: DroneData,
        message: BasicIDMessage | LocationMessage | SystemMessage | OperatorIDMessage,
    ) -> None:
        """Send drone data to DragonSync via ZMQ.

        Formats data in the structure expected by DragonSync's telemetry parser.
        """
        try:
            # Build message in DragonSync format
            zmq_message: dict[str, Any] = {}

            # Always include Basic ID info if available
            if drone.uas_id or drone.id_type:
                zmq_message["Basic ID"] = {
                    "id_type": ID_TYPE_NAMES.get(
                        drone.id_type.value if drone.id_type else 0, "None"
                    ),
                    "id": drone.uas_id or "unknown",
                    "ua_type": drone.ua_type.value if drone.ua_type else 0,
                    "MAC": drone.source_address,
                    "RSSI": drone.rssi,
                }

            # Include Location data if we have coordinates
            if drone.latitude is not None and drone.longitude is not None:
                zmq_message["Location/Vector Message"] = {
                    "latitude": drone.latitude,
                    "longitude": drone.longitude,
                    "speed": drone.speed_horizontal or 0.0,
                    "vert_speed": drone.speed_vertical or 0.0,
                    "geodetic_altitude": drone.altitude_geo or 0.0,
                    "pressure_altitude": drone.altitude_baro or 0.0,
                    "height_agl": drone.height or 0.0,
                    "op_status": OP_STATUS_NAMES.get(
                        drone.status.value if drone.status else 0, "Undeclared"
                    ),
                    "direction": drone.direction or 0,
                    "height_type": (
                        drone.height_type.name if drone.height_type else "Above Takeoff"
                    ),
                }

            # Include Operator ID if available
            if drone.operator_id:
                zmq_message["Operator ID Message"] = {
                    "operator_id": drone.operator_id,
                    "operator_id_type": "",
                }

            # Include System Message (operator location) if available
            if drone.operator_latitude is not None:
                zmq_message["System Message"] = {
                    "operator_lat": drone.operator_latitude,
                    "operator_lon": drone.operator_longitude or 0.0,
                }

            # Send via ZMQ
            if zmq_message:
                self._zmq_socket.send_json(zmq_message)
                _LOGGER.debug(
                    "Sent to DragonSync: %s", drone.uas_id or drone.source_address
                )

        except (OSError, ValueError, TypeError):
            _LOGGER.exception("Failed to send to DragonSync")

    @callback
    def async_remove_inactive_drones(self) -> list[str]:
        """Remove drones that haven't been seen recently.

        Returns list of removed drone IDs.
        """
        now = time.time()
        removed: list[str] = []

        for drone_id, drone in list(self.data.items()):
            if now - drone.last_seen > self._inactive_timeout:
                del self.data[drone_id]
                removed.append(drone_id)
                _LOGGER.info(
                    "Drone %s removed (inactive for %ds)",
                    drone_id,
                    self._inactive_timeout,
                )

        if removed:
            self.async_set_updated_data(self.data)

        return removed
