"""Config flow for Smart Room Manager integration (v0.3.0)."""

from __future__ import annotations

import logging
import uuid
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import (
    CLIMATE_MODE_FIL_PILOTE,
    CLIMATE_MODE_NONE,
    CLIMATE_MODE_THERMOSTAT_COOL,
    CLIMATE_MODE_THERMOSTAT_HEAT,
    CLIMATE_MODE_THERMOSTAT_HEAT_COOL,
    CONF_ALARM_ENTITY,
    CONF_ALLOW_EXTERNAL_IN_AWAY,
    CONF_CLIMATE_BYPASS_SWITCH,
    CONF_CLIMATE_ENTITY,
    CONF_CLIMATE_MODE,
    CONF_CLIMATE_WINDOW_CHECK,
    CONF_DOOR_WINDOW_SENSORS,
    CONF_EXTERNAL_CONTROL_PRESET,
    CONF_EXTERNAL_CONTROL_SWITCH,
    CONF_EXTERNAL_CONTROL_TEMP,
    CONF_HUMIDITY_SENSOR,
    CONF_HYSTERESIS,
    CONF_IGNORE_IN_AWAY,
    CONF_LIGHT_TIMEOUT,
    CONF_LIGHTS,
    CONF_MAX_SETPOINT,
    CONF_MIN_SETPOINT,
    CONF_PAUSE_DURATION_MINUTES,
    CONF_PAUSE_INFINITE,
    CONF_PRESET_AWAY,
    CONF_PRESET_COMFORT,
    CONF_PRESET_ECO,
    CONF_PRESET_HEAT,
    CONF_PRESET_IDLE,
    CONF_PRESET_NIGHT,
    CONF_PRESET_SCHEDULE_OFF,
    CONF_PRESET_SCHEDULE_ON,
    CONF_PRESET_WINDOW,
    CONF_ROOM_ICON,
    CONF_ROOM_ID,
    CONF_ROOM_NAME,
    CONF_ROOM_TYPE,
    CONF_ROOMS,
    CONF_SCHEDULE_ENTITY,
    CONF_SEASON_CALENDAR,
    CONF_SETPOINT_INPUT,
    CONF_SUMMER_POLICY,
    CONF_TEMP_COMFORT,
    CONF_TEMP_COOL_COMFORT,
    CONF_TEMP_COOL_ECO,
    CONF_TEMP_ECO,
    CONF_TEMP_FROST_PROTECTION,
    CONF_TEMP_NIGHT,
    CONF_TEMPERATURE_SENSOR,
    CONF_THERMOSTAT_CONTROL_MODE,
    CONF_VMC_ENTITY,
    CONF_VMC_TIMER,
    CONF_WINDOW_DELAY_CLOSE,
    CONF_WINDOW_DELAY_OPEN,
    DEFAULT_ALLOW_EXTERNAL_IN_AWAY,
    DEFAULT_CLIMATE_MODE,
    DEFAULT_EXTERNAL_CONTROL_PRESET,
    DEFAULT_EXTERNAL_CONTROL_TEMP,
    DEFAULT_HYSTERESIS,
    DEFAULT_LIGHT_TIMEOUT,
    DEFAULT_LIGHT_TIMEOUT_BATHROOM,
    DEFAULT_MAX_SETPOINT,
    DEFAULT_MIN_SETPOINT,
    DEFAULT_PAUSE_DURATION,
    DEFAULT_PAUSE_INFINITE,
    DEFAULT_PRESET_AWAY,
    DEFAULT_PRESET_COMFORT,
    DEFAULT_PRESET_ECO,
    DEFAULT_PRESET_HEAT,
    DEFAULT_PRESET_IDLE,
    DEFAULT_PRESET_NIGHT,
    DEFAULT_PRESET_WINDOW,
    DEFAULT_SUMMER_POLICY,
    DEFAULT_TEMP_COMFORT,
    DEFAULT_TEMP_COOL_COMFORT,
    DEFAULT_TEMP_COOL_ECO,
    DEFAULT_TEMP_ECO,
    DEFAULT_TEMP_FROST_PROTECTION,
    DEFAULT_TEMP_NIGHT,
    DEFAULT_THERMOSTAT_CONTROL_MODE,
    DEFAULT_VMC_TIMER,
    DEFAULT_WINDOW_DELAY_CLOSE,
    DEFAULT_WINDOW_DELAY_OPEN,
    DOMAIN,
    FP_PRESET_AWAY,
    FP_PRESET_COMFORT,
    FP_PRESET_ECO,
    FP_PRESET_OFF,
    MODE_COMFORT,
    MODE_ECO,
    MODE_FROST_PROTECTION,
    MODE_NIGHT,
    ROOM_TYPE_BATHROOM,
    ROOM_TYPE_CORRIDOR,
    ROOM_TYPE_NORMAL,
    THERMOSTAT_CONTROL_BOTH,
    THERMOSTAT_CONTROL_PRESET,
    THERMOSTAT_CONTROL_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)


# Helper functions for config flow


# DEPRECATED (v0.3.1+): These functions are kept for backward compatibility only
# night_start and comfort_ranges are no longer exposed in the UI
# but existing configurations will continue to work using these values
def parse_comfort_ranges(comfort_ranges_text: str) -> list[dict[str, str]]:
    """Parse comfort time ranges from text format.

    DEPRECATED: No longer used in config flow UI (v0.3.1+)
    Kept for backward compatibility with existing configurations.

    Format: "HH:MM-HH:MM,HH:MM-HH:MM"
    Example: "07:00-09:00,18:00-22:00"

    Returns list of dicts with "start" and "end" keys.
    """
    comfort_ranges = []
    if comfort_ranges_text:
        for range_str in comfort_ranges_text.split(","):
            range_str = range_str.strip()
            if "-" in range_str:
                try:
                    start, end = range_str.split("-")
                    comfort_ranges.append(
                        {
                            "start": start.strip(),
                            "end": end.strip(),
                        }
                    )
                except Exception:
                    _LOGGER.warning("Invalid time range format: %s", range_str)
    return comfort_ranges


def format_comfort_ranges(comfort_ranges: list[dict[str, str]]) -> str:
    """Format comfort time ranges to text.

    DEPRECATED: No longer used in config flow UI (v0.3.1+)
    Kept for backward compatibility with existing configurations.

    Converts list of dicts to "HH:MM-HH:MM,HH:MM-HH:MM" format.
    """
    return ",".join(
        [
            f"{r['start']}-{r['end']}"
            for r in comfort_ranges
            if r.get("start") and r.get("end")
        ]
    )


def should_save_field(user_input: dict[str, Any], field_name: str) -> bool:
    """Check if a field should be saved (is configured and non-empty)."""
    value = user_input.get(field_name)
    if value is None:
        return False
    if isinstance(value, (list, tuple)) and len(value) == 0:
        return False
    return True


