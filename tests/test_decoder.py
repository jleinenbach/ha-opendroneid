"""Tests for OpenDroneID decoder."""

from __future__ import annotations

import struct

import pytest

from custom_components.opendroneid.decoder import (
    BasicIDMessage,
    IDType,
    LocationMessage,
    OpenDroneIDDecoder,
    OperationalStatus,
    OperatorIDMessage,
    SystemMessage,
    UAType,
)


@pytest.fixture
def decoder() -> OpenDroneIDDecoder:
    """Create decoder instance."""
    return OpenDroneIDDecoder()


class TestServiceDataDecoding:
    """Tests for BLE service data decoding."""

    def test_valid_service_data(self, decoder: OpenDroneIDDecoder) -> None:
        """Test decoding valid service data."""
        # App code 0x0D + counter 0x42 + 25-byte message
        data = bytes([0x0D, 0x42]) + bytes(25)
        result = decoder.decode_service_data(data)
        assert result is not None
        counter, message = result
        assert counter == 0x42
        assert len(message) == 25

    def test_invalid_app_code(self, decoder: OpenDroneIDDecoder) -> None:
        """Test rejection of invalid app code."""
        data = bytes([0x0E, 0x00]) + bytes(25)  # Wrong app code
        result = decoder.decode_service_data(data)
        assert result is None

    def test_short_data(self, decoder: OpenDroneIDDecoder) -> None:
        """Test rejection of too short data."""
        data = bytes([0x0D, 0x00]) + bytes(10)  # Too short
        result = decoder.decode_service_data(data)
        assert result is None


class TestBasicIDMessage:
    """Tests for Basic ID message decoding."""

    def test_decode_basic_id_serial(self, decoder: OpenDroneIDDecoder) -> None:
        """Test decoding Basic ID with serial number."""
        # msg_type=0, id_type=1 (Serial)
        # ua_type=2 (Helicopter)
        # UAS ID: "TEST12345"
        data = bytes([
            0x01,  # msg_type=0, id_type=1
            0x02,  # ua_type=2
        ]) + b"TEST12345" + bytes(11) + bytes(3)  # ID + padding + reserved

        msg = decoder.decode_message(data)
        assert isinstance(msg, BasicIDMessage)
        assert msg.id_type == IDType.SERIAL_NUMBER
        assert msg.ua_type == UAType.HELICOPTER
        assert msg.uas_id == "TEST12345"

    def test_decode_basic_id_caa(self, decoder: OpenDroneIDDecoder) -> None:
        """Test decoding Basic ID with CAA registration."""
        data = bytes([
            0x02,  # msg_type=0, id_type=2 (CAA)
            0x01,  # ua_type=1 (Aeroplane)
        ]) + b"REG-12345" + bytes(11) + bytes(3)

        msg = decoder.decode_message(data)
        assert isinstance(msg, BasicIDMessage)
        assert msg.id_type == IDType.CAA_REGISTRATION
        assert msg.ua_type == UAType.AEROPLANE


class TestLocationMessage:
    """Tests for Location message decoding."""

    def test_decode_location_airborne(self, decoder: OpenDroneIDDecoder) -> None:
        """Test decoding location of airborne drone."""
        # Build a valid location message
        data = bytearray(25)
        data[0] = 0x12  # msg_type=1, status=2 (Airborne)
        data[1] = 0x00  # flags
        data[2] = 90    # direction: 180 degrees
        data[3] = 40    # speed: 10 m/s (40 * 0.25)
        data[4] = 63    # vertical speed: 0

        # Latitude: 49.866250 * 1e7 = 498662500
        struct.pack_into("<i", data, 5, 498662500)
        # Longitude: 10.839480 * 1e7 = 108394800
        struct.pack_into("<i", data, 9, 108394800)

        # Altitude baro: 283m -> (283 + 1000) / 0.5 = 2566
        struct.pack_into("<H", data, 13, 2566)
        # Altitude geo: 300m -> (300 + 1000) / 0.5 = 2600
        struct.pack_into("<H", data, 15, 2600)
        # Height: 50m -> (50 + 1000) / 0.5 = 2100
        struct.pack_into("<H", data, 17, 2100)

        msg = decoder.decode_message(bytes(data))
        assert isinstance(msg, LocationMessage)
        assert msg.status == OperationalStatus.AIRBORNE
        assert abs(msg.latitude - 49.86625) < 0.0001
        assert abs(msg.longitude - 10.83948) < 0.0001
        assert abs(msg.altitude_geo - 300.0) < 0.5
        assert abs(msg.speed_horizontal - 10.0) < 0.5

    def test_decode_location_ground(self, decoder: OpenDroneIDDecoder) -> None:
        """Test decoding location of grounded drone."""
        data = bytearray(25)
        data[0] = 0x11  # msg_type=1, status=1 (Ground)

        msg = decoder.decode_message(bytes(data))
        assert isinstance(msg, LocationMessage)
        assert msg.status == OperationalStatus.GROUND


class TestSystemMessage:
    """Tests for System message decoding."""

    def test_decode_system_operator_location(
        self, decoder: OpenDroneIDDecoder
    ) -> None:
        """Test decoding operator location."""
        data = bytearray(25)
        data[0] = 0x40  # msg_type=4

        # Operator latitude: 49.866 * 1e7 = 498660000
        struct.pack_into("<i", data, 1, 498660000)
        # Operator longitude: 10.839 * 1e7 = 108390000
        struct.pack_into("<i", data, 5, 108390000)

        msg = decoder.decode_message(bytes(data))
        assert isinstance(msg, SystemMessage)
        assert abs(msg.operator_latitude - 49.866) < 0.0001
        assert abs(msg.operator_longitude - 10.839) < 0.0001


class TestOperatorIDMessage:
    """Tests for Operator ID message decoding."""

    def test_decode_operator_id(self, decoder: OpenDroneIDDecoder) -> None:
        """Test decoding operator ID."""
        data = bytes([0x50]) + b"OP-12345-EU" + bytes(9) + bytes(4)

        msg = decoder.decode_message(bytes(data))
        assert isinstance(msg, OperatorIDMessage)
        assert msg.operator_id == "OP-12345-EU"


class TestUnknownMessage:
    """Tests for unknown message handling."""

    def test_unknown_message_type(self, decoder: OpenDroneIDDecoder) -> None:
        """Test handling of unknown message type."""
        data = bytes([0xA0]) + bytes(24)  # msg_type=10 (unknown)
        msg = decoder.decode_message(data)
        assert msg is None
