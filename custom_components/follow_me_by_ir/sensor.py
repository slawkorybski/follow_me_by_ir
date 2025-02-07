"""Sensor platform for Follow Me by IR"""
from __future__ import annotations

from datetime import timedelta, datetime
import logging

import voluptuous as vol

from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.event import async_track_state_change
from homeassistant.util import Throttle
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from typing import Optional
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, CONF_SCAN_INTERVAL, CONF_IR_BLASTER_IEEE, CONF_TEMPERATURE_ENTITY_ID
from .coordinator import DeviceCoordinatorEntity, DeviceUpdateCoordinator
from .temperature_to_ir import encode_temperature

logger = logging.getLogger(__name__)

DEFAULT_NAME = 'FollowMe by IR'

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Setup the sensor platform for Follow Me by IR"""

    logger.info("Setting up sensor platform.")

    options = config_entry.options
    
    _name = options.get(CONF_NAME, DEFAULT_NAME)
    _temperature_entity_id = options.get(CONF_TEMPERATURE_ENTITY_ID)
    
    logger.info(f"Setting up sensor platform. _temperature_entity_id: {_temperature_entity_id}")

    # Fetch coordinator from global data
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    entities.append(FollowMeIrSensor(coordinator, _name, _temperature_entity_id))

    async_add_entities(entities)


class FollowMeIrSensor(DeviceCoordinatorEntity, SensorEntity):
    """Generic sensor class for Follow Me by IR."""

    def __init__(self,
                 coordinator: DeviceUpdateCoordinator,
                 name, 
                 temperature_entity_id) -> None:
        DeviceCoordinatorEntity.__init__(self, coordinator)

        #self._hass = hass
        self._client_name = name
        self._state: str | None = None
        self._temperature_entity_id = temperature_entity_id
        self._code = None
        self._error = None
        self._prop = "temperature"
        
    @property
    def name(self):
        return f"{self._client_name} {self._prop}"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        state_attr = {
            'code': self._code,
            'error': self._error
        }
        return state_attr

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._device.id}_{self._prop}"

    @property
    def device_info(self) -> dict:
        """Return info for device registry."""
        return {
            "identifiers": {
                (DOMAIN, self._device.id)
            },
        }

    @property
    def available(self) -> bool:
        """Check entity availability."""
        # Sensor is unavailable if device is offline or value is None
        return super().available and self.native_value is not None

    @property
    def native_value(self) -> str | None:
        """Return the current native value."""
        value = getattr(self._device, self._prop, None)

        if value is None:
            return None
        
        return value
       
    @callback
    def _handle_coordinator_update(self):
        """Update the sensor with the provided data."""
        self._state = self.native_value
        self.async_write_ha_state()
      
    async def async_added_to_hass(self) -> None:
        """Run when entity is about to be added to hass."""
        await super().async_added_to_hass() 

        logger.info('FollowMeIrSensor async_added_to_hass')  

        @callback
        async def async_update_event_state_callback(event: Event[EventStateChangedData]) -> None:
            """Call when entity state changes."""
            try:
                logger.info('async_update_event_state_callback new_state: {0}'.format(event.data["new_state"]))
                new_state = event.data["new_state"]
                if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                    return

                await self.coordinator.set_temperature( new_state.state )
            except (ValueError, TypeError) as ex:
                logger.error(ex)        
       
        if self._temperature_entity_id:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._temperature_entity_id], async_update_event_state_callback
                )
            )            
            
            temp_sensor_state = self.hass.states.get(self._temperature_entity_id)
            logger.info('async_added_to_hass temp_sensor_state: {0}'.format(temp_sensor_state))
            if temp_sensor_state and temp_sensor_state.state != STATE_UNKNOWN and temp_sensor_state.state != STATE_UNAVAILABLE:
                await self.coordinator.set_temperature( temp_sensor_state.state )

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        # Call super method to ensure lifecycle is properly handled
        await super().async_will_remove_from_hass()

        logger.info('FollowMeIrSensor async_will_remove_from_hass')        


