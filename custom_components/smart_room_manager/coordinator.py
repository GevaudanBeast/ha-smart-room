"""DataUpdateCoordinator for Smart Room Manager."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_ROOMS,
    DOMAIN,
    UPDATE_INTERVAL,
)
from .room_manager import RoomManager

_LOGGER = logging.getLogger(__name__)


class SmartRoomCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from rooms."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.entry = entry
        self.room_managers: dict[str, RoomManager] = {}
        self._unsub_update = None

        # Initialize room managers
        self._setup_room_managers()

    def _setup_room_managers(self) -> None:
        """Set up room managers from config."""
        rooms_config = self.entry.options.get(CONF_ROOMS, [])
        _LOGGER.debug("Setting up %d room managers", len(rooms_config))

        # Remove old room managers
        for room_id in list(self.room_managers.keys()):
            if not any(room["room_id"] == room_id for room in rooms_config):
                _LOGGER.debug("Removing room manager for %s", room_id)
                self.room_managers.pop(room_id)

        # Create/update room managers
        for room_config in rooms_config:
            room_id = room_config["room_id"]
            if room_id in self.room_managers:
                # Update existing room manager
                self.room_managers[room_id].update_config(room_config)
            else:
                # Create new room manager
                _LOGGER.debug("Creating room manager for %s", room_config.get("room_name"))
                self.room_managers[room_id] = RoomManager(
                    self.hass,
                    room_config,
                    self.entry.options,
                )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            data = {}
            for room_id, room_manager in self.room_managers.items():
                data[room_id] = await room_manager.async_update()
            return data
        except Exception as err:
            _LOGGER.exception("Error updating Smart Room Manager data")
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    @callback
    def async_add_listener(self, update_callback) -> None:
        """Listen for data updates."""
        super().async_add_listener(update_callback)

    async def async_shutdown(self) -> None:
        """Shutdown coordinator and room managers."""
        _LOGGER.debug("Shutting down coordinator")
        if self._unsub_update:
            self._unsub_update()

        for room_manager in self.room_managers.values():
            await room_manager.async_shutdown()

    async def async_config_entry_first_refresh(self) -> None:
        """Refresh data for the first time when a config entry is setup."""
        await super().async_config_entry_first_refresh()

    def get_room_manager(self, room_id: str) -> RoomManager | None:
        """Get room manager by room_id."""
        return self.room_managers.get(room_id)

    def get_all_room_managers(self) -> list[RoomManager]:
        """Get all room managers."""
        return list(self.room_managers.values())
