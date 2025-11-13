"""Light control logic for Smart Room Manager."""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from homeassistant.components.light import ATTR_BRIGHTNESS
from homeassistant.const import STATE_ON, SERVICE_TURN_ON, SERVICE_TURN_OFF
from homeassistant.core import HomeAssistant

from .const import (
    CONF_LIGHTS,
    CONF_LIGHT_DAY_BRIGHTNESS,
    CONF_LIGHT_LUX_THRESHOLD,
    CONF_LIGHT_NIGHT_BRIGHTNESS,
    CONF_LIGHT_NIGHT_MODE,
    DEFAULT_LIGHT_DAY_BRIGHTNESS,
    DEFAULT_LIGHT_LUX_THRESHOLD,
    DEFAULT_LIGHT_NIGHT_BRIGHTNESS,
    TIME_PERIOD_NIGHT,
)

if TYPE_CHECKING:
    from .room_manager import RoomManager

_LOGGER = logging.getLogger(__name__)


class LightController:
    """Control lights in a room."""

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

        self._should_be_on: bool = False
        self._current_brightness: int | None = None

    def update_config(self, room_config: dict[str, Any]) -> None:
        """Update configuration."""
        self.room_config = room_config

    async def async_update(self) -> None:
        """Update light control logic."""
        light_entities = self.room_config.get(CONF_LIGHTS, [])

        if not light_entities:
            return

        # Determine if lights should be on
        should_be_on = self._should_lights_be_on()
        target_brightness = self._get_target_brightness()

        # Control lights if state has changed
        if should_be_on != self._should_be_on:
            self._should_be_on = should_be_on

            if should_be_on:
                await self._turn_on_lights(light_entities, target_brightness)
            else:
                await self._turn_off_lights(light_entities)

        # Update brightness if already on and brightness changed
        elif should_be_on and target_brightness != self._current_brightness:
            await self._update_brightness(light_entities, target_brightness)

    def _should_lights_be_on(self) -> bool:
        """Determine if lights should be turned on."""
        # Must be occupied
        if not self.room_manager.is_occupied():
            return False

        # Check luminosity threshold
        lux_threshold = self.room_config.get(
            CONF_LIGHT_LUX_THRESHOLD, DEFAULT_LIGHT_LUX_THRESHOLD
        )
        current_lux = self.room_manager.get_luminosity()

        # If no lux sensor, assume lights are needed during night period
        if current_lux is None:
            time_period = self.room_manager.get_time_period()
            return time_period == TIME_PERIOD_NIGHT

        # Check if luminosity is below threshold
        return current_lux < lux_threshold

    def _get_target_brightness(self) -> int:
        """Get target brightness based on time period and mode."""
        time_period = self.room_manager.get_time_period()
        night_mode = self.room_config.get(CONF_LIGHT_NIGHT_MODE, True)

        if time_period == TIME_PERIOD_NIGHT and night_mode:
            brightness_pct = self.room_config.get(
                CONF_LIGHT_NIGHT_BRIGHTNESS, DEFAULT_LIGHT_NIGHT_BRIGHTNESS
            )
        else:
            brightness_pct = self.room_config.get(
                CONF_LIGHT_DAY_BRIGHTNESS, DEFAULT_LIGHT_DAY_BRIGHTNESS
            )

        # Convert percentage to 0-255 range
        return int((brightness_pct / 100) * 255)

    async def _turn_on_lights(
        self, light_entities: list[str], brightness: int
    ) -> None:
        """Turn on lights with specified brightness."""
        _LOGGER.debug(
            "Turning on lights in %s with brightness %d",
            self.room_manager.room_name,
            brightness,
        )

        for entity_id in light_entities:
            # Check if entity supports brightness
            state = self.hass.states.get(entity_id)
            if not state:
                continue

            service_data = {"entity_id": entity_id}

            # Add brightness only for lights that support it
            if "light." in entity_id and state.attributes.get("supported_features", 0) & 1:
                service_data[ATTR_BRIGHTNESS] = brightness

            try:
                await self.hass.services.async_call(
                    "light" if "light." in entity_id else "switch",
                    SERVICE_TURN_ON,
                    service_data,
                    blocking=True,
                )
                self._current_brightness = brightness
            except Exception as err:
                _LOGGER.error(
                    "Error turning on light %s: %s",
                    entity_id,
                    err,
                )

    async def _turn_off_lights(self, light_entities: list[str]) -> None:
        """Turn off lights."""
        _LOGGER.debug("Turning off lights in %s", self.room_manager.room_name)

        for entity_id in light_entities:
            # Don't turn off if manually turned on
            state = self.hass.states.get(entity_id)
            if state and self._was_manually_controlled(state):
                _LOGGER.debug("Skipping %s - manually controlled", entity_id)
                continue

            try:
                await self.hass.services.async_call(
                    "light" if "light." in entity_id else "switch",
                    SERVICE_TURN_OFF,
                    {"entity_id": entity_id},
                    blocking=True,
                )
                self._current_brightness = None
            except Exception as err:
                _LOGGER.error(
                    "Error turning off light %s: %s",
                    entity_id,
                    err,
                )

    async def _update_brightness(
        self, light_entities: list[str], brightness: int
    ) -> None:
        """Update brightness for lights that are already on."""
        _LOGGER.debug(
            "Updating brightness in %s to %d",
            self.room_manager.room_name,
            brightness,
        )

        for entity_id in light_entities:
            state = self.hass.states.get(entity_id)
            if not state or state.state != STATE_ON:
                continue

            # Only update if light supports brightness
            if "light." in entity_id and state.attributes.get("supported_features", 0) & 1:
                try:
                    await self.hass.services.async_call(
                        "light",
                        SERVICE_TURN_ON,
                        {
                            "entity_id": entity_id,
                            ATTR_BRIGHTNESS: brightness,
                        },
                        blocking=True,
                    )
                    self._current_brightness = brightness
                except Exception as err:
                    _LOGGER.error(
                        "Error updating brightness for %s: %s",
                        entity_id,
                        err,
                    )

    def _was_manually_controlled(self, state) -> bool:
        """Check if entity was manually controlled recently."""
        # Check if last_changed is very recent (< 5 seconds)
        # This helps avoid fighting with manual control
        if not state.last_changed:
            return False

        from homeassistant.util import dt as dt_util

        time_since_change = (dt_util.utcnow() - state.last_changed).total_seconds()
        return time_since_change < 5

    def get_state(self) -> dict[str, Any]:
        """Get current light controller state."""
        return {
            "should_be_on": self._should_be_on,
            "current_brightness": self._current_brightness,
            "brightness_percentage": (
                int((self._current_brightness / 255) * 100)
                if self._current_brightness
                else None
            ),
        }

    async def async_shutdown(self) -> None:
        """Shutdown light controller."""
        pass
