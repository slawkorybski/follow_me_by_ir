"""Integration for Follow Me by IR."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (CONF_ID,
                                 Platform)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (DOMAIN, CONF_SCAN_INTERVAL, CONF_IR_BLASTER_IEEE)
from .coordinator import DeviceUpdateCoordinator
from .device import Device

_LOGGER = logging.getLogger(__name__)
_PLATFORMS = [
    Platform.SENSOR,
    Platform.SWITCH
]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Setup Follow Me device from a config entry."""

    # Ensure the global data dict exists
    hass.data.setdefault(DOMAIN, {})

    _LOGGER.info("config_entry.data %s, options %s.", config_entry.data, config_entry.options)

    refresh_interval = config_entry.options.get(CONF_SCAN_INTERVAL)
    ieee = config_entry.options.get(CONF_IR_BLASTER_IEEE)

    _LOGGER.info("refresh_interval %s.", refresh_interval)
    _LOGGER.info("ieee %s.", ieee)

    # Construct the device
    device = Device(hass=hass, ieee=ieee, refresh_interval=refresh_interval)

    # Create device coordinator and fetch data
    coordinator = DeviceUpdateCoordinator(hass, device)
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator in global data
    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    # Forward setup to all platforms
    await hass.config_entries.async_forward_entry_setups(config_entry, _PLATFORMS)

    # Reload entry when its updated
    config_entry.async_on_unload(
        config_entry.add_update_listener(async_reload_entry))

    return True


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate config entry."""

    _LOGGER.debug("Migrating configuration from version %s.%s.",
                  config_entry.version, config_entry.minor_version)

    if config_entry.version > 1:
        # Unsupported downgrade
        return False

    _LOGGER.debug("Migration to configuration version %s.%s successful.",
                  config_entry.version, config_entry.minor_version)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove the coordinator from global data
    try:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    except KeyError:
        _LOGGER.warning("Failed remove device from global data.")

    # Forward unload to all platforms
    for platform in _PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(config_entry, platform)

    return True


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload a config entry."""
    await hass.config_entries.async_reload(config_entry.entry_id)