def build_room_list_choices(rooms: list[dict[str, Any]]) -> dict[str, str]:
    """Build choices dict for room list selection."""
    room_choices = {}
    for idx, room in enumerate(rooms):
        room_name = room.get("room_name", f"Room {idx + 1}")
        room_type = room.get("room_type", "normal")
        room_choices[f"edit_{idx}"] = f"✏️ Modifier: {room_name} ({room_type})"
        room_choices[f"delete_{idx}"] = f"🗑️ Supprimer: {room_name}"
    room_choices["back"] = "⬅️ Retour au menu"
    return room_choices


# Schema builders for config flow forms


def build_global_settings_schema(current_data: dict[str, Any]) -> vol.Schema:
    """Build schema for global settings."""
    schema_dict = {}

    # Alarm entity
    alarm = current_data.get(CONF_ALARM_ENTITY)
    if alarm is not None:
        schema_dict[vol.Optional(CONF_ALARM_ENTITY, default=alarm)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["alarm_control_panel"])
            )
        )
    else:
        schema_dict[vol.Optional(CONF_ALARM_ENTITY)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["alarm_control_panel"])
        )

    # Season calendar
    calendar = current_data.get(CONF_SEASON_CALENDAR)
    if calendar is not None:
        schema_dict[vol.Optional(CONF_SEASON_CALENDAR, default=calendar)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["calendar", "binary_sensor"])
            )
        )
    else:
        schema_dict[vol.Optional(CONF_SEASON_CALENDAR)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["calendar", "binary_sensor"])
        )

    # VMC entity (high speed switch)
    vmc = current_data.get(CONF_VMC_ENTITY)
    if vmc is not None:
        schema_dict[vol.Optional(CONF_VMC_ENTITY, default=vmc)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain=[SWITCH_DOMAIN, "fan"])
            )
        )
    else:
        schema_dict[vol.Optional(CONF_VMC_ENTITY)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=[SWITCH_DOMAIN, "fan"])
        )

    # VMC timer
    schema_dict[
        vol.Optional(
            CONF_VMC_TIMER,
            default=current_data.get(CONF_VMC_TIMER, DEFAULT_VMC_TIMER),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=60,
            max=1800,
            step=60,
            mode=selector.NumberSelectorMode.SLIDER,
            unit_of_measurement="s",
        )
    )

    return vol.Schema(schema_dict)


def build_room_basic_schema(room_data: dict[str, Any] | None = None) -> vol.Schema:
    """Build schema for basic room info."""
    if room_data is None:
        return vol.Schema(
            {
                vol.Required(CONF_ROOM_NAME): cv.string,
                vol.Optional(
                    CONF_ROOM_TYPE, default=ROOM_TYPE_NORMAL
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            ROOM_TYPE_NORMAL,
                            ROOM_TYPE_CORRIDOR,
                            ROOM_TYPE_BATHROOM,
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="room_type",
                    )
                ),
                vol.Optional(
                    CONF_ROOM_ICON, default="mdi:home"
                ): selector.IconSelector(),
            }
        )

    return vol.Schema(
        {
            vol.Required(
                CONF_ROOM_NAME,
                default=room_data.get(CONF_ROOM_NAME, ""),
            ): cv.string,
            vol.Optional(
                CONF_ROOM_TYPE,
                default=room_data.get(CONF_ROOM_TYPE, ROOM_TYPE_NORMAL),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[ROOM_TYPE_NORMAL, ROOM_TYPE_CORRIDOR, ROOM_TYPE_BATHROOM],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="room_type",
                )
            ),
            vol.Optional(
                CONF_ROOM_ICON,
                default=room_data.get(CONF_ROOM_ICON, "mdi:home"),
            ): selector.IconSelector(),
        }
    )


def build_room_sensors_schema(room_data: dict[str, Any]) -> vol.Schema:
    """Build schema for room sensors."""
    schema_dict = {}

    # Door/window sensors (always show, default to empty list)
    schema_dict[
        vol.Optional(
            CONF_DOOR_WINDOW_SENSORS,
            default=room_data.get(CONF_DOOR_WINDOW_SENSORS) or [],
        )
    ] = selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=[BINARY_SENSOR_DOMAIN],
            multiple=True,
        )
    )

    # Temperature sensor (only set default if it exists and is not None)
    temp_sensor = room_data.get(CONF_TEMPERATURE_SENSOR)
    if temp_sensor is not None:
        schema_dict[vol.Optional(CONF_TEMPERATURE_SENSOR, default=temp_sensor)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain=[SENSOR_DOMAIN])
            )
        )
    else:
        schema_dict[vol.Optional(CONF_TEMPERATURE_SENSOR)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=[SENSOR_DOMAIN])
        )

    # Humidity sensor (only set default if it exists and is not None)
    humidity_sensor = room_data.get(CONF_HUMIDITY_SENSOR)
    if humidity_sensor is not None:
        schema_dict[vol.Optional(CONF_HUMIDITY_SENSOR, default=humidity_sensor)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain=[SENSOR_DOMAIN])
            )
        )
    else:
        schema_dict[vol.Optional(CONF_HUMIDITY_SENSOR)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=[SENSOR_DOMAIN])
        )

    return vol.Schema(schema_dict)


