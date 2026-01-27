"""OpenDroneID message decoder.

Implements decoding of ASTM F3411-22a / ASD-STAN prEN 4709-002 messages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Final
import struct

# Message type constants
MSG_TYPE_BASIC_ID: Final = 0x00
MSG_TYPE_LOCATION: Final = 0x01
MSG_TYPE_AUTH: Final = 0x02
MSG_TYPE_SELF_ID: Final = 0x03
MSG_TYPE_SYSTEM: Final = 0x04
MSG_TYPE_OPERATOR_ID: Final = 0x05
MSG_TYPE_MESSAGE_PACK: Final = 0x0F

# ID types (Basic ID)
class IDType(IntEnum):
    """UAS ID type."""
    NONE = 0
    SERIAL_NUMBER = 1
    CAA_REGISTRATION = 2
    UTM_ASSIGNED = 3
    SPECIFIC_SESSION = 4


class UAType(IntEnum):
    """UA (Unmanned Aircraft) type."""
    NONE = 0
    AEROPLANE = 1
    HELICOPTER = 2
    GYROPLANE = 3
    HYBRID_LIFT = 4
    ORNITHOPTER = 5
    GLIDER = 6
    KITE = 7
    FREE_BALLOON = 8
    CAPTIVE_BALLOON = 9
    AIRSHIP = 10
    PARACHUTE = 11
    ROCKET = 12
    TETHERED = 13
    GROUND_OBSTACLE = 14
    OTHER = 15


class OperationalStatus(IntEnum):
    """Operational status."""
    UNDECLARED = 0
    GROUND = 1
    AIRBORNE = 2
    EMERGENCY = 3
    REMOTE_ID_FAILURE = 4


class HeightType(IntEnum):
    """Height reference type."""
    ABOVE_TAKEOFF = 0
    AGL = 1  # Above Ground Level


@dataclass
class BasicIDMessage:
    """Basic ID message (type 0x00)."""

    id_type: IDType = IDType.NONE
    ua_type: UAType = UAType.NONE
    uas_id: str = ""


@dataclass
class LocationMessage:
    """Location/Vector message (type 0x01)."""

    status: OperationalStatus = OperationalStatus.UNDECLARED
    height_type: HeightType = HeightType.ABOVE_TAKEOFF
    direction: float = 0.0  # degrees, 0-360
    speed_horizontal: float = 0.0  # m/s
    speed_vertical: float = 0.0  # m/s
    latitude: float = 0.0  # degrees
    longitude: float = 0.0  # degrees
    altitude_baro: float = 0.0  # meters (pressure altitude)
    altitude_geo: float = 0.0  # meters (geodetic/GPS altitude)
    height: float = 0.0  # meters (above takeoff or AGL)
    horizontal_accuracy: int = 0
    vertical_accuracy: int = 0
    baro_accuracy: int = 0
    speed_accuracy: int = 0
    timestamp: float = 0.0  # seconds since hour
    timestamp_accuracy: float = 0.0


@dataclass
class SystemMessage:
    """System message (type 0x04) - Operator location."""

    operator_location_type: int = 0
    classification_type: int = 0
    operator_latitude: float = 0.0
    operator_longitude: float = 0.0
    area_count: int = 0
    area_radius: float = 0.0  # meters
    area_ceiling: float = 0.0  # meters
    area_floor: float = 0.0  # meters
    ua_classification_category: int = 0
    ua_classification_class: int = 0
    operator_altitude_geo: float = 0.0


@dataclass
class OperatorIDMessage:
    """Operator ID message (type 0x05)."""

    operator_id_type: int = 0
    operator_id: str = ""


@dataclass
class DroneData:
    """Aggregated drone data from multiple messages."""

    # From Basic ID
    uas_id: str = ""
    id_type: IDType = IDType.NONE
    ua_type: UAType = UAType.NONE

    # From Location
    status: OperationalStatus = OperationalStatus.UNDECLARED
    latitude: float | None = None
    longitude: float | None = None
    altitude_geo: float | None = None
    altitude_baro: float | None = None
    height: float | None = None
    height_type: HeightType = HeightType.ABOVE_TAKEOFF
    speed_horizontal: float | None = None
    speed_vertical: float | None = None
    direction: float | None = None
    timestamp: float | None = None

    # From System (operator location)
    operator_latitude: float | None = None
    operator_longitude: float | None = None
    operator_altitude: float | None = None

    # From Operator ID
    operator_id: str = ""

    # Metadata
    rssi: int = -100
    last_seen: float = 0.0
    message_counter: int = 0
    source_address: str = ""


class OpenDroneIDDecoder:
    """Decoder for OpenDroneID BLE messages."""

    # Latitude/Longitude encoding: value * 1e-7 degrees
    LAT_LON_SCALE: Final = 1e-7

    # Altitude encoding: value * 0.5 - 1000 meters
    ALT_SCALE: Final = 0.5
    ALT_OFFSET: Final = -1000.0

    # Speed encoding
    SPEED_H_SCALE: Final = 0.25  # m/s per unit (0-254 * 0.25)
    SPEED_V_SCALE: Final = 0.5   # m/s per unit

    # Invalid values
    INVALID_LAT_LON: Final = 0
    INVALID_ALT: Final = 0xFFFF
    INVALID_SPEED: Final = 0xFF

    def decode_service_data(self, data: bytes) -> tuple[int, bytes] | None:
        """Extract message from BLE service data.

        Service data format:
        [App Code 0x0D][Message Counter][25-byte Message]

        Returns:
            Tuple of (message_counter, message_data) or None if invalid.
        """
        if len(data) < 27:  # 1 (app) + 1 (counter) + 25 (message)
            return None

        app_code = data[0]
        if app_code != 0x0D:
            return None

        counter = data[1]
        message = data[2:27]

        return counter, message

    def decode_message(self, data: bytes) -> BasicIDMessage | LocationMessage | SystemMessage | OperatorIDMessage | None:
        """Decode a 25-byte OpenDroneID message."""
        if len(data) < 25:
            return None

        msg_type = (data[0] >> 4) & 0x0F

        if msg_type == MSG_TYPE_BASIC_ID:
            return self._decode_basic_id(data)
        elif msg_type == MSG_TYPE_LOCATION:
            return self._decode_location(data)
        elif msg_type == MSG_TYPE_SYSTEM:
            return self._decode_system(data)
        elif msg_type == MSG_TYPE_OPERATOR_ID:
            return self._decode_operator_id(data)

        return None

    def _decode_basic_id(self, data: bytes) -> BasicIDMessage:
        """Decode Basic ID message (type 0x00)."""
        msg = BasicIDMessage()

        # Byte 0: [msg_type:4][id_type:4]
        msg.id_type = IDType(data[0] & 0x0F)

        # Byte 1: UA type
        msg.ua_type = UAType(data[1] & 0x0F)

        # Bytes 2-21: UAS ID (20 characters, null-terminated ASCII)
        uas_id_bytes = data[2:22]
        msg.uas_id = uas_id_bytes.rstrip(b'\x00').decode('ascii', errors='replace')

        return msg

    def _decode_location(self, data: bytes) -> LocationMessage:
        """Decode Location/Vector message (type 0x01)."""
        msg = LocationMessage()

        # Byte 0: [msg_type:4][status:4]
        msg.status = OperationalStatus(data[0] & 0x0F)

        # Byte 1: [height_type:1][ew_dir:1][speed_mult:1][reserved:5]
        flags = data[1]
        msg.height_type = HeightType((flags >> 2) & 0x01)
        ew_direction = (flags >> 1) & 0x01  # 0=East, 1=West
        speed_multiplier = 0.25 if (flags & 0x01) == 0 else 0.75

        # Byte 2: Direction (0-360 degrees, encoded as 0-179 for 2-degree resolution)
        if data[2] <= 179:
            msg.direction = data[2] * 2.0
            if ew_direction:
                msg.direction = 360.0 - msg.direction

        # Byte 3: Horizontal speed
        if data[3] != self.INVALID_SPEED:
            msg.speed_horizontal = data[3] * speed_multiplier

        # Byte 4: Vertical speed (signed, 0.5 m/s resolution)
        if data[4] != 0x3F:  # Invalid marker for vertical speed
            # Convert from offset binary
            vs_raw = data[4]
            if vs_raw > 62:
                msg.speed_vertical = (vs_raw - 63) * self.SPEED_V_SCALE
            else:
                msg.speed_vertical = (vs_raw - 62) * self.SPEED_V_SCALE

        # Bytes 5-8: Latitude (int32, little-endian, *1e-7 degrees)
        lat_raw = struct.unpack('<i', data[5:9])[0]
        if lat_raw != self.INVALID_LAT_LON:
            msg.latitude = lat_raw * self.LAT_LON_SCALE

        # Bytes 9-12: Longitude (int32, little-endian, *1e-7 degrees)
        lon_raw = struct.unpack('<i', data[9:13])[0]
        if lon_raw != self.INVALID_LAT_LON:
            msg.longitude = lon_raw * self.LAT_LON_SCALE

        # Bytes 13-14: Pressure altitude (uint16, little-endian)
        alt_baro_raw = struct.unpack('<H', data[13:15])[0]
        if alt_baro_raw != self.INVALID_ALT:
            msg.altitude_baro = alt_baro_raw * self.ALT_SCALE + self.ALT_OFFSET

        # Bytes 15-16: Geodetic altitude (uint16, little-endian)
        alt_geo_raw = struct.unpack('<H', data[15:17])[0]
        if alt_geo_raw != self.INVALID_ALT:
            msg.altitude_geo = alt_geo_raw * self.ALT_SCALE + self.ALT_OFFSET

        # Bytes 17-18: Height (uint16, little-endian)
        height_raw = struct.unpack('<H', data[17:19])[0]
        if height_raw != self.INVALID_ALT:
            msg.height = height_raw * self.ALT_SCALE + self.ALT_OFFSET

        # Byte 19: Accuracy values
        accuracy = data[19]
        msg.vertical_accuracy = (accuracy >> 4) & 0x0F
        msg.horizontal_accuracy = accuracy & 0x0F

        # Byte 20: More accuracy
        accuracy2 = data[20]
        msg.baro_accuracy = (accuracy2 >> 4) & 0x0F
        msg.speed_accuracy = accuracy2 & 0x0F

        # Bytes 21-22: Timestamp (uint16, 0.1s resolution since hour)
        ts_raw = struct.unpack('<H', data[21:23])[0]
        if ts_raw != 0xFFFF:
            msg.timestamp = ts_raw * 0.1

        # Byte 23: Timestamp accuracy
        msg.timestamp_accuracy = data[23] * 0.1

        return msg

    def _decode_system(self, data: bytes) -> SystemMessage:
        """Decode System message (type 0x04)."""
        msg = SystemMessage()

        # Byte 0: [msg_type:4][operator_location_type:2][classification_type:2]
        msg.operator_location_type = (data[0] >> 2) & 0x03
        msg.classification_type = data[0] & 0x03

        # Bytes 1-4: Operator latitude
        lat_raw = struct.unpack('<i', data[1:5])[0]
        if lat_raw != 0:
            msg.operator_latitude = lat_raw * self.LAT_LON_SCALE

        # Bytes 5-8: Operator longitude
        lon_raw = struct.unpack('<i', data[5:9])[0]
        if lon_raw != 0:
            msg.operator_longitude = lon_raw * self.LAT_LON_SCALE

        # Bytes 9-10: Area count
        msg.area_count = struct.unpack('<H', data[9:11])[0]

        # Byte 11: Area radius (10m units)
        msg.area_radius = data[11] * 10.0

        # Bytes 12-13: Area ceiling
        ceiling_raw = struct.unpack('<H', data[12:14])[0]
        if ceiling_raw != self.INVALID_ALT:
            msg.area_ceiling = ceiling_raw * self.ALT_SCALE + self.ALT_OFFSET

        # Bytes 14-15: Area floor
        floor_raw = struct.unpack('<H', data[14:16])[0]
        if floor_raw != self.INVALID_ALT:
            msg.area_floor = floor_raw * self.ALT_SCALE + self.ALT_OFFSET

        # Byte 16: Classification
        msg.ua_classification_category = (data[16] >> 4) & 0x0F
        msg.ua_classification_class = data[16] & 0x0F

        # Bytes 17-18: Operator altitude
        alt_raw = struct.unpack('<H', data[17:19])[0]
        if alt_raw != self.INVALID_ALT:
            msg.operator_altitude_geo = alt_raw * self.ALT_SCALE + self.ALT_OFFSET

        return msg

    def _decode_operator_id(self, data: bytes) -> OperatorIDMessage:
        """Decode Operator ID message (type 0x05)."""
        msg = OperatorIDMessage()

        # Byte 0: [msg_type:4][operator_id_type:4]
        msg.operator_id_type = data[0] & 0x0F

        # Bytes 1-20: Operator ID (20 characters, null-terminated ASCII)
        op_id_bytes = data[1:21]
        msg.operator_id = op_id_bytes.rstrip(b'\x00').decode('ascii', errors='replace')

        return msg
