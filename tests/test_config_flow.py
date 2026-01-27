"""Tests for config flow."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.opendroneid.const import (
    CONF_INACTIVE_TIMEOUT,
    DEFAULT_INACTIVE_TIMEOUT,
    DOMAIN,
)


async def test_user_flow_success(hass: HomeAssistant) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_INACTIVE_TIMEOUT: DEFAULT_INACTIVE_TIMEOUT},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "OpenDroneID BLE Receiver"
    assert result["options"] == {CONF_INACTIVE_TIMEOUT: DEFAULT_INACTIVE_TIMEOUT}


async def test_user_flow_already_configured(hass: HomeAssistant) -> None:
    """Test user flow when already configured."""
    # First setup
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_INACTIVE_TIMEOUT: DEFAULT_INACTIVE_TIMEOUT},
    )

    # Second setup should abort
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
