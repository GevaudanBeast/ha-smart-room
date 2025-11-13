"""Sensor platform for Smart Room Manager."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CLIMATE_STATE,
    ATTR_CURRENT_MODE,
    ATTR_HUMIDITY,
    ATTR_LIGHT_STATE,
    ATTR_LUMINOSITY,
    ATTR_OCCUPIED,
    ATTR_ROOM_ID,
    ATTR_ROOM_NAME,
    ATTR_TARGET_TEMPERATURE,
    ATTR_TEMPERATURE,
    ATTR_WINDOWS_OPEN,
    DOMAIN,
)
from .coordinator import SmartRoomCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Room Manager sensors."""
    coordinator: SmartRoomCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for room_manager in coordinator.get_all_room_managers():
        entities.append(SmartRoomStateSensor(coordinator, room_manager.room_id))

    async_add_entities(entities)


class SmartRoomStateSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing the state of a smart room."""

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._room_id = room_id
        self._attr_has_entity_name = True

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} State"
            self._attr_unique_id = f"smart_room_{room_id}_state"
            self._attr_icon = "mdi:home-automation"

    @property
    def device_info(self):
        """Return device information."""
        room_manager = self.coordinator.get_room_manager(self._room_id)
        if not room_manager:
            return None

        return {
            "identifiers": {(DOMAIN, self._room_id)},
            "name": f"Smart Room: {room_manager.room_name}",
            "manufacturer": "HA-SMART",
            "model": "Smart Room Manager",
            "sw_version": "0.1.0",
        }

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self.coordinator.data and self._room_id in self.coordinator.data:
            room_data = self.coordinator.data[self._room_id]
            return room_data.get("current_mode", "unknown")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data or self._room_id not in self.coordinator.data:
            return {}

        room_data = self.coordinator.data[self._room_id]

        attributes = {
            ATTR_ROOM_ID: room_data.get("room_id"),
            ATTR_ROOM_NAME: room_data.get("room_name"),
            ATTR_OCCUPIED: room_data.get("occupied"),
            ATTR_WINDOWS_OPEN: room_data.get("windows_open"),
            ATTR_CURRENT_MODE: room_data.get("current_mode"),
            "time_period": room_data.get("time_period"),
            "automation_enabled": room_data.get("automation_enabled"),
        }

        # Add sensor values if available
        if room_data.get("luminosity") is not None:
            attributes[ATTR_LUMINOSITY] = room_data.get("luminosity")

        if room_data.get("temperature") is not None:
            attributes[ATTR_TEMPERATURE] = room_data.get("temperature")

        if room_data.get("humidity") is not None:
            attributes[ATTR_HUMIDITY] = room_data.get("humidity")

        # Add light state
        light_state = room_data.get("light_state", {})
        attributes[ATTR_LIGHT_STATE] = {
            "should_be_on": light_state.get("should_be_on"),
            "brightness_percentage": light_state.get("brightness_percentage"),
        }

        # Add climate state
        climate_state = room_data.get("climate_state", {})
        attributes[ATTR_CLIMATE_STATE] = {
            "target_temperature": climate_state.get("target_temperature"),
            "heating_active": climate_state.get("heating_active"),
        }

        if climate_state.get("target_temperature") is not None:
            attributes[ATTR_TARGET_TEMPERATURE] = climate_state.get("target_temperature")

        return attributes

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
