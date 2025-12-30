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
    # New v0.3.0 constants
    CONF_EXTERNAL_CONTROL_SWITCH,
    CONF_EXTERNAL_CONTROL_PRESET,
    CONF_EXTERNAL_CONTROL_TEMP,
    CONF_ALLOW_EXTERNAL_IN_AWAY,
    CONF_TEMPERATURE_SENSOR,
    CONF_SETPOINT_INPUT,
    CONF_HYSTERESIS,
    CONF_MIN_SETPOINT,
    CONF_MAX_SETPOINT,
    CONF_PRESET_HEAT,
    CONF_PRESET_IDLE,
    DEFAULT_HYSTERESIS,
    DEFAULT_MIN_SETPOINT,
    DEFAULT_MAX_SETPOINT,
    DEFAULT_PRESET_HEAT,
    DEFAULT_PRESET_IDLE,
    DEFAULT_EXTERNAL_CONTROL_PRESET,
    DEFAULT_EXTERNAL_CONTROL_TEMP,
    DEFAULT_ALLOW_EXTERNAL_IN_AWAY,
    HYSTERESIS_HEATING,
    HYSTERESIS_IDLE,
    HYSTERESIS_DEADBAND,
    PRIORITY_PAUSED,
    PRIORITY_BYPASS,
    PRIORITY_WINDOWS_OPEN,
    PRIORITY_EXTERNAL_CONTROL,
    PRIORITY_AWAY,
    PRIORITY_SCHEDULE,
    PRIORITY_NORMAL,
    ALARM_STATE_ARMED_AWAY,
    CONF_ALARM_ENTITY,
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

        # v0.3.0 state tracking
        self._current_priority: str = PRIORITY_NORMAL
        self._external_control_active: bool = False
        self._hysteresis_state: str = HYSTERESIS_DEADBAND
        self._hysteresis_current_temp: float | None = None
        self._hysteresis_setpoint: float | None = None

    def update_config(self, room_config: dict[str, Any]) -> None:
        """Update configuration."""
        self.room_config = room_config
        # Reset climate type detection on config change
        self._climate_type = None

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
            if self.room_manager.is_windows_open():
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
            # Summer mode - Check if thermostat is reversible (has COOL mode)
            state = self.hass.states.get(climate_entity)
            is_reversible = False
            if state:
                hvac_modes = state.attributes.get("hvac_modes", [])
                is_reversible = HVACMode.COOL in hvac_modes

            if mode == MODE_FROST_PROTECTION:
                target_hvac = HVACMode.OFF
                target_temp = None
            elif mode == MODE_COMFORT:
                if is_reversible:
                    target_hvac = HVACMode.COOL
                    target_temp = self.room_config.get(
                        CONF_TEMP_COOL_COMFORT, DEFAULT_TEMP_COOL_COMFORT
                    )
                else:
                    # Heat-only thermostat in summer comfort → OFF
                    target_hvac = HVACMode.OFF
                    target_temp = None
            else:  # eco, night
                if is_reversible:
                    # Reversible: use COOL with higher temperature (eco cooling)
                    target_hvac = HVACMode.COOL
                    target_temp = self.room_config.get(
                        CONF_TEMP_COOL_ECO, DEFAULT_TEMP_COOL_ECO
                    )
                else:
                    # Heat-only: turn OFF
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
            if self._current_preset == preset:
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
                self._current_preset = preset
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
                        self._target_temperature = target_temp
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

    async def _apply_mode(
        self, climate_entity: str, mode: str, is_summer: bool
    ) -> None:
        """Unified method to apply a mode (normal or schedule)."""
        if self._climate_type == CLIMATE_TYPE_X4FP:
            # Check if hysteresis control is configured
            if self._has_hysteresis_control():
                await self._control_x4fp_with_hysteresis(
                    climate_entity, mode, is_summer
                )
            else:
                await self._control_x4fp(climate_entity, mode, is_summer)
        else:
            await self._control_thermostat(climate_entity, mode, is_summer)

    def _has_hysteresis_control(self) -> bool:
        """Check if X4FP has temperature sensor and setpoint configured."""
        temp_sensor = self.room_config.get(CONF_TEMPERATURE_SENSOR)
        setpoint_input = self.room_config.get(CONF_SETPOINT_INPUT)
        return temp_sensor is not None and setpoint_input is not None

    async def _control_x4fp_with_hysteresis(
        self, climate_entity: str, mode: str, is_summer: bool
    ) -> None:
        """Control X4FP with temperature hysteresis (Type 3b)."""
        if is_summer:
            # Summer: turn off (or eco depending on policy - for now OFF)
            target_preset = X4FP_PRESET_OFF
            self._hysteresis_state = HYSTERESIS_DEADBAND
        else:
            # Winter: use hysteresis control
            # Get current temperature
            temp_sensor = self.room_config.get(CONF_TEMPERATURE_SENSOR)
            temp_state = self.hass.states.get(temp_sensor)
            if not temp_state:
                _LOGGER.warning(
                    "Temperature sensor %s not found for %s",
                    temp_sensor,
                    self.room_manager.room_name,
                )
                # Fallback to preset-only control
                await self._control_x4fp(climate_entity, mode, is_summer)
                return

            try:
                current_temp = float(temp_state.state)
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Invalid temperature value from %s: %s",
                    temp_sensor,
                    temp_state.state,
                )
                await self._control_x4fp(climate_entity, mode, is_summer)
                return

            # Get setpoint
            setpoint_input = self.room_config.get(CONF_SETPOINT_INPUT)
            setpoint_state = self.hass.states.get(setpoint_input)
            if not setpoint_state:
                _LOGGER.warning(
                    "Setpoint input %s not found for %s",
                    setpoint_input,
                    self.room_manager.room_name,
                )
                await self._control_x4fp(climate_entity, mode, is_summer)
                return

            try:
                setpoint = float(setpoint_state.state)
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Invalid setpoint value from %s: %s",
                    setpoint_input,
                    setpoint_state.state,
                )
                await self._control_x4fp(climate_entity, mode, is_summer)
                return

            # Clamp setpoint to min/max
            min_setpoint = self.room_config.get(
                CONF_MIN_SETPOINT, DEFAULT_MIN_SETPOINT
            )
            max_setpoint = self.room_config.get(
                CONF_MAX_SETPOINT, DEFAULT_MAX_SETPOINT
            )
            setpoint = max(min_setpoint, min(max_setpoint, setpoint))

            # Get hysteresis
            hysteresis = self.room_config.get(CONF_HYSTERESIS, DEFAULT_HYSTERESIS)

            # Store for debug sensor
            self._hysteresis_current_temp = current_temp
            self._hysteresis_setpoint = setpoint

            # Calculate hysteresis
            if current_temp <= setpoint - hysteresis:
                # Too cold - heat
                target_preset = self.room_config.get(
                    CONF_PRESET_HEAT, DEFAULT_PRESET_HEAT
                )
                self._hysteresis_state = HYSTERESIS_HEATING
            elif current_temp >= setpoint + hysteresis:
                # Too hot - idle
                target_preset = self.room_config.get(
                    CONF_PRESET_IDLE, DEFAULT_PRESET_IDLE
                )
                self._hysteresis_state = HYSTERESIS_IDLE
            else:
                # In deadband - keep current preset
                self._hysteresis_state = HYSTERESIS_DEADBAND
                return

        # Apply preset
        if self._current_preset == target_preset:
            return

        _LOGGER.debug(
            "Setting X4FP hysteresis preset for %s to %s (temp: %.1f°C, setpoint: %.1f°C, state: %s)",
            self.room_manager.room_name,
            target_preset,
            self._hysteresis_current_temp or 0,
            self._hysteresis_setpoint or 0,
            self._hysteresis_state,
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
                "Error setting hysteresis preset for %s: %s",
                climate_entity,
                err,
            )

    def get_state(self) -> dict[str, Any]:
        """Get current climate controller state."""
        state = {
            "climate_type": self._climate_type,
            "target_temperature": self._target_temperature,
            "current_preset": self._current_preset,
            "current_hvac_mode": self._current_hvac_mode,
            # v0.3.0 debug info
            "current_priority": self._current_priority,
            "external_control_active": self._external_control_active,
            "hysteresis_state": self._hysteresis_state,
        }

        # Add hysteresis details if active
        if self._hysteresis_current_temp is not None:
            state["hysteresis_current_temp"] = self._hysteresis_current_temp
            state["hysteresis_setpoint"] = self._hysteresis_setpoint
            hysteresis = self.room_config.get(CONF_HYSTERESIS, DEFAULT_HYSTERESIS)
            state["hysteresis_value"] = hysteresis
            state["hysteresis_lower_threshold"] = self._hysteresis_setpoint - hysteresis if self._hysteresis_setpoint else None
            state["hysteresis_upper_threshold"] = self._hysteresis_setpoint + hysteresis if self._hysteresis_setpoint else None

        return state

    async def async_shutdown(self) -> None:
        """Shutdown climate controller."""
        pass
