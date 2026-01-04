"""Binary sensor platform for Smart Room Manager."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SmartRoomCoordinator
from .entity import SmartRoomEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Room Manager binary sensors."""
    coordinator: SmartRoomCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for room_manager in coordinator.get_all_room_managers():
        entities.extend(
            [
                SmartRoomOccupiedSensor(coordinator, room_manager.room_id),
                SmartRoomLightNeededSensor(coordinator, room_manager.room_id),
                # v0.3.0 debug sensors
                SmartRoomExternalControlActiveSensor(coordinator, room_manager.room_id),
                SmartRoomScheduleActiveSensor(coordinator, room_manager.room_id),
                # v0.3.3 light timer and VMC sensors (only for bathroom)
                SmartRoomLightTimerSensor(coordinator, room_manager.room_id),
                SmartRoomVMCSensor(coordinator, room_manager.room_id),
            ]
        )

    async_add_entities(entities)


class SmartRoomOccupiedSensor(SmartRoomEntity, BinarySensorEntity):
    """Binary sensor for room occupation."""

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, room_id)

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} Occupied"
            self._attr_unique_id = f"smart_room_{room_id}_occupied"
            self._attr_icon = "mdi:account-check"

    @property
    def is_on(self) -> bool | None:
        """Return true if the room is occupied."""
        if self.coordinator.data and self._room_id in self.coordinator.data:
            return self.coordinator.data[self._room_id].get("occupied", False)
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class SmartRoomLightNeededSensor(SmartRoomEntity, BinarySensorEntity):
    """Binary sensor indicating if lights should be on."""

    _attr_device_class = BinarySensorDeviceClass.LIGHT

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, room_id)

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} Light Needed"
            self._attr_unique_id = f"smart_room_{room_id}_light_needed"
            self._attr_icon = "mdi:lightbulb-on"

    @property
    def is_on(self) -> bool | None:
        """Return true if lights should be on."""
        if self.coordinator.data and self._room_id in self.coordinator.data:
            room_data = self.coordinator.data[self._room_id]
            light_state = room_data.get("light_state", {})
            return light_state.get("should_be_on", False)
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class SmartRoomExternalControlActiveSensor(SmartRoomEntity, BinarySensorEntity):
    """Binary sensor indicating if external control is active (v0.3.0 debug)."""

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, room_id)

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} External Control Active"
            self._attr_unique_id = f"smart_room_{room_id}_external_control_active"
            self._attr_icon = "mdi:solar-power"

    @property
    def is_on(self) -> bool | None:
        """Return true if external control is active."""
        if self.coordinator.data and self._room_id in self.coordinator.data:
            room_data = self.coordinator.data[self._room_id]
            climate_state = room_data.get("climate_state", {})
            return climate_state.get("external_control_active", False)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "description": (
                "Contrôle externe actif (Solar Optimizer, tarif dynamique, etc.)"
                if self.is_on
                else "Aucun contrôle externe actif"
            )
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class SmartRoomScheduleActiveSensor(SmartRoomEntity, BinarySensorEntity):
    """Binary sensor indicating if schedule/calendar is active (v0.3.0 debug)."""

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, room_id)

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} Schedule Active"
            self._attr_unique_id = f"smart_room_{room_id}_schedule_active"
            self._attr_icon = "mdi:calendar-clock"

    @property
    def is_on(self) -> bool | None:
        """Return true if schedule is configured and active."""
        if self.coordinator.data and self._room_id in self.coordinator.data:
            room_data = self.coordinator.data[self._room_id]
            return room_data.get("schedule_active", False)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "description": (
                "Planning/calendrier contrôle le chauffage"
                if self.is_on
                else "Pas de calendrier configuré ou actif"
            )
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class SmartRoomLightTimerSensor(SmartRoomEntity, BinarySensorEntity):
    """Binary sensor indicating if light timer is active (v0.3.3)."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, room_id)

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} Timer Lumière"
            self._attr_unique_id = f"smart_room_{room_id}_light_timer"
            self._attr_icon = "mdi:timer-outline"

    @property
    def is_on(self) -> bool | None:
        """Return true if light timer is running."""
        if self.coordinator.data and self._room_id in self.coordinator.data:
            room_data = self.coordinator.data[self._room_id]
            light_state = room_data.get("light_state", {})
            return light_state.get("timer_active", False)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data or self._room_id not in self.coordinator.data:
            return {}

        room_data = self.coordinator.data[self._room_id]
        light_state = room_data.get("light_state", {})

        time_remaining = light_state.get("time_remaining", 0)
        timeout = light_state.get("timeout_seconds", 0)

        attrs = {
            "timeout_seconds": timeout,
            "time_remaining": time_remaining,
        }

        if time_remaining > 0:
            mins = time_remaining // 60
            secs = time_remaining % 60
            attrs["description"] = f"Extinction dans {mins}m {secs}s"
        else:
            attrs["description"] = "Timer inactif"

        return attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class SmartRoomVMCSensor(SmartRoomEntity, BinarySensorEntity):
    """Binary sensor indicating if VMC high speed is active (v0.3.3)."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: SmartRoomCoordinator, room_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, room_id)

        room_manager = coordinator.get_room_manager(room_id)
        if room_manager:
            room_name = room_manager.room_name
            self._attr_name = f"{room_name} VMC Grande Vitesse"
            self._attr_unique_id = f"smart_room_{room_id}_vmc_active"
            self._attr_icon = "mdi:fan"

    @property
    def is_on(self) -> bool | None:
        """Return true if VMC high speed is active."""
        if self.coordinator.data and self._room_id in self.coordinator.data:
            room_data = self.coordinator.data[self._room_id]
            light_state = room_data.get("light_state", {})
            return light_state.get("vmc_active", False)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data or self._room_id not in self.coordinator.data:
            return {}

        room_data = self.coordinator.data[self._room_id]
        light_state = room_data.get("light_state", {})

        vmc_time_remaining = light_state.get("vmc_time_remaining", 0)

        if vmc_time_remaining == -1:
            # VMC active, light still on, no countdown yet
            description = "💨 VMC GV active (lumière allumée)"
        elif vmc_time_remaining > 0:
            mins = vmc_time_remaining // 60
            secs = vmc_time_remaining % 60
            description = f"💨 VMC GV active - arrêt dans {mins}m {secs}s"
        else:
            description = "VMC en vitesse normale"

        return {
            "time_remaining": vmc_time_remaining if vmc_time_remaining >= 0 else None,
            "description": description,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
