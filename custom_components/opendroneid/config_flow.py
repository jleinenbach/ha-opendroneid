"""Config flow for OpenDroneID BLE Receiver.

This integration uses Home Assistant's Bluetooth integration to receive
BLE advertisements from ESPHome proxies. No manual configuration of
proxies is needed - they are automatically discovered.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
import voluptuous as vol

from .const import (
    CONF_DRAGONSYNC_ENABLED,
    CONF_DRAGONSYNC_HOST,
    CONF_DRAGONSYNC_PORT,
    CONF_ENTITY_CLEANUP_DAYS,
    CONF_INACTIVE_TIMEOUT,
    DEFAULT_DRAGONSYNC_HOST,
    DEFAULT_DRAGONSYNC_PORT,
    DEFAULT_ENTITY_CLEANUP_DAYS,
    DEFAULT_INACTIVE_TIMEOUT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class OpenDroneIDConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenDroneID BLE Receiver."""

    VERSION = 1
    MINOR_VERSION = 2

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step.

        OpenDroneID uses Bluetooth, so we just need to confirm setup.
        ESPHome proxies are automatically discovered by HA's Bluetooth integration.
        """
        # Prevent duplicate entries
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="OpenDroneID BLE Receiver",
                data={},
                options={
                    CONF_INACTIVE_TIMEOUT: user_input.get(
                        CONF_INACTIVE_TIMEOUT, DEFAULT_INACTIVE_TIMEOUT
                    ),
                    CONF_ENTITY_CLEANUP_DAYS: user_input.get(
                        CONF_ENTITY_CLEANUP_DAYS, DEFAULT_ENTITY_CLEANUP_DAYS
                    ),
                    CONF_DRAGONSYNC_ENABLED: user_input.get(
                        CONF_DRAGONSYNC_ENABLED, False
                    ),
                    CONF_DRAGONSYNC_HOST: user_input.get(
                        CONF_DRAGONSYNC_HOST, DEFAULT_DRAGONSYNC_HOST
                    ),
                    CONF_DRAGONSYNC_PORT: user_input.get(
                        CONF_DRAGONSYNC_PORT, DEFAULT_DRAGONSYNC_PORT
                    ),
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_INACTIVE_TIMEOUT,
                        default=DEFAULT_INACTIVE_TIMEOUT,
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=30,
                            max=600,
                            step=10,
                            unit_of_measurement="seconds",
                            mode=NumberSelectorMode.SLIDER,
                        )
                    ),
                    vol.Optional(
                        CONF_ENTITY_CLEANUP_DAYS,
                        default=DEFAULT_ENTITY_CLEANUP_DAYS,
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=365,
                            step=1,
                            unit_of_measurement="days",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_DRAGONSYNC_ENABLED,
                        default=False,
                    ): BooleanSelector(),
                    vol.Optional(
                        CONF_DRAGONSYNC_HOST,
                        default=DEFAULT_DRAGONSYNC_HOST,
                    ): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.TEXT,
                        )
                    ),
                    vol.Optional(
                        CONF_DRAGONSYNC_PORT,
                        default=DEFAULT_DRAGONSYNC_PORT,
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1024,
                            max=65535,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
            description_placeholders={
                "ble_info": "The integration will use all available Bluetooth "
                "adapters and ESPHome proxies to detect drones."
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Get the options flow."""
        return OpenDroneIDOptionsFlow()


class OpenDroneIDOptionsFlow(OptionsFlow):
    """Handle options flow for OpenDroneID."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_INACTIVE_TIMEOUT,
                        default=self.config_entry.options.get(
                            CONF_INACTIVE_TIMEOUT, DEFAULT_INACTIVE_TIMEOUT
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=30,
                            max=600,
                            step=10,
                            unit_of_measurement="seconds",
                            mode=NumberSelectorMode.SLIDER,
                        )
                    ),
                    vol.Optional(
                        CONF_ENTITY_CLEANUP_DAYS,
                        default=self.config_entry.options.get(
                            CONF_ENTITY_CLEANUP_DAYS, DEFAULT_ENTITY_CLEANUP_DAYS
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=365,
                            step=1,
                            unit_of_measurement="days",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_DRAGONSYNC_ENABLED,
                        default=self.config_entry.options.get(
                            CONF_DRAGONSYNC_ENABLED, False
                        ),
                    ): BooleanSelector(),
                    vol.Optional(
                        CONF_DRAGONSYNC_HOST,
                        default=self.config_entry.options.get(
                            CONF_DRAGONSYNC_HOST, DEFAULT_DRAGONSYNC_HOST
                        ),
                    ): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.TEXT,
                        )
                    ),
                    vol.Optional(
                        CONF_DRAGONSYNC_PORT,
                        default=self.config_entry.options.get(
                            CONF_DRAGONSYNC_PORT, DEFAULT_DRAGONSYNC_PORT
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1024,
                            max=65535,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
