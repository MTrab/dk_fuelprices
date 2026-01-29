"""Initialize the braendstofpriser component."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.loader import async_get_integration

from .api import APIClient, BraendstofpriserConfigEntry
from .const import (
    ATTR_COORDINATOR,
    CONF_COMPANY,
    CONF_PRODUCTS,
    CONF_STATION,
    DOMAIN,
    STARTUP,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up braendstofpriser from a config entry."""
    result = await _setup(hass, config_entry)

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return result


async def _setup(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Setup the integration."""
    integration = await async_get_integration(hass, DOMAIN)
    _LOGGER.info(STARTUP, integration.version)

    coordinator = APIClient(
        hass,
        config_entry.options.get(CONF_API_KEY),
        config_entry.data.get(CONF_COMPANY),
        config_entry.data.get(CONF_STATION),
        config_entry.options.get(CONF_PRODUCTS, {}),
    )
    # coordinator.station_name = (await coordinator._api.get_prices(int(config_entry.data.get(CONF_STATION))))["station"]["name"]

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {ATTR_COORDINATOR: coordinator}

    if config_entry.state == ConfigEntryState.SETUP_IN_PROGRESS:
        await coordinator.async_config_entry_first_refresh()


    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: BraendstofpriserConfigEntry, device_entry
) -> bool:
    """Remove a config entry from a device."""

    return not any(
        identifier
        for identifier in device_entry.identifiers
        if identifier[0] == DOMAIN and identifier[1] in config_entry.options
    )


def remove_stale_devices(
    hass: HomeAssistant,
    config_entry: BraendstofpriserConfigEntry,
    devices,
) -> None:
    """Remove stale devices from device registry."""
    device_registry = dr.async_get(hass)
    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    all_device_ids = {device.deviceid for device in devices.values()}

    for device_entry in device_entries:
        device_id: str | None = None

        for identifier in device_entry.identifiers:
            if identifier[0] == DOMAIN:
                device_id = identifier[1]
                break

        if device_id is None or device_id not in all_device_ids:
            # If device_id is None an invalid device entry was found for this config entry.
            # If the device_id is not in existing device ids it's a stale device entry.
            # Remove config entry from this device entry in either case.
            device_registry.async_update_device(
                device_entry.id, remove_config_entry_id=config_entry.entry_id
            )
