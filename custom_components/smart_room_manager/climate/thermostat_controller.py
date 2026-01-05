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
    DEFAULT_TEMP_COMFORT,
    DEFAULT_TEMP_COOL_COMFORT,
    DEFAULT_TEMP_COOL_ECO,
    DEFAULT_TEMP_ECO,
    DEFAULT_TEMP_FROST_PROTECTION,
    DEFAULT_TEMP_NIGHT,
    MODE_COMFORT,
    MODE_FROST_PROTECTION,
    MODE_NIGHT,
)

# Standard thermostat presets
PRESET_AWAY = "away"
PRESET_HOME = "home"

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
        self._supports_away_preset: bool | None = None
        self._supports_home_preset: bool | None = None

    def _detect_preset_support(self, climate_entity: str) -> None:
        """Detect if thermostat supports away/home presets."""
        if self._supports_away_preset is not None:
            return  # Already detected

        state = self.hass.states.get(climate_entity)
        if not state:
            self._supports_away_preset = False
            self._supports_home_preset = False
            return

        preset_modes = state.attributes.get("preset_modes", [])
        self._supports_away_preset = PRESET_AWAY in preset_modes
        self._supports_home_preset = PRESET_HOME in preset_modes

        if self._supports_away_preset or self._supports_home_preset:
            _LOGGER.info(
                "Thermostat %s preset support: away=%s, home=%s",
                climate_entity,
                self._supports_away_preset,
                self._supports_home_preset,
            )

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
        """Control thermostat climate entity via hvac_mode + temperature."""
        # Detect preset support on first call
        self._detect_preset_support(climate_entity)

        # If thermostat supports "home" preset, ensure it's set when not in frost mode
        if self._supports_home_preset and mode != MODE_FROST_PROTECTION:
            await self._set_preset(climate_entity, PRESET_HOME)

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

        # If thermostat supports "away" preset, set it
        if self._supports_away_preset:
            await self._set_preset(climate_entity, PRESET_AWAY)

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
        try:
            await self.hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_TEMPERATURE,
                {
                    "entity_id": climate_entity,
                    ATTR_TEMPERATURE: frost_temp,
                },
                blocking=True,
            )
            self._target_temperature = frost_temp
        except Exception as err:
            _LOGGER.error(
                "Error setting frost protection for %s: %s",
                climate_entity,
                err,
            )

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
        return {
            "target_temperature": self._target_temperature,
            "current_hvac_mode": self._current_hvac_mode,
            "current_preset": self._current_preset,
            "supports_away_preset": self._supports_away_preset,
            "supports_home_preset": self._supports_home_preset,
        }
