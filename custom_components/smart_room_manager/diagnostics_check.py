"""Configuration diagnostics for Smart Room Manager (v0.3.9).

Pure logic: reads the state machine and config entries, returns a list of
anomalies. No side effects, so it can be tested without a running integration.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    CLIMATE_MODE_NONE,
    CONF_CLIMATE_BYPASS_SWITCH,
    CONF_CLIMATE_ENTITY,
    CONF_CLIMATE_MODE,
    CONF_DOOR_WINDOW_SENSORS,
    CONF_EXTERNAL_CONTROL_SWITCH,
    CONF_HUMIDITY_SENSOR,
    CONF_LIGHTS,
    CONF_MIN_SETPOINT,
    CONF_ROOM_ID,
    CONF_ROOM_NAME,
    CONF_SCHEDULE_ENTITY,
    CONF_SETPOINT_INPUT,
    CONF_TEMP_ECO,
    CONF_TEMPERATURE_SENSOR,
    DEFAULT_MIN_SETPOINT,
    DEFAULT_TEMP_ECO,
)

# Anomaly codes (also used as translation keys for repair issues)
ISSUE_MISSING_ENTITY = "missing_entity"
ISSUE_UNAVAILABLE_ENTITY = "unavailable_entity"
ISSUE_CLIMATE_WITHOUT_ACTUATOR = "climate_without_actuator"
ISSUE_MULTI_CONTROLLER = "multi_controller"
ISSUE_SETPOINT_BELOW_ECO = "setpoint_below_eco"

UNAVAILABLE_GRACE = timedelta(minutes=10)

# Config keys holding one entity_id, or a list of entity_ids
_SINGLE_KEYS = [
    CONF_CLIMATE_ENTITY,
    CONF_CLIMATE_BYPASS_SWITCH,
    CONF_EXTERNAL_CONTROL_SWITCH,
    CONF_SCHEDULE_ENTITY,
    CONF_TEMPERATURE_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_SETPOINT_INPUT,
]
_LIST_KEYS = [CONF_LIGHTS, CONF_DOOR_WINDOW_SENSORS]

# Other integrations whose config entries can drive an actuator directly
_EXTERNAL_DRIVERS = ["solar_optimizer"]


def _anomaly(
    code: str, room: dict[str, Any], entity_id: str | None = None, **extra
) -> dict[str, Any]:
    data = {
        "code": code,
        "room_id": room.get(CONF_ROOM_ID),
        "room_name": room.get(CONF_ROOM_NAME, "?"),
        "entity_id": entity_id,
    }
    data.update(extra)
    return data


def _room_entities(room: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for key in _SINGLE_KEYS:
        value = room.get(key)
        if isinstance(value, str) and value:
            ids.append(value)
    for key in _LIST_KEYS:
        for value in room.get(key) or []:
            if isinstance(value, str) and value:
                ids.append(value)
    return ids


def _external_drivers(hass: HomeAssistant) -> dict[str, str]:
    """Map entity_id -> 'integration: title' for actuators driven elsewhere."""
    drivers: dict[str, str] = {}
    for domain in _EXTERNAL_DRIVERS:
        for entry in hass.config_entries.async_entries(domain):
            for source in (entry.data, entry.options):
                entity_id = source.get("entity_id") if source else None
                if isinstance(entity_id, str):
                    drivers[entity_id] = f"{domain}: {entry.title}"
    return drivers


def check_rooms(
    hass: HomeAssistant, rooms: list[dict[str, Any]], global_data: dict[str, Any]
) -> list[dict[str, Any]]:
    """Return the list of anomalies for the configured rooms."""
    anomalies: list[dict[str, Any]] = []
    now = dt_util.utcnow()
    drivers = _external_drivers(hass)
    climate_owners: dict[str, str] = {}

    for room in rooms:
        # 1. Referenced entities: missing or unavailable for too long
        for entity_id in _room_entities(room):
            state = hass.states.get(entity_id)
            if state is None:
                anomalies.append(_anomaly(ISSUE_MISSING_ENTITY, room, entity_id))
            elif (
                state.state == "unavailable"
                and now - state.last_changed >= UNAVAILABLE_GRACE
            ):
                anomalies.append(_anomaly(ISSUE_UNAVAILABLE_ENTITY, room, entity_id))

        # 2. Heating configured without actuator
        climate_mode = room.get(CONF_CLIMATE_MODE, CLIMATE_MODE_NONE)
        climate_entity = room.get(CONF_CLIMATE_ENTITY)
        if climate_mode != CLIMATE_MODE_NONE and not climate_entity:
            anomalies.append(_anomaly(ISSUE_CLIMATE_WITHOUT_ACTUATOR, room))

        # 3. Actuator driven by several controllers
        if climate_entity:
            if climate_entity in drivers:
                anomalies.append(
                    _anomaly(
                        ISSUE_MULTI_CONTROLLER,
                        room,
                        climate_entity,
                        other=drivers[climate_entity],
                    )
                )
            if climate_entity in climate_owners:
                anomalies.append(
                    _anomaly(
                        ISSUE_MULTI_CONTROLLER,
                        room,
                        climate_entity,
                        other=f"Smart Room Manager: {climate_owners[climate_entity]}",
                    )
                )
            climate_owners.setdefault(climate_entity, room.get(CONF_ROOM_NAME, "?"))

        # 4. Comfort setpoint (helper, after clamping) below the eco setpoint
        setpoint_input = room.get(CONF_SETPOINT_INPUT)
        if setpoint_input and room.get(CONF_TEMPERATURE_SENSOR):
            state = hass.states.get(setpoint_input)
            try:
                value = float(state.state) if state else None
            except (TypeError, ValueError):
                value = None
            if value is not None:
                comfort = max(room.get(CONF_MIN_SETPOINT, DEFAULT_MIN_SETPOINT), value)
                eco = room.get(CONF_TEMP_ECO, DEFAULT_TEMP_ECO)
                if comfort < eco:
                    anomalies.append(
                        _anomaly(
                            ISSUE_SETPOINT_BELOW_ECO,
                            room,
                            setpoint_input,
                            comfort=comfort,
                            eco=eco,
                        )
                    )

    return anomalies


def issue_id(anomaly: dict[str, Any]) -> str:
    """Stable repair issue id for an anomaly."""
    return (
        f"{anomaly['code']}_{anomaly['room_id']}_{anomaly.get('entity_id') or 'room'}"
    )
