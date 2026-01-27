# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-01-27

### Added

- Initial release
- BLE Remote ID detection via ESPHome Bluetooth proxies
- OpenDroneID protocol decoder (ASTM F3411-22a / ASD-STAN prEN 4709-002)
- Support for message types:
  - Basic ID (drone identification)
  - Location (position, velocity, altitude)
  - System (operator location)
  - Operator ID (operator registration)
- Device tracker entities with GPS coordinates for map display
- Entity attributes: altitude, speed, heading, operator location, RSSI
- Configurable inactive timeout
- Automatic drone removal when signal lost
- Translations: English, German, French, Dutch, Portuguese, Polish, Ukrainian, Spanish
- HACS compatibility
- Comprehensive documentation

### Technical Details

- Uses Home Assistant Bluetooth integration for passive BLE scanning
- Service UUID: 0xFFFA (ASTM International Remote ID)
- App Code: 0x0D (OpenDroneID)
- Pure Python decoder (no external dependencies)

[Unreleased]: https://github.com/jleinenbach/ha-opendroneid/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jleinenbach/ha-opendroneid/releases/tag/v0.1.0