def build_room_actuators_schema(room_data: dict[str, Any]) -> vol.Schema:
    """Build schema for room actuators."""
    schema_dict = {}

    # Lights (always show, default to empty list)
    schema_dict[
        vol.Optional(
            CONF_LIGHTS,
            default=room_data.get(CONF_LIGHTS) or [],
        )
    ] = selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=[LIGHT_DOMAIN, SWITCH_DOMAIN],
            multiple=True,
        )
    )

    # Climate mode selection (new in v0.4.0)
    schema_dict[
        vol.Optional(
            CONF_CLIMATE_MODE,
            default=room_data.get(CONF_CLIMATE_MODE, DEFAULT_CLIMATE_MODE),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=CLIMATE_MODE_NONE, label="Aucun"),
                selector.SelectOptionDict(
                    value=CLIMATE_MODE_FIL_PILOTE,
                    label="Fil Pilote (IPX800, Qubino...)",
                ),
                selector.SelectOptionDict(
                    value=CLIMATE_MODE_THERMOSTAT_HEAT,
                    label="Thermostat (chauffage)",
                ),
                selector.SelectOptionDict(
                    value=CLIMATE_MODE_THERMOSTAT_COOL,
                    label="Thermostat (climatisation)",
                ),
                selector.SelectOptionDict(
                    value=CLIMATE_MODE_THERMOSTAT_HEAT_COOL,
                    label="Thermostat (chaud/froid)",
                ),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )

    # Climate entity (shown for all climate modes except "none")
    climate_entity = room_data.get(CONF_CLIMATE_ENTITY)
    if climate_entity is not None:
        schema_dict[vol.Optional(CONF_CLIMATE_ENTITY, default=climate_entity)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain=[CLIMATE_DOMAIN])
            )
        )
    else:
        schema_dict[vol.Optional(CONF_CLIMATE_ENTITY)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=[CLIMATE_DOMAIN])
        )

    # Bypass switch
    bypass_switch = room_data.get(CONF_CLIMATE_BYPASS_SWITCH)
    if bypass_switch is not None:
        schema_dict[vol.Optional(CONF_CLIMATE_BYPASS_SWITCH, default=bypass_switch)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain=[SWITCH_DOMAIN, "input_boolean"])
            )
        )
    else:
        schema_dict[vol.Optional(CONF_CLIMATE_BYPASS_SWITCH)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=[SWITCH_DOMAIN, "input_boolean"])
        )

    # External control switch (v0.3.0)
    external_switch = room_data.get(CONF_EXTERNAL_CONTROL_SWITCH)
    if external_switch is not None:
        schema_dict[
            vol.Optional(CONF_EXTERNAL_CONTROL_SWITCH, default=external_switch)
        ] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=[SWITCH_DOMAIN, "input_boolean"])
        )
    else:
        schema_dict[vol.Optional(CONF_EXTERNAL_CONTROL_SWITCH)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain=[SWITCH_DOMAIN, "input_boolean"])
            )
        )

    # Note: VMC entity is now in global settings, not per-room

    return vol.Schema(schema_dict)


def build_light_config_schema(room_data: dict[str, Any], room_type: str) -> vol.Schema:
    """Build schema for light configuration."""
    default_timeout = (
        DEFAULT_LIGHT_TIMEOUT_BATHROOM
        if room_type == ROOM_TYPE_BATHROOM
        else DEFAULT_LIGHT_TIMEOUT
    )

    return vol.Schema(
        {
            vol.Optional(
                CONF_LIGHT_TIMEOUT,
                default=room_data.get(CONF_LIGHT_TIMEOUT, default_timeout),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=60,
                    max=1800,
                    step=30,
                    mode=selector.NumberSelectorMode.SLIDER,
                    unit_of_measurement="s",
                )
            ),
        }
    )


def build_climate_config_schema(
    room_data: dict[str, Any], climate_mode: str
) -> vol.Schema:
    """Build schema for climate configuration based on climate mode."""
    schema_dict = {}

    # Check if temperature sensor is configured
    has_temp_sensor = room_data.get(CONF_TEMPERATURE_SENSOR) is not None

    # Thermostat modes always need temperature setpoints
    # Fil Pilote needs them only if a temperature sensor is available
    thermostat_heating_modes = [
        CLIMATE_MODE_THERMOSTAT_HEAT,
        CLIMATE_MODE_THERMOSTAT_HEAT_COOL,
    ]
    fil_pilote_with_sensor = climate_mode == CLIMATE_MODE_FIL_PILOTE and has_temp_sensor
    show_heating_temps = (
        climate_mode in thermostat_heating_modes or fil_pilote_with_sensor
    )

    # Heating temperatures
    if show_heating_temps:
        schema_dict[
            vol.Optional(
                CONF_TEMP_COMFORT,
                default=room_data.get(CONF_TEMP_COMFORT, DEFAULT_TEMP_COMFORT),
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=15,
                max=25,
                step=0.5,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement="°C",
            )
        )
        schema_dict[
            vol.Optional(
                CONF_TEMP_ECO,
                default=room_data.get(CONF_TEMP_ECO, DEFAULT_TEMP_ECO),
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=15,
                max=25,
                step=0.5,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement="°C",
            )
        )
        schema_dict[
            vol.Optional(
                CONF_TEMP_NIGHT,
                default=room_data.get(CONF_TEMP_NIGHT, DEFAULT_TEMP_NIGHT),
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=15,
                max=25,
                step=0.5,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement="°C",
            )
        )
        schema_dict[
            vol.Optional(
                CONF_TEMP_FROST_PROTECTION,
                default=room_data.get(
                    CONF_TEMP_FROST_PROTECTION, DEFAULT_TEMP_FROST_PROTECTION
                ),
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=5,
                max=15,
                step=0.5,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement="°C",
            )
        )

    # Cooling temperatures (thermostat_cool, thermostat_heat_cool)
    cooling_modes = [CLIMATE_MODE_THERMOSTAT_COOL, CLIMATE_MODE_THERMOSTAT_HEAT_COOL]
    if climate_mode in cooling_modes:
        schema_dict[
            vol.Optional(
                CONF_TEMP_COOL_COMFORT,
                default=room_data.get(
                    CONF_TEMP_COOL_COMFORT, DEFAULT_TEMP_COOL_COMFORT
                ),
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=20,
                max=28,
                step=0.5,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement="°C",
            )
        )
        schema_dict[
            vol.Optional(
                CONF_TEMP_COOL_ECO,
                default=room_data.get(CONF_TEMP_COOL_ECO, DEFAULT_TEMP_COOL_ECO),
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=20,
                max=30,
                step=0.5,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement="°C",
            )
        )

    # Window check (for all modes with climate)
    if climate_mode != CLIMATE_MODE_NONE:
        schema_dict[
            vol.Optional(
                CONF_CLIMATE_WINDOW_CHECK,
                default=room_data.get(CONF_CLIMATE_WINDOW_CHECK, True),
            )
        ] = selector.BooleanSelector()
        schema_dict[
            vol.Optional(
                CONF_WINDOW_DELAY_OPEN,
                default=room_data.get(
                    CONF_WINDOW_DELAY_OPEN, DEFAULT_WINDOW_DELAY_OPEN
                ),
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=30,
                step=1,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement="min",
            )
        )
        schema_dict[
            vol.Optional(
                CONF_WINDOW_DELAY_CLOSE,
                default=room_data.get(
                    CONF_WINDOW_DELAY_CLOSE, DEFAULT_WINDOW_DELAY_CLOSE
                ),
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=30,
                step=1,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement="min",
            )
        )

    # Summer policy (only for fil_pilote)
    if climate_mode == CLIMATE_MODE_FIL_PILOTE:
        schema_dict[
            vol.Optional(
                CONF_SUMMER_POLICY,
                default=room_data.get(CONF_SUMMER_POLICY, DEFAULT_SUMMER_POLICY),
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value="off", label="Arrêt"),
                    selector.SelectOptionDict(value="eco", label="Eco"),
                    selector.SelectOptionDict(value="comfort", label="Confort"),
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )

    return vol.Schema(schema_dict)


