"""The Smart Room Manager integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, VERSION
from .coordinator import SmartRoomCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]


def _clean_none_values_from_config(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clean None values from room configurations (migration from v0.2.1).

    In v0.2.1 and earlier, optional fields were saved with None values.
    This function removes those None values to prevent 'Entity None' errors.
    """
    rooms = list(entry.options.get("rooms", []))
    cleaned = False

    for room in rooms:
        # List of optional fields that should not be saved as None
        optional_fields = [
            "door_window_sensors",  # Added: can be None instead of []
            "lights",  # Added: can be None instead of []
            "temperature_sensor",
            "humidity_sensor",
            "climate_entity",
            "climate_bypass_switch",
        ]

        for field in optional_fields:
            if field in room and room[field] is None:
                del room[field]
                cleaned = True
                _LOGGER.debug(
                    "Cleaned None value for field '%s' in room '%s'",
                    field,
                    room.get("room_name", "unknown"),
                )

    # Update the config entry if we cleaned anything
    if cleaned:
        hass.config_entries.async_update_entry(
            entry,
            options={**entry.options, "rooms": rooms},
        )
        _LOGGER.info("Cleaned None values from room configurations (v0.2.1 migration)")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Room Manager from a config entry."""
    _LOGGER.debug("Setting up Smart Room Manager integration")

    hass.data.setdefault(DOMAIN, {})

    # Clean up None values from old configurations (v0.2.1 migration)
    _clean_none_values_from_config(hass, entry)

    # Create coordinator
    coordinator = SmartRoomCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register device for the integration
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="Smart Room Manager",
        manufacturer="HA-SMART",
        model="Room Manager",
        sw_version=VERSION,
    )

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options flow
    entry.async_on_unload(entry.add_update_listener(update_listener))

    _LOGGER.info("Smart Room Manager integration setup completed")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Smart Room Manager integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: SmartRoomCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Stop the coordinator
        await coordinator.async_shutdown()

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Options updated, reloading integration")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        # Migration logic if needed in future
        _LOGGER.info("Migration to version %s successful", config_entry.version)
        return True

    return False
