"""Thermostat climate controller."""

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
from homeassistant.core import HomeAssistant

from ..const import (
    CONF_TEMP_COMFORT,
    CONF_TEMP_COOL_COMFORT,
    CONF_TEMP_COOL_ECO,
    CONF_TEMP_ECO,
    CONF_TEMP_FROST_PROTECTION,
    CONF_TEMP_NIGHT,
    CONF_THERMOSTAT_CONTROL_MODE,
    DEFAULT_TEMP_COMFORT,
    DEFAULT_TEMP_COOL_COMFORT,
    DEFAULT_TEMP_COOL_ECO,
    DEFAULT_TEMP_ECO,
    DEFAULT_TEMP_FROST_PROTECTION,
    DEFAULT_TEMP_NIGHT,
    DEFAULT_THERMOSTAT_CONTROL_MODE,
    MODE_COMFORT,
    MODE_ECO,
    MODE_FROST_PROTECTION,
    MODE_NIGHT,
    THERMOSTAT_CONTROL_PRESET,
    THERMOSTAT_CONTROL_TEMPERATURE,
)

# Standard thermostat presets (common across many thermostats)
PRESET_AWAY = "away"
PRESET_HOME = "home"
PRESET_COMFORT = "comfort"
PRESET_ECO = "eco"
PRESET_SLEEP = "sleep"
PRESET_BOOST = "boost"

if TYPE_CHECKING:
    from ..room_manager import RoomManager

_LOGGER = logging.getLogger(__name__)


