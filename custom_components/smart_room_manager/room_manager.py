"""Room manager for Smart Room Manager."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_ON
from datetime import timedelta

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .climate_control import ClimateController
from .const import (  # v0.3.0 additions; Priority 2 additions
    ALARM_STATE_ARMED_AWAY,
    CONF_ALARM_ENTITY,
    CONF_CLIMATE_ENTITY,
    CONF_CLIMATE_WINDOW_CHECK,
    CONF_MANUAL_OVERRIDE_MINUTES,
    DEFAULT_MANUAL_OVERRIDE_MINUTES,
    PAUSE_REASON_MANUAL_OVERRIDE,
    PAUSE_REASON_MANUAL_SWITCH,
    CONF_COMFORT_TIME_RANGES,
    CONF_DOOR_WINDOW_SENSORS,
    CONF_IGNORE_IN_AWAY,
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
    DEFAULT_DAY_START,
    DEFAULT_NIGHT_START,
    DEFAULT_WINDOW_DELAY_CLOSE,
    DEFAULT_WINDOW_DELAY_OPEN,
    MODE_COMFORT,
    MODE_ECO,
    MODE_FROST_PROTECTION,
    MODE_NIGHT,
    NOTIFY_FROST_PROTECTION,
    NOTIFY_HEATING_BLOCKED,
    NOTIFY_HEATING_UNBLOCKED,
    NOTIFY_MANUAL_OVERRIDE,
    NOTIFY_MANUAL_OVERRIDE_END,
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
        self._windows_effective_open: bool = False  # v0.3.9 latch (B10)
        self._is_night: bool = False
        self._current_mode: str = MODE_COMFORT
        self._automation_enabled: bool = True
        self._paused: bool = False
        # v0.3.9: manual override detection (pause until this time, UTC)
        self._manual_until = None
        self._unsub_climate = None
        # v0.3.9: manual request kept while a window blocks it
        self._manual_request: dict[str, Any] | None = None
        self.manual_restore_pending: bool = False
        # v0.3.9: heating blocked by an open window
        self._heating_blocked: bool = False
        self._heating_blocked_info: dict[str, Any] = {}
        # v0.3.9: notification transitions
        self._override_prev: bool = False
        self._mode_prev: str | None = None

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
        self._check_frost_notification()

        # Update controllers
        if self._automation_enabled:
            await self.light_controller.async_update()
            await self.climate_controller.async_update()

        # v0.3.9: end of a manual-override period
        override_active = self.is_manual_override()
        if self._override_prev and not override_active:
            self._notify(NOTIFY_MANUAL_OVERRIDE_END)
        self._override_prev = override_active

        # Return current state
        return self.get_state()

    def _update_window_states(self) -> None:
        """Update window/door open states.

        v0.3.9: the timestamps come from the sensors' ``last_changed``
        (not from the 30 s update loop), so the delays are measured from
        the real opening/closing.
        """
        door_window_sensors = self.room_config.get(CONF_DOOR_WINDOW_SENSORS) or []

        open_since = None
        closed_since = None
        for entity_id in door_window_sensors:
            state = self.hass.states.get(entity_id)
            if state is None:
                continue
            if state.state == STATE_ON:
                if open_since is None or state.last_changed < open_since:
                    open_since = state.last_changed
            elif closed_since is None or state.last_changed > closed_since:
                closed_since = state.last_changed

        previous_state = self._windows_open
        self._windows_open = open_since is not None

        now = dt_util.utcnow()
        if self._windows_open:
            # A timestamp in the future (clock change) falls back to the
            # first time the opening was seen by this loop.
            if open_since > now:
                open_since = (
                    self._windows_opened_at
                    if previous_state and self._windows_opened_at
                    else now
                )
            self._windows_opened_at = open_since
            self._windows_closed_at = None
        else:
            self._windows_opened_at = None
            if previous_state:
                if closed_since is None or closed_since > now:
                    closed_since = now
                self._windows_closed_at = closed_since

    def _update_night_period(self) -> None:
        """Update night period status.

        Handles midnight crossing: night_start=22:00, day_start=06:00
        means night is 22:00-23:59 AND 00:00-05:59.
        """
        now = dt_util.now().time()
        night_start = dt_util.parse_time(
            self.room_config.get(CONF_NIGHT_START, DEFAULT_NIGHT_START)
        )
        day_start = dt_util.parse_time(DEFAULT_DAY_START)

        # Night period crosses midnight (e.g., 22:00 to 06:00)
        # is_night = True if now >= 22:00 OR now < 06:00
        self._is_night = now >= night_start or now < day_start

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

    def _compute_mode(self, include_windows: bool = True) -> str:
        """Determine current operating mode.

        Priority order (aligned with climate_control.async_update):
        1. Windows open (with delay) → frost_protection
        2. Away mode (alarm armed_away) → frost_protection OR schedule if ignore_in_away
        3. Bathroom special logic
        4. Schedule
        5. Night period
        6. Comfort time ranges
        7. Default: Eco
        """
        # PRIORITY 1: Check windows open (aligned with climate_control PRIORITY 2)
        if include_windows and self.room_config.get(CONF_CLIMATE_WINDOW_CHECK, True):
            if self.is_windows_open_delayed():
                return MODE_FROST_PROTECTION

        # PRIORITY 2: Check alarm armed_away
        alarm_entity = self.coordinator.entry.data.get(CONF_ALARM_ENTITY)
        if alarm_entity:
            alarm_state = self.hass.states.get(alarm_entity)
            if alarm_state and alarm_state.state == ALARM_STATE_ARMED_AWAY:
                # Check if schedule should be used even when away
                ignore_in_away = self.room_config.get(CONF_IGNORE_IN_AWAY, False)
                if ignore_in_away:
                    schedule_mode = self.get_schedule_mode()
                    if schedule_mode:
                        return schedule_mode
                # Default away behavior: frost protection
                return MODE_FROST_PROTECTION

        # PRIORITY 3: Bathroom special logic (light state determines mode)
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
                    return MODE_COMFORT
                # v0.3.9: light off -> follow the calendar when one is set,
                # otherwise eco (previous behaviour)
                schedule_mode = self.get_schedule_mode()
                return schedule_mode or MODE_ECO

        # PRIORITY 4: Check schedule/calendar (v0.3.0+)
        # Schedule has priority over night period (explicit user config)
        schedule_mode = self.get_schedule_mode()
        if schedule_mode:
            return schedule_mode

        # PRIORITY 5: Night period
        if self._is_night:
            return MODE_NIGHT

        # PRIORITY 6: Check legacy comfort time ranges (backward compatibility)
        if self._is_in_comfort_time_range():
            return MODE_COMFORT

        # DEFAULT: Eco
        return MODE_ECO

    def _update_current_mode(self) -> None:
        """Determine current operating mode (see _compute_mode)."""
        self._current_mode = self._compute_mode(include_windows=True)

    def get_mode_ignoring_windows(self) -> str:
        """Mode that would apply if every window were closed (v0.3.9)."""
        return self._compute_mode(include_windows=False)

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
        """Return True when the room must be treated as "window open".

        v0.3.9 (B10): hysteresis with a latch.
        - becomes True only after the window has stayed open >= delay_open
        - once True, stays True until the window has stayed closed >= delay_close
        A short opening (< delay_open) never triggers frost protection,
        neither while open nor after closing.
        """
        delay_open = self.room_config.get(
            CONF_WINDOW_DELAY_OPEN, DEFAULT_WINDOW_DELAY_OPEN
        )
        delay_close = self.room_config.get(
            CONF_WINDOW_DELAY_CLOSE, DEFAULT_WINDOW_DELAY_CLOSE
        )
        now = dt_util.utcnow()

        if self._windows_open:
            if self._windows_opened_at is not None and (
                now - self._windows_opened_at
            ).total_seconds() >= delay_open * 60:
                self._windows_effective_open = True
        elif self._windows_effective_open:
            if self._windows_closed_at is None or (
                now - self._windows_closed_at
            ).total_seconds() >= delay_close * 60:
                self._windows_effective_open = False

        return self._windows_effective_open

    def is_bathroom_light_on(self) -> bool:
        """Return True when a bathroom light is on (v0.3.9)."""
        for light_entity in self.room_config.get(CONF_LIGHTS) or []:
            light_state = self.hass.states.get(light_entity)
            if light_state and light_state.state == STATE_ON:
                return True
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
        """Check if manual pause is active.

        v0.3.9: the state is held by the room manager and set by the pause
        switch (the previous lookup by entity_id never matched the real id).
        """
        return self._paused

    def set_paused(self, paused: bool) -> None:
        """Set manual pause state (called by the pause switch).

        Turning the pause off also ends a manual-override pause.
        """
        self._paused = paused
        if not paused:
            self._manual_until = None
            self._manual_request = None
            self.manual_restore_pending = False

    # ---- v0.3.9: manual override detection -------------------------------
    @callback
    def async_setup_listeners(self) -> None:
        """Watch the climate entity for changes made by a user."""
        climate_entity = self.room_config.get(CONF_CLIMATE_ENTITY)
        if climate_entity and self._unsub_climate is None:
            self._unsub_climate = async_track_state_change_event(
                self.hass, [climate_entity], self._handle_climate_change
            )

    @callback
    def _handle_climate_change(self, event: Event) -> None:
        old = event.data.get("old_state")
        new = event.data.get("new_state")
        if old is None or new is None:
            return
        if "unavailable" in (old.state, new.state) or "unknown" in (old.state, new.state):
            return
        changed = (
            old.state != new.state
            or old.attributes.get("preset_mode") != new.attributes.get("preset_mode")
            or old.attributes.get("temperature") != new.attributes.get("temperature")
        )
        # SRM's own service calls carry no user_id: only a person counts
        if changed and event.context.user_id:
            if self.start_manual_override():
                self._manual_request = {
                    "hvac_mode": new.state,
                    "preset_mode": new.attributes.get("preset_mode"),
                    "temperature": new.attributes.get("temperature"),
                }
                self.manual_restore_pending = False
                self._override_prev = True
                self._notify(
                    NOTIFY_MANUAL_OVERRIDE,
                    {
                        "until_text": dt_util.as_local(self._manual_until).strftime(
                            "%H:%M"
                        )
                    },
                )
                self.coordinator.async_update_listeners()

    def start_manual_override(self) -> bool:
        """Pause the room after a manual change. Returns False if disabled."""
        minutes = self.room_config.get(
            CONF_MANUAL_OVERRIDE_MINUTES, DEFAULT_MANUAL_OVERRIDE_MINUTES
        )
        if not minutes:
            return False
        until = dt_util.utcnow() + timedelta(minutes=int(minutes))
        self._manual_until = until
        _LOGGER.info(
            "Manual change detected in %s - automation paused until %s",
            self.room_name,
            dt_util.as_local(until).strftime("%Y-%m-%d %H:%M"),
        )
        return True

    def is_manual_override(self) -> bool:
        """Return True while a manual-override pause is active."""
        if self._manual_until is None:
            return False
        if dt_util.utcnow() >= self._manual_until:
            self._manual_until = None
            self._manual_request = None
            self.manual_restore_pending = False
            return False
        return True

    def get_manual_request(self) -> dict[str, Any] | None:
        """Settings requested by hand, while the override period runs."""
        return self._manual_request if self.is_manual_override() else None

    def manual_request_is_demand(self) -> bool:
        """True when the manual request asks for heating or cooling."""
        request = self.get_manual_request()
        if not request:
            return False
        if request.get("hvac_mode") in ("off",):
            return False
        return request.get("preset_mode") not in ("eco", "away", "none") or (
            request.get("preset_mode") is None
        )

    # ---- v0.3.9: heating blocked by an open window -------------------------
    def get_open_window_names(self) -> list[str]:
        names = []
        for entity_id in self.room_config.get(CONF_DOOR_WINDOW_SENSORS) or []:
            state = self.hass.states.get(entity_id)
            if state and state.state == STATE_ON:
                names.append(state.attributes.get("friendly_name", entity_id))
        return names

    def set_heating_blocked(
        self, blocked: bool, source: str | None = None, direction: str = "heat"
    ) -> None:
        """Record the blocked state and fire an event on each change."""
        if blocked == self._heating_blocked:
            return
        self._heating_blocked = blocked
        data = {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "climate_entity": self.room_config.get(CONF_CLIMATE_ENTITY),
            "windows": self.get_open_window_names(),
            "source": source,
            "direction": direction,
        }
        self._heating_blocked_info = data if blocked else {}
        self.hass.bus.async_fire(
            "smart_room_manager_heating_blocked"
            if blocked
            else "smart_room_manager_heating_unblocked",
            data,
        )
        self._notify(
            NOTIFY_HEATING_BLOCKED if blocked else NOTIFY_HEATING_UNBLOCKED,
            data,
            extra_entities=[
                e
                for e in self.room_config.get(CONF_DOOR_WINDOW_SENSORS) or []
                if (st := self.hass.states.get(e)) and st.state == STATE_ON
            ],
        )
        _LOGGER.info(
            "Heating %s in %s (source: %s, windows: %s)",
            "blocked by a window" if blocked else "no longer blocked",
            self.room_name,
            source,
            data["windows"],
        )

    # ---- v0.3.9: notifications ------------------------------------------
    def _notify(
        self,
        ntype: str,
        values: dict[str, Any] | None = None,
        extra_entities: list[str] | None = None,
    ) -> None:
        notifier = getattr(self.coordinator, "notifier", None)
        if notifier is None:
            return
        entities = [e for e in [self.room_config.get(CONF_CLIMATE_ENTITY)] if e]
        entities += list(extra_entities or [])
        try:
            notifier.notify(ntype, self.room_config, values, entities)
        except Exception as err:  # noqa: BLE001 - never break the room logic
            _LOGGER.warning("Notification %s failed in %s: %s", ntype, self.room_name, err)

    def _check_frost_notification(self) -> None:
        """Notify when a heated room enters frost protection."""
        mode = self._current_mode
        previous = self._mode_prev
        self._mode_prev = mode
        if previous is None or not self.room_config.get(CONF_CLIMATE_ENTITY):
            return
        if mode != MODE_FROST_PROTECTION or previous == MODE_FROST_PROTECTION:
            return
        if self._paused or not self._automation_enabled:
            return
        reason = (
            "window"
            if self.room_config.get(CONF_CLIMATE_WINDOW_CHECK, True)
            and self.is_windows_open_delayed()
            else "away"
        )
        self._notify(NOTIFY_FROST_PROTECTION, {"reason": reason})

    def is_heating_blocked(self) -> bool:
        return self._heating_blocked

    def get_pause_reason(self) -> str | None:
        if self._paused:
            return PAUSE_REASON_MANUAL_SWITCH
        if self.is_manual_override():
            return PAUSE_REASON_MANUAL_OVERRIDE
        return None

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
        pause_active = self.is_paused() or self.is_manual_override()

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
            "pause_reason": self.get_pause_reason(),
            "heating_blocked": self._heating_blocked,
            "heating_blocked_info": dict(self._heating_blocked_info),
            "manual_override_until": (
                dt_util.as_local(self._manual_until).isoformat()
                if self.is_manual_override()
                else None
            ),
        }

    async def async_shutdown(self) -> None:
        """Shutdown room manager."""
        if self._unsub_climate:
            self._unsub_climate()
            self._unsub_climate = None
        await self.light_controller.async_shutdown()
        await self.climate_controller.async_shutdown()
        _LOGGER.debug("Room manager shut down for %s", self.room_name)
