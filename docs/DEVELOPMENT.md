# Development Guide

This document describes how to set up a development environment and contribute to the OpenDroneID integration.

## Prerequisites

- Python 3.12+
- Home Assistant development environment
- Git

## Setup

### Clone Repository

```bash
git clone https://github.com/jleinenbach/ha-opendroneid.git
cd ha-opendroneid
```

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

### Install Dependencies

```bash
pip install -r requirements_dev.txt
```

## Project Structure

```
ha-opendroneid/
├── custom_components/opendroneid/
│   ├── __init__.py          # Integration entry point
│   ├── config_flow.py       # Setup UI flow
│   ├── const.py             # Constants
│   ├── coordinator/         # BLE data coordinator
│   │   └── __init__.py
│   ├── decoder/             # OpenDroneID protocol decoder
│   │   └── __init__.py
│   ├── device_tracker/      # Device tracker platform
│   │   └── __init__.py
│   ├── diagnostics.py       # Diagnostics support
│   ├── manifest.json        # Integration manifest
│   ├── strings.json         # UI strings (English)
│   └── translations/        # Localized strings
│       ├── de.json
│       ├── en.json
│       ├── es.json
│       ├── fr.json
│       ├── nl.json
│       ├── pl.json
│       ├── pt.json
│       └── uk.json
├── tests/                   # Test suite
├── docs/                    # Documentation
├── hacs.json               # HACS configuration
├── README.md               # Main documentation
└── requirements_dev.txt    # Development dependencies
```

## Code Quality

### Linting

```bash
# Run ruff linter
ruff check custom_components/opendroneid

# Auto-fix issues
ruff check --fix custom_components/opendroneid
```

### Type Checking

```bash
# Run mypy
mypy custom_components/opendroneid

# Run pyright (stricter)
pyright custom_components/opendroneid
```

### Formatting

```bash
# Format code with ruff
ruff format custom_components/opendroneid
```

### All Checks

```bash
# Run all quality checks
./script/check
```

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=custom_components/opendroneid --cov-report=html

# Run specific test file
pytest tests/test_decoder.py -v
```

### Test Data

Test payloads can be generated using the [OpenDroneID transmitter](https://github.com/opendroneid/transmitter-linux) or captured from real drones.

Example test payload (Basic ID):

```python
# Basic ID message: Serial Number "TEST1234567890"
BASIC_ID_PAYLOAD = bytes([
    0x01,  # msg_type=0, id_type=1 (Serial)
    0x02,  # ua_type=2 (Helicopter)
    # UAS ID: "TEST1234567890" + padding
    0x54, 0x45, 0x53, 0x54, 0x31, 0x32, 0x33, 0x34,
    0x35, 0x36, 0x37, 0x38, 0x39, 0x30, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00,  # Reserved
])
```

## Adding a New Message Type

1. Add constants to `const.py`:

```python
MSG_TYPE_NEW: Final = 0x06
```

2. Create dataclass in `decoder/__init__.py`:

```python
@dataclass
class NewMessage:
    """New message type (type 0x06)."""
    field1: int = 0
    field2: str = ""
```

3. Add decoder method:

```python
def _decode_new(self, data: bytes) -> NewMessage:
    """Decode New message (type 0x06)."""
    msg = NewMessage()
    # ... decode fields
    return msg
```

4. Register in `decode_message()`:

```python
elif msg_type == MSG_TYPE_NEW:
    return self._decode_new(data)
```

5. Update `DroneData` if needed and handle in coordinator.

6. Add tests for the new message type.

## Translations

### Adding a New Language

1. Copy `translations/en.json` to `translations/<lang>.json`
2. Translate all strings
3. Test in Home Assistant

### Translation Guidelines

- Keep technical terms (like "Remote ID") unchanged
- Maintain placeholder syntax: `{placeholder}`
- Keep JSON structure identical to English

## Debugging

### Enable Debug Logging

In Home Assistant `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.opendroneid: debug
```

### BLE Debugging

To see raw BLE advertisements:

```yaml
logger:
  logs:
    homeassistant.components.bluetooth: debug
```

## Pull Request Guidelines

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/my-feature`
3. **Make** your changes
4. **Run** all checks: `./script/check`
5. **Commit** with clear message
6. **Push** to your fork
7. **Open** a Pull Request

### Commit Messages

Follow conventional commits:

```
feat: add support for Auth messages
fix: correct altitude calculation for negative values
docs: update installation instructions
test: add decoder unit tests
```

## Release Process

1. Update version in `manifest.json`
2. Update `CHANGELOG.md`
3. Create GitHub Release with tag `vX.Y.Z`
4. HACS will automatically pick up the new release

## Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Home Assistant Bluetooth Integration](https://developers.home-assistant.io/docs/core/bluetooth/)
- [ASTM F3411 Standard](https://www.astm.org/f3411-22a.html)
- [OpenDroneID Reference](https://github.com/opendroneid/opendroneid-core-c)
