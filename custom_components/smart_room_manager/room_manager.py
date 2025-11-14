"""Room manager for Smart Room Manager."""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from homeassistant.const import STATE_ON, ALARM_STATE_ARMED_AWAY
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    ALARM_STATE_ARMED_AWAY as CONF_ALARM_STATE_ARMED_AWAY,
    CONF_ALARM_ENTITY,
    CONF_DOOR_WINDOW_SENSORS,
    CONF_LIGHTS,
    CONF_NIGHT_START,
    CONF_ROOM_ID,
    CONF_ROOM_NAME,
    CONF_ROOM_TYPE,
    DEFAULT_NIGHT_START,
    MODE_COMFORT,
    MODE_ECO,
    MODE_FROST_PROTECTION,
    MODE_NIGHT,
    ROOM_TYPE_BATHROOM,
    TIME_PERIOD_DAY,
    TIME_PERIOD_NIGHT,
)
from .climate_control import ClimateController
from .light_control import LightController

if TYPE_CHECKING:
    from .coordinator import SmartRoomCoordinator

_LOGGER = logging.getLogger(__name__)


class RoomManager:
    """Manage a single room's automation logic."""

    def __init__(
        self,
        hass: HomeAssistant,
        room_config: dict[str, Any],
        coordinator: SmartRoomCoordinator,
    ) -> None:
        """Initialize room manager."""
        self.hass = hass
        self.room_config = room_config
        self.coordinator = coordinator

        self.room_id: str = room_config[CONF_ROOM_ID]
        self.room_name: str = room_config[CONF_ROOM_NAME]
        self.room_type: str = room_config.get(CONF_ROOM_TYPE, "normal")

        # State tracking
        self._windows_open: bool = False
        self._is_night: bool = False
        self._current_mode: str = MODE_COMFORT
        self._automation_enabled: bool = True

        # Controllers
        self.light_controller = LightController(hass, room_config, self)
        self.climate_controller = ClimateController(hass, room_config, self)

        _LOGGER.debug(
            "Room manager initialized for %s (ID: %s, Type: %s)",
            self.room_name,
            self.room_id,
            self.room_type,
        )

    def update_config(self, room_config: dict[str, Any]) -> None:
        """Update room configuration."""
        self.room_config = room_config
        self.room_name = room_config[CONF_ROOM_NAME]
        self.room_type = room_config.get(CONF_ROOM_TYPE, "normal")
        self.light_controller.update_config(room_config)
        self.climate_controller.update_config(room_config)
        _LOGGER.debug("Room config updated for %s", self.room_name)

    async def async_update(self) -> dict[str, Any]:
        """Update room state and control logic."""
        # Update window states
        self._update_window_states()

        # Update night period
        self._update_night_period()

        # Determine current mode
        self._update_current_mode()

        # Update controllers
        if self._automation_enabled:
            await self.light_controller.async_update()
            await self.climate_controller.async_update()

        # Return current state
        return self.get_state()

    def _update_window_states(self) -> None:
        """Update window/door open states."""
        door_window_sensors = self.room_config.get(CONF_DOOR_WINDOW_SENSORS, [])

        if not door_window_sensors:
            self._windows_open = False
            return

        # Check if any door/window sensor is open
        for entity_id in door_window_sensors:
            state = self.hass.states.get(entity_id)
            if state and state.state == STATE_ON:
                self._windows_open = True
                return

        self._windows_open = False

    def _update_night_period(self) -> None:
        """Update night period status."""
        now = dt_util.now().time()
        night_start = dt_util.parse_time(
            self.room_config.get(CONF_NIGHT_START, DEFAULT_NIGHT_START)
        )

        self._is_night = now >= night_start

    def _update_current_mode(self) -> None:
        """Determine current operating mode."""
        # PRIORITY 1: Check alarm armed_away
        alarm_entity = self.coordinator.entry.data.get(CONF_ALARM_ENTITY)
        if alarm_entity:
            alarm_state = self.hass.states.get(alarm_entity)
            if alarm_state and alarm_state.state == ALARM_STATE_ARMED_AWAY:
                self._current_mode = MODE_FROST_PROTECTION
                return

        # PRIORITY 2: Bathroom special logic (light state determines mode)
        if self.room_type == ROOM_TYPE_BATHROOM:
            lights = self.room_config.get(CONF_LIGHTS, [])
            if lights:
                # Check if ANY light is ON
                any_light_on = False
                for light_entity in lights:
                    light_state = self.hass.states.get(light_entity)
                    if light_state and light_state.state == STATE_ON:
                        any_light_on = True
                        break

                if any_light_on:
                    self._current_mode = MODE_COMFORT
                    return
                else:
                    self._current_mode = MODE_ECO
                    return

        # PRIORITY 3: Night period
        if self._is_night:
            self._current_mode = MODE_NIGHT
            return

        # DEFAULT: Comfort
        self._current_mode = MODE_COMFORT

    def is_night_period(self) -> bool:
        """Check if it's night period."""
        return self._is_night

    def get_time_period(self) -> str:
        """Get current time period (simplified)."""
        return TIME_PERIOD_NIGHT if self._is_night else TIME_PERIOD_DAY

    def is_windows_open(self) -> bool:
        """Check if any windows/doors are open."""
        return self._windows_open

    def get_current_mode(self) -> str:
        """Get current operating mode."""
        return self._current_mode

    def is_automation_enabled(self) -> bool:
        """Check if automation is enabled for this room."""
        return self._automation_enabled

    def set_automation_enabled(self, enabled: bool) -> None:
        """Enable or disable automation for this room."""
        self._automation_enabled = enabled
        _LOGGER.info(
            "Room %s automation %s",
            self.room_name,
            "enabled" if enabled else "disabled",
        )

    def get_state(self) -> dict[str, Any]:
        """Get current room state."""
        # Get alarm state for state reporting
        alarm_entity = self.coordinator.entry.data.get(CONF_ALARM_ENTITY)
        alarm_state_value = "unknown"
        if alarm_entity:
            alarm_state = self.hass.states.get(alarm_entity)
            if alarm_state:
                alarm_state_value = alarm_state.state

        # Check if any light is on (for bathroom logic reporting)
        lights = self.room_config.get(CONF_LIGHTS, [])
        light_on = False
        if lights:
            for light_entity in lights:
                light_state = self.hass.states.get(light_entity)
                if light_state and light_state.state == STATE_ON:
                    light_on = True
                    break

        return {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "room_type": self.room_type,
            "is_night": self._is_night,
            "windows_open": self._windows_open,
            "current_mode": self._current_mode,
            "time_period": self.get_time_period(),
            "alarm_state": alarm_state_value,
            "light_on": light_on,
            "automation_enabled": self._automation_enabled,
            "light_state": self.light_controller.get_state(),
            "climate_state": self.climate_controller.get_state(),
        }

    async def async_shutdown(self) -> None:
        """Shutdown room manager."""
        await self.light_controller.async_shutdown()
        await self.climate_controller.async_shutdown()
        _LOGGER.debug("Room manager shut down for %s", self.room_name)
