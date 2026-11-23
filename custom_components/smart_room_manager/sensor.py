"""Sensor platform for Smart Room Manager."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_CLIMATE_STATE  # v0.3.0 debug sensors
from .const import (
    ATTR_CURRENT_MODE,
    ATTR_CURRENT_PRIORITY,
    ATTR_HUMIDITY,
    ATTR_HYSTERESIS_STATE,
    ATTR_LIGHT_STATE,
    ATTR_LUMINOSITY,
    ATTR_OCCUPIED,
    ATTR_ROOM_ID,
    ATTR_ROOM_NAME,
    ATTR_TARGET_TEMPERATURE,
    ATTR_TEMPERATURE,
    ATTR_WINDOWS_OPEN,
    DOMAIN,
    HYSTERESIS_DEADBAND,
    PRIORITY_NORMAL,
)
from .coordinator import SmartRoomCoordinator
from .entity import SmartRoomEntity

_LOGGER = logging.getLogger(__name__)

PAUSE_REASON_MANUAL_OVERRIDE = "manual_override"


def _manual_override_text(room_data: dict[str, Any]) -> str:
    """Description of a manual-change period (v0.3.9)."""
    until = room_data.get("manual_override_until")
    if until:
        try:
            return f"Réglage manuel respecté jusqu'à {str(until)[11:16]}"
        except (TypeError, IndexError):
            pass
    return "Réglage manuel respecté"


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
        entities.append(
            SmartRoomCurrentPrioritySensor(coordinator, room_manager.room_id)
        )
        entities.append(SmartRoomHysteresisSensor(coordinator, room_manager.room_id))
        # v0.3.3 activity log sensor
        entities.append(SmartRoomActivitySensor(coordinator, room_manager.room_id))

    # v0.3.9: integration-level anomalies sensor
    entities.append(SmartRoomAnomaliesSensor(coordinator, config_entry.entry_id))

    async_add_entities(entities)


class SmartRoomAnomaliesSensor(CoordinatorEntity, SensorEntity):
    """Number of configuration anomalies found by the diagnostics (v0.3.9)."""

    _attr_has_entity_name = True
    _attr_name = "Anomalies"
    _attr_icon = "mdi:alert-circle-check-outline"

    def __init__(self, coordinator: SmartRoomCoordinator, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_anomalies"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry_id)}}

    @property
    def native_value(self) -> int:
        """Return the number of anomalies."""
        return len(getattr(self.coordinator, "anomalies", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the anomalies list."""
        return {"anomalies": list(getattr(self.coordinator, "anomalies", []))}

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


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
                climate_state.get(ATTR_CURRENT_PRIORITY, PRIORITY_NORMAL),
                room_data,
            ),
            "external_control_active": climate_state.get(
                "external_control_active", False
            ),
            "pause_active": room_data.get("pause_active", False),
            "pause_reason": room_data.get("pause_reason"),
            "manual_override_until": room_data.get("manual_override_until"),
            "schedule_active": room_data.get("schedule_active", False),
        }

    def _get_priority_description(
        self, priority: str, room_data: dict[str, Any] | None = None
    ) -> str:
        """Get human-readable description of priority."""
        # v0.3.9: a manual change is not the pause switch
        if priority == "paused" and room_data and (
            room_data.get("pause_reason") == PAUSE_REASON_MANUAL_OVERRIDE
        ):
            return _manual_override_text(room_data)
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
    """Sensor showing hysteresis state for Fil Pilote Type 3b (v0.3.0 debug)."""

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


