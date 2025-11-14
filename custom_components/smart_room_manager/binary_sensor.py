"""Binary sensor platform for Smart Room Manager."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VERSION
from .coordinator import SmartRoomCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Room Manager binary sensors."""
    coordinator: SmartRoomCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for room_manager in coordinator.get_all_room_managers():
        entities.extend(
            [
                SmartRoomOccupiedSensor(coordinator, room_manager.room_id),
                SmartRoomLightNeededSensor(coordinator, room_manager.room_id),
            ]
        )

    async_add_entities(entities)


class SmartRoomOccupiedSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for room occupation."""

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._room_id = room_id
        self._attr_has_entity_name = True

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} Occupied"
            self._attr_unique_id = f"smart_room_{room_id}_occupied"
            self._attr_icon = "mdi:account-check"

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
            "sw_version": VERSION,
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the room is occupied."""
        if self.coordinator.data and self._room_id in self.coordinator.data:
            return self.coordinator.data[self._room_id].get("occupied", False)
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class SmartRoomLightNeededSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor indicating if lights should be on."""

    _attr_device_class = BinarySensorDeviceClass.LIGHT

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._room_id = room_id
        self._attr_has_entity_name = True

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} Light Needed"
            self._attr_unique_id = f"smart_room_{room_id}_light_needed"
            self._attr_icon = "mdi:lightbulb-on"

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
            "sw_version": VERSION,
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if lights should be on."""
        if self.coordinator.data and self._room_id in self.coordinator.data:
            room_data = self.coordinator.data[self._room_id]
            light_state = room_data.get("light_state", {})
            return light_state.get("should_be_on", False)
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
