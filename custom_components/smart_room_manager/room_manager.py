"""Room manager for Smart Room Manager."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.const import STATE_ON, STATE_OFF, STATE_HOME, STATE_ALARM_ARMED_AWAY
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers.sun import get_astral_event_date
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ALARM_ENTITY,
    CONF_CLIMATE_ENTITY,
    CONF_CLIMATE_PRESENCE_REQUIRED,
    CONF_CLIMATE_UNOCCUPIED_DELAY,
    CONF_CLIMATE_WINDOW_CHECK,
    CONF_DAY_START,
    CONF_DOOR_WINDOW_SENSORS,
    CONF_EVENING_START,
    CONF_GUEST_MODE_ENTITY,
    CONF_HEATING_SWITCHES,
    CONF_HUMIDITY_SENSOR,
    CONF_LIGHTS,
    CONF_LIGHT_DAY_BRIGHTNESS,
    CONF_LIGHT_LUX_THRESHOLD,
    CONF_LIGHT_NIGHT_BRIGHTNESS,
    CONF_LIGHT_NIGHT_MODE,
    CONF_LIGHT_TIMEOUT,
    CONF_LUMINOSITY_SENSOR,
    CONF_MORNING_START,
    CONF_NIGHT_START,
    CONF_PRESENCE_SENSORS,
    CONF_ROOM_ID,
    CONF_ROOM_NAME,
    CONF_SEASON_SENSOR,
    CONF_TEMPERATURE_SENSOR,
    CONF_TEMP_AWAY,
    CONF_TEMP_COMFORT,
    CONF_TEMP_ECO,
    CONF_TEMP_FROST_PROTECTION,
    CONF_TEMP_NIGHT,
    CONF_VACATION_MODE_ENTITY,
    DEFAULT_CLIMATE_UNOCCUPIED_DELAY,
    DEFAULT_LIGHT_LUX_THRESHOLD,
    DEFAULT_LIGHT_TIMEOUT,
    MODE_AWAY,
    MODE_COMFORT,
    MODE_ECO,
    MODE_FROST_PROTECTION,
    MODE_GUEST,
    MODE_NIGHT,
    TIME_PERIOD_DAY,
    TIME_PERIOD_EVENING,
    TIME_PERIOD_MORNING,
    TIME_PERIOD_NIGHT,
)
from .light_control import LightController
from .climate_control import ClimateController

_LOGGER = logging.getLogger(__name__)


class RoomManager:
    """Manage a single room's automation logic."""

    def __init__(
        self,
        hass: HomeAssistant,
        room_config: dict[str, Any],
        global_config: dict[str, Any],
    ) -> None:
        """Initialize room manager."""
        self.hass = hass
        self.room_config = room_config
        self.global_config = global_config

        self.room_id: str = room_config[CONF_ROOM_ID]
        self.room_name: str = room_config[CONF_ROOM_NAME]

        # State tracking
        self._occupied: bool = False
        self._last_presence_time: datetime | None = None
        self._last_motion_time: datetime | None = None
        self._windows_open: bool = False
        self._current_mode: str = MODE_ECO
        self._automation_enabled: bool = True

        # Controllers
        self.light_controller = LightController(hass, room_config, self)
        self.climate_controller = ClimateController(hass, room_config, self)

        _LOGGER.debug(
            "Room manager initialized for %s (ID: %s)",
            self.room_name,
            self.room_id,
        )

    def update_config(self, room_config: dict[str, Any]) -> None:
        """Update room configuration."""
        self.room_config = room_config
        self.room_name = room_config[CONF_ROOM_NAME]
        self.light_controller.update_config(room_config)
        self.climate_controller.update_config(room_config)
        _LOGGER.debug("Room config updated for %s", self.room_name)

    async def async_update(self) -> dict[str, Any]:
        """Update room state and control logic."""
        # Update presence
        self._update_presence()

        # Update window states
        self._update_window_states()

        # Determine current mode
        self._update_current_mode()

        # Update controllers
        if self._automation_enabled:
            await self.light_controller.async_update()
            await self.climate_controller.async_update()

        # Return current state
        return self.get_state()

    def _update_presence(self) -> None:
        """Update presence detection."""
        presence_sensors = self.room_config.get(CONF_PRESENCE_SENSORS, [])

        if not presence_sensors:
            self._occupied = False
            return

        # Check if any presence sensor is on
        any_presence = False
        for entity_id in presence_sensors:
            state = self.hass.states.get(entity_id)
            if state and state.state == STATE_ON:
                any_presence = True
                self._last_motion_time = dt_util.utcnow()
                break

        # Update occupation with timeout
        if any_presence:
            self._occupied = True
            self._last_presence_time = dt_util.utcnow()
        else:
            # Check if we should still consider the room occupied
            if self._last_presence_time:
                timeout = self.room_config.get(CONF_LIGHT_TIMEOUT, DEFAULT_LIGHT_TIMEOUT)
                time_since_presence = (
                    dt_util.utcnow() - self._last_presence_time
                ).total_seconds()

                if time_since_presence > timeout:
                    self._occupied = False

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

    def _update_current_mode(self) -> None:
        """Determine current operating mode based on global conditions."""
        # Check vacation mode
        vacation_entity = self.global_config.get(CONF_VACATION_MODE_ENTITY)
        if vacation_entity:
            state = self.hass.states.get(vacation_entity)
            if state and state.state == STATE_ON:
                self._current_mode = MODE_FROST_PROTECTION
                return

        # Check alarm state
        alarm_entity = self.global_config.get(CONF_ALARM_ENTITY)
        if alarm_entity:
            state = self.hass.states.get(alarm_entity)
            if state and state.state == STATE_ALARM_ARMED_AWAY:
                self._current_mode = MODE_AWAY
                return

        # Check guest mode
        guest_entity = self.global_config.get(CONF_GUEST_MODE_ENTITY)
        if guest_entity:
            state = self.hass.states.get(guest_entity)
            if state and state.state == STATE_ON:
                self._current_mode = MODE_GUEST
                return

        # Determine mode based on time period
        time_period = self.get_time_period()

        if time_period == TIME_PERIOD_NIGHT:
            self._current_mode = MODE_NIGHT
        elif self._occupied:
            self._current_mode = MODE_COMFORT
        else:
            self._current_mode = MODE_ECO

    def get_time_period(self) -> str:
        """Get current time period."""
        now = dt_util.now().time()

        morning = dt_util.parse_time(
            self.room_config.get(CONF_MORNING_START, "07:00:00")
        )
        day = dt_util.parse_time(self.room_config.get(CONF_DAY_START, "09:00:00"))
        evening = dt_util.parse_time(
            self.room_config.get(CONF_EVENING_START, "18:00:00")
        )
        night = dt_util.parse_time(self.room_config.get(CONF_NIGHT_START, "22:00:00"))

        if night <= now or now < morning:
            return TIME_PERIOD_NIGHT
        elif morning <= now < day:
            return TIME_PERIOD_MORNING
        elif day <= now < evening:
            return TIME_PERIOD_DAY
        else:
            return TIME_PERIOD_EVENING

    def get_luminosity(self) -> float | None:
        """Get current luminosity value."""
        lux_sensor = self.room_config.get(CONF_LUMINOSITY_SENSOR)
        if not lux_sensor:
            return None

        state = self.hass.states.get(lux_sensor)
        if not state:
            return None

        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    def get_temperature(self) -> float | None:
        """Get current temperature value."""
        temp_sensor = self.room_config.get(CONF_TEMPERATURE_SENSOR)
        if not temp_sensor:
            return None

        state = self.hass.states.get(temp_sensor)
        if not state:
            return None

        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    def get_humidity(self) -> float | None:
        """Get current humidity value."""
        humidity_sensor = self.room_config.get(CONF_HUMIDITY_SENSOR)
        if not humidity_sensor:
            return None

        state = self.hass.states.get(humidity_sensor)
        if not state:
            return None

        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    def is_occupied(self) -> bool:
        """Check if room is currently occupied."""
        return self._occupied

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
        return {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "occupied": self._occupied,
            "windows_open": self._windows_open,
            "current_mode": self._current_mode,
            "time_period": self.get_time_period(),
            "luminosity": self.get_luminosity(),
            "temperature": self.get_temperature(),
            "humidity": self.get_humidity(),
            "automation_enabled": self._automation_enabled,
            "light_state": self.light_controller.get_state(),
            "climate_state": self.climate_controller.get_state(),
        }

    async def async_shutdown(self) -> None:
        """Shutdown room manager."""
        await self.light_controller.async_shutdown()
        await self.climate_controller.async_shutdown()
        _LOGGER.debug("Room manager shut down for %s", self.room_name)
