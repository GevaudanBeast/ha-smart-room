"""Light control logic for Smart Room Manager."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, TYPE_CHECKING

from homeassistant.components.light import ATTR_BRIGHTNESS
from homeassistant.const import STATE_ON, SERVICE_TURN_ON, SERVICE_TURN_OFF
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    CONF_LIGHTS,
    CONF_LIGHT_DAY_BRIGHTNESS,
    CONF_LIGHT_NIGHT_BRIGHTNESS,
    CONF_LIGHT_NIGHT_MODE,
    CONF_LIGHT_TIMEOUT,
    CONF_ROOM_TYPE,
    DEFAULT_LIGHT_DAY_BRIGHTNESS,
    DEFAULT_LIGHT_NIGHT_BRIGHTNESS,
    DEFAULT_LIGHT_TIMEOUT,
    DEFAULT_LIGHT_TIMEOUT_BATHROOM,
    ROOM_TYPE_BATHROOM,
    ROOM_TYPE_CORRIDOR,
    TIME_PERIOD_NIGHT,
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

    def update_config(self, room_config: dict[str, Any]) -> None:
        """Update configuration."""
        self.room_config = room_config

    async def async_update(self) -> None:
        """Update light control logic.

        Simplified logic:
        - User turns on lights manually (or via automation like door sensor)
        - For corridor/bathroom types: auto-off after timeout
        - For normal types (bedrooms): no auto-off
        - Night mode: reduced brightness (optional)
        """
        light_entities = self.room_config.get(CONF_LIGHTS, [])
        room_type = self.room_config.get(CONF_ROOM_TYPE, "normal")

        if not light_entities:
            return

        # Only auto-off for corridor and bathroom types
        if room_type not in [ROOM_TYPE_CORRIDOR, ROOM_TYPE_BATHROOM]:
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
                    self._light_on_times[entity_id] = state.last_changed
                    _LOGGER.debug(
                        "Light %s turned on in %s at %s",
                        entity_id,
                        self.room_manager.room_name,
                        state.last_changed,
                    )

                # Check if timeout exceeded
                time_on = (dt_util.utcnow() - self._light_on_times[entity_id]).total_seconds()
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

    async def _turn_off_light(self, entity_id: str) -> None:
        """Turn off a single light."""
        try:
            await self.hass.services.async_call(
                "light" if "light." in entity_id else "switch",
                SERVICE_TURN_OFF,
                {"entity_id": entity_id},
                blocking=True,
            )
        except Exception as err:
            _LOGGER.error(
                "Error turning off light %s: %s",
                entity_id,
                err,
            )

    def get_state(self) -> dict[str, Any]:
        """Get current light controller state."""
        room_type = self.room_config.get(CONF_ROOM_TYPE, "normal")

        if room_type == ROOM_TYPE_BATHROOM:
            timeout = self.room_config.get(
                CONF_LIGHT_TIMEOUT, DEFAULT_LIGHT_TIMEOUT_BATHROOM
            )
        else:
            timeout = self.room_config.get(CONF_LIGHT_TIMEOUT, DEFAULT_LIGHT_TIMEOUT)

        return {
            "room_type": room_type,
            "timeout_seconds": timeout,
            "lights_tracked": len(self._light_on_times),
            "lights_on": list(self._light_on_times.keys()),
        }

    async def async_shutdown(self) -> None:
        """Shutdown light controller."""
        pass
