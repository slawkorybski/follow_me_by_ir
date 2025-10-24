"""Device update coordination for Follow Me by IR."""

import datetime
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import (CoordinatorEntity,
                                                      DataUpdateCoordinator)
from .device import Device
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class DeviceUpdateCoordinator(DataUpdateCoordinator):
    """Device update coordinator for Follow Me by IR."""

    def __init__(self, hass: HomeAssistant, device: Device) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=datetime.timedelta(seconds=device.refresh_interval),
            request_refresh_debouncer=Debouncer(
                hass,
                _LOGGER,
                cooldown=1,
                immediate=True,
            )
        )

        self._device = device

    @property
    def device(self) -> Device:
        """Fetch the device object."""
        return self._device

    async def _async_update_data(self) -> None:
        """Update the device data."""
        _LOGGER.info(f"DeviceUpdateCoordinator _async_update_data")
        
        await self._device.send_temperature_ir()    
        
    async def set_temperature(self, temperature: str) -> None:
        self._device.set_temperature( temperature ) 
        # Update state
        await self.async_request_refresh() 

    async def set_enabled(self, enabled: bool) -> None:
        self._device.set_enabled( enabled ) 
        # Update state
        await self.async_request_refresh() 


class DeviceCoordinatorEntity(CoordinatorEntity):
    """Coordinator entity for Follow Me."""

    def __init__(self, coordinator: DeviceUpdateCoordinator) -> None:
        super().__init__(coordinator)

        # Save reference to device
        self._device = coordinator.device

    @property
    def available(self) -> bool:
        """Check device availability."""
        return self._device._enabled        

    @property
    def enabled(self) -> bool:
        """Check device availability."""
        return self._device._enabled        
