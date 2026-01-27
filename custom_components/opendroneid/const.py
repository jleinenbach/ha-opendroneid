"""Constants for OpenDroneID BLE Receiver integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "opendroneid"

# BLE Remote ID identifiers (ASTM F3411 / ASD-STAN prEN 4709-002)
REMOTE_ID_SERVICE_UUID: Final = 0xFFFA  # ASTM International Remote ID
REMOTE_ID_APP_CODE: Final = 0x0D  # Open Drone ID

# Message types (ASTM F3411-22a)
MSG_TYPE_BASIC_ID: Final = 0x00
MSG_TYPE_LOCATION: Final = 0x01
MSG_TYPE_AUTH: Final = 0x02
MSG_TYPE_SELF_ID: Final = 0x03
MSG_TYPE_SYSTEM: Final = 0x04
MSG_TYPE_OPERATOR_ID: Final = 0x05
MSG_TYPE_MESSAGE_PACK: Final = 0x0F

# Default values
DEFAULT_SCAN_INTERVAL: Final = 5  # seconds
DEFAULT_INACTIVE_TIMEOUT: Final = 120  # seconds

# Configuration keys
CONF_ESPHOME_PROXIES: Final = "esphome_proxies"
CONF_INACTIVE_TIMEOUT: Final = "inactive_timeout"

# DragonSync configuration
CONF_DRAGONSYNC_ENABLED: Final = "dragonsync_enabled"
CONF_DRAGONSYNC_HOST: Final = "dragonsync_host"
CONF_DRAGONSYNC_PORT: Final = "dragonsync_port"
DEFAULT_DRAGONSYNC_HOST: Final = ""
DEFAULT_DRAGONSYNC_PORT: Final = 4224