class ThermostatController:
    """Controller for thermostat climate entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        room_config: dict[str, Any],
        room_manager: RoomManager,
    ) -> None:
        """Initialize thermostat controller."""
        self.hass = hass
        self.room_config = room_config
        self.room_manager = room_manager

        self._target_temperature: float | None = None
        self._current_hvac_mode: str | None = None
        self._current_preset: str | None = None

        # Preset support detection
        self._preset_modes: list[str] = []
        self._presets_detected: bool = False

    def _detect_preset_support(self, climate_entity: str) -> None:
        """Detect which presets the thermostat supports."""
        if self._presets_detected:
            return  # Already detected

        state = self.hass.states.get(climate_entity)
        if not state:
            self._preset_modes = []
            self._presets_detected = True
            return

        self._preset_modes = state.attributes.get("preset_modes", []) or []
        self._presets_detected = True

        if self._preset_modes:
            _LOGGER.info(
                "Thermostat %s supports presets: %s",
                climate_entity,
                self._preset_modes,
            )

    def _supports_preset(self, preset: str) -> bool:
        """Check if thermostat supports a specific preset."""
        return preset in self._preset_modes

    def _get_best_preset_for_mode(self, mode: str) -> str | None:
        """Get the best available preset for a given SRM mode.

        Maps SRM modes to thermostat presets with fallbacks:
        - MODE_COMFORT → comfort, home, boost
        - MODE_ECO → eco, home
        - MODE_NIGHT → sleep, eco, home
        - MODE_FROST_PROTECTION → away
        """
        if mode == MODE_FROST_PROTECTION:
            # For frost protection, only "away" makes sense
            if self._supports_preset(PRESET_AWAY):
                return PRESET_AWAY
            return None

        if mode == MODE_COMFORT:
            # Comfort: prefer comfort, then home, then boost
            for preset in [PRESET_COMFORT, PRESET_HOME, PRESET_BOOST]:
                if self._supports_preset(preset):
                    return preset
            return None

        if mode == MODE_ECO:
            # Eco: prefer eco, then home
            for preset in [PRESET_ECO, PRESET_HOME]:
                if self._supports_preset(preset):
                    return preset
            return None

        if mode == MODE_NIGHT:
            # Night: prefer sleep, then eco, then home
            for preset in [PRESET_SLEEP, PRESET_ECO, PRESET_HOME]:
                if self._supports_preset(preset):
                    return preset
            return None

        return None

    async def _set_preset(self, climate_entity: str, preset: str) -> bool:
        """Set thermostat preset if supported. Returns True if preset was set."""
        # Get actual preset from entity state
        state = self.hass.states.get(climate_entity)
        if not state:
            return False

        actual_preset = state.attributes.get(ATTR_PRESET_MODE)
        if actual_preset == preset:
            return True  # Already at target preset

        _LOGGER.debug(
            "Setting thermostat preset for %s in %s to %s",
            climate_entity,
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
            return True
        except Exception as err:
            _LOGGER.error(
                "Error setting preset for %s: %s",
                climate_entity,
                err,
            )
            return False

    async def control(self, climate_entity: str, mode: str, is_summer: bool) -> None:
        """Control thermostat climate entity.

        Control mode depends on CONF_THERMOSTAT_CONTROL_MODE:
        - preset_only: Only switch presets, let thermostat manage temperatures
        - temperature: Control via hvac_mode + temperature (legacy)
        - preset_and_temp: Use both presets and temperature
        """
        # Detect preset support on first call
        self._detect_preset_support(climate_entity)

        # Get control mode from config
        control_mode = self.room_config.get(
            CONF_THERMOSTAT_CONTROL_MODE, DEFAULT_THERMOSTAT_CONTROL_MODE
        )

        _LOGGER.debug(
            "Thermostat control for %s: mode=%s, control_mode=%s, presets=%s",
            self.room_manager.room_name,
            mode,
            control_mode,
            self._preset_modes,
        )

        # Preset-only mode: just switch presets
        if control_mode == THERMOSTAT_CONTROL_PRESET:
            await self._control_preset_only(climate_entity, mode, is_summer)
            return

        # Temperature mode: control via hvac_mode + temperature
        if control_mode == THERMOSTAT_CONTROL_TEMPERATURE:
            await self._control_temperature(climate_entity, mode, is_summer)
            return

        # Both mode: use presets and set temperature
        # First set preset, then adjust temperature
        target_preset = self._get_best_preset_for_mode(mode)
        if target_preset:
            await self._set_preset(climate_entity, target_preset)
        await self._control_temperature(climate_entity, mode, is_summer)

    async def _control_preset_only(
        self, climate_entity: str, mode: str, is_summer: bool
    ) -> None:
        """Control thermostat using presets only.

        The thermostat manages its own temperatures for each preset.
        User configures temperatures in the thermostat app.
        """
        _LOGGER.debug(
            "Using preset_only mode for %s (mode: %s)",
            self.room_manager.room_name,
            mode,
        )

        state = self.hass.states.get(climate_entity)
        if not state:
            return

        hvac_modes = state.attributes.get("hvac_modes", [])

        # In summer with non-reversible thermostat, just turn off
        if is_summer and mode != MODE_FROST_PROTECTION:
            is_reversible = HVACMode.COOL in hvac_modes
            if not is_reversible:
                if state.state != HVACMode.OFF:
                    await self._set_hvac_mode(climate_entity, HVACMode.OFF)
                return

        # Find the best preset for this mode
        target_preset = self._get_best_preset_for_mode(mode)

        _LOGGER.debug(
            "Preset_only for %s: mode=%s -> target_preset=%s",
            self.room_manager.room_name,
            mode,
            target_preset,
        )

        if target_preset:
            # Set the preset (no temperature change!)
            await self._set_preset(climate_entity, target_preset)

            # Ensure thermostat is ON (not OFF)
            if state.state == HVACMode.OFF:
                # Turn on - prefer HEAT in winter, COOL in summer
                if is_summer and HVACMode.COOL in hvac_modes:
                    await self._set_hvac_mode(climate_entity, HVACMode.COOL)
                elif HVACMode.HEAT in hvac_modes:
                    await self._set_hvac_mode(climate_entity, HVACMode.HEAT)
                elif HVACMode.HEAT_COOL in hvac_modes:
                    await self._set_hvac_mode(climate_entity, HVACMode.HEAT_COOL)
        else:
            # No suitable preset found, fallback to hvac_mode control
            _LOGGER.debug(
                "No preset found for mode %s in %s, using hvac_mode fallback",
                mode,
                self.room_manager.room_name,
            )
            if mode == MODE_FROST_PROTECTION:
                # Turn off or set very low temperature
                await self._set_hvac_mode(climate_entity, HVACMode.OFF)
            elif is_summer:
                if HVACMode.COOL in hvac_modes:
                    await self._set_hvac_mode(climate_entity, HVACMode.COOL)
                else:
                    await self._set_hvac_mode(climate_entity, HVACMode.OFF)
            else:
                if HVACMode.HEAT in hvac_modes:
                    await self._set_hvac_mode(climate_entity, HVACMode.HEAT)
                elif HVACMode.HEAT_COOL in hvac_modes:
                    await self._set_hvac_mode(climate_entity, HVACMode.HEAT_COOL)

    async def _control_temperature(
        self, climate_entity: str, mode: str, is_summer: bool
    ) -> None:
        """Control thermostat via hvac_mode + temperature (legacy mode)."""
        state = self.hass.states.get(climate_entity)
        if not state:
            return

        hvac_modes = state.attributes.get("hvac_modes", [])
        is_reversible = HVACMode.COOL in hvac_modes

        if is_summer:
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
                    target_hvac = HVACMode.OFF
                    target_temp = None
            else:  # eco, night
                if is_reversible:
                    target_hvac = HVACMode.COOL
                    target_temp = self.room_config.get(
                        CONF_TEMP_COOL_ECO, DEFAULT_TEMP_COOL_ECO
                    )
                else:
                    target_hvac = HVACMode.OFF
                    target_temp = None
        else:
            # Winter mode
            target_hvac = HVACMode.HEAT
            target_temp = self._get_target_temperature(mode)

        current_hvac = state.state
        current_temp = state.attributes.get(ATTR_TEMPERATURE)

        # Set HVAC mode if different
        if current_hvac != target_hvac:
            await self._set_hvac_mode(climate_entity, target_hvac)

        # Set temperature if needed
        if target_temp is not None:
            if current_temp is None or abs(current_temp - target_temp) >= 0.5:
                await self._set_temperature(climate_entity, target_temp)

    async def _set_hvac_mode(self, climate_entity: str, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        _LOGGER.debug(
            "Setting HVAC mode for %s in %s to %s",
            climate_entity,
            self.room_manager.room_name,
            hvac_mode,
        )
        try:
            await self.hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_HVAC_MODE,
                {
                    "entity_id": climate_entity,
                    ATTR_HVAC_MODE: hvac_mode,
                },
                blocking=True,
            )
            self._current_hvac_mode = hvac_mode
        except Exception as err:
            _LOGGER.error(
                "Error setting HVAC mode for %s: %s",
                climate_entity,
                err,
            )

    async def _set_temperature(self, climate_entity: str, temperature: float) -> None:
        """Set target temperature."""
        _LOGGER.debug(
            "Setting temperature for %s in %s to %.1f°C",
            climate_entity,
            self.room_manager.room_name,
            temperature,
        )
        try:
            await self.hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_TEMPERATURE,
                {
                    "entity_id": climate_entity,
                    ATTR_TEMPERATURE: temperature,
                },
                blocking=True,
            )
            self._target_temperature = temperature
        except Exception as err:
            _LOGGER.error(
                "Error setting temperature for %s: %s",
                climate_entity,
                err,
            )

    async def set_frost_protection(
        self, climate_entity: str, reason: str = "window"
    ) -> None:
        """Set frost protection temperature and preset if supported.

        Args:
            climate_entity: The climate entity to control
            reason: "window" for windows open, "away" for away mode
        """
        # Detect preset support on first call
        self._detect_preset_support(climate_entity)

        # Get control mode
        control_mode = self.room_config.get(
            CONF_THERMOSTAT_CONTROL_MODE, DEFAULT_THERMOSTAT_CONTROL_MODE
        )

        # If thermostat supports "away" preset, set it
        if self._supports_preset(PRESET_AWAY):
            await self._set_preset(climate_entity, PRESET_AWAY)

            # In preset_only mode, just set the preset and we're done
            if control_mode == THERMOSTAT_CONTROL_PRESET:
                _LOGGER.debug(
                    "Setting thermostat frost protection for %s using 'away' preset (reason: %s)",
                    self.room_manager.room_name,
                    reason,
                )
                return

        # Get configured frost protection temperature
        frost_temp = self.room_config.get(
            CONF_TEMP_FROST_PROTECTION, DEFAULT_TEMP_FROST_PROTECTION
        )

        _LOGGER.debug(
            "Setting thermostat frost protection for %s to %.1f°C (reason: %s)",
            self.room_manager.room_name,
            frost_temp,
            reason,
        )

        # Set frost protection temperature
        await self._set_temperature(climate_entity, frost_temp)

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
        """Get current controller state."""
        control_mode = self.room_config.get(
            CONF_THERMOSTAT_CONTROL_MODE, DEFAULT_THERMOSTAT_CONTROL_MODE
        )
        return {
            "control_mode": control_mode,
            "target_temperature": self._target_temperature,
            "current_hvac_mode": self._current_hvac_mode,
            "current_preset": self._current_preset,
            "available_presets": self._preset_modes,
        }
