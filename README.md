# OpenDroneID BLE Receiver

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/jleinenbach/ha-opendroneid.svg)](https://github.com/jleinenbach/ha-opendroneid/releases)
[![License](https://img.shields.io/github/license/jleinenbach/ha-opendroneid.svg)](LICENSE)

**Home Assistant integration to detect drones via BLE Remote ID broadcasts using ESPHome Bluetooth Proxies.**

Since January 2024, all drones sold in the EU must broadcast their identification and location via Bluetooth Low Energy (BLE) according to the Remote ID standard. This integration allows you to detect these drones in your area using your existing ESPHome Bluetooth proxies.

![Drone Detection Map](docs/images/map-example.png)

## Features

- 🛸 **Drone Detection** - Automatically detects drones transmitting BLE Remote ID
- 📍 **Real-time Position Tracking** - Shows drone position on Home Assistant maps
- 🏠 **Pilot Location** - Displays operator/pilot position when available
- 📡 **Multi-Proxy Support** - Uses all your existing ESPHome BLE proxies
- 🔋 **No Additional Hardware** - Works with your existing ESPHome devices
- ⚡ **Instant Updates** - Real-time data via BLE advertisements

## Standards Compliance

This integration decodes Remote ID broadcasts compliant with:

- **ASTM F3411-22a** - Standard Specification for Remote ID (FAA)
- **ASD-STAN prEN 4709-002** - European Standard for UAS Remote ID (EU)

## Requirements

- Home Assistant **2026.1** or newer
- One or more **ESPHome devices** with `bluetooth_proxy` enabled
- Drones in range transmitting **BLE Remote ID** (mandatory in EU since Jan 2024)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu (⋮) → **Custom repositories**
3. Add `https://github.com/jleinenbach/ha-opendroneid` as **Integration**
4. Search for "OpenDroneID" in HACS
5. Click **Download**
6. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/jleinenbach/ha-opendroneid/releases)
2. Extract and copy `custom_components/opendroneid` to your `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **"OpenDroneID"**
4. Configure the inactive timeout (default: 120 seconds)
5. Click **Submit**

That's it! The integration will automatically use all available Bluetooth adapters and ESPHome proxies to detect drones.

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| Inactive Timeout | 120s | Time before a drone is removed after losing signal |

## Entities Created

For each detected drone, the integration creates a `device_tracker` entity:

### Device Tracker

| Entity ID | Description |
|-----------|-------------|
| `device_tracker.drone_<id>` | Drone position for map display |

### Attributes

Each drone entity includes these attributes:

| Attribute | Description |
|-----------|-------------|
| `latitude` | Current latitude (WGS84) |
| `longitude` | Current longitude (WGS84) |
| `altitude` | Geodetic altitude in meters |
| `altitude_barometric` | Pressure altitude in meters |
| `height` | Height above takeoff/ground |
| `speed` | Horizontal speed in m/s |
| `vertical_speed` | Vertical speed in m/s |
| `heading` | Direction in degrees (0-360) |
| `uas_id` | Drone serial number or registration |
| `id_type` | ID type (Serial, CAA Registration, etc.) |
| `ua_type` | Aircraft type (Helicopter, Aeroplane, etc.) |
| `status` | Operational status (Ground, Airborne, Emergency) |
| `operator_latitude` | Pilot/operator latitude |
| `operator_longitude` | Pilot/operator longitude |
| `operator_id` | Operator registration ID |
| `rssi` | Signal strength in dBm |
| `last_seen` | Timestamp of last received message |

### Entity States

| State | Description |
|-------|-------------|
| `ground` | Drone is on the ground |
| `airborne` | Drone is flying |
| `emergency` | Drone declared emergency |
| `malfunction` | Remote ID system failure |
| `unknown` | Status not reported |

## ESPHome Proxy Configuration

Ensure your ESPHome devices have Bluetooth proxy enabled:

```yaml
esp32:
  board: esp32dev
  framework:
    type: esp-idf  # Recommended for best BLE performance

bluetooth_proxy:
  active: true
```

**Tip:** For best coverage, distribute multiple ESPHome proxies around your property. The integration will combine data from all proxies.

## Dashboard Examples

### Map Card

```yaml
type: map
entities:
  - device_tracker.drone_abc123def456
default_zoom: 15
```

### Entities Card with Drone Info

```yaml
type: entities
title: Detected Drones
entities:
  - entity: device_tracker.drone_abc123def456
    secondary_info: attribute
    attribute: uas_id
```

### Automation Example

```yaml
automation:
  - alias: "Drone Detected Alert"
    trigger:
      - platform: state
        entity_id: device_tracker.drone_abc123def456
        to: "airborne"
    action:
      - service: notify.mobile_app
        data:
          title: "Drone Detected!"
          message: "A drone is flying nearby"
```

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  ESPHome Proxy  │────▶│  Home Assistant │────▶│  Device Tracker │
│  (BLE Scanner)  │     │  (This Integr.) │     │  + Map Display  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         ▲
         │ BLE Advertisement
         │ Service UUID: 0xFFFA
         │
    ┌─────────────┐
    │   Drone     │
    │ (Remote ID) │
    └─────────────┘
```

1. Drones broadcast Remote ID data via BLE (Service UUID 0xFFFA)
2. ESPHome proxies receive advertisements and forward to Home Assistant
3. This integration decodes the OpenDroneID protocol
4. Creates device_tracker entities with GPS coordinates
5. Entities appear on maps and can trigger automations

## Troubleshooting

### No Drones Detected

1. **Check ESPHome proxies** - Ensure `bluetooth_proxy` is enabled and active
2. **Verify BLE range** - Remote ID broadcasts have limited range (~300-500m)
3. **Check drone compliance** - Not all drones transmit Remote ID (older models, DIY)
4. **Enable debug logging**:

```yaml
logger:
  logs:
    custom_components.opendroneid: debug
```

### Drones Disappear Quickly

Increase the inactive timeout in the integration options.

### Position Not Updating

The drone may not be transmitting location data (e.g., GPS not acquired). Check the `status` attribute.

## Privacy & Legal

This integration only receives **publicly broadcast** Remote ID data. Drones are legally required to transmit this information for aviation safety. The data received includes:

- Drone identification (serial number or registration)
- Drone position and altitude
- Pilot/operator position
- Flight status

No private data is collected. All information is broadcast openly by the drone per legal requirements.

## Related Projects

- [opendroneid-core-c](https://github.com/opendroneid/opendroneid-core-c) - Reference C implementation
- [DragonSync](https://github.com/alphafox02/DragonSync) - Alternative receiver with dedicated hardware
- [Bermuda BLE Trilateration](https://github.com/agittins/bermuda) - BLE room presence tracking

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

For bug reports, please [open an issue](https://github.com/jleinenbach/ha-opendroneid/issues).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenDroneID community for protocol documentation
- ESPHome team for the excellent Bluetooth proxy
- Home Assistant community

---

**Note:** This integration is not affiliated with any drone manufacturer. Remote ID is a regulatory requirement, not a tracking feature.
