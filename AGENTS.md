# CLAUDE.md - AI Agent Instructions

> **Primary instruction file for Claude, GitHub Copilot, and other AI coding assistants.**
>
> This file follows the [CLAUDE.md specification](https://docs.anthropic.com/en/docs/claude-code/memory#claudemd) for AI-assisted development.

## 🎯 Project Overview

This is a **Home Assistant Custom Integration** targeting **Platinum Quality Scale** standards.

| Property | Value |
|----------|-------|
| **Target HA Version** | 2026.1+ (minimum) |
| **Python Version** | 3.13+ |
| **Quality Scale Target** | Platinum |
| **HACS Compatible** | Yes |
| **Type Checking** | Pyright + mypy --strict |
| **Linting** | Ruff (format + check) |

---

## ⚠️ CRITICAL: Quality Scale Tracking

**AI agents MUST maintain `custom_components/your_domain/quality_scale.yaml`!**

This file tracks compliance with [Home Assistant Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/). After implementing or modifying any feature:

1. **Update the corresponding rule status** from `todo` to `done`
2. **Add a comment** explaining how the rule is satisfied
3. **Never mark a rule as `done` without implementation**

```yaml
# Example update after implementing diagnostics:
rules:
  diagnostics:
    status: done  # Changed from 'todo'
    comment: "Implemented in diagnostics.py with redacted sensitive data"
```

### Quality Scale Rules Summary

| Tier | Rules Count | Required Coverage |
|------|-------------|-------------------|
| Bronze | 18 | 100% - Basics |
| Silver | 10 | 100% - Robustness |
| Gold | 22 | 100% - Polish |
| Platinum | 3 | 100% - Excellence |

---

## 🔧 Build & Validation Commands

### Mandatory Pre-Commit Checks

Run ALL checks before committing:

```bash
# Full validation suite (REQUIRED before every commit)
./script/check

# Individual checks:
./script/lint          # Ruff format + check --fix
./script/type-check    # Pyright + mypy --strict
./script/test --cov    # pytest with >95% coverage
./script/hassfest      # Home Assistant manifest validation
```

### Quick Commands

```bash
# Format code (auto-fix)
ruff format .
ruff check --fix .

# Type checking (strict)
pyright .
mypy --strict custom_components/

# Run tests
pytest -v --cov=custom_components --cov-fail-under=95

# Validate manifest
python -m homeassistant.scripts.hassfest validate
```

---

## 📁 Project Structure

```
custom_components/your_domain/
├── __init__.py              # Entry point (setup/unload)
├── config_flow.py           # Config flow (user/reauth/reconfigure)
├── const.py                 # Constants (DOMAIN, etc.)
├── diagnostics.py           # Diagnostics download
├── manifest.json            # Integration metadata
├── quality_scale.yaml       # ⚠️ MUST BE MAINTAINED BY AI
├── strings.json             # English translations
├── py.typed                 # Strict typing marker (Platinum)
│
├── api/
│   ├── __init__.py
│   ├── client.py            # Async API client
│   └── exceptions.py        # Custom exceptions
│
├── coordinator/
│   └── __init__.py          # DataUpdateCoordinator
│
├── entity/
│   └── __init__.py          # Base entity class
│
├── [platform]/              # sensor, switch, binary_sensor, etc.
│   └── __init__.py          # Platform setup
│
└── translations/
    ├── en.json              # English
    └── de.json              # German
```

---

## 🚨 CRITICAL CODE PATTERNS

### 1. Async Timeout (MANDATORY)

```python
# ✅ CORRECT - Python 3.11+ asyncio.timeout
import asyncio

async with asyncio.timeout(10):
    await some_async_operation()

# ❌ WRONG - DEPRECATED async_timeout
# from async_timeout import timeout  # DO NOT USE
```

### 2. ConfigEntry.runtime_data (MANDATORY)

```python
# In __init__.py
from dataclasses import dataclass
from homeassistant.config_entries import ConfigEntry

type YourDomainConfigEntry = ConfigEntry[YourDomainData]

@dataclass
class YourDomainData:
    """Runtime data for the integration."""
    coordinator: YourDomainCoordinator
    client: YourDomainApiClient

async def async_setup_entry(
    hass: HomeAssistant,
    entry: YourDomainConfigEntry,
) -> bool:
    """Set up from config entry."""
    client = YourDomainApiClient(...)
    coordinator = YourDomainCoordinator(hass, client, entry)
    
    await coordinator.async_config_entry_first_refresh()
    
    # ✅ CORRECT - Use runtime_data
    entry.runtime_data = YourDomainData(
        coordinator=coordinator,
        client=client,
    )
    
    # ❌ WRONG - Do NOT use hass.data
    # hass.data.setdefault(DOMAIN, {})[entry.entry_id] = ...
```

### 3. Entity Definition (MANDATORY)

```python
class YourDomainEntity(CoordinatorEntity[YourDomainCoordinator]):
    """Base entity for YourDomain."""

    _attr_has_entity_name = True  # ⚠️ REQUIRED

    def __init__(
        self,
        coordinator: YourDomainCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self.entity_description = description
        
        # ⚠️ REQUIRED - Unique ID
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        
        # ⚠️ REQUIRED - Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name="Device Name",
            manufacturer="Manufacturer",
            model="Model",
        )
```

### 4. Inject WebSession (Platinum)

```python
# In __init__.py or wherever API client is created
from homeassistant.helpers.aiohttp_client import async_get_clientsession

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # ✅ CORRECT - Get session from Home Assistant
    session = async_get_clientsession(hass)
    client = YourDomainApiClient(
        host=entry.data[CONF_HOST],
        session=session,  # ⚠️ INJECT SESSION
    )
    
    # ❌ WRONG - Creating own session
    # client = YourDomainApiClient(host=..., session=aiohttp.ClientSession())
```

### 5. Exception Handling (MANDATORY)

```python
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    HomeAssistantError,
    ServiceValidationError,
)

# In async_setup_entry:
async def async_setup_entry(...) -> bool:
    try:
        await client.async_connect()
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed("Invalid credentials") from err
    except ConnectionError as err:
        raise ConfigEntryNotReady("Cannot connect") from err

# In services (action-exceptions rule):
async def async_handle_service(call: ServiceCall) -> None:
    try:
        await client.do_something()
    except AuthenticationError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="auth_failed",
        ) from err
```

### 6. Log When Unavailable (Silver)

```python
class YourDomainCoordinator(DataUpdateCoordinator):
    """Coordinator with proper unavailable logging."""
    
    _unavailable_logged: bool = False

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.client.async_get_data()
            
            # Log ONCE when connection restored
            if self._unavailable_logged:
                _LOGGER.info("Connection to %s restored", self.client.host)
                self._unavailable_logged = False
            
            return data
            
        except YourDomainApiCommunicationError as err:
            # Log ONCE when unavailable
            if not self._unavailable_logged:
                _LOGGER.warning("Unable to connect to %s", self.client.host)
                self._unavailable_logged = True
            
            raise UpdateFailed(f"Communication error: {err}") from err
```

---

## 📋 Type Annotation Requirements

### Full Strict Typing (Platinum)

```python
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

# All functions MUST have type annotations
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up from config entry."""
    ...

# All class attributes MUST be typed
class YourDomainSensor(YourDomainEntity, SensorEntity):
    """Sensor entity."""
    
    _attr_native_unit_of_measurement: str | None = None
    _attr_native_value: float | None = None
```

### py.typed Marker

The `py.typed` file MUST exist in the integration root:
```
custom_components/your_domain/py.typed
```

---

## 🔴 Common Mistakes to AVOID

| ❌ Mistake | ✅ Correct |
|-----------|-----------|
| `async_timeout.timeout()` | `asyncio.timeout()` |
| `hass.data[DOMAIN][entry_id]` | `entry.runtime_data` |
| Missing `has_entity_name = True` | `_attr_has_entity_name = True` |
| Creating own `ClientSession` | `async_get_clientsession(hass)` |
| Hardcoded entity names | Translation keys in `strings.json` |
| Log on every poll failure | Log once, flag `_unavailable_logged` |
| Missing `unique_id` | `_attr_unique_id = f"{entry_id}_{key}"` |
| Exception without translation | `HomeAssistantError(translation_key=...)` |

---

## 🧪 Testing Requirements

### Minimum Coverage: 95%

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_config_entry():
    """Create mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100"},
        entry_id="test_entry_id",
    )

@pytest.fixture
def mock_api_client():
    """Create mock API client."""
    with patch(
        "custom_components.your_domain.api.client.YourDomainApiClient"
    ) as mock:
        client = mock.return_value
        client.async_get_data = AsyncMock(return_value={"value": 42})
        yield client
```

### Required Test Files

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_config_flow.py      # 100% coverage (Bronze)
├── test_init.py             # Setup/unload tests
├── test_coordinator.py      # Coordinator tests
├── test_diagnostics.py      # Diagnostics tests
└── test_[platform].py       # Per-platform tests
```

---

## 📦 CI/CD Requirements

### GitHub Workflows

The CI workflow MUST include:

1. **Ruff** - `ruff format --check` + `ruff check`
2. **Pyright** - Type checking
3. **mypy --strict** - Additional strict type checking
4. **HACS Validation** - `hacs/action@main`
5. **Hassfest** - Manifest validation
6. **Tests** - pytest with >95% coverage
7. **HA Integration Test** - Verify module loads

---

## 📖 Reference Documentation

- [Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/)
- [Config Flow Documentation](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)
- [DataUpdateCoordinator](https://developers.home-assistant.io/docs/integration_fetching_data)
- [Entity Documentation](https://developers.home-assistant.io/docs/core/entity)
- [Diagnostics](https://developers.home-assistant.io/docs/integration_diagnostics)

### Platinum Reference Integrations

Study these in HA Core:
- `heos` - Full Platinum example
- `shelly` - Extensive device support  
- `brother` - Clean coordinator pattern
- `tplink` - Modern async patterns

---

## 📝 AI Agent Workflow

When working on this integration:

1. **Before coding**: Read `quality_scale.yaml` to understand current status
2. **During coding**: Follow patterns in this document exactly
3. **After coding**: 
   - Run `./script/check` 
   - Update `quality_scale.yaml` status
   - Ensure all tests pass
4. **Before committing**: Verify `ruff format .` and `mypy --strict` pass

### Reporting Issues

If you encounter blocking issues:
1. Document in code comment with `# TODO(AI):` prefix
2. Note in `quality_scale.yaml` under relevant rule
3. Suggest workaround if possible