def build_fil_pilote_advanced_schema(room_data: dict[str, Any]) -> vol.Schema:
    """Build schema for Fil Pilote advanced configuration (hysteresis + presets)."""
    schema_dict = {}

    # Hysteresis configuration (optional - requires temperature sensor)
    setpoint_input = room_data.get(CONF_SETPOINT_INPUT)
    if setpoint_input is not None:
        schema_dict[vol.Optional(CONF_SETPOINT_INPUT, default=setpoint_input)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["input_number", SENSOR_DOMAIN])
            )
        )
    else:
        schema_dict[vol.Optional(CONF_SETPOINT_INPUT)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["input_number", SENSOR_DOMAIN])
        )

    schema_dict[
        vol.Optional(
            CONF_HYSTERESIS,
            default=room_data.get(CONF_HYSTERESIS, DEFAULT_HYSTERESIS),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0.1,
            max=5.0,
            step=0.1,
            mode=selector.NumberSelectorMode.SLIDER,
            unit_of_measurement="°C",
        )
    )

    schema_dict[
        vol.Optional(
            CONF_MIN_SETPOINT,
            default=room_data.get(CONF_MIN_SETPOINT, DEFAULT_MIN_SETPOINT),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=10,
            max=25,
            step=0.5,
            mode=selector.NumberSelectorMode.SLIDER,
            unit_of_measurement="°C",
        )
    )

    schema_dict[
        vol.Optional(
            CONF_MAX_SETPOINT,
            default=room_data.get(CONF_MAX_SETPOINT, DEFAULT_MAX_SETPOINT),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=15,
            max=30,
            step=0.5,
            mode=selector.NumberSelectorMode.SLIDER,
            unit_of_measurement="°C",
        )
    )

    schema_dict[
        vol.Optional(
            CONF_PRESET_HEAT,
            default=room_data.get(CONF_PRESET_HEAT, DEFAULT_PRESET_HEAT),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=FP_PRESET_COMFORT, label="Confort"),
                selector.SelectOptionDict(value=FP_PRESET_ECO, label="Eco"),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )

    schema_dict[
        vol.Optional(
            CONF_PRESET_IDLE,
            default=room_data.get(CONF_PRESET_IDLE, DEFAULT_PRESET_IDLE),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=FP_PRESET_ECO, label="Eco"),
                selector.SelectOptionDict(value=FP_PRESET_OFF, label="Arrêt"),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )

    return vol.Schema(schema_dict)


def build_fil_pilote_presets_schema(room_data: dict[str, Any]) -> vol.Schema:
    """Build schema for Fil Pilote configurable presets."""
    schema_dict = {}

    # Fil Pilote Configurable Presets - what preset to send for each mode
    schema_dict[
        vol.Optional(
            CONF_PRESET_COMFORT,
            default=room_data.get(CONF_PRESET_COMFORT, DEFAULT_PRESET_COMFORT),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=FP_PRESET_COMFORT, label="Confort"),
                selector.SelectOptionDict(value=FP_PRESET_ECO, label="Eco"),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )

    schema_dict[
        vol.Optional(
            CONF_PRESET_ECO,
            default=room_data.get(CONF_PRESET_ECO, DEFAULT_PRESET_ECO),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=FP_PRESET_ECO, label="Eco"),
                selector.SelectOptionDict(value=FP_PRESET_COMFORT, label="Confort"),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )

    schema_dict[
        vol.Optional(
            CONF_PRESET_NIGHT,
            default=room_data.get(CONF_PRESET_NIGHT, DEFAULT_PRESET_NIGHT),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=FP_PRESET_ECO, label="Eco"),
                selector.SelectOptionDict(value=FP_PRESET_COMFORT, label="Confort"),
                selector.SelectOptionDict(value=FP_PRESET_AWAY, label="Hors-gel"),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )

    schema_dict[
        vol.Optional(
            CONF_PRESET_AWAY,
            default=room_data.get(CONF_PRESET_AWAY, DEFAULT_PRESET_AWAY),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=FP_PRESET_AWAY, label="Hors-gel"),
                selector.SelectOptionDict(value=FP_PRESET_ECO, label="Eco"),
                selector.SelectOptionDict(value=FP_PRESET_OFF, label="Arrêt"),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )

    schema_dict[
        vol.Optional(
            CONF_PRESET_WINDOW,
            default=room_data.get(CONF_PRESET_WINDOW, DEFAULT_PRESET_WINDOW),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=FP_PRESET_AWAY, label="Hors-gel"),
                selector.SelectOptionDict(value=FP_PRESET_ECO, label="Eco"),
                selector.SelectOptionDict(value=FP_PRESET_OFF, label="Arrêt"),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )

    # External Control configuration for Fil Pilote
    schema_dict[
        vol.Optional(
            CONF_EXTERNAL_CONTROL_PRESET,
            default=room_data.get(
                CONF_EXTERNAL_CONTROL_PRESET, DEFAULT_EXTERNAL_CONTROL_PRESET
            ),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=FP_PRESET_COMFORT, label="Confort"),
                selector.SelectOptionDict(value=FP_PRESET_ECO, label="Eco"),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )

    schema_dict[
        vol.Optional(
            CONF_ALLOW_EXTERNAL_IN_AWAY,
            default=room_data.get(
                CONF_ALLOW_EXTERNAL_IN_AWAY, DEFAULT_ALLOW_EXTERNAL_IN_AWAY
            ),
        )
    ] = selector.BooleanSelector()

    return vol.Schema(schema_dict)


