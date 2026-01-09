"""Fil Pilote climate controller."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.climate import ATTR_PRESET_MODE
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.climate import SERVICE_SET_PRESET_MODE
from homeassistant.core import HomeAssistant

from ..const import (
    CONF_HYSTERESIS,
    CONF_MAX_SETPOINT,
    CONF_MIN_SETPOINT,
    CONF_PRESET_AWAY,
    CONF_PRESET_COMFORT,
    CONF_PRESET_ECO,
    CONF_PRESET_HEAT,
    CONF_PRESET_IDLE,
    CONF_PRESET_NIGHT,
    CONF_PRESET_WINDOW,
    CONF_SETPOINT_INPUT,
    CONF_SUMMER_POLICY,
    CONF_TEMP_COMFORT,
    CONF_TEMP_ECO,
    CONF_TEMP_NIGHT,
    CONF_TEMPERATURE_SENSOR,
    DEFAULT_HYSTERESIS,
    DEFAULT_MAX_SETPOINT,
    DEFAULT_MIN_SETPOINT,
    DEFAULT_PRESET_AWAY,
    DEFAULT_PRESET_COMFORT,
    DEFAULT_PRESET_ECO,
    DEFAULT_PRESET_HEAT,
    DEFAULT_PRESET_IDLE,
    DEFAULT_PRESET_NIGHT,
    DEFAULT_PRESET_WINDOW,
    DEFAULT_SUMMER_POLICY,
    DEFAULT_TEMP_COMFORT,
    DEFAULT_TEMP_ECO,
    DEFAULT_TEMP_NIGHT,
    FP_PRESET_AWAY,
    FP_PRESET_ECO,
    FP_PRESET_OFF,
    HYSTERESIS_DEADBAND,
    HYSTERESIS_HEATING,
    HYSTERESIS_IDLE,
    MODE_COMFORT,
    MODE_ECO,
    MODE_FROST_PROTECTION,
    MODE_NIGHT,
)

if TYPE_CHECKING:
    from ..room_manager import RoomManager

_LOGGER = logging.getLogger(__name__)


class FilPiloteController:
    """Controller for Fil Pilote climate entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        room_config: dict[str, Any],
        room_manager: RoomManager,
    ) -> None:
        """Initialize Fil Pilote controller."""
        self.hass = hass
        self.room_config = room_config
        self.room_manager = room_manager

        self._current_preset: str | None = None
        self._hysteresis_state: str = HYSTERESIS_DEADBAND
        self._hysteresis_current_temp: float | None = None
        self._hysteresis_setpoint: float | None = None

    async def control(self, climate_entity: str, mode: str, is_summer: bool) -> None:
        """Control Fil Pilote climate entity via preset_mode."""
        # Check if hysteresis control is configured
        if self._has_hysteresis_control():
            await self._control_with_hysteresis(climate_entity, mode, is_summer)
        else:
            await self._control_normal(climate_entity, mode, is_summer)

    async def _control_normal(
        self, climate_entity: str, mode: str, is_summer: bool
    ) -> None:
        """Control Fil Pilote without hysteresis (preset-based)."""
        # Summer: apply summer policy (off or eco)
        if is_summer:
            if mode != MODE_FROST_PROTECTION:
                # Use configured summer policy
                summer_policy = self.room_config.get(
                    CONF_SUMMER_POLICY, DEFAULT_SUMMER_POLICY
                )
                if summer_policy == "eco":
                    target_preset = FP_PRESET_ECO
                else:  # "off"
                    target_preset = FP_PRESET_OFF
            else:
                # Frost protection always uses away
                target_preset = FP_PRESET_AWAY
        else:
            # Winter: map mode to preset
            target_preset = self._get_preset_for_mode(mode)

        # Get actual preset from entity state (not just internal tracking)
        # This handles cases where preset was changed externally or after HA restart
        state = self.hass.states.get(climate_entity)
        actual_preset = None
        if state:
            actual_preset = state.attributes.get(ATTR_PRESET_MODE)
            # Sync internal state with actual state
            if actual_preset and self._current_preset != actual_preset:
                _LOGGER.debug(
                    "Fil Pilote preset sync: internal=%s, actual=%s for %s",
                    self._current_preset,
                    actual_preset,
                    self.room_manager.room_name,
                )
                self._current_preset = actual_preset

        # Only change if different from actual state
        if actual_preset == target_preset:
            return

        _LOGGER.debug(
            "Setting Fil Pilote preset for %s in %s to %s (mode: %s, summer: %s)",
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

    async def _control_with_hysteresis(
        self, climate_entity: str, mode: str, is_summer: bool
    ) -> None:
        """Control Fil Pilote with temperature hysteresis.

        Uses hysteresis to prevent rapid switching between presets.
        The temperature sensor provides feedback to stop heating at the right temp.

        Setpoint source (in order of priority):
        1. setpoint_input (input_number) if configured - for dynamic setpoint control
        2. Configured temperatures based on current mode (comfort, eco, night)
        """
        if is_summer:
            # Summer: apply summer policy (off or eco)
            summer_policy = self.room_config.get(
                CONF_SUMMER_POLICY, DEFAULT_SUMMER_POLICY
            )
            if summer_policy == "eco":
                target_preset = FP_PRESET_ECO
            else:  # "off"
                target_preset = FP_PRESET_OFF
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
                await self._control_normal(climate_entity, mode, is_summer)
                return

            try:
                current_temp = float(temp_state.state)
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Invalid temperature value from %s: %s",
                    temp_sensor,
                    temp_state.state,
                )
                await self._control_normal(climate_entity, mode, is_summer)
                return

            # Get setpoint - priority: setpoint_input > mode-based temperature
            setpoint = self._get_setpoint(mode)
            if setpoint is None:
                # No valid setpoint, fallback to preset-only
                await self._control_normal(climate_entity, mode, is_summer)
                return

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

        # Get actual preset from entity state (sync with reality)
        state = self.hass.states.get(climate_entity)
        actual_preset = None
        if state:
            actual_preset = state.attributes.get(ATTR_PRESET_MODE)
            if actual_preset and self._current_preset != actual_preset:
                self._current_preset = actual_preset

        # Apply preset only if different from actual
        if actual_preset == target_preset:
            return

        _LOGGER.debug(
            "Setting Fil Pilote hysteresis preset for %s to %s (temp: %.1f°C, setpoint: %.1f°C, state: %s)",
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

    def _get_setpoint(self, mode: str) -> float | None:
        """Get the setpoint temperature for hysteresis control.

        Priority:
        1. setpoint_input (input_number) if configured
        2. Mode-based temperature (comfort, eco, night)
        """
        # Try setpoint_input first (for dynamic control)
        setpoint_input = self.room_config.get(CONF_SETPOINT_INPUT)
        if setpoint_input:
            setpoint_state = self.hass.states.get(setpoint_input)
            if setpoint_state:
                try:
                    setpoint = float(setpoint_state.state)
                    # Clamp to min/max
                    min_setpoint = self.room_config.get(
                        CONF_MIN_SETPOINT, DEFAULT_MIN_SETPOINT
                    )
                    max_setpoint = self.room_config.get(
                        CONF_MAX_SETPOINT, DEFAULT_MAX_SETPOINT
                    )
                    return max(min_setpoint, min(max_setpoint, setpoint))
                except (ValueError, TypeError):
                    _LOGGER.warning(
                        "Invalid setpoint value from %s: %s",
                        setpoint_input,
                        setpoint_state.state,
                    )
            else:
                _LOGGER.warning(
                    "Setpoint input %s not found for %s",
                    setpoint_input,
                    self.room_manager.room_name,
                )

        # Fall back to mode-based temperature
        if mode == MODE_COMFORT:
            return self.room_config.get(CONF_TEMP_COMFORT, DEFAULT_TEMP_COMFORT)
        elif mode == MODE_NIGHT:
            return self.room_config.get(CONF_TEMP_NIGHT, DEFAULT_TEMP_NIGHT)
        elif mode == MODE_ECO:
            return self.room_config.get(CONF_TEMP_ECO, DEFAULT_TEMP_ECO)
        elif mode == MODE_FROST_PROTECTION:
            # For frost protection, use a low setpoint (don't need hysteresis really)
            return 7.0

        # Unknown mode
        return None

    async def set_frost_protection(
        self, climate_entity: str, reason: str = "window"
    ) -> None:
        """Set frost protection preset.

        Args:
            climate_entity: The climate entity to control
            reason: "window" for windows open, "away" for away mode
        """
        # Use configurable preset based on reason
        if reason == "away":
            target_preset = self.room_config.get(CONF_PRESET_AWAY, DEFAULT_PRESET_AWAY)
        else:  # "window"
            target_preset = self.room_config.get(
                CONF_PRESET_WINDOW, DEFAULT_PRESET_WINDOW
            )

        # Get actual preset from entity state (sync with reality)
        state = self.hass.states.get(climate_entity)
        actual_preset = None
        if state:
            actual_preset = state.attributes.get(ATTR_PRESET_MODE)
            if actual_preset and self._current_preset != actual_preset:
                self._current_preset = actual_preset

        if actual_preset == target_preset:
            return

        _LOGGER.debug(
            "Setting Fil Pilote frost protection for %s to %s (reason: %s)",
            self.room_manager.room_name,
            target_preset,
            reason,
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
                "Error setting frost protection for %s: %s",
                climate_entity,
                err,
            )

    def _get_preset_for_mode(self, mode: str) -> str:
        """Map mode to Fil Pilote preset (configurable per room)."""
        if mode == MODE_FROST_PROTECTION:
            return self.room_config.get(CONF_PRESET_AWAY, DEFAULT_PRESET_AWAY)
        elif mode == MODE_COMFORT:
            return self.room_config.get(CONF_PRESET_COMFORT, DEFAULT_PRESET_COMFORT)
        elif mode == MODE_NIGHT:
            return self.room_config.get(CONF_PRESET_NIGHT, DEFAULT_PRESET_NIGHT)
        else:  # MODE_ECO
            return self.room_config.get(CONF_PRESET_ECO, DEFAULT_PRESET_ECO)

    def _has_hysteresis_control(self) -> bool:
        """Check if hysteresis control is available.

        Hysteresis control requires only a temperature sensor.
        The setpoint can come from:
        - setpoint_input (input_number) if configured
        - Mode-based temperatures (comfort, eco, night) as fallback
        """
        temp_sensor = self.room_config.get(CONF_TEMPERATURE_SENSOR)
        return temp_sensor is not None

    def get_state(self) -> dict[str, Any]:
        """Get current controller state."""
        state = {
            "current_preset": self._current_preset,
            "hysteresis_state": self._hysteresis_state,
        }

        # Add hysteresis details if active
        if self._hysteresis_current_temp is not None:
            state["hysteresis_current_temp"] = self._hysteresis_current_temp
            state["hysteresis_setpoint"] = self._hysteresis_setpoint
            hysteresis = self.room_config.get(CONF_HYSTERESIS, DEFAULT_HYSTERESIS)
            state["hysteresis_value"] = hysteresis
            state["hysteresis_lower_threshold"] = (
                self._hysteresis_setpoint - hysteresis
                if self._hysteresis_setpoint
                else None
            )
            state["hysteresis_upper_threshold"] = (
                self._hysteresis_setpoint + hysteresis
                if self._hysteresis_setpoint
                else None
            )

        return state
