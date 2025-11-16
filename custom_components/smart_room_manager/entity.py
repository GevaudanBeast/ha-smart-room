"""Base entity for Smart Room Manager."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VERSION
from .coordinator import SmartRoomCoordinator


class SmartRoomEntity(CoordinatorEntity):
    """Base entity for Smart Room Manager."""

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._room_id = room_id
        self._attr_has_entity_name = True

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
