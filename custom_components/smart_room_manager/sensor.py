"""Sensor platform for Smart Room Manager."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_CLIMATE_STATE,
    ATTR_CURRENT_MODE,
    ATTR_HUMIDITY,
    ATTR_LIGHT_STATE,
    ATTR_LUMINOSITY,
    ATTR_OCCUPIED,
    ATTR_ROOM_ID,
    ATTR_ROOM_NAME,
    ATTR_TARGET_TEMPERATURE,
    ATTR_TEMPERATURE,
    ATTR_WINDOWS_OPEN,
    DOMAIN,
    # v0.3.0 debug sensors
    ATTR_CURRENT_PRIORITY,
    ATTR_HYSTERESIS_STATE,
    PRIORITY_NORMAL,
    HYSTERESIS_DEADBAND,
)
from .coordinator import SmartRoomCoordinator
from .entity import SmartRoomEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Room Manager sensors."""
    coordinator: SmartRoomCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for room_manager in coordinator.get_all_room_managers():
        entities.append(SmartRoomStateSensor(coordinator, room_manager.room_id))
        # v0.3.0 debug sensors
        entities.append(SmartRoomCurrentPrioritySensor(coordinator, room_manager.room_id))
        entities.append(SmartRoomHysteresisSensor(coordinator, room_manager.room_id))

    async_add_entities(entities)


class SmartRoomStateSensor(SmartRoomEntity, SensorEntity):
    """Sensor representing the state of a smart room."""

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, room_id)

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} State"
            self._attr_unique_id = f"smart_room_{room_id}_state"
            self._attr_icon = "mdi:home-automation"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self.coordinator.data and self._room_id in self.coordinator.data:
            room_data = self.coordinator.data[self._room_id]
            return room_data.get("current_mode", "unknown")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data or self._room_id not in self.coordinator.data:
            return {}

        room_data = self.coordinator.data[self._room_id]

        attributes = {
            ATTR_ROOM_ID: room_data.get("room_id"),
            ATTR_ROOM_NAME: room_data.get("room_name"),
            ATTR_OCCUPIED: room_data.get("occupied"),
            ATTR_WINDOWS_OPEN: room_data.get("windows_open"),
            ATTR_CURRENT_MODE: room_data.get("current_mode"),
            "time_period": room_data.get("time_period"),
            "automation_enabled": room_data.get("automation_enabled"),
        }

        # Add sensor values if available
        if room_data.get("luminosity") is not None:
            attributes[ATTR_LUMINOSITY] = room_data.get("luminosity")

        if room_data.get("temperature") is not None:
            attributes[ATTR_TEMPERATURE] = room_data.get("temperature")

        if room_data.get("humidity") is not None:
            attributes[ATTR_HUMIDITY] = room_data.get("humidity")

        # Add light state
        light_state = room_data.get("light_state", {})
        attributes[ATTR_LIGHT_STATE] = {
            "should_be_on": light_state.get("should_be_on"),
            "brightness_percentage": light_state.get("brightness_percentage"),
        }

        # Add climate state
        climate_state = room_data.get("climate_state", {})
        attributes[ATTR_CLIMATE_STATE] = {
            "target_temperature": climate_state.get("target_temperature"),
            "heating_active": climate_state.get("heating_active"),
        }

        if climate_state.get("target_temperature") is not None:
            attributes[ATTR_TARGET_TEMPERATURE] = climate_state.get(
                "target_temperature"
            )

        return attributes

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class SmartRoomCurrentPrioritySensor(SmartRoomEntity, SensorEntity):
    """Sensor showing current climate control priority (v0.3.0 debug)."""

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, room_id)

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} Current Priority"
            self._attr_unique_id = f"smart_room_{room_id}_current_priority"
            self._attr_icon = "mdi:priority-high"

    @property
    def native_value(self) -> str | None:
        """Return the current priority."""
        if self.coordinator.data and self._room_id in self.coordinator.data:
            room_data = self.coordinator.data[self._room_id]
            climate_state = room_data.get("climate_state", {})
            return climate_state.get(ATTR_CURRENT_PRIORITY, PRIORITY_NORMAL)
        return PRIORITY_NORMAL

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data or self._room_id not in self.coordinator.data:
            return {}

        room_data = self.coordinator.data[self._room_id]
        climate_state = room_data.get("climate_state", {})

        return {
            "description": self._get_priority_description(
                climate_state.get(ATTR_CURRENT_PRIORITY, PRIORITY_NORMAL)
            ),
            "external_control_active": climate_state.get("external_control_active", False),
            "pause_active": room_data.get("pause_active", False),
            "schedule_active": room_data.get("schedule_active", False),
        }

    def _get_priority_description(self, priority: str) -> str:
        """Get human-readable description of priority."""
        descriptions = {
            "paused": "Pause manuelle active",
            "bypass": "Bypass activé (contrôle externe complet)",
            "windows_open": "Fenêtres ouvertes",
            "external_control": "Contrôle externe (Solar Optimizer, etc.)",
            "away": "Mode absent (alarme)",
            "schedule": "Calendrier/planning actif",
            "normal": "Logique normale",
        }
        return descriptions.get(priority, priority)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class SmartRoomHysteresisSensor(SmartRoomEntity, SensorEntity):
    """Sensor showing hysteresis state for X4FP Type 3b (v0.3.0 debug)."""

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, room_id)

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} Hysteresis State"
            self._attr_unique_id = f"smart_room_{room_id}_hysteresis_state"
            self._attr_icon = "mdi:thermometer-lines"

    @property
    def native_value(self) -> str | None:
        """Return the hysteresis state."""
        if self.coordinator.data and self._room_id in self.coordinator.data:
            room_data = self.coordinator.data[self._room_id]
            climate_state = room_data.get("climate_state", {})
            return climate_state.get(ATTR_HYSTERESIS_STATE, HYSTERESIS_DEADBAND)
        return HYSTERESIS_DEADBAND

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data or self._room_id not in self.coordinator.data:
            return {}

        room_data = self.coordinator.data[self._room_id]
        climate_state = room_data.get("climate_state", {})

        attrs = {
            "description": self._get_hysteresis_description(
                climate_state.get(ATTR_HYSTERESIS_STATE, HYSTERESIS_DEADBAND)
            ),
        }

        # Add temperature details if available
        if climate_state.get("hysteresis_current_temp") is not None:
            attrs["current_temp"] = climate_state.get("hysteresis_current_temp")
            attrs["setpoint"] = climate_state.get("hysteresis_setpoint")
            attrs["hysteresis_value"] = climate_state.get("hysteresis_value")
            attrs["lower_threshold"] = climate_state.get("hysteresis_lower_threshold")
            attrs["upper_threshold"] = climate_state.get("hysteresis_upper_threshold")

        return attrs

    def _get_hysteresis_description(self, state: str) -> str:
        """Get human-readable description of hysteresis state."""
        descriptions = {
            "heating": "Chauffage actif (température < consigne - hystérésis)",
            "idle": "Repos (température > consigne + hystérésis)",
            "deadband": "Zone morte (maintien preset actuel)",
        }
        return descriptions.get(state, state)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
