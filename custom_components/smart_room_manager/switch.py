"""Switch platform for Smart Room Manager."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import SmartRoomCoordinator
from .entity import SmartRoomEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Room Manager switches."""
    coordinator: SmartRoomCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for room_manager in coordinator.get_all_room_managers():
        entities.append(SmartRoomAutomationSwitch(coordinator, room_manager.room_id))

    async_add_entities(entities)


class SmartRoomAutomationSwitch(SmartRoomEntity, SwitchEntity):
    """Switch to enable/disable room automation."""

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, room_id)

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} Automation"
            self._attr_unique_id = f"smart_room_{room_id}_automation"
            self._attr_icon = "mdi:auto-mode"

    @property
    def is_on(self) -> bool:
        """Return true if automation is enabled."""
        room_manager = self.coordinator.get_room_manager(self._room_id)
        if room_manager:
            return room_manager.is_automation_enabled()
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the automation."""
        room_manager = self.coordinator.get_room_manager(self._room_id)
        if room_manager:
            room_manager.set_automation_enabled(True)
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the automation."""
        room_manager = self.coordinator.get_room_manager(self._room_id)
        if room_manager:
            room_manager.set_automation_enabled(False)
            await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
