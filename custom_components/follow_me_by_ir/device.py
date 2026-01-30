"""Device update coordination for Follow Me by IR."""

import datetime
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import (CoordinatorEntity,
                                                      DataUpdateCoordinator)
from .temperature_to_ir import encode_temperature

from .const import DOMAIN

logger = logging.getLogger(__name__)


class Device():
    """Device update coordinator for Follow Me by IR."""

    def __init__(self, hass: HomeAssistant, ieee: str, refresh_interval) -> None:
        self._hass = hass
        self._ieee = ieee
        self._enabled = True
        self._refresh_interval = refresh_interval
        self._temperature = None
        self._previous_temperature = None
        self._error = None

    @property    
    def id(self) -> str:
        return self._ieee[-5:]
        
    @property
    def temperature(self) -> int:
        return self._temperature
        
    @property    
    def id(self) -> str:
        return self._ieee[-5:]
        
    @property
    def refresh_interval(self) -> int:
        return self._refresh_interval

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_temperature(self, temperature: str) -> None:
        logger.info(f"temperature: {temperature}")

        current_temperature = float(temperature)
        temperature_to_send = round(current_temperature) 
        trend_up = None

        if self._previous_temperature is not None:
            if self._previous_temperature < current_temperature:
                trend_up = True
            elif self._previous_temperature > current_temperature:
                trend_up = False

        if trend_up is not None:
            # Summer
            # if trend_up:
                # temperature_to_send = int(current_temperature)
            # else:
                # if current_temperature % 1 > 0.0:
                    # temperature_to_send = int(current_temperature) + 1
                # else:
                    # temperature_to_send = int(current_temperature)
            # Winter
            temperature_to_send = int(current_temperature)

        self._previous_temperature = current_temperature

        logger.info(f"temperature_to_send: {temperature_to_send}")
        self._temperature = temperature_to_send
        
    async def send_temperature_ir(self) -> None:
        try:
            logger.info(f"temperature to send: {self._temperature}")
            logger.info(f"enabled: {self._enabled}")
            
            if self._temperature is not None and self._enabled:
                self._code = encode_temperature( self._temperature )
                logger.info(f"ir code to send: {self._code}")

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
                
                await self._hass.services.async_call(
                        "zha", "issue_zigbee_cluster_command", service_data, False
                    ) 
                #self._hass.async_create_task(
                #    self._hass.services.async_call(
                #        "zha", "issue_zigbee_cluster_command", service_data, False
                #    ) 
                #)
                #self._hass.services.call("zha", "issue_zigbee_cluster_command", service_data, False)  

                self._error = None
        except (ValueError, TypeError) as ex:
            self._error = ex
            logger.error(ex)


