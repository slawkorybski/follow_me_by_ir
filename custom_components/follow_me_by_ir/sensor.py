from datetime import timedelta, datetime
import logging

import voluptuous as vol

from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.event import async_track_state_change
from homeassistant.util import Throttle
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfElectricCurrent, UnitOfEnergy, UnitOfPower, UnitOfElectricPotential, UnitOfTemperature, UnitOfFrequency
from homeassistant.const import (CONF_NAME, CONF_SCAN_INTERVAL)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .temperature_to_ir import encode_temperature

CONF_SOURCE_TEMPERATURE_ID = "temperature_entity_id"
CONF_IEEE = "ieee"

logger = logging.getLogger(__name__)

DEFAULT_NAME = 'FollowMe by IR'
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SOURCE_TEMPERATURE_ID): cv.string,
    vol.Required(CONF_IEEE): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    cv.time_period, cv.positive_timedelta
                )
})

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    _name = config.get(CONF_NAME)
    _temperature_entity_id = config.get(CONF_SOURCE_TEMPERATURE_ID)
    _ieee = config.get(CONF_IEEE)
    _scan_interval = config.get(CONF_SCAN_INTERVAL)
    
    dev = []
    dev.append(FollowMeIrSensor(hass, _name, _ieee, _temperature_entity_id, _scan_interval))

    async_add_entities(dev)

class FollowMeIrSensor(SensorEntity):
    def __init__(self, hass, name, ieee, temperature_entity_id, scan_interval):
        self._hass = hass
        self._client_name = name
        self._state = None
        self._temperature_entity_id = temperature_entity_id
        self._ieee = ieee
        self._code = None
        self._error = None
        #self.update = Throttle(scan_interval)(self._update)     
        
    async def async_added_to_hass(self) -> None:
        """Entity has been added to hass."""

        @callback
        def async_update_event_state_callback(event: Event[EventStateChangedData]) -> None:
            """Call when entity state changes."""
            try:
                logger.info('sensor state: {0}'.format(event.data["new_state"]))
                new_state = event.data["new_state"]
                if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                    return
                self._state = new_state.state
                self.async_schedule_update_ha_state(True)
            except (ValueError, TypeError) as ex:
                logger.error(ex)        

        self.async_on_remove(
            async_track_state_change_event(
                self._hass, [self._temperature_entity_id], async_update_event_state_callback
            )
        )        
   
    @property
    def name(self):
        return '{}'.format(self._client_name)

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
        return f"follow-me-{self._client_name.lower()}"  

    def update(self):
        try:
            logger.info(f"temperature to send: {self._state}")
            if self._state != None:
                self._code = encode_temperature( float(self._state) )
                logger.info(f"ir code to send: {self._code}")
                #self._code = "BTIjYREvAuADAQGeBuAFA0AB4AMT4AcB4AMbwAvgFwHAJ8AHCY+bMiPTCC8C///gAgcCCC8C"

                param = {
                    "code": self._code
                }
         
                service_data = {
                    "ieee": self._ieee,
                    "endpoint_id": 1,
                    "cluster_id": 57348,
                    "cluster_type": "in",
                    "command": 2,
                    "command_type": "server",
                    "params": param
                }
        
                message = f"service_data is {service_data}"
                logger.info(message)

                self._hass.services.call("zha", "issue_zigbee_cluster_command", service_data, False)  

                self._error = None
        except (ValueError, TypeError) as ex:
            self._error = ex
            logger.error(ex)