class SmartRoomActivitySensor(SmartRoomEntity, SensorEntity):
    """Sensor showing human-readable activity log (v0.3.3)."""

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, room_id)

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} Activité"
            self._attr_unique_id = f"smart_room_{room_id}_activity"
            self._attr_icon = "mdi:clipboard-text"

    @property
    def native_value(self) -> str | None:
        """Return a short summary of current activity."""
        if not self.coordinator.data or self._room_id not in self.coordinator.data:
            return "Inactif"

        room_data = self.coordinator.data[self._room_id]

        if not room_data.get("automation_enabled"):
            return "Automation désactivée"

        if room_data.get("pause_reason") == "manual_override":
            return "Réglage manuel"
        if room_data.get("pause_active"):
            return "En pause"

        climate_state = room_data.get("climate_state", {})
        priority = climate_state.get(ATTR_CURRENT_PRIORITY, PRIORITY_NORMAL)

        priority_labels = {
            "paused": "En pause",
            "bypass": "Mode manuel",
            "windows_open": "Fenêtres ouvertes",
            "external_control": "Contrôle externe",
            "away": "Absent",
            "schedule": "Selon planning",
            "normal": room_data.get("current_mode", "Normal"),
        }
        return priority_labels.get(priority, priority)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed activity log."""
        if not self.coordinator.data or self._room_id not in self.coordinator.data:
            return {"log": "Pas de données"}

        room_data = self.coordinator.data[self._room_id]
        climate_state = room_data.get("climate_state", {})

        # Build human-readable log
        log_lines = []

        # Room info
        room_name = room_data.get("room_name", "?")
        room_type = room_data.get("room_type", "normal")
        log_lines.append(f"Pièce: {room_name} ({room_type})")

        # Automation status
        if not room_data.get("automation_enabled"):
            log_lines.append("⛔ Automation désactivée")
            return {"log": "\n".join(log_lines)}

        if room_data.get("pause_active"):
            if room_data.get("pause_reason") == PAUSE_REASON_MANUAL_OVERRIDE:
                log_lines.append("✋ " + _manual_override_text(room_data))
            else:
                log_lines.append("⏸️ Pause manuelle active")
            return {"log": "\n".join(log_lines)}

        # Current mode and why
        mode = room_data.get("current_mode", "?")
        priority = climate_state.get(ATTR_CURRENT_PRIORITY, PRIORITY_NORMAL)

        mode_labels = {
            "comfort": "Confort",
            "eco": "Éco",
            "night": "Nuit",
            "frost_protection": "Hors-gel",
        }
        mode_label = mode_labels.get(mode, mode)

        # Explain why this mode
        if priority == "away":
            log_lines.append(f"🏠 Mode: {mode_label} (alarme armée)")
        elif priority == "windows_open":
            log_lines.append("🪟 Mode: Hors-gel (fenêtres ouvertes)")
        elif priority == "external_control":
            log_lines.append("🌞 Mode: Contrôle externe actif")
        elif priority == "bypass":
            log_lines.append("🔌 Mode: Manuel (bypass ON)")
        elif priority == "schedule":
            log_lines.append(f"📅 Mode: {mode_label} (selon planning)")
        else:
            log_lines.append(f"🏠 Mode: {mode_label}")

        # Climate details
        climate_type = climate_state.get("climate_type")
        if climate_type:
            # Handle both old "x4fp" and new "fil_pilote" values
            if climate_type in ("x4fp", "fil_pilote"):
                preset = climate_state.get("current_preset", "?")
                log_lines.append(f"🔥 Fil Pilote: preset {preset}")
            else:
                temp = climate_state.get("target_temperature")
                if temp:
                    log_lines.append(f"🌡️ Thermostat: consigne {temp}°C")

        # Hysteresis info if applicable
        hyst_state = climate_state.get(ATTR_HYSTERESIS_STATE)
        if hyst_state and hyst_state != HYSTERESIS_DEADBAND:
            if hyst_state == "heating":
                log_lines.append("📈 Hystérésis: chauffe")
            elif hyst_state == "idle":
                log_lines.append("📉 Hystérésis: repos")

        # Windows state
        if room_data.get("windows_open"):
            log_lines.append("🪟 Fenêtres: ouvertes")

        # Light state for bathroom
        if room_type == "bathroom" and room_data.get("light_on"):
            log_lines.append("💡 Lumière: allumée")

        return {
            "log": "\n".join(log_lines),
            "mode": mode,
            "priority": priority,
            "climate_type": climate_type,
            "windows_open": room_data.get("windows_open", False),
            "occupied": room_data.get("occupied", True),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
