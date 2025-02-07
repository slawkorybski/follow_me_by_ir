"""Switch platform for Follow Me by IR"""
from __future__ import annotations

import logging
from typing import Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import DeviceCoordinatorEntity, DeviceUpdateCoordinator

logger = logging.getLogger(__name__)
DEFAULT_NAME = 'FollowMe by IR'

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    add_entities: AddEntitiesCallback,
) -> None:
    """Setup the switch platform for Follow Me by IR."""

    logger.info("Setting up switch platform.")
    
    options = config_entry.options
    
    _name = options.get(CONF_NAME, DEFAULT_NAME)    

    # Fetch coordinator from global data
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Add supported switch entities
    entities = [
        MideaFollowMeSwitch(coordinator, _name)
    ]

    add_entities(entities)

           
class MideaFollowMeSwitch(DeviceCoordinatorEntity, SwitchEntity):
    """Generic switch for Follow Me by IR."""

    _attr_translation_key = "enabled"

    def __init__(self, coordinator: DeviceUpdateCoordinator, name) -> None:
        DeviceCoordinatorEntity.__init__(self, coordinator)
        
        self._client_name = name
        self._prop = "enabled"
        
    @property
    def name(self):
        return f"{self._client_name} {self._prop}"      

    @property
    def unique_id(self) -> str:
        """Return the unique ID of this entity."""
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
    def id(self) -> str:
        return self._ieee[-5:]
        
    @property
    def available(self) -> bool:
        """Check entity availability."""
        return True

    @property
    def entity_category(self) -> str:
        """Return the entity category of this entity."""
        return EntityCategory.CONFIG

    @property
    def is_on(self) -> bool | None:
        """Return the on state of the switch."""
        return self.enabled
        
    async def _set_state(self, state) -> None:
        await self.coordinator.set_enabled(state)   
  
    async def async_turn_on(self) -> None:
        """Turn the switch on."""
        await self._set_state(True)

    async def async_turn_off(self) -> None:
        """Turn the switch off."""
        await self._set_state(False)            
            


