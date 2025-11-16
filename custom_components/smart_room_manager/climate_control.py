"""Climate control logic for Smart Room Manager."""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ATTR_TEMPERATURE,
    DOMAIN as CLIMATE_DOMAIN,
    HVACMode,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_TEMPERATURE,
)
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant

from .const import (
    CLIMATE_TYPE_THERMOSTAT,
    CLIMATE_TYPE_X4FP,
    CONF_CLIMATE_BYPASS_SWITCH,
    CONF_CLIMATE_ENTITY,
    CONF_CLIMATE_WINDOW_CHECK,
    CONF_SEASON_CALENDAR,
    CONF_TEMP_COMFORT,
    CONF_TEMP_COOL_COMFORT,
    CONF_TEMP_COOL_ECO,
    CONF_TEMP_ECO,
    CONF_TEMP_FROST_PROTECTION,
    CONF_TEMP_NIGHT,
    DEFAULT_TEMP_COMFORT,
    DEFAULT_TEMP_COOL_COMFORT,
    DEFAULT_TEMP_COOL_ECO,
    DEFAULT_TEMP_ECO,
    DEFAULT_TEMP_FROST_PROTECTION,
    DEFAULT_TEMP_NIGHT,
    MODE_COMFORT,
    MODE_ECO,
    MODE_FROST_PROTECTION,
    MODE_NIGHT,
    X4FP_PRESET_COMFORT,
    X4FP_PRESET_ECO,
    X4FP_PRESET_AWAY,
    X4FP_PRESET_OFF,
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

        self._climate_type: str | None = None
        self._target_temperature: float | None = None
        self._current_preset: str | None = None
        self._current_hvac_mode: str | None = None

    def update_config(self, room_config: dict[str, Any]) -> None:
        """Update configuration."""
        self.room_config = room_config
        # Reset climate type detection on config change
        self._climate_type = None

    async def async_update(self) -> None:
        """Update climate control logic."""
        climate_entity = self.room_config.get(CONF_CLIMATE_ENTITY)

        if not climate_entity:
            return

        # PRIORITY 1: Check bypass switch (Solar Optimizer, manual control, etc.)
        bypass_switch = self.room_config.get(CONF_CLIMATE_BYPASS_SWITCH)
        if bypass_switch:
            bypass_state = self.hass.states.get(bypass_switch)
            if bypass_state and bypass_state.state == STATE_ON:
                _LOGGER.debug(
                    "🔌 Climate bypass active (%s ON) in %s - skipping control",
                    bypass_switch,
                    self.room_manager.room_name,
                )
                return

        # Detect climate type if not already done
        if self._climate_type is None:
            self._climate_type = self._detect_climate_type(climate_entity)
            _LOGGER.info(
                "Climate type detected for %s: %s (%s)",
                self.room_manager.room_name,
                self._climate_type,
                climate_entity,
            )

        # PRIORITY 2: Check windows
        if self.room_config.get(CONF_CLIMATE_WINDOW_CHECK, True):
            if self.room_manager.is_windows_open():
                _LOGGER.debug(
                    "🪟 Windows open in %s - setting frost protection",
                    self.room_manager.room_name,
                )
                await self._set_frost_protection(climate_entity)
                return

        # PRIORITY 3: Check summer mode
        is_summer = self._is_summer_mode()

        # PRIORITY 4: Get current mode and apply
        mode = self.room_manager.get_current_mode()

        if self._climate_type == CLIMATE_TYPE_X4FP:
            await self._control_x4fp(climate_entity, mode, is_summer)
        else:
            await self._control_thermostat(climate_entity, mode, is_summer)

    def _detect_climate_type(self, climate_entity: str) -> str:
        """Detect if climate entity is X4FP (preset_mode) or thermostat (hvac_mode)."""
        state = self.hass.states.get(climate_entity)
        if not state:
            _LOGGER.warning("Climate entity %s not found", climate_entity)
            return CLIMATE_TYPE_THERMOSTAT

        # Check if entity has X4FP-style preset modes
        preset_modes = state.attributes.get("preset_modes", [])

        # X4FP has "comfort" and/or "eco" preset modes
        if X4FP_PRESET_COMFORT in preset_modes or X4FP_PRESET_ECO in preset_modes:
            return CLIMATE_TYPE_X4FP

        return CLIMATE_TYPE_THERMOSTAT

    def _is_summer_mode(self) -> bool:
        """Check if summer mode is active (from calendar)."""
        # Get season calendar from global config (entry.data)
        season_calendar = self.room_manager.coordinator.entry.data.get(
            CONF_SEASON_CALENDAR
        )

        if not season_calendar:
            return False

        calendar_state = self.hass.states.get(season_calendar)
        return calendar_state and calendar_state.state == STATE_ON

    async def _control_x4fp(
        self, climate_entity: str, mode: str, is_summer: bool
    ) -> None:
        """Control X4FP climate entity via preset_mode."""
        # Summer: turn off (except frost protection)
        if is_summer:
            if mode != MODE_FROST_PROTECTION:
                target_preset = X4FP_PRESET_OFF
            else:
                target_preset = X4FP_PRESET_AWAY
        else:
            # Winter: map mode to preset
            target_preset = self._get_x4fp_preset(mode)

        # Only change if different
        if self._current_preset == target_preset:
            return

        _LOGGER.debug(
            "Setting X4FP preset for %s in %s to %s (mode: %s, summer: %s)",
            climate_entity,
            self.room_manager.room_name,
            target_preset,
            mode,
            is_summer,
        )

        try:
            await self.hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_PRESET_MODE,
                {
                    "entity_id": climate_entity,
                    ATTR_PRESET_MODE: target_preset,
                },
                blocking=True,
            )
            self._current_preset = target_preset
        except Exception as err:
            _LOGGER.error(
                "Error setting preset mode for %s: %s",
                climate_entity,
                err,
            )

    async def _control_thermostat(
        self, climate_entity: str, mode: str, is_summer: bool
    ) -> None:
        """Control thermostat climate entity via hvac_mode + temperature."""
        if is_summer:
            # Summer mode
            if mode == MODE_FROST_PROTECTION:
                target_hvac = HVACMode.OFF
                target_temp = None
            elif mode == MODE_COMFORT:
                target_hvac = HVACMode.COOL
                target_temp = self.room_config.get(
                    CONF_TEMP_COOL_COMFORT, DEFAULT_TEMP_COOL_COMFORT
                )
            else:  # eco, night
                # Option: cool à température plus haute ou OFF
                target_hvac = HVACMode.OFF
                target_temp = None
        else:
            # Winter mode
            target_hvac = HVACMode.HEAT
            target_temp = self._get_target_temperature(mode)

        # Check current state
        state = self.hass.states.get(climate_entity)
        if not state:
            return

        current_hvac = state.state
        current_temp = state.attributes.get(ATTR_TEMPERATURE)

        # Set HVAC mode if different
        if current_hvac != target_hvac:
            _LOGGER.debug(
                "Setting HVAC mode for %s in %s to %s",
                climate_entity,
                self.room_manager.room_name,
                target_hvac,
            )
            try:
                await self.hass.services.async_call(
                    CLIMATE_DOMAIN,
                    SERVICE_SET_HVAC_MODE,
                    {
                        "entity_id": climate_entity,
                        ATTR_HVAC_MODE: target_hvac,
                    },
                    blocking=True,
                )
                self._current_hvac_mode = target_hvac
            except Exception as err:
                _LOGGER.error(
                    "Error setting HVAC mode for %s: %s",
                    climate_entity,
                    err,
                )
                return

        # Set temperature if needed and different
        if target_temp is not None:
            if current_temp is None or abs(current_temp - target_temp) >= 0.5:
                _LOGGER.debug(
                    "Setting temperature for %s in %s to %.1f°C",
                    climate_entity,
                    self.room_manager.room_name,
                    target_temp,
                )
                try:
                    await self.hass.services.async_call(
                        CLIMATE_DOMAIN,
                        SERVICE_SET_TEMPERATURE,
                        {
                            "entity_id": climate_entity,
                            ATTR_TEMPERATURE: target_temp,
                        },
                        blocking=True,
                    )
                    self._target_temperature = target_temp
                except Exception as err:
                    _LOGGER.error(
                        "Error setting temperature for %s: %s",
                        climate_entity,
                        err,
                    )

    async def _set_frost_protection(self, climate_entity: str) -> None:
        """Set frost protection when windows open."""
        try:
            if self._climate_type == CLIMATE_TYPE_X4FP:
                await self.hass.services.async_call(
                    CLIMATE_DOMAIN,
                    SERVICE_SET_PRESET_MODE,
                    {
                        "entity_id": climate_entity,
                        ATTR_PRESET_MODE: X4FP_PRESET_AWAY,
                    },
                    blocking=True,
                )
            else:
                await self.hass.services.async_call(
                    CLIMATE_DOMAIN,
                    SERVICE_SET_TEMPERATURE,
                    {
                        "entity_id": climate_entity,
                        ATTR_TEMPERATURE: DEFAULT_TEMP_FROST_PROTECTION,
                    },
                    blocking=True,
                )
        except Exception as err:
            _LOGGER.error(
                "Error setting frost protection for %s: %s",
                climate_entity,
                err,
            )

    def _get_x4fp_preset(self, mode: str) -> str:
        """Map mode to X4FP preset."""
        if mode == MODE_FROST_PROTECTION:
            return X4FP_PRESET_AWAY
        elif mode == MODE_COMFORT:
            return X4FP_PRESET_COMFORT
        else:  # eco, night
            return X4FP_PRESET_ECO

    def _get_target_temperature(self, mode: str) -> float:
        """Get target temperature based on mode."""
        if mode == MODE_FROST_PROTECTION:
            return self.room_config.get(
                CONF_TEMP_FROST_PROTECTION, DEFAULT_TEMP_FROST_PROTECTION
            )
        elif mode == MODE_NIGHT:
            return self.room_config.get(CONF_TEMP_NIGHT, DEFAULT_TEMP_NIGHT)
        elif mode == MODE_COMFORT:
            return self.room_config.get(CONF_TEMP_COMFORT, DEFAULT_TEMP_COMFORT)
        else:  # MODE_ECO
            return self.room_config.get(CONF_TEMP_ECO, DEFAULT_TEMP_ECO)

    def get_state(self) -> dict[str, Any]:
        """Get current climate controller state."""
        return {
            "climate_type": self._climate_type,
            "target_temperature": self._target_temperature,
            "current_preset": self._current_preset,
            "current_hvac_mode": self._current_hvac_mode,
        }

    async def async_shutdown(self) -> None:
        """Shutdown climate controller."""
        pass
