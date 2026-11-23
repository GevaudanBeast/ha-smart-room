"""Switch platform for Smart Room Manager."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_PAUSE_DURATION_MINUTES,
    CONF_PAUSE_INFINITE,
    DEFAULT_PAUSE_DURATION,
    DEFAULT_PAUSE_INFINITE,
    DOMAIN,
)
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
        # Automation on/off switch
        entities.append(SmartRoomAutomationSwitch(coordinator, room_manager.room_id))
        # Manual pause switch (v0.3.0)
        entities.append(SmartRoomPauseSwitch(coordinator, room_manager.room_id))

    async_add_entities(entities)


class SmartRoomAutomationSwitch(SmartRoomEntity, SwitchEntity, RestoreEntity):
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

    async def async_added_to_hass(self) -> None:
        """Restore the previous state after a restart (v0.3.9)."""
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        room_manager = self.coordinator.get_room_manager(self._room_id)
        if last is not None and room_manager and last.state == "off":
            room_manager.set_automation_enabled(False)
            self.async_write_ha_state()

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


class SmartRoomPauseSwitch(SmartRoomEntity, SwitchEntity, RestoreEntity):
    """Switch to pause room automation temporarily (v0.3.0)."""

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the pause switch."""
        super().__init__(coordinator, room_id)

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} Pause"
            self._attr_unique_id = f"smart_room_{room_id}_pause"
            self._attr_icon = "mdi:pause-circle-outline"

        self._pause_timer = None
        self._pause_until = None
        self._set_paused(False)

    async def async_added_to_hass(self) -> None:
        """Restore an active pause after a restart (v0.3.9)."""
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is None or last.state != "on":
            return
        until = last.attributes.get("pause_until")
        if until:
            until_dt = dt_util.parse_datetime(until)
            if until_dt is None or until_dt <= dt_util.now():
                return  # pause expired while Home Assistant was stopped
            self._pause_until = until_dt
            self._pause_timer = async_call_later(
                self.hass,
                (until_dt - dt_util.now()).total_seconds(),
                self._auto_turn_off,
            )
        self._set_paused(True)
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Cancel the pause timer when the entity is removed (v0.3.9)."""
        if self._pause_timer:
            self._pause_timer()
            self._pause_timer = None
        await super().async_will_remove_from_hass()

    def _set_paused(self, paused: bool) -> None:
        self._attr_is_on = paused
        room_manager = self.coordinator.get_room_manager(self._room_id)
        if room_manager:
            room_manager.set_paused(paused)

    @property
    def is_on(self) -> bool:
        """Return true if pause is active (switch or manual override)."""
        room_manager = self.coordinator.get_room_manager(self._room_id)
        manual = room_manager.is_manual_override() if room_manager else False
        return self._attr_is_on or manual

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        room_manager = self.coordinator.get_room_manager(self._room_id)
        if not room_manager:
            return {}

        room_config = room_manager.room_config
        attrs = {
            "duration_minutes": room_config.get(
                CONF_PAUSE_DURATION_MINUTES, DEFAULT_PAUSE_DURATION
            ),
            "infinite_enabled": room_config.get(
                CONF_PAUSE_INFINITE, DEFAULT_PAUSE_INFINITE
            ),
        }

        reason = room_manager.get_pause_reason()
        if reason:
            attrs["reason"] = (
                "réglage manuel" if reason == "manual_override" else "pause manuelle"
            )
        if reason == "manual_override" and room_manager._manual_until:
            attrs["pause_until"] = dt_util.as_local(
                room_manager._manual_until
            ).isoformat()
        if self._pause_until:
            attrs["pause_until"] = self._pause_until.isoformat()
            remaining = (self._pause_until - dt_util.now()).total_seconds() / 60
            attrs["remaining_minutes"] = max(0, int(remaining))

        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on pause - temporarily disable automation."""
        room_manager = self.coordinator.get_room_manager(self._room_id)
        if not room_manager:
            return

        room_config = room_manager.room_config
        duration = room_config.get(CONF_PAUSE_DURATION_MINUTES, DEFAULT_PAUSE_DURATION)
        infinite = room_config.get(CONF_PAUSE_INFINITE, DEFAULT_PAUSE_INFINITE)

        # Cancel any existing timer
        if self._pause_timer:
            self._pause_timer()
            self._pause_timer = None

        if infinite or duration == 0:
            # Infinite pause - no auto-off
            self._pause_timer = None
            self._pause_until = None
            _LOGGER.info(
                "Infinite pause activated for %s",
                room_manager.room_name,
            )
        else:
            # Timed pause - set auto-off
            self._pause_until = dt_util.now() + timedelta(minutes=duration)
            self._pause_timer = async_call_later(
                self.hass,
                duration * 60,
                self._auto_turn_off,
            )
            _LOGGER.info(
                "Pause activated for %s for %d minutes (until %s)",
                room_manager.room_name,
                duration,
                self._pause_until.strftime("%H:%M:%S"),
            )

        self._set_paused(True)
        self.async_write_ha_state()

        # Request coordinator refresh to update climate control
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off pause - resume automation."""
        room_manager = self.coordinator.get_room_manager(self._room_id)
        if not room_manager:
            return

        # Cancel timer if exists
        if self._pause_timer:
            self._pause_timer()
            self._pause_timer = None

        self._pause_until = None
        self._set_paused(False)

        _LOGGER.info(
            "Pause deactivated for %s",
            room_manager.room_name,
        )

        self.async_write_ha_state()

        # Request coordinator refresh to resume climate control
        await self.coordinator.async_request_refresh()

    async def _auto_turn_off(self, _):
        """Auto-deactivate pause after duration expires."""
        room_manager = self.coordinator.get_room_manager(self._room_id)
        if room_manager:
            _LOGGER.info(
                "Pause expired for %s - resuming automation",
                room_manager.room_name,
            )

        await self.async_turn_off()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
