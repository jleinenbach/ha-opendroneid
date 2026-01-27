# CLAUDE.md - OpenDroneID BLE Receiver

> **Home Assistant Custom Integration for Drone Detection via BLE Remote ID**

## Project Overview

| Property | Value |
|----------|-------|
| **Domain** | `opendroneid` |
| **Purpose** | Detect drones via BLE Remote ID broadcasts |
| **Data Source** | ESPHome Bluetooth Proxies |
| **Standards** | ASTM F3411-22a, ASD-STAN prEN 4709-002 |
| **Target HA Version** | 2026.1+ |
| **Quality Scale Target** | Platinum |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Home Assistant                                       │
│                                                                          │
│  ┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐ │
│  │ ESPHome Proxy 1  │────▶│                  │────▶│ device_tracker  │ │
│  │ (Living Room)    │     │   OpenDroneID    │     │ drone_<serial>  │ │
│  └──────────────────┘     │   Integration    │     ├─────────────────┤ │
│  ┌──────────────────┐     │                  │     │ sensor          │ │
│  │ ESPHome Proxy 2  │────▶│  - BLE Scanner   │────▶│ altitude, speed │ │
│  │ (Garden)         │     │  - Decoder       │     │ rssi, distance  │ │
│  └──────────────────┘     │  - Coordinator   │     └─────────────────┘ │
│  ┌──────────────────┐     │                  │                         │
│  │ ESPHome Proxy N  │────▶│                  │                         │
│  └──────────────────┘     └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## BLE Remote ID Protocol

### Identification

| Field | Value | Description |
|-------|-------|-------------|
| Service UUID | `0xFFFA` | ASTM International Remote ID |
| App Code | `0x0D` | Open Drone ID |
| Payload | 25 bytes | Drone ID message |

### Message Types (ASTM F3411-22a)

| Type | Code | Content |
|------|------|---------|
| Basic ID | `0x00` | Serial number, registration |
| Location | `0x01` | Lat, Lon, Alt, Speed, Direction |
| Auth | `0x02` | Authentication data |
| Self ID | `0x03` | Operator description |
| System | `0x04` | Operator location, area |
| Operator ID | `0x05` | Operator registration |
| Message Pack | `0x0F` | Multiple messages combined |

### BLE Advertisement Structure

```
[AD Length][AD Type 0x16][UUID 0xFFFA][App 0x0D][Counter][25-byte Payload]
```

---

## Implementation Plan

### Phase 1: Core Infrastructure
- [ ] BLE advertisement parser for `0xFFFA` service data
- [ ] OpenDroneID message decoder (Basic ID, Location)
- [ ] Coordinator to manage drone states
- [ ] Device tracker entity for each drone

### Phase 2: Full Protocol Support
- [ ] All message types (Auth, Self ID, System, Operator ID)
- [ ] Message pack parsing
- [ ] Sensor entities (altitude, speed, RSSI, heading)

### Phase 3: Advanced Features
- [ ] Trilateration using multiple proxies
- [ ] Pilot location tracking
- [ ] Zone-based alerts
- [ ] Integration with DragonSync (optional)

---

## Key Files

| File | Purpose |
|------|---------|
| `const.py` | Constants, UUIDs, message types |
| `decoder.py` | OpenDroneID message decoder |
| `coordinator/` | DataUpdateCoordinator for drones |
| `device_tracker/` | Drone position entities |
| `sensor/` | Altitude, speed, RSSI sensors |

---

## BLE Integration Pattern

This integration uses Home Assistant's Bluetooth integration to receive
BLE advertisements from ESPHome proxies. Key pattern:

```python
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_register_callback,
)

def _async_handle_bluetooth_event(
    service_info: BluetoothServiceInfoBleak,
    change: BluetoothChange,
) -> None:
    """Handle BLE advertisement."""
    # Check for Remote ID service data
    if REMOTE_ID_SERVICE_UUID in service_info.service_data:
        payload = service_info.service_data[REMOTE_ID_SERVICE_UUID]
        # Decode and process...
```

---

## Testing Strategy

### Unit Tests
- Decoder tests with known payloads
- Coordinator state management
- Entity creation and updates

### Integration Tests
- Mock BLE advertisements
- Config flow validation
- Entity state changes

### Reference Data
Use captures from real drones or test broadcasts from:
- https://github.com/opendroneid/transmitter-linux

---

## Related Projects

- [opendroneid-core-c](https://github.com/opendroneid/opendroneid-core-c) - Reference C library
- [micropython-remoteid](https://github.com/Gurkengewuerz/micropython-remoteid) - MicroPython decoder
- [RemoteIDReceiver](https://github.com/cyber-defence-campus/RemoteIDReceiver) - Python backend
- [DragonSync](https://github.com/alphafox02/DragonSync) - Alternative receiver

---

## Coding Standards

See base CLAUDE.md patterns. Additional rules for this project:

1. **Decoder must be pure Python** - No C dependencies
2. **All coordinates in WGS84** - Lat/Lon as float
3. **Altitudes in meters** - Both geodetic and pressure
4. **Speeds in m/s** - Convert for display if needed
5. **RSSI from each proxy** - For potential trilateration

---

## Commands

```bash
# Run all checks
./script/check

# Run tests
pytest -v --cov=custom_components/opendroneid

# Type check
pyright custom_components/opendroneid
mypy --strict custom_components/opendroneid
```
