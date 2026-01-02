"""Room manager for Smart Room Manager."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .climate_control import ClimateController
from .const import (  # v0.3.0 additions; Priority 2 additions
    ALARM_STATE_ARMED_AWAY,
    CONF_ALARM_ENTITY,
    CONF_COMFORT_TIME_RANGES,
    CONF_DOOR_WINDOW_SENSORS,
    CONF_LIGHTS,
    CONF_NIGHT_START,
    CONF_PRESET_SCHEDULE_OFF,
    CONF_PRESET_SCHEDULE_ON,
    CONF_ROOM_ID,
    CONF_ROOM_NAME,
    CONF_ROOM_TYPE,
    CONF_SCHEDULE_ENTITY,
    CONF_WINDOW_DELAY_CLOSE,
    CONF_WINDOW_DELAY_OPEN,
    DEFAULT_NIGHT_START,
    DEFAULT_WINDOW_DELAY_CLOSE,
    DEFAULT_WINDOW_DELAY_OPEN,
    MODE_COMFORT,
    MODE_ECO,
    MODE_FROST_PROTECTION,
    MODE_NIGHT,
    ROOM_TYPE_BATHROOM,
    TIME_PERIOD_DAY,
    TIME_PERIOD_NIGHT,
)
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

        # Validate required fields
        self.room_id: str = room_config.get(CONF_ROOM_ID)
        if not self.room_id:
            raise ValueError("Room config missing required field 'room_id'")

        self.room_name: str = room_config.get(CONF_ROOM_NAME)
        if not self.room_name:
            raise ValueError(
                f"Room config for {self.room_id} missing required field 'room_name'"
            )

        self.room_type: str = room_config.get(CONF_ROOM_TYPE, "normal")

        # State tracking
        self._windows_open: bool = False
        self._is_night: bool = False
        self._current_mode: str = MODE_COMFORT
        self._automation_enabled: bool = True

        # Window delay tracking (Priority 2)
        self._windows_opened_at = None  # Timestamp when windows opened
        self._windows_closed_at = None  # Timestamp when windows closed

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

        # Validate required fields
        new_name = room_config.get(CONF_ROOM_NAME)
        if not new_name:
            _LOGGER.error(
                "Room config for %s missing required field 'room_name'", self.room_id
            )
            return

        self.room_name = new_name
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
        """Update window/door open states with delay tracking."""
        # Use 'or []' to handle None values (dict.get returns None if value is None)
        door_window_sensors = self.room_config.get(CONF_DOOR_WINDOW_SENSORS) or []

        if not door_window_sensors:
            previous_state = self._windows_open
            self._windows_open = False
            # Track close timestamp if changed
            if previous_state and not self._windows_open:
                self._windows_closed_at = dt_util.now()
            return

        # Check if any door/window sensor is open
        any_open = False
        for entity_id in door_window_sensors:
            state = self.hass.states.get(entity_id)
            if state and state.state == STATE_ON:
                any_open = True
                break

        # Track state changes with timestamps
        previous_state = self._windows_open
        self._windows_open = any_open

        # Track open/close timestamps
        if not previous_state and self._windows_open:
            # Windows just opened
            self._windows_opened_at = dt_util.now()
            self._windows_closed_at = None
        elif previous_state and not self._windows_open:
            # Windows just closed
            self._windows_closed_at = dt_util.now()
            self._windows_opened_at = None

    def _update_night_period(self) -> None:
        """Update night period status."""
        now = dt_util.now().time()
        night_start = dt_util.parse_time(
            self.room_config.get(CONF_NIGHT_START, DEFAULT_NIGHT_START)
        )

        self._is_night = now >= night_start

    def _is_in_comfort_time_range(self) -> bool:
        """Check if current time is within any configured comfort time range."""
        # Use 'or []' to handle None values (dict.get returns None if value is None)
        comfort_ranges = self.room_config.get(CONF_COMFORT_TIME_RANGES) or []

        if not comfort_ranges:
            return False

        now = dt_util.now().time()

        for time_range in comfort_ranges:
            start_str = time_range.get("start")
            end_str = time_range.get("end")

            if not start_str or not end_str:
                continue

            try:
                start_time = dt_util.parse_time(start_str)
                end_time = dt_util.parse_time(end_str)

                # Handle time ranges that cross midnight
                if start_time <= end_time:
                    if start_time <= now <= end_time:
                        return True
                else:
                    # Range crosses midnight
                    if now >= start_time or now <= end_time:
                        return True
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Invalid time range in %s: %s - %s",
                    self.room_name,
                    start_str,
                    end_str,
                )
                continue

        return False

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
            # Use 'or []' to handle None values (dict.get returns None if value is None)
            lights = self.room_config.get(CONF_LIGHTS) or []
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

        # PRIORITY 4: Check if in comfort time range
        if self._is_in_comfort_time_range():
            self._current_mode = MODE_COMFORT
            return

        # DEFAULT: Eco
        self._current_mode = MODE_ECO

    def is_night_period(self) -> bool:
        """Check if it's night period."""
        return self._is_night

    def get_time_period(self) -> str:
        """Get current time period (simplified)."""
        return TIME_PERIOD_NIGHT if self._is_night else TIME_PERIOD_DAY

    def is_windows_open(self) -> bool:
        """Check if any windows/doors are open."""
        return self._windows_open

    def is_windows_open_delayed(self) -> bool:
        """Check if windows are open with delay (Priority 2).

        Returns True only if windows have been open longer than delay_open.
        Returns False only if windows have been closed longer than delay_close.
        """
        # Get configured delays
        delay_open = self.room_config.get(
            CONF_WINDOW_DELAY_OPEN, DEFAULT_WINDOW_DELAY_OPEN
        )
        delay_close = self.room_config.get(
            CONF_WINDOW_DELAY_CLOSE, DEFAULT_WINDOW_DELAY_CLOSE
        )

        now = dt_util.now()

        # If windows are currently open
        if self._windows_open:
            # Check if we have an open timestamp and delay has elapsed
            if self._windows_opened_at:
                elapsed = (now - self._windows_opened_at).total_seconds() / 60
                return elapsed >= delay_open
            # No timestamp yet (first check), assume not delayed
            return False

        # If windows are currently closed
        else:
            # Check if we have a close timestamp and delay has elapsed
            if self._windows_closed_at:
                elapsed = (now - self._windows_closed_at).total_seconds() / 60
                # Return False (not open) only after delay has elapsed
                return elapsed < delay_close
            # No timestamp, windows were already closed
            return False

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

    def is_paused(self) -> bool:
        """Check if manual pause is active (v0.3.0)."""
        # Get pause switch state from HA
        pause_switch_id = f"switch.smart_room_{self.room_id}_pause"
        pause_state = self.hass.states.get(pause_switch_id)
        return pause_state and pause_state.state == STATE_ON

    def get_schedule_mode(self) -> str | None:
        """Get mode from schedule calendar (v0.3.0).

        Returns:
            MODE_COMFORT if event active and preset_schedule_on is comfort
            MODE_ECO if no event and preset_schedule_off is eco
            None if no schedule configured
        """
        schedule_entity = self.room_config.get(CONF_SCHEDULE_ENTITY)
        if not schedule_entity:
            return None

        # Check if calendar entity exists
        calendar_state = self.hass.states.get(schedule_entity)
        if not calendar_state:
            return None

        # Get presets for on/off states
        preset_on = self.room_config.get(CONF_PRESET_SCHEDULE_ON, MODE_COMFORT)
        preset_off = self.room_config.get(CONF_PRESET_SCHEDULE_OFF, MODE_ECO)

        # Calendar state ON = event active
        if calendar_state.state == STATE_ON:
            return preset_on
        else:
            return preset_off

    def get_state(self) -> dict[str, Any]:
        """Get current room state."""
        # Get alarm state for state reporting
        alarm_entity = self.coordinator.entry.data.get(CONF_ALARM_ENTITY)
        alarm_state_value = "unknown"
        occupied = True  # Default to occupied if no alarm

        if alarm_entity:
            alarm_state = self.hass.states.get(alarm_entity)
            if alarm_state:
                alarm_state_value = alarm_state.state
                # In v0.2.0: occupied = NOT armed_away (simplified presence detection)
                occupied = alarm_state_value != ALARM_STATE_ARMED_AWAY

        # Check if any light is on (for bathroom logic reporting)
        # Use 'or []' to handle None values (dict.get returns None if value is None)
        lights = self.room_config.get(CONF_LIGHTS) or []
        light_on = False
        if lights:
            for light_entity in lights:
                light_state = self.hass.states.get(light_entity)
                if light_state and light_state.state == STATE_ON:
                    light_on = True
                    break

        # Get light state with should_be_on
        light_state_data = self.light_controller.get_state()
        # In simplified v0.2.0: no automatic "should be on" logic
        # Lights are manual or via external automation
        light_state_data["should_be_on"] = False

        # v0.3.0: Get schedule and pause status
        schedule_active = self.get_schedule_mode() is not None
        pause_active = self.is_paused()

        return {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "room_type": self.room_type,
            "is_night": self._is_night,
            "windows_open": self._windows_open,
            "current_mode": self._current_mode,
            "time_period": self.get_time_period(),
            "alarm_state": alarm_state_value,
            "occupied": occupied,
            "light_on": light_on,
            "automation_enabled": self._automation_enabled,
            "light_state": light_state_data,
            "climate_state": self.climate_controller.get_state(),
            # v0.3.0 additions
            "schedule_active": schedule_active,
            "pause_active": pause_active,
        }

    async def async_shutdown(self) -> None:
        """Shutdown room manager."""
        await self.light_controller.async_shutdown()
        await self.climate_controller.async_shutdown()
        _LOGGER.debug("Room manager shut down for %s", self.room_name)