def build_thermostat_advanced_schema(room_data: dict[str, Any]) -> vol.Schema:
    """Build schema for Thermostat advanced configuration."""
    schema_dict = {}

    # Thermostat control mode
    schema_dict[
        vol.Optional(
            CONF_THERMOSTAT_CONTROL_MODE,
            default=room_data.get(
                CONF_THERMOSTAT_CONTROL_MODE, DEFAULT_THERMOSTAT_CONTROL_MODE
            ),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(
                    value=THERMOSTAT_CONTROL_PRESET,
                    label="Presets uniquement (recommandé)",
                ),
                selector.SelectOptionDict(
                    value=THERMOSTAT_CONTROL_TEMPERATURE,
                    label="Températures (contrôle direct)",
                ),
                selector.SelectOptionDict(
                    value=THERMOSTAT_CONTROL_BOTH,
                    label="Presets et températures",
                ),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )

    # External Control configuration for Thermostat
    schema_dict[
        vol.Optional(
            CONF_EXTERNAL_CONTROL_TEMP,
            default=room_data.get(
                CONF_EXTERNAL_CONTROL_TEMP, DEFAULT_EXTERNAL_CONTROL_TEMP
            ),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=15,
            max=25,
            step=0.5,
            mode=selector.NumberSelectorMode.SLIDER,
            unit_of_measurement="°C",
        )
    )

    schema_dict[
        vol.Optional(
            CONF_ALLOW_EXTERNAL_IN_AWAY,
            default=room_data.get(
                CONF_ALLOW_EXTERNAL_IN_AWAY, DEFAULT_ALLOW_EXTERNAL_IN_AWAY
            ),
        )
    ] = selector.BooleanSelector()

    return vol.Schema(schema_dict)


def build_schedule_schema(room_data: dict[str, Any]) -> vol.Schema:
    """Build schema for schedule configuration."""
    schema_dict = {}

    # v0.3.0 - Calendar entity support (optional)
    schedule_entity = room_data.get(CONF_SCHEDULE_ENTITY)
    if schedule_entity is not None:
        schema_dict[vol.Optional(CONF_SCHEDULE_ENTITY, default=schedule_entity)] = (
            selector.EntitySelector(selector.EntitySelectorConfig(domain="calendar"))
        )
    else:
        schema_dict[vol.Optional(CONF_SCHEDULE_ENTITY)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="calendar")
        )

    # Presets for schedule on/off (only shown if using calendar)
    schema_dict[
        vol.Optional(
            CONF_PRESET_SCHEDULE_ON,
            default=room_data.get(CONF_PRESET_SCHEDULE_ON, MODE_COMFORT),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                MODE_COMFORT,
                MODE_ECO,
                MODE_NIGHT,
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
            translation_key="preset_schedule_on",
        )
    )

    schema_dict[
        vol.Optional(
            CONF_PRESET_SCHEDULE_OFF,
            default=room_data.get(CONF_PRESET_SCHEDULE_OFF, MODE_ECO),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                MODE_ECO,
                MODE_NIGHT,
                MODE_FROST_PROTECTION,
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
            translation_key="preset_schedule_off",
        )
    )

    # Ignore schedule when away
    schema_dict[
        vol.Optional(
            CONF_IGNORE_IN_AWAY,
            default=room_data.get(CONF_IGNORE_IN_AWAY, False),
        )
    ] = selector.BooleanSelector()

    return vol.Schema(schema_dict)


def build_room_control_schema(room_data: dict[str, Any]) -> vol.Schema:
    """Build schema for room control configuration."""
    # Get current value and convert to string for SelectSelector
    current_pause = room_data.get(CONF_PAUSE_DURATION_MINUTES, DEFAULT_PAUSE_DURATION)
    # Ensure default is a string (SelectSelector requires string options)
    if current_pause is not None:
        default_pause = str(current_pause)
    else:
        default_pause = str(DEFAULT_PAUSE_DURATION)

    return vol.Schema(
        {
            vol.Optional(
                CONF_PAUSE_DURATION_MINUTES,
                default=default_pause,
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["15", "30", "60", "120", "240", "480"],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="pause_duration",
                )
            ),
            vol.Optional(
                CONF_PAUSE_INFINITE,
                default=room_data.get(CONF_PAUSE_INFINITE, DEFAULT_PAUSE_INFINITE),
            ): selector.BooleanSelector(),
        }
    )


# Config flow classes


class SmartRoomManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Room Manager (v0.3.0)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step - simplified for v0.2.0."""
        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            # Store minimal initial configuration
            # Global settings go in data (not modifiable after creation)
            # Room configurations go in options (modifiable)
            return self.async_create_entry(
                title="Smart Room Manager",
                data={
                    CONF_ALARM_ENTITY: user_input.get(CONF_ALARM_ENTITY),
                    CONF_SEASON_CALENDAR: user_input.get(CONF_SEASON_CALENDAR),
                },
                options={
                    CONF_ROOMS: [],
                },
            )

        # Show simplified initial form
        data_schema = vol.Schema(
            {
                vol.Optional(CONF_ALARM_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["alarm_control_panel"],
                    )
                ),
                vol.Optional(CONF_SEASON_CALENDAR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["calendar", "binary_sensor"],
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            description_placeholders={
                "description": (
                    "Simplified v0.2.0 configuration - "
                    "Alarm determines presence, no presence/luminosity sensors"
                )
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SmartRoomManagerOptionsFlow:
        """Get the options flow for this handler."""
        return SmartRoomManagerOptionsFlow()


class SmartRoomManagerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Smart Room Manager (v0.3.0)."""

    def __init__(self) -> None:
        """Initialize options flow."""
        # Note: self.config_entry is automatically provided by OptionsFlow
        # parent class (HA 2025.12+)
        super().__init__()
        self._current_room: dict[str, Any] | None = None
        self._room_index: int | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "list_rooms",
                "add_room",
                "global_settings",
            ],
        )

    async def async_step_list_rooms(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """List all configured rooms."""
        rooms = self.config_entry.options.get(CONF_ROOMS, [])

        if not rooms:
            return self.async_show_form(
                step_id="list_rooms",
                description_placeholders={
                    "rooms": "No rooms configured. Return to the menu to add a room."
                },
            )

        if user_input is not None:
            room_selection = user_input.get("room_action")
            if room_selection == "back":
                return await self.async_step_init()

            # Parse selection (format: "edit_0", "delete_1", etc.)
            action, index = room_selection.split("_")
            self._room_index = int(index)

            if action == "edit":
                self._current_room = rooms[self._room_index].copy()
                return await self.async_step_edit_room_basic()
            elif action == "delete":
                return await self.async_step_delete_room()

        # Build room list for selection
        room_choices = build_room_list_choices(rooms)

        return self.async_show_form(
            step_id="list_rooms",
            data_schema=vol.Schema(
                {
                    vol.Required("room_action"): vol.In(room_choices),
                }
            ),
        )

    async def async_step_add_room(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Add a new room - step 1: basic info (v0.2.0)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._current_room = {
                CONF_ROOM_ID: str(uuid.uuid4())[:8],
                CONF_ROOM_NAME: user_input[CONF_ROOM_NAME],
                CONF_ROOM_TYPE: user_input.get(CONF_ROOM_TYPE, ROOM_TYPE_NORMAL),
                CONF_ROOM_ICON: user_input.get(CONF_ROOM_ICON, "mdi:home"),
            }
            return await self.async_step_room_sensors()

        return self.async_show_form(
            step_id="add_room",
            data_schema=build_room_basic_schema(None),
            errors=errors,
            description_placeholders={
                "info": "Normal type: no timer. Corridor/Bathroom: auto-off timer."
            },
        )

    async def async_step_edit_room_basic(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Edit room - step 1: basic info."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._current_room[CONF_ROOM_NAME] = user_input[CONF_ROOM_NAME]
            self._current_room[CONF_ROOM_TYPE] = user_input.get(
                CONF_ROOM_TYPE, ROOM_TYPE_NORMAL
            )
            self._current_room[CONF_ROOM_ICON] = user_input.get(
                CONF_ROOM_ICON, "mdi:home"
            )
            return await self.async_step_room_sensors()

        return self.async_show_form(
            step_id="edit_room_basic",
            data_schema=build_room_basic_schema(self._current_room),
            errors=errors,
        )

    async def async_step_room_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure room sensors (v0.2.0 - simplified, optional)."""
        if user_input is not None:
            # Only save sensors that are actually configured (non-empty)
            update_data = {
                CONF_DOOR_WINDOW_SENSORS: user_input.get(CONF_DOOR_WINDOW_SENSORS, []),
            }

            # Add optional sensors only if they are configured
            if user_input.get(CONF_TEMPERATURE_SENSOR):
                update_data[CONF_TEMPERATURE_SENSOR] = user_input.get(
                    CONF_TEMPERATURE_SENSOR
                )

            if user_input.get(CONF_HUMIDITY_SENSOR):
                update_data[CONF_HUMIDITY_SENSOR] = user_input.get(CONF_HUMIDITY_SENSOR)

            self._current_room.update(update_data)
            return await self.async_step_room_actuators()

        return self.async_show_form(
            step_id="room_sensors",
            data_schema=build_room_sensors_schema(self._current_room),
            description_placeholders={
                "room_name": self._current_room[CONF_ROOM_NAME],
                "info": "All optional. Windows → frost protection if open.",
            },
        )

    async def async_step_room_actuators(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure room actuators (v0.4.0 - with climate mode selection)."""
        if user_input is not None:
            # Get climate entity and mode
            has_climate = user_input.get(CONF_CLIMATE_ENTITY)
            climate_mode = user_input.get(CONF_CLIMATE_MODE, DEFAULT_CLIMATE_MODE)

            # If no climate entity, force mode to "none"
            if not has_climate:
                climate_mode = CLIMATE_MODE_NONE

            update_data = {
                CONF_LIGHTS: user_input.get(CONF_LIGHTS, []),
                CONF_CLIMATE_MODE: climate_mode,
            }

            # Add climate-related options only if climate is configured
            if climate_mode != CLIMATE_MODE_NONE and has_climate:
                update_data[CONF_CLIMATE_ENTITY] = has_climate

                # Bypass switch (only relevant with climate)
                if user_input.get(CONF_CLIMATE_BYPASS_SWITCH):
                    update_data[CONF_CLIMATE_BYPASS_SWITCH] = user_input.get(
                        CONF_CLIMATE_BYPASS_SWITCH
                    )

                # External control switch (only relevant with climate)
                if user_input.get(CONF_EXTERNAL_CONTROL_SWITCH):
                    update_data[CONF_EXTERNAL_CONTROL_SWITCH] = user_input.get(
                        CONF_EXTERNAL_CONTROL_SWITCH
                    )

            # Note: VMC entity is now in global settings, not per-room

            self._current_room.update(update_data)
            return await self.async_step_room_light_config()

        return self.async_show_form(
            step_id="room_actuators",
            data_schema=build_room_actuators_schema(self._current_room),
            description_placeholders={
                "room_name": self._current_room[CONF_ROOM_NAME],
                "info": "Type de chauffage → détermine les options de configuration.",
            },
        )

    async def async_step_room_light_config(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure light behavior (v0.2.0 - simplified, timer only)."""
        room_type = self._current_room.get(CONF_ROOM_TYPE, ROOM_TYPE_NORMAL)

        if user_input is not None:
            # Only save timeout if room type uses timer (corridor, bathroom)
            if room_type in [ROOM_TYPE_CORRIDOR, ROOM_TYPE_BATHROOM]:
                self._current_room[CONF_LIGHT_TIMEOUT] = user_input.get(
                    CONF_LIGHT_TIMEOUT
                )
            return await self.async_step_room_climate_config()

        # Show timeout config only for corridor/bathroom
        if room_type in [ROOM_TYPE_CORRIDOR, ROOM_TYPE_BATHROOM]:
            return self.async_show_form(
                step_id="room_light_config",
                data_schema=build_light_config_schema(self._current_room, room_type),
                description_placeholders={
                    "room_name": self._current_room[CONF_ROOM_NAME],
                    "info": f"Type {room_type}: auto-off after timeout",
                },
            )
        else:
            # Skip light config for normal rooms (no timer)
            return await self.async_step_room_climate_config()

    async def async_step_room_climate_config(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure climate behavior (v0.4.0 - contextual based on climate mode)."""
        climate_mode = self._current_room.get(CONF_CLIMATE_MODE, DEFAULT_CLIMATE_MODE)

        # Skip climate config, schedule, and control if no climate configured
        if climate_mode == CLIMATE_MODE_NONE:
            return await self._save_room()

        if user_input is not None:
            update_data = {}

            # Check if temperature sensor is configured
            has_temp_sensor = (
                self._current_room.get(CONF_TEMPERATURE_SENSOR) is not None
            )

            # Heating temperatures: thermostat modes OR Fil Pilote with temp sensor
            thermostat_heating_modes = [
                CLIMATE_MODE_THERMOSTAT_HEAT,
                CLIMATE_MODE_THERMOSTAT_HEAT_COOL,
            ]
            fil_pilote_with_sensor = (
                climate_mode == CLIMATE_MODE_FIL_PILOTE and has_temp_sensor
            )
            if climate_mode in thermostat_heating_modes or fil_pilote_with_sensor:
                update_data[CONF_TEMP_COMFORT] = user_input.get(
                    CONF_TEMP_COMFORT, DEFAULT_TEMP_COMFORT
                )
                update_data[CONF_TEMP_ECO] = user_input.get(
                    CONF_TEMP_ECO, DEFAULT_TEMP_ECO
                )
                update_data[CONF_TEMP_NIGHT] = user_input.get(
                    CONF_TEMP_NIGHT, DEFAULT_TEMP_NIGHT
                )
                update_data[CONF_TEMP_FROST_PROTECTION] = user_input.get(
                    CONF_TEMP_FROST_PROTECTION, DEFAULT_TEMP_FROST_PROTECTION
                )

            # Cooling temperatures (thermostat_cool, thermostat_heat_cool)
            cooling_modes = [
                CLIMATE_MODE_THERMOSTAT_COOL,
                CLIMATE_MODE_THERMOSTAT_HEAT_COOL,
            ]
            if climate_mode in cooling_modes:
                update_data[CONF_TEMP_COOL_COMFORT] = user_input.get(
                    CONF_TEMP_COOL_COMFORT, DEFAULT_TEMP_COOL_COMFORT
                )
                update_data[CONF_TEMP_COOL_ECO] = user_input.get(
                    CONF_TEMP_COOL_ECO, DEFAULT_TEMP_COOL_ECO
                )

            # Window check (for all climate modes)
            update_data[CONF_CLIMATE_WINDOW_CHECK] = user_input.get(
                CONF_CLIMATE_WINDOW_CHECK, True
            )
            update_data[CONF_WINDOW_DELAY_OPEN] = user_input.get(
                CONF_WINDOW_DELAY_OPEN, DEFAULT_WINDOW_DELAY_OPEN
            )
            update_data[CONF_WINDOW_DELAY_CLOSE] = user_input.get(
                CONF_WINDOW_DELAY_CLOSE, DEFAULT_WINDOW_DELAY_CLOSE
            )

            # Summer policy (only for fil_pilote)
            if climate_mode == CLIMATE_MODE_FIL_PILOTE:
                update_data[CONF_SUMMER_POLICY] = user_input.get(
                    CONF_SUMMER_POLICY, DEFAULT_SUMMER_POLICY
                )

            self._current_room.update(update_data)
            return await self.async_step_room_climate_advanced()

        # Build description based on climate mode
        if climate_mode == CLIMATE_MODE_FIL_PILOTE:
            info = "Températures de chauffage et politique été pour Fil Pilote."
        elif climate_mode == CLIMATE_MODE_THERMOSTAT_HEAT:
            info = "Températures de chauffage pour thermostat."
        elif climate_mode == CLIMATE_MODE_THERMOSTAT_COOL:
            info = "Températures de climatisation pour thermostat."
        else:  # THERMOSTAT_HEAT_COOL
            info = "Températures de chauffage et climatisation pour thermostat."

        return self.async_show_form(
            step_id="room_climate_config",
            data_schema=build_climate_config_schema(self._current_room, climate_mode),
            description_placeholders={
                "room_name": self._current_room[CONF_ROOM_NAME],
                "info": info,
            },
        )

    async def async_step_room_climate_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure advanced climate features (v0.4.0 - route to appropriate step)."""
        climate_mode = self._current_room.get(CONF_CLIMATE_MODE, DEFAULT_CLIMATE_MODE)

        # Route to appropriate advanced config based on climate mode
        thermostat_modes = [
            CLIMATE_MODE_THERMOSTAT_HEAT,
            CLIMATE_MODE_THERMOSTAT_COOL,
            CLIMATE_MODE_THERMOSTAT_HEAT_COOL,
        ]
        if climate_mode == CLIMATE_MODE_FIL_PILOTE:
            return await self.async_step_fil_pilote_hysteresis(user_input)
        elif climate_mode in thermostat_modes:
            return await self.async_step_thermostat_advanced(user_input)
        else:
            # No advanced config for CLIMATE_MODE_NONE
            return await self.async_step_room_schedule()

    async def async_step_fil_pilote_hysteresis(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure Fil Pilote hysteresis (optional - requires temperature sensor)."""
        if user_input is not None:
            update_data = {}

            # Hysteresis configuration (only if setpoint is configured)
            if user_input.get(CONF_SETPOINT_INPUT):
                update_data[CONF_SETPOINT_INPUT] = user_input.get(CONF_SETPOINT_INPUT)
                update_data[CONF_HYSTERESIS] = user_input.get(
                    CONF_HYSTERESIS, DEFAULT_HYSTERESIS
                )
                update_data[CONF_MIN_SETPOINT] = user_input.get(
                    CONF_MIN_SETPOINT, DEFAULT_MIN_SETPOINT
                )
                update_data[CONF_MAX_SETPOINT] = user_input.get(
                    CONF_MAX_SETPOINT, DEFAULT_MAX_SETPOINT
                )
                update_data[CONF_PRESET_HEAT] = user_input.get(
                    CONF_PRESET_HEAT, DEFAULT_PRESET_HEAT
                )
                update_data[CONF_PRESET_IDLE] = user_input.get(
                    CONF_PRESET_IDLE, DEFAULT_PRESET_IDLE
                )

            self._current_room.update(update_data)
            return await self.async_step_fil_pilote_presets()

        return self.async_show_form(
            step_id="fil_pilote_hysteresis",
            data_schema=build_fil_pilote_advanced_schema(self._current_room),
            description_placeholders={
                "room_name": self._current_room[CONF_ROOM_NAME],
                "info": "Hystérésis : contrôle via température.",
            },
        )

    async def async_step_fil_pilote_presets(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure Fil Pilote presets and external control."""
        if user_input is not None:
            update_data = {}

            # Fil Pilote Configurable Presets
            update_data[CONF_PRESET_COMFORT] = user_input.get(
                CONF_PRESET_COMFORT, DEFAULT_PRESET_COMFORT
            )
            update_data[CONF_PRESET_ECO] = user_input.get(
                CONF_PRESET_ECO, DEFAULT_PRESET_ECO
            )
            update_data[CONF_PRESET_NIGHT] = user_input.get(
                CONF_PRESET_NIGHT, DEFAULT_PRESET_NIGHT
            )
            update_data[CONF_PRESET_AWAY] = user_input.get(
                CONF_PRESET_AWAY, DEFAULT_PRESET_AWAY
            )
            update_data[CONF_PRESET_WINDOW] = user_input.get(
                CONF_PRESET_WINDOW, DEFAULT_PRESET_WINDOW
            )

            # External Control configuration for Fil Pilote
            update_data[CONF_EXTERNAL_CONTROL_PRESET] = user_input.get(
                CONF_EXTERNAL_CONTROL_PRESET, DEFAULT_EXTERNAL_CONTROL_PRESET
            )
            update_data[CONF_ALLOW_EXTERNAL_IN_AWAY] = user_input.get(
                CONF_ALLOW_EXTERNAL_IN_AWAY, DEFAULT_ALLOW_EXTERNAL_IN_AWAY
            )

            self._current_room.update(update_data)
            return await self.async_step_room_schedule()

        return self.async_show_form(
            step_id="fil_pilote_presets",
            data_schema=build_fil_pilote_presets_schema(self._current_room),
            description_placeholders={
                "room_name": self._current_room[CONF_ROOM_NAME],
                "info": "Presets Fil Pilote et contrôle externe.",
            },
        )

    async def async_step_thermostat_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure Thermostat control mode and external control."""
        if user_input is not None:
            update_data = {}

            # Thermostat control mode
            update_data[CONF_THERMOSTAT_CONTROL_MODE] = user_input.get(
                CONF_THERMOSTAT_CONTROL_MODE, DEFAULT_THERMOSTAT_CONTROL_MODE
            )

            # External Control configuration for Thermostat
            update_data[CONF_EXTERNAL_CONTROL_TEMP] = user_input.get(
                CONF_EXTERNAL_CONTROL_TEMP, DEFAULT_EXTERNAL_CONTROL_TEMP
            )
            update_data[CONF_ALLOW_EXTERNAL_IN_AWAY] = user_input.get(
                CONF_ALLOW_EXTERNAL_IN_AWAY, DEFAULT_ALLOW_EXTERNAL_IN_AWAY
            )

            self._current_room.update(update_data)
            return await self.async_step_room_schedule()

        return self.async_show_form(
            step_id="thermostat_advanced",
            data_schema=build_thermostat_advanced_schema(self._current_room),
            description_placeholders={
                "room_name": self._current_room[CONF_ROOM_NAME],
                "info": "Mode de contrôle et contrôle externe.",
            },
        )

    async def async_step_room_schedule(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure room schedule (v0.3.0 - calendar, presets)."""
        if user_input is not None:
            # v0.3.0 - Schedule entity (calendar) support (optional)
            # Only save if not empty string
            schedule_entity = user_input.get(CONF_SCHEDULE_ENTITY)
            if schedule_entity:
                self._current_room[CONF_SCHEDULE_ENTITY] = schedule_entity
            elif CONF_SCHEDULE_ENTITY in self._current_room:
                # Remove if was previously set but now empty
                self._current_room.pop(CONF_SCHEDULE_ENTITY, None)

            # Save presets - ensure valid values from the allowed list
            preset_on = user_input.get(CONF_PRESET_SCHEDULE_ON, MODE_COMFORT)
            if preset_on in [MODE_COMFORT, MODE_ECO, MODE_NIGHT]:
                self._current_room[CONF_PRESET_SCHEDULE_ON] = preset_on
            else:
                self._current_room[CONF_PRESET_SCHEDULE_ON] = MODE_COMFORT

            preset_off = user_input.get(CONF_PRESET_SCHEDULE_OFF, MODE_ECO)
            if preset_off in [MODE_ECO, MODE_NIGHT, MODE_FROST_PROTECTION]:
                self._current_room[CONF_PRESET_SCHEDULE_OFF] = preset_off
            else:
                self._current_room[CONF_PRESET_SCHEDULE_OFF] = MODE_ECO

            # Ignore schedule when away
            self._current_room[CONF_IGNORE_IN_AWAY] = user_input.get(
                CONF_IGNORE_IN_AWAY, False
            )

            return await self.async_step_room_control()

        return self.async_show_form(
            step_id="room_schedule",
            data_schema=build_schedule_schema(self._current_room),
            description_placeholders={
                "room_name": self._current_room[CONF_ROOM_NAME],
                "info": "Calendar: external. Presets: mode when ON/OFF",
            },
        )

    async def async_step_room_control(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure room control options (v0.3.0 - Manual pause configuration)."""
        if user_input is not None:
            # Save pause configuration
            # Convert string value from SelectSelector to int
            default_pause = str(DEFAULT_PAUSE_DURATION)
            pause_value = user_input.get(CONF_PAUSE_DURATION_MINUTES, default_pause)
            self._current_room[CONF_PAUSE_DURATION_MINUTES] = int(pause_value)
            self._current_room[CONF_PAUSE_INFINITE] = user_input.get(
                CONF_PAUSE_INFINITE, DEFAULT_PAUSE_INFINITE
            )

            return await self._save_room()

        return self.async_show_form(
            step_id="room_control",
            data_schema=build_room_control_schema(self._current_room),
            description_placeholders={
                "room_name": self._current_room[CONF_ROOM_NAME],
                "info": "Pause duration default. Infinite: no time limit.",
            },
        )

    async def async_step_delete_room(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Confirm room deletion."""
        rooms = list(self.config_entry.options.get(CONF_ROOMS, []))
        room_data = rooms[self._room_index]
        room_name = room_data.get(CONF_ROOM_NAME, "Unknown")
        room_id = room_data.get(CONF_ROOM_ID)

        if user_input is not None:
            if user_input.get("confirm"):
                # Remove entities from registry before deleting room
                if room_id:
                    await self._remove_room_entities(room_id)

                rooms.pop(self._room_index)
                return self.async_create_entry(
                    title="",
                    data={
                        **self.config_entry.options,
                        CONF_ROOMS: rooms,
                    },
                )
            return await self.async_step_list_rooms()

        return self.async_show_form(
            step_id="delete_room",
            data_schema=vol.Schema(
                {
                    vol.Required("confirm", default=False): selector.BooleanSelector(),
                }
            ),
            description_placeholders={"room_name": room_name},
        )

    async def _save_room(self) -> config_entries.FlowResult:
        """Save the current room configuration."""
        rooms = list(self.config_entry.options.get(CONF_ROOMS, []))
        if self._room_index is not None:
            # Edit existing room
            rooms[self._room_index] = self._current_room
        else:
            # Add new room
            rooms.append(self._current_room)

        return self.async_create_entry(
            title="",
            data={
                **self.config_entry.options,
                CONF_ROOMS: rooms,
            },
        )

    async def _remove_room_entities(self, room_id: str) -> None:
        """Remove all entities associated with a room from the entity registry."""
        entity_registry = er.async_get(self.hass)

        # List of entity suffixes for each room
        entity_suffixes = [
            "automation",
            "pause",
            "state",
            "current_priority",
            "hysteresis_state",
            "occupied",
            "light_needed",
            "external_control_active",
            "schedule_active",
        ]

        for suffix in entity_suffixes:
            unique_id = f"smart_room_{room_id}_{suffix}"
            entity_id = entity_registry.async_get_entity_id(
                # Try all possible domains
                "sensor",
                DOMAIN,
                unique_id,
            )
            if not entity_id:
                entity_id = entity_registry.async_get_entity_id(
                    "binary_sensor", DOMAIN, unique_id
                )
            if not entity_id:
                entity_id = entity_registry.async_get_entity_id(
                    "switch", DOMAIN, unique_id
                )

            if entity_id:
                entity_registry.async_remove(entity_id)

    async def async_step_global_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure global settings (v0.2.0 - alarm + season calendar + VMC)."""
        if user_input is not None:
            # Update entry data (not options) for global settings
            # Note: This requires updating entry.data which is normally immutable
            # We create a new data dict
            new_data = {
                **self.config_entry.data,
                CONF_ALARM_ENTITY: user_input.get(CONF_ALARM_ENTITY),
                CONF_SEASON_CALENDAR: user_input.get(CONF_SEASON_CALENDAR),
                CONF_VMC_ENTITY: user_input.get(CONF_VMC_ENTITY),
                CONF_VMC_TIMER: user_input.get(CONF_VMC_TIMER, DEFAULT_VMC_TIMER),
            }

            # Update the config entry
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )

            return self.async_create_entry(title="", data=self.config_entry.options)

        return self.async_show_form(
            step_id="global_settings",
            data_schema=build_global_settings_schema(self.config_entry.data),
            description_placeholders={
                "info": "VMC: durée après extinction lumière SDB/WC.",
            },
        )
