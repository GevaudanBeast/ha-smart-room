"""Light control logic for Smart Room Manager."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.const import SERVICE_TURN_OFF, SERVICE_TURN_ON, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    CONF_LIGHT_TIMEOUT,
    CONF_LIGHTS,
    CONF_ROOM_TYPE,
    CONF_VMC_ENTITY,
    CONF_VMC_TIMER,
    DEFAULT_LIGHT_TIMEOUT,
    DEFAULT_LIGHT_TIMEOUT_BATHROOM,
    DEFAULT_VMC_TIMER,
    ROOM_TYPE_BATHROOM,
    ROOM_TYPE_CORRIDOR,
)

if TYPE_CHECKING:
    from .room_manager import RoomManager

_LOGGER = logging.getLogger(__name__)


class LightController:
    """Control lights in a room - simplified logic based on manual control + timer."""

    def __init__(
        self,
        hass: HomeAssistant,
        room_config: dict[str, Any],
        room_manager: RoomManager,
    ) -> None:
        """Initialize light controller."""
        self.hass = hass
        self.room_config = room_config
        self.room_manager = room_manager

        self._light_on_times: dict[str, datetime] = {}
        self._current_brightness: int | None = None

        # VMC control state
        self._vmc_active: bool = False
        self._vmc_started_at: datetime | None = None
        self._any_light_was_on: bool = False

    def update_config(self, room_config: dict[str, Any]) -> None:
        """Update configuration."""
        self.room_config = room_config

    async def async_update(self) -> None:
        """Update light control logic.

        Simplified logic:
        - User turns on lights manually (or via automation like door sensor)
        - For corridor/bathroom types: auto-off after timeout
        - For normal types (bedrooms): no auto-off
        - For bathroom: trigger VMC high speed when lights go off
        """
        # Check if manual pause is active - skip all automation
        if self.room_manager.is_paused():
            _LOGGER.debug(
                "⏸️ Manual pause active in %s - skipping light automation",
                self.room_manager.room_name,
            )
            return

        # Use 'or []' to handle None values (dict.get returns None if value is None)
        light_entities = self.room_config.get(CONF_LIGHTS) or []
        room_type = self.room_config.get(CONF_ROOM_TYPE, "normal")

        # Check if any light is currently on
        any_light_on = False
        for entity_id in light_entities:
            state = self.hass.states.get(entity_id)
            if state and state.state == STATE_ON:
                any_light_on = True
                break

        # Handle VMC for bathroom rooms
        if room_type == ROOM_TYPE_BATHROOM:
            await self._update_vmc_control(any_light_on)

        if not light_entities:
            self._any_light_was_on = any_light_on
            return

        # Only auto-off for corridor and bathroom types
        if room_type not in [ROOM_TYPE_CORRIDOR, ROOM_TYPE_BATHROOM]:
            self._any_light_was_on = any_light_on
            return

        # Get timeout based on room type
        if room_type == ROOM_TYPE_BATHROOM:
            timeout = self.room_config.get(
                CONF_LIGHT_TIMEOUT, DEFAULT_LIGHT_TIMEOUT_BATHROOM
            )
        else:
            timeout = self.room_config.get(CONF_LIGHT_TIMEOUT, DEFAULT_LIGHT_TIMEOUT)

        # Check each light for auto-off
        for entity_id in light_entities:
            state = self.hass.states.get(entity_id)
            if not state:
                continue

            # If light just turned on, record time
            if state.state == STATE_ON:
                if entity_id not in self._light_on_times:
                    # Use last_changed or current time as fallback
                    self._light_on_times[entity_id] = (
                        state.last_changed or dt_util.utcnow()
                    )
                    _LOGGER.debug(
                        "Light %s turned on in %s at %s",
                        entity_id,
                        self.room_manager.room_name,
                        state.last_changed,
                    )

                # Check if timeout exceeded
                time_on = (
                    dt_util.utcnow() - self._light_on_times[entity_id]
                ).total_seconds()
                if time_on > timeout:
                    _LOGGER.debug(
                        "Auto-off light %s in %s after %d seconds (timeout: %d)",
                        entity_id,
                        self.room_manager.room_name,
                        time_on,
                        timeout,
                    )
                    await self._turn_off_light(entity_id)
                    if entity_id in self._light_on_times:
                        del self._light_on_times[entity_id]

            else:
                # Light is off, remove from tracking
                if entity_id in self._light_on_times:
                    del self._light_on_times[entity_id]

        self._any_light_was_on = any_light_on

    async def _update_vmc_control(self, any_light_on: bool) -> None:
        """Update VMC control for bathroom rooms.

        Logic:
        - Light turns ON → VMC high speed ON immediately
        - Light turns OFF → Start timer
        - Timer expires → VMC high speed OFF
        """
        # Get VMC config from global settings
        vmc_entity = self.room_manager.coordinator.entry.data.get(CONF_VMC_ENTITY)
        vmc_timer = self.room_manager.coordinator.entry.data.get(
            CONF_VMC_TIMER, DEFAULT_VMC_TIMER
        )

        if not vmc_entity:
            return

        now = dt_util.utcnow()

        # Light just turned ON (was off, now on) -> start VMC high speed
        if not self._any_light_was_on and any_light_on:
            _LOGGER.info(
                "💨 Bathroom light ON in %s - starting VMC high speed",
                self.room_manager.room_name,
            )
            await self._turn_on_vmc(vmc_entity)
            self._vmc_active = True
            self._vmc_started_at = None  # No timer yet, light is still on

        # Light just turned OFF (was on, now off) -> start the countdown timer
        if self._any_light_was_on and not any_light_on:
            _LOGGER.info(
                "💨 Bathroom light OFF in %s - VMC will stop in %ds",
                self.room_manager.room_name,
                vmc_timer,
            )
            self._vmc_started_at = now  # Start countdown

        # Check if VMC timer expired (light is off and timer running)
        if self._vmc_active and self._vmc_started_at and not any_light_on:
            elapsed = (now - self._vmc_started_at).total_seconds()
            if elapsed >= vmc_timer:
                # Before turning off VMC, check if any OTHER bathroom has lights on
                # VMC is global, so we must not turn it off if another bathroom needs it
                if self._any_other_bathroom_active():
                    _LOGGER.debug(
                        "💨 VMC timer expired in %s but another bathroom is active",
                        self.room_manager.room_name,
                    )
                    self._vmc_active = False
                    self._vmc_started_at = None
                else:
                    _LOGGER.info(
                        "💨 VMC timer expired in %s - stopping high speed",
                        self.room_manager.room_name,
                    )
                    await self._turn_off_vmc(vmc_entity)
                    self._vmc_active = False
                    self._vmc_started_at = None

        # If light turns back on while timer is running, cancel the timer
        if any_light_on and self._vmc_started_at:
            _LOGGER.debug(
                "Light back ON in %s - canceling VMC shutdown timer",
                self.room_manager.room_name,
            )
            self._vmc_started_at = None  # Cancel timer, VMC stays on

    def _any_other_bathroom_active(self) -> bool:
        """Check if any other bathroom has lights on or VMC timer running.

        This prevents turning off the global VMC when another bathroom needs it.
        """
        coordinator = self.room_manager.coordinator
        current_room_id = self.room_manager.room_id

        for room_manager in coordinator.get_all_room_managers():
            # Skip current room
            if room_manager.room_id == current_room_id:
                continue

            # Only check other bathrooms
            if room_manager.room_type != ROOM_TYPE_BATHROOM:
                continue

            # Check if lights are on in this bathroom
            light_controller = room_manager.light_controller
            if light_controller._any_light_was_on:
                return True

            # Check if VMC timer is still running in this bathroom
            if light_controller._vmc_active and light_controller._vmc_started_at:
                return True

        return False

    def _get_entity_domain(self, entity_id: str, default: str = "light") -> str:
        """Extract domain from entity_id (e.g., 'light.kitchen' -> 'light')."""
        return entity_id.split(".")[0] if "." in entity_id else default

    async def _control_entity(
        self, entity_id: str, turn_on: bool, default_domain: str = "light"
    ) -> None:
        """Turn an entity on or off."""
        try:
            domain = self._get_entity_domain(entity_id, default_domain)
            service = SERVICE_TURN_ON if turn_on else SERVICE_TURN_OFF
            await self.hass.services.async_call(
                domain,
                service,
                {"entity_id": entity_id},
                blocking=True,
            )
        except Exception as err:
            action = "on" if turn_on else "off"
            _LOGGER.error("Error turning %s %s: %s", action, entity_id, err)

    async def _turn_on_vmc(self, vmc_entity: str) -> None:
        """Turn on VMC high speed."""
        await self._control_entity(vmc_entity, turn_on=True, default_domain="switch")

    async def _turn_off_vmc(self, vmc_entity: str) -> None:
        """Turn off VMC high speed."""
        await self._control_entity(vmc_entity, turn_on=False, default_domain="switch")

    async def _turn_off_light(self, entity_id: str) -> None:
        """Turn off a single light."""
        await self._control_entity(entity_id, turn_on=False, default_domain="light")

    def get_state(self) -> dict[str, Any]:
        """Get current light controller state."""
        room_type = self.room_config.get(CONF_ROOM_TYPE, "normal")

        if room_type == ROOM_TYPE_BATHROOM:
            timeout = self.room_config.get(
                CONF_LIGHT_TIMEOUT, DEFAULT_LIGHT_TIMEOUT_BATHROOM
            )
        else:
            timeout = self.room_config.get(CONF_LIGHT_TIMEOUT, DEFAULT_LIGHT_TIMEOUT)

        # Calculate remaining time for each tracked light
        timer_active = False
        time_remaining = 0
        if self._light_on_times and room_type in [
            ROOM_TYPE_CORRIDOR,
            ROOM_TYPE_BATHROOM,
        ]:
            now = dt_util.utcnow()
            for entity_id, on_time in self._light_on_times.items():
                elapsed = (now - on_time).total_seconds()
                remaining = max(0, timeout - elapsed)
                if remaining > 0:
                    timer_active = True
                    time_remaining = max(time_remaining, remaining)

        # Calculate VMC timer remaining (only when light is off and timer running)
        vmc_time_remaining = 0
        if self._vmc_active and self._vmc_started_at:
            vmc_timer = self.room_manager.coordinator.entry.data.get(
                CONF_VMC_TIMER, DEFAULT_VMC_TIMER
            )
            elapsed = (dt_util.utcnow() - self._vmc_started_at).total_seconds()
            vmc_time_remaining = max(0, vmc_timer - elapsed)
        elif self._vmc_active and not self._vmc_started_at:
            # VMC active but no timer = light still on, show -1 to indicate "waiting"
            vmc_time_remaining = -1

        return {
            "room_type": room_type,
            "timeout_seconds": timeout,
            "lights_tracked": len(self._light_on_times),
            "lights_on": list(self._light_on_times.keys()),
            "timer_active": timer_active,
            "time_remaining": int(time_remaining),
            "vmc_active": self._vmc_active,
            "vmc_time_remaining": int(vmc_time_remaining),
        }

    async def async_shutdown(self) -> None:
        """Shutdown light controller."""
        pass
