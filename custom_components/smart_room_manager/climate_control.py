"""Climate control logic for Smart Room Manager (Refactored v0.3.0)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ATTR_TEMPERATURE,
)
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.climate import (
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_TEMPERATURE,
    HVACMode,
)
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant

from .climate.thermostat_controller import ThermostatController
from .climate.x4fp_controller import X4FPController
from .const import (
    ALARM_STATE_ARMED_AWAY,
    CLIMATE_TYPE_THERMOSTAT,
    CLIMATE_TYPE_X4FP,
    CONF_ALARM_ENTITY,
    CONF_ALLOW_EXTERNAL_IN_AWAY,
    CONF_CLIMATE_BYPASS_SWITCH,
    CONF_CLIMATE_ENTITY,
    CONF_CLIMATE_WINDOW_CHECK,
    CONF_EXTERNAL_CONTROL_PRESET,
    CONF_EXTERNAL_CONTROL_SWITCH,
    CONF_EXTERNAL_CONTROL_TEMP,
    CONF_SEASON_CALENDAR,
    DEFAULT_ALLOW_EXTERNAL_IN_AWAY,
    DEFAULT_EXTERNAL_CONTROL_PRESET,
    DEFAULT_EXTERNAL_CONTROL_TEMP,
    PRIORITY_AWAY,
    PRIORITY_BYPASS,
    PRIORITY_EXTERNAL_CONTROL,
    PRIORITY_NORMAL,
    PRIORITY_PAUSED,
    PRIORITY_SCHEDULE,
    PRIORITY_WINDOWS_OPEN,
    X4FP_PRESET_COMFORT,
    X4FP_PRESET_ECO,
)

if TYPE_CHECKING:
    from .room_manager import RoomManager

_LOGGER = logging.getLogger(__name__)


class ClimateController:
    """Control climate/heating in a room - Refactored orchestrator."""

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

        # v0.3.0 state tracking
        self._current_priority: str = PRIORITY_NORMAL
        self._external_control_active: bool = False

        # Specialized controllers (lazy loaded)
        self._x4fp_controller: X4FPController | None = None
        self._thermostat_controller: ThermostatController | None = None

    def update_config(self, room_config: dict[str, Any]) -> None:
        """Update configuration."""
        self.room_config = room_config
        # Reset climate type detection on config change
        self._climate_type = None
        self._x4fp_controller = None
        self._thermostat_controller = None

    async def async_update(self) -> None:
        """Update climate control logic with v0.3.0 priority system."""
        climate_entity = self.room_config.get(CONF_CLIMATE_ENTITY)

        if not climate_entity:
            self._current_priority = PRIORITY_NORMAL
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

        # PRIORITY 0.5: Check manual pause
        if self.room_manager.is_paused():
            _LOGGER.debug(
                "⏸️ Manual pause active in %s - skipping automation",
                self.room_manager.room_name,
            )
            self._current_priority = PRIORITY_PAUSED
            return

        # PRIORITY 1: Check bypass switch
        bypass_switch = self.room_config.get(CONF_CLIMATE_BYPASS_SWITCH)
        if bypass_switch:
            bypass_state = self.hass.states.get(bypass_switch)
            if bypass_state and bypass_state.state == STATE_ON:
                _LOGGER.debug(
                    "🔌 Climate bypass active (%s ON) in %s - skipping control",
                    bypass_switch,
                    self.room_manager.room_name,
                )
                self._current_priority = PRIORITY_BYPASS
                return

        # PRIORITY 2: Check windows
        if self.room_config.get(CONF_CLIMATE_WINDOW_CHECK, True):
            if self.room_manager.is_windows_open_delayed():
                _LOGGER.debug(
                    "🪟 Windows open in %s - setting frost protection",
                    self.room_manager.room_name,
                )
                self._current_priority = PRIORITY_WINDOWS_OPEN
                await self._set_frost_protection(climate_entity)
                return

        # PRIORITY 3: Check External Control (Solar Optimizer, etc.)
        if await self._is_external_control_active():
            _LOGGER.debug(
                "🌞 External control active in %s - applying external control",
                self.room_manager.room_name,
            )
            self._current_priority = PRIORITY_EXTERNAL_CONTROL
            await self._apply_external_control(climate_entity)
            return

        # PRIORITY 4: Check away mode (alarm armed_away)
        if self._is_away_mode():
            _LOGGER.debug(
                "🏠 Away mode active in %s - setting frost protection",
                self.room_manager.room_name,
            )
            self._current_priority = PRIORITY_AWAY
            await self._set_frost_protection(climate_entity)
            return

        # PRIORITY 5: Check schedule (calendar)
        schedule_mode = self.room_manager.get_schedule_mode()
        if schedule_mode is not None:
            _LOGGER.debug(
                "📅 Schedule active in %s - mode: %s",
                self.room_manager.room_name,
                schedule_mode,
            )
            self._current_priority = PRIORITY_SCHEDULE
            is_summer = self._is_summer_mode()
            await self._apply_mode(climate_entity, schedule_mode, is_summer)
            return

        # PRIORITY 6: Normal logic
        self._current_priority = PRIORITY_NORMAL
        is_summer = self._is_summer_mode()
        mode = self.room_manager.get_current_mode()

        await self._apply_mode(climate_entity, mode, is_summer)

    def _detect_climate_type(self, climate_entity: str) -> str:
        """Detect if climate entity is X4FP (preset_mode) or thermostat (hvac_mode)."""
        state = self.hass.states.get(climate_entity)
        if not state:
            _LOGGER.warning("Climate entity %s not found", climate_entity)
            return CLIMATE_TYPE_THERMOSTAT

        # Check if entity has X4FP-style preset modes
        preset_modes = state.attributes.get("preset_modes", [])

        # X4FP has "comfort" and/or "eco" preset modes
        if "comfort" in preset_modes or "eco" in preset_modes:
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

    async def _apply_mode(
        self, climate_entity: str, mode: str, is_summer: bool
    ) -> None:
        """Unified method to apply a mode (normal or schedule)."""
        if self._climate_type == CLIMATE_TYPE_X4FP:
            controller = self._get_x4fp_controller()
            await controller.control(climate_entity, mode, is_summer)
        else:
            controller = self._get_thermostat_controller()
            await controller.control(climate_entity, mode, is_summer)

    async def _set_frost_protection(self, climate_entity: str) -> None:
        """Set frost protection when windows open or away."""
        if self._climate_type == CLIMATE_TYPE_X4FP:
            controller = self._get_x4fp_controller()
            await controller.set_frost_protection(climate_entity)
        else:
            controller = self._get_thermostat_controller()
            await controller.set_frost_protection(climate_entity)

    async def _is_external_control_active(self) -> bool:
        """Check if external control (Solar Optimizer, etc.) is active."""
        external_switch = self.room_config.get(CONF_EXTERNAL_CONTROL_SWITCH)
        if not external_switch:
            self._external_control_active = False
            return False

        # Check if entity exists
        state = self.hass.states.get(external_switch)
        if not state:
            self._external_control_active = False
            return False

        # Check is_active attribute (primary) or state ON (fallback)
        is_active = state.attributes.get("is_active", False)
        if not is_active:
            is_active = state.state.lower() == STATE_ON.lower()

        # Check if we should override away mode
        if is_active:
            allow_in_away = self.room_config.get(
                CONF_ALLOW_EXTERNAL_IN_AWAY, DEFAULT_ALLOW_EXTERNAL_IN_AWAY
            )
            if not allow_in_away and self._is_away_mode():
                # External control wants to activate, but away mode blocks it
                self._external_control_active = False
                return False

        self._external_control_active = is_active
        return is_active

    async def _apply_external_control(self, climate_entity: str) -> None:
        """Apply external control preset/temperature."""
        if self._climate_type == CLIMATE_TYPE_X4FP:
            # X4FP: use preset
            preset = self.room_config.get(
                CONF_EXTERNAL_CONTROL_PRESET, DEFAULT_EXTERNAL_CONTROL_PRESET
            )

            controller = self._get_x4fp_controller()
            if controller._current_preset == preset:
                return

            _LOGGER.debug(
                "Setting External Control preset for %s to %s",
                self.room_manager.room_name,
                preset,
            )
            try:
                await self.hass.services.async_call(
                    CLIMATE_DOMAIN,
                    SERVICE_SET_PRESET_MODE,
                    {
                        "entity_id": climate_entity,
                        ATTR_PRESET_MODE: preset,
                    },
                    blocking=True,
                )
                controller._current_preset = preset
            except Exception as err:
                _LOGGER.error(
                    "Error setting external control preset for %s: %s",
                    climate_entity,
                    err,
                )
        else:
            # Thermostat: use temperature
            target_temp = self.room_config.get(
                CONF_EXTERNAL_CONTROL_TEMP, DEFAULT_EXTERNAL_CONTROL_TEMP
            )

            controller = self._get_thermostat_controller()

            # Set to HEAT mode and target temperature
            state = self.hass.states.get(climate_entity)
            if state:
                current_hvac = state.state
                if current_hvac != HVACMode.HEAT:
                    try:
                        await self.hass.services.async_call(
                            CLIMATE_DOMAIN,
                            SERVICE_SET_HVAC_MODE,
                            {
                                "entity_id": climate_entity,
                                ATTR_HVAC_MODE: HVACMode.HEAT,
                            },
                            blocking=True,
                        )
                    except Exception as err:
                        _LOGGER.error(
                            "Error setting HVAC mode for external control %s: %s",
                            climate_entity,
                            err,
                        )
                        return

                current_temp = state.attributes.get(ATTR_TEMPERATURE)
                if current_temp is None or abs(current_temp - target_temp) >= 0.5:
                    _LOGGER.debug(
                        "Setting External Control temperature for %s to %.1f°C",
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
                        controller._target_temperature = target_temp
                    except Exception as err:
                        _LOGGER.error(
                            "Error setting external control temperature for %s: %s",
                            climate_entity,
                            err,
                        )

    def _is_away_mode(self) -> bool:
        """Check if alarm is in armed_away mode."""
        alarm_entity = self.room_manager.coordinator.entry.data.get(CONF_ALARM_ENTITY)
        if not alarm_entity:
            return False

        alarm_state = self.hass.states.get(alarm_entity)
        return alarm_state and alarm_state.state == ALARM_STATE_ARMED_AWAY

    def _get_x4fp_controller(self) -> X4FPController:
        """Get or create X4FP controller (lazy load)."""
        if self._x4fp_controller is None:
            self._x4fp_controller = X4FPController(
                self.hass, self.room_config, self.room_manager
            )
        return self._x4fp_controller

    def _get_thermostat_controller(self) -> ThermostatController:
        """Get or create thermostat controller (lazy load)."""
        if self._thermostat_controller is None:
            self._thermostat_controller = ThermostatController(
                self.hass, self.room_config, self.room_manager
            )
        return self._thermostat_controller

    def get_state(self) -> dict[str, Any]:
        """Get current climate controller state."""
        state = {
            "climate_type": self._climate_type,
            "current_priority": self._current_priority,
            "external_control_active": self._external_control_active,
        }

        # Get state from active controller
        if self._climate_type == CLIMATE_TYPE_X4FP and self._x4fp_controller:
            state.update(self._x4fp_controller.get_state())
        elif (
            self._climate_type == CLIMATE_TYPE_THERMOSTAT
            and self._thermostat_controller
        ):
            state.update(self._thermostat_controller.get_state())

        return state

    async def async_shutdown(self) -> None:
        """Shutdown climate controller."""
        pass
