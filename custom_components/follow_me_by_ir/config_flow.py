"""Config flow for Follow Me by IR."""
from __future__ import annotations

from typing import Any, Optional, cast
import logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import (CONF_ID)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (CountrySelector,
                                            CountrySelectorConfig,
                                            SelectSelector,
                                            SelectSelectorConfig,
                                            SelectSelectorMode)

from .const import (DOMAIN, CONF_SCAN_INTERVAL, CONF_IR_BLASTER_IEEE,
                    CONF_TEMPERATURE_ENTITY_ID)

logger = logging.getLogger(__name__)

_DEFAULT_OPTIONS = {
    CONF_SCAN_INTERVAL: 60,
    CONF_IR_BLASTER_IEEE: "00:00:00:00:00:00:00:00",
    CONF_TEMPERATURE_ENTITY_ID: "sensor.temperature"
}


class FollowMeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Follow Me by IR."""

    VERSION = 1
    MINOR_VERSION = 1
    
    async def async_step_user(self, user_input) -> FlowResult:
        """Handle a config flow initialized by the user."""

        if user_input is not None:
            # Save the device into global data
            self.hass.data.setdefault(DOMAIN, {})

            # Populate config data
            data = {**user_input}

            logger.info(f"FollowMeConfigFlow data: {data}")

            # Create a config entry with the config data and default options
            return self.async_create_entry(title=f"{DOMAIN}", data=data, options=data)

        user_input = user_input or {}

        data_schema = vol.Schema({
            vol.Required(CONF_SCAN_INTERVAL,
                         default=user_input.get(CONF_SCAN_INTERVAL, _DEFAULT_OPTIONS[CONF_SCAN_INTERVAL])): vol.All(vol.Coerce(int), vol.Range(min=5, max=180)),
            vol.Required(CONF_IR_BLASTER_IEEE,
                         description={"suggested_value": user_input.get(CONF_IR_BLASTER_IEEE, _DEFAULT_OPTIONS[CONF_IR_BLASTER_IEEE] )}): cv.string,
            vol.Required(CONF_TEMPERATURE_ENTITY_ID,
                         description={"suggested_value": user_input.get(CONF_TEMPERATURE_ENTITY_ID, _DEFAULT_OPTIONS[CONF_TEMPERATURE_ENTITY_ID] )}): cv.string,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)
    

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return FollowMeOptionsFlow(config_entry)


class FollowMeOptionsFlow(OptionsFlow):
    """Options flow from Follow Me by IR."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        # Store the config entry in a private attribute to avoid assigning
        # to a read-only property on the base OptionsFlow.
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Handle the first step of options flow."""
        if user_input is not None:
            logger.info(f"FollowMeOptionsFlow user_input: {user_input}")
            
            # Confusingly, data argument in OptionsFlow is passed to async_setup_entry in the options member
            return self.async_create_entry(title=f"{DOMAIN}", data=user_input)

        logger.info(f"FollowMeOptionsFlow data: {self._config_entry.data}, options: {self._config_entry.options}")

        OPTIONS_SCHEMA = vol.Schema({
            vol.Required(CONF_SCAN_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=5, max=180)),
            vol.Required(CONF_IR_BLASTER_IEEE): cv.string,
            vol.Required(CONF_TEMPERATURE_ENTITY_ID): cv.string,
        })
        
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self._config_entry.options
            ),
        )
