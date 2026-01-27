# OpenDroneID Protocol Documentation

This document describes the BLE Remote ID protocol as implemented by this integration.

## Overview

Remote ID is a regulatory requirement that enables drones to broadcast their identification and location information. This allows authorities and the public to identify drones and their operators.

## BLE Advertisement Structure

### Service UUID

Remote ID uses the 16-bit UUID assigned by ASTM International:

| Field | Value |
|-------|-------|
| UUID | `0xFFFA` |
| Full UUID | `0000fffa-0000-1000-8000-00805f9b34fb` |

### Service Data Format

```
[App Code: 1 byte][Counter: 1 byte][Message: 25 bytes]
```

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0 | 1 | App Code | Always `0x0D` for OpenDroneID |
| 1 | 1 | Counter | Message sequence number (0-255) |
| 2 | 25 | Payload | OpenDroneID message |

## Message Types

Each 25-byte message starts with a type nibble:

| Type | Code | Description |
|------|------|-------------|
| Basic ID | `0x0` | Drone identification |
| Location | `0x1` | Position and velocity |
| Auth | `0x2` | Authentication data |
| Self ID | `0x3` | Operator description |
| System | `0x4` | Operator location |
| Operator ID | `0x5` | Operator registration |
| Message Pack | `0xF` | Multiple messages |

### Basic ID Message (0x00)

Contains the drone's identification.

```
Byte 0: [msg_type:4][id_type:4]
Byte 1: [ua_type:4][reserved:4]
Bytes 2-21: UAS ID (20 chars, null-terminated ASCII)
Bytes 22-24: Reserved
```

**ID Types:**

| Value | Type |
|-------|------|
| 0 | None |
| 1 | Serial Number (ANSI/CTA-2063-A) |
| 2 | CAA Registration ID |
| 3 | UTM Assigned ID |
| 4 | Specific Session ID |

**UA Types:**

| Value | Aircraft Type |
|-------|---------------|
| 0 | None |
| 1 | Aeroplane |
| 2 | Helicopter/Multicopter |
| 3 | Gyroplane |
| 4 | Hybrid Lift (VTOL) |
| 5 | Ornithopter |
| 6 | Glider |
| 7 | Kite |
| 8 | Free Balloon |
| 9 | Captive Balloon |
| 10 | Airship |
| 11 | Parachute |
| 12 | Rocket |
| 13 | Tethered |
| 14 | Ground Obstacle |
| 15 | Other |

### Location Message (0x01)

Contains position, velocity, and altitude data.

```
Byte 0: [msg_type:4][status:4]
Byte 1: [height_type:1][ew_dir:1][speed_mult:1][reserved:5]
Byte 2: Direction (0-179 = 0-358°, 2° resolution)
Byte 3: Horizontal speed
Byte 4: Vertical speed (signed, offset binary)
Bytes 5-8: Latitude (int32 LE, 1e-7 degrees)
Bytes 9-12: Longitude (int32 LE, 1e-7 degrees)
Bytes 13-14: Pressure altitude (uint16 LE)
Bytes 15-16: Geodetic altitude (uint16 LE)
Bytes 17-18: Height (uint16 LE)
Byte 19: [vertical_acc:4][horizontal_acc:4]
Byte 20: [baro_acc:4][speed_acc:4]
Bytes 21-22: Timestamp (uint16 LE, 0.1s since hour)
Byte 23: Timestamp accuracy
Byte 24: Reserved
```

**Operational Status:**

| Value | Status |
|-------|--------|
| 0 | Undeclared |
| 1 | Ground |
| 2 | Airborne |
| 3 | Emergency |
| 4 | Remote ID System Failure |

**Altitude Encoding:**

```
altitude_meters = raw_value * 0.5 - 1000
```

Valid range: -1000m to +31767m

**Invalid Values:**

| Field | Invalid Value |
|-------|---------------|
| Latitude/Longitude | 0 |
| Altitude | 0xFFFF |
| Speed | 0xFF |
| Timestamp | 0xFFFF |

### System Message (0x04)

Contains operator/pilot location and area information.

```
Byte 0: [msg_type:4][op_loc_type:2][class_type:2]
Bytes 1-4: Operator latitude (int32 LE, 1e-7 degrees)
Bytes 5-8: Operator longitude (int32 LE, 1e-7 degrees)
Bytes 9-10: Area count (uint16 LE)
Byte 11: Area radius (10m units)
Bytes 12-13: Area ceiling (uint16 LE)
Bytes 14-15: Area floor (uint16 LE)
Byte 16: [category:4][class:4]
Bytes 17-18: Operator altitude (uint16 LE)
Bytes 19-24: Reserved
```

### Operator ID Message (0x05)

Contains the operator's registration ID.

```
Byte 0: [msg_type:4][op_id_type:4]
Bytes 1-20: Operator ID (20 chars, null-terminated ASCII)
Bytes 21-24: Reserved
```

## Coordinate Systems

### WGS84

All coordinates use the WGS84 datum (same as GPS).

- **Latitude:** -90.0 to +90.0 degrees
- **Longitude:** -180.0 to +180.0 degrees

### Altitude References

| Type | Description |
|------|-------------|
| Geodetic (HAE) | Height Above Ellipsoid (GPS altitude) |
| Barometric | Pressure altitude (QNE) |
| Height | Above takeoff point or AGL |

## References

- [ASTM F3411-22a](https://www.astm.org/f3411-22a.html) - Standard Specification for Remote ID
- [ASD-STAN prEN 4709-002](https://www.asd-stan.org/) - European Standard for UAS Remote ID
- [opendroneid-core-c](https://github.com/opendroneid/opendroneid-core-c) - Reference implementation
