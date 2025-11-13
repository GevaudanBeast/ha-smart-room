"""Climate control logic for Smart Room Manager."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any, TYPE_CHECKING

from homeassistant.components.climate import (
    ATTR_TEMPERATURE,
    SERVICE_SET_TEMPERATURE,
)
from homeassistant.const import SERVICE_TURN_ON, SERVICE_TURN_OFF
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CLIMATE_ENTITY,
    CONF_CLIMATE_PRESENCE_REQUIRED,
    CONF_CLIMATE_UNOCCUPIED_DELAY,
    CONF_CLIMATE_WINDOW_CHECK,
    CONF_HEATING_SWITCHES,
    CONF_TEMP_AWAY,
    CONF_TEMP_COMFORT,
    CONF_TEMP_ECO,
    CONF_TEMP_FROST_PROTECTION,
    CONF_TEMP_NIGHT,
    DEFAULT_CLIMATE_UNOCCUPIED_DELAY,
    DEFAULT_TEMP_AWAY,
    DEFAULT_TEMP_COMFORT,
    DEFAULT_TEMP_ECO,
    DEFAULT_TEMP_FROST_PROTECTION,
    DEFAULT_TEMP_NIGHT,
    MODE_AWAY,
    MODE_COMFORT,
    MODE_ECO,
    MODE_FROST_PROTECTION,
    MODE_GUEST,
    MODE_NIGHT,
)

if TYPE_CHECKING:
    from .room_manager import RoomManager

_LOGGER = logging.getLogger(__name__)


class ClimateController:
    """Control climate/heating in a room."""

    def __init__(
        self,
        hass: HomeAssistant,
        room_config: dict[str, Any],
        room_manager: RoomManager,
    ) -> None:
        """Initialize climate controller."""
        self.hass = hass
        self.room_config = room_config
        self.room_manager = room_manager

        self._target_temperature: float | None = None
        self._last_unoccupied_time: Any = None

    def update_config(self, room_config: dict[str, Any]) -> None:
        """Update configuration."""
        self.room_config = room_config

    async def async_update(self) -> None:
        """Update climate control logic."""
        climate_entity = self.room_config.get(CONF_CLIMATE_ENTITY)
        heating_switches = self.room_config.get(CONF_HEATING_SWITCHES, [])

        if not climate_entity and not heating_switches:
            return

        # Check if heating should be on
        should_heat, target_temp = self._should_heat()

        # Control climate entity
        if climate_entity and target_temp is not None:
            await self._set_climate_temperature(climate_entity, target_temp, should_heat)

        # Control heating switches
        if heating_switches:
            await self._control_heating_switches(heating_switches, should_heat)

    def _should_heat(self) -> tuple[bool, float | None]:
        """Determine if heating should be active and target temperature."""
        # Check window state if configured
        if self.room_config.get(CONF_CLIMATE_WINDOW_CHECK, True):
            if self.room_manager.is_windows_open():
                _LOGGER.debug(
                    "Windows open in %s, turning off heating",
                    self.room_manager.room_name,
                )
                return False, None

        # Get target temperature based on mode
        target_temp = self._get_target_temperature()

        # Check presence requirement
        if self.room_config.get(CONF_CLIMATE_PRESENCE_REQUIRED, False):
            if not self.room_manager.is_occupied():
                # Check unoccupied delay
                if self._last_unoccupied_time is None:
                    self._last_unoccupied_time = dt_util.utcnow()

                delay = self.room_config.get(
                    CONF_CLIMATE_UNOCCUPIED_DELAY, DEFAULT_CLIMATE_UNOCCUPIED_DELAY
                )
                time_unoccupied = (
                    dt_util.utcnow() - self._last_unoccupied_time
                ).total_seconds()

                if time_unoccupied > delay:
                    _LOGGER.debug(
                        "Room %s unoccupied for %d seconds, reducing heating",
                        self.room_manager.room_name,
                        time_unoccupied,
                    )
                    # Use eco or away temperature
                    target_temp = self.room_config.get(CONF_TEMP_ECO, DEFAULT_TEMP_ECO)
            else:
                # Reset unoccupied timer
                self._last_unoccupied_time = None

        self._target_temperature = target_temp
        return True, target_temp

    def _get_target_temperature(self) -> float:
        """Get target temperature based on current mode."""
        mode = self.room_manager.get_current_mode()

        if mode == MODE_FROST_PROTECTION:
            return self.room_config.get(
                CONF_TEMP_FROST_PROTECTION, DEFAULT_TEMP_FROST_PROTECTION
            )
        elif mode == MODE_AWAY:
            return self.room_config.get(CONF_TEMP_AWAY, DEFAULT_TEMP_AWAY)
        elif mode == MODE_NIGHT:
            return self.room_config.get(CONF_TEMP_NIGHT, DEFAULT_TEMP_NIGHT)
        elif mode == MODE_COMFORT or mode == MODE_GUEST:
            return self.room_config.get(CONF_TEMP_COMFORT, DEFAULT_TEMP_COMFORT)
        else:  # MODE_ECO
            return self.room_config.get(CONF_TEMP_ECO, DEFAULT_TEMP_ECO)

    async def _set_climate_temperature(
        self, climate_entity: str, temperature: float, turn_on: bool
    ) -> None:
        """Set climate entity temperature."""
        state = self.hass.states.get(climate_entity)
        if not state:
            _LOGGER.warning("Climate entity %s not found", climate_entity)
            return

        current_temp = state.attributes.get(ATTR_TEMPERATURE)

        # Only update if temperature changed significantly (> 0.5°C)
        if current_temp is not None and abs(current_temp - temperature) < 0.5:
            return

        _LOGGER.debug(
            "Setting temperature for %s in %s to %.1f°C",
            climate_entity,
            self.room_manager.room_name,
            temperature,
        )

        try:
            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_TEMPERATURE,
                {
                    "entity_id": climate_entity,
                    ATTR_TEMPERATURE: temperature,
                },
                blocking=True,
            )
        except Exception as err:
            _LOGGER.error(
                "Error setting temperature for %s: %s",
                climate_entity,
                err,
            )

    async def _control_heating_switches(
        self, heating_switches: list[str], turn_on: bool
    ) -> None:
        """Control heating switches."""
        for entity_id in heating_switches:
            state = self.hass.states.get(entity_id)
            if not state:
                continue

            current_state = state.state
            desired_state = "on" if turn_on else "off"

            if current_state != desired_state:
                _LOGGER.debug(
                    "Turning %s heating switch %s in %s",
                    desired_state,
                    entity_id,
                    self.room_manager.room_name,
                )

                try:
                    await self.hass.services.async_call(
                        "switch",
                        SERVICE_TURN_ON if turn_on else SERVICE_TURN_OFF,
                        {"entity_id": entity_id},
                        blocking=True,
                    )
                except Exception as err:
                    _LOGGER.error(
                        "Error controlling heating switch %s: %s",
                        entity_id,
                        err,
                    )

    def get_state(self) -> dict[str, Any]:
        """Get current climate controller state."""
        return {
            "target_temperature": self._target_temperature,
            "heating_active": self._target_temperature is not None,
        }

    async def async_shutdown(self) -> None:
        """Shutdown climate controller."""
        pass
