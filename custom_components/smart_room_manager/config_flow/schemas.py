"""Schema builders for config flow forms."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from ..const import (
    CONF_ALARM_ENTITY,
    CONF_CLIMATE_BYPASS_SWITCH,
    CONF_CLIMATE_ENTITY,
    CONF_CLIMATE_WINDOW_CHECK,
    CONF_DOOR_WINDOW_SENSORS,
    CONF_EXTERNAL_CONTROL_PRESET,
    CONF_EXTERNAL_CONTROL_SWITCH,
    CONF_EXTERNAL_CONTROL_TEMP,
    CONF_HUMIDITY_SENSOR,
    CONF_HYSTERESIS,
    CONF_LIGHTS,
    CONF_LIGHT_TIMEOUT,
    CONF_MAX_SETPOINT,
    CONF_MIN_SETPOINT,
    CONF_NIGHT_START,
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
    CONF_ROOM_NAME,
    CONF_ROOM_TYPE,
    CONF_SCHEDULE_ENTITY,
    CONF_SEASON_CALENDAR,
    CONF_SETPOINT_INPUT,
    CONF_SUMMER_POLICY,
    CONF_TEMPERATURE_SENSOR,
    CONF_TEMP_COMFORT,
    CONF_TEMP_COOL_COMFORT,
    CONF_TEMP_COOL_ECO,
    CONF_TEMP_ECO,
    CONF_TEMP_FROST_PROTECTION,
    CONF_TEMP_NIGHT,
    CONF_WINDOW_DELAY_CLOSE,
    CONF_WINDOW_DELAY_OPEN,
    CONF_ALLOW_EXTERNAL_IN_AWAY,
    DEFAULT_EXTERNAL_CONTROL_PRESET,
    DEFAULT_EXTERNAL_CONTROL_TEMP,
    DEFAULT_ALLOW_EXTERNAL_IN_AWAY,
    DEFAULT_HYSTERESIS,
    DEFAULT_LIGHT_TIMEOUT,
    DEFAULT_LIGHT_TIMEOUT_BATHROOM,
    DEFAULT_MAX_SETPOINT,
    DEFAULT_MIN_SETPOINT,
    DEFAULT_NIGHT_START,
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
    DEFAULT_WINDOW_DELAY_CLOSE,
    DEFAULT_WINDOW_DELAY_OPEN,
    MODE_COMFORT,
    MODE_ECO,
    MODE_FROST_PROTECTION,
    MODE_NIGHT,
    ROOM_TYPE_BATHROOM,
    ROOM_TYPE_CORRIDOR,
    ROOM_TYPE_NORMAL,
    X4FP_PRESET_AWAY,
    X4FP_PRESET_COMFORT,
    X4FP_PRESET_ECO,
    X4FP_PRESET_OFF,
)


def build_global_settings_schema(current_data: dict[str, Any]) -> vol.Schema:
    """Build schema for global settings."""
    return vol.Schema(
        {
            vol.Optional(
                CONF_ALARM_ENTITY,
                default=current_data.get(CONF_ALARM_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["alarm_control_panel"],
                )
            ),
            vol.Optional(
                CONF_SEASON_CALENDAR,
                default=current_data.get(CONF_SEASON_CALENDAR),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["calendar", "binary_sensor"],
                )
            ),
        }
    )


def build_room_basic_schema(room_data: dict[str, Any] | None = None) -> vol.Schema:
    """Build schema for basic room info."""
    if room_data is None:
        return vol.Schema(
            {
                vol.Required(CONF_ROOM_NAME): cv.string,
                vol.Optional(CONF_ROOM_TYPE, default=ROOM_TYPE_NORMAL): vol.In(
                    {
                        ROOM_TYPE_NORMAL: "Normal (chambres - pas de timer lumière)",
                        ROOM_TYPE_CORRIDOR: "Couloir (timer 5min)",
                        ROOM_TYPE_BATHROOM: "Salle de bain (timer 15min + lumière pilote chauffage)",
                    }
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
            ): vol.In(
                {
                    ROOM_TYPE_NORMAL: "Normal (chambres)",
                    ROOM_TYPE_CORRIDOR: "Couloir (timer 5min)",
                    ROOM_TYPE_BATHROOM: "Salle de bain (timer 15min + pilote chauffage)",
                }
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
        schema_dict[vol.Optional(CONF_TEMPERATURE_SENSOR)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain=[SENSOR_DOMAIN])
            )
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

    # Climate entity
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
        schema_dict[
            vol.Optional(CONF_CLIMATE_BYPASS_SWITCH, default=bypass_switch)
        ] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=[SWITCH_DOMAIN, "input_boolean"])
        )
    else:
        schema_dict[vol.Optional(CONF_CLIMATE_BYPASS_SWITCH)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=[SWITCH_DOMAIN, "input_boolean"]
                )
            )
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
                selector.EntitySelectorConfig(
                    domain=[SWITCH_DOMAIN, "input_boolean"]
                )
            )
        )

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


def build_climate_config_schema(room_data: dict[str, Any]) -> vol.Schema:
    """Build schema for climate configuration."""
    return vol.Schema(
        {
            vol.Optional(
                CONF_TEMP_COMFORT,
                default=room_data.get(CONF_TEMP_COMFORT, DEFAULT_TEMP_COMFORT),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=15,
                    max=25,
                    step=0.5,
                    mode=selector.NumberSelectorMode.SLIDER,
                    unit_of_measurement="°C",
                )
            ),
            vol.Optional(
                CONF_TEMP_ECO,
                default=room_data.get(CONF_TEMP_ECO, DEFAULT_TEMP_ECO),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=15,
                    max=25,
                    step=0.5,
                    mode=selector.NumberSelectorMode.SLIDER,
                    unit_of_measurement="°C",
                )
            ),
            vol.Optional(
                CONF_TEMP_NIGHT,
                default=room_data.get(CONF_TEMP_NIGHT, DEFAULT_TEMP_NIGHT),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=15,
                    max=25,
                    step=0.5,
                    mode=selector.NumberSelectorMode.SLIDER,
                    unit_of_measurement="°C",
                )
            ),
            vol.Optional(
                CONF_TEMP_FROST_PROTECTION,
                default=room_data.get(
                    CONF_TEMP_FROST_PROTECTION, DEFAULT_TEMP_FROST_PROTECTION
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5,
                    max=15,
                    step=0.5,
                    mode=selector.NumberSelectorMode.SLIDER,
                    unit_of_measurement="°C",
                )
            ),
            vol.Optional(
                CONF_TEMP_COOL_COMFORT,
                default=room_data.get(
                    CONF_TEMP_COOL_COMFORT, DEFAULT_TEMP_COOL_COMFORT
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=20,
                    max=28,
                    step=0.5,
                    mode=selector.NumberSelectorMode.SLIDER,
                    unit_of_measurement="°C",
                )
            ),
            vol.Optional(
                CONF_TEMP_COOL_ECO,
                default=room_data.get(CONF_TEMP_COOL_ECO, DEFAULT_TEMP_COOL_ECO),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=20,
                    max=30,
                    step=0.5,
                    mode=selector.NumberSelectorMode.SLIDER,
                    unit_of_measurement="°C",
                )
            ),
            vol.Optional(
                CONF_CLIMATE_WINDOW_CHECK,
                default=room_data.get(CONF_CLIMATE_WINDOW_CHECK, True),
            ): selector.BooleanSelector(),
            # v0.3.0 Priority 2 additions
            vol.Optional(
                CONF_WINDOW_DELAY_OPEN,
                default=room_data.get(
                    CONF_WINDOW_DELAY_OPEN, DEFAULT_WINDOW_DELAY_OPEN
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=30,
                    step=1,
                    mode=selector.NumberSelectorMode.SLIDER,
                    unit_of_measurement="min",
                )
            ),
            vol.Optional(
                CONF_WINDOW_DELAY_CLOSE,
                default=room_data.get(
                    CONF_WINDOW_DELAY_CLOSE, DEFAULT_WINDOW_DELAY_CLOSE
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=30,
                    step=1,
                    mode=selector.NumberSelectorMode.SLIDER,
                    unit_of_measurement="min",
                )
            ),
            vol.Optional(
                CONF_SUMMER_POLICY,
                default=room_data.get(CONF_SUMMER_POLICY, DEFAULT_SUMMER_POLICY),
            ): vol.In(
                {
                    "off": "Off (éteindre radiateurs en été)",
                    "eco": "Eco (garder radiateurs en eco en été)",
                }
            ),
        }
    )


def build_climate_advanced_schema(room_data: dict[str, Any]) -> vol.Schema:
    """Build schema for advanced climate configuration."""
    schema_dict = {}

    # Hysteresis configuration (X4FP Type 3b)
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
    ] = vol.In(
        {
            X4FP_PRESET_COMFORT: "Comfort",
            X4FP_PRESET_ECO: "Eco",
        }
    )

    schema_dict[
        vol.Optional(
            CONF_PRESET_IDLE,
            default=room_data.get(CONF_PRESET_IDLE, DEFAULT_PRESET_IDLE),
        )
    ] = vol.In(
        {
            X4FP_PRESET_ECO: "Eco",
            X4FP_PRESET_OFF: "Off (none)",
        }
    )

    # External Control configuration
    schema_dict[
        vol.Optional(
            CONF_EXTERNAL_CONTROL_PRESET,
            default=room_data.get(
                CONF_EXTERNAL_CONTROL_PRESET, DEFAULT_EXTERNAL_CONTROL_PRESET
            ),
        )
    ] = vol.In(
        {
            X4FP_PRESET_COMFORT: "Comfort",
            X4FP_PRESET_ECO: "Eco",
        }
    )

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

    # X4FP Configurable Presets
    schema_dict[
        vol.Optional(
            CONF_PRESET_COMFORT,
            default=room_data.get(CONF_PRESET_COMFORT, DEFAULT_PRESET_COMFORT),
        )
    ] = vol.In(
        {
            X4FP_PRESET_COMFORT: "Comfort",
            X4FP_PRESET_ECO: "Eco",
        }
    )

    schema_dict[
        vol.Optional(
            CONF_PRESET_ECO,
            default=room_data.get(CONF_PRESET_ECO, DEFAULT_PRESET_ECO),
        )
    ] = vol.In(
        {
            X4FP_PRESET_ECO: "Eco",
            X4FP_PRESET_COMFORT: "Comfort",
        }
    )

    schema_dict[
        vol.Optional(
            CONF_PRESET_NIGHT,
            default=room_data.get(CONF_PRESET_NIGHT, DEFAULT_PRESET_NIGHT),
        )
    ] = vol.In(
        {
            X4FP_PRESET_ECO: "Eco",
            X4FP_PRESET_COMFORT: "Comfort",
            X4FP_PRESET_AWAY: "Away",
        }
    )

    schema_dict[
        vol.Optional(
            CONF_PRESET_AWAY,
            default=room_data.get(CONF_PRESET_AWAY, DEFAULT_PRESET_AWAY),
        )
    ] = vol.In(
        {
            X4FP_PRESET_AWAY: "Away (hors-gel)",
            X4FP_PRESET_ECO: "Eco",
            X4FP_PRESET_OFF: "Off (none)",
        }
    )

    schema_dict[
        vol.Optional(
            CONF_PRESET_WINDOW,
            default=room_data.get(CONF_PRESET_WINDOW, DEFAULT_PRESET_WINDOW),
        )
    ] = vol.In(
        {
            X4FP_PRESET_AWAY: "Away (hors-gel)",
            X4FP_PRESET_ECO: "Eco",
            X4FP_PRESET_OFF: "Off (none)",
        }
    )

    return vol.Schema(schema_dict)


def build_schedule_schema(room_data: dict[str, Any]) -> vol.Schema:
    """Build schema for schedule configuration."""
    # Format existing comfort ranges for display
    from .helpers import format_comfort_ranges

    comfort_ranges = room_data.get(CONF_COMFORT_TIME_RANGES, [])
    comfort_ranges_text = format_comfort_ranges(comfort_ranges)

    schema_dict = {
        vol.Optional(
            CONF_NIGHT_START,
            default=room_data.get(CONF_NIGHT_START, DEFAULT_NIGHT_START),
        ): selector.TimeSelector(),
        vol.Optional(
            "comfort_ranges",
            default=comfort_ranges_text,
        ): cv.string,
    }

    # v0.3.0 - Calendar/Schedule entity support
    schedule_entity = room_data.get(CONF_SCHEDULE_ENTITY)
    if schedule_entity is not None:
        schema_dict[vol.Optional(CONF_SCHEDULE_ENTITY, default=schedule_entity)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["calendar", "schedule"])
            )
        )
    else:
        schema_dict[vol.Optional(CONF_SCHEDULE_ENTITY)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["calendar", "schedule"])
        )

    # Presets for schedule on/off
    schema_dict[
        vol.Optional(
            CONF_PRESET_SCHEDULE_ON,
            default=room_data.get(CONF_PRESET_SCHEDULE_ON, MODE_COMFORT),
        )
    ] = vol.In(
        {
            MODE_COMFORT: "Comfort",
            MODE_ECO: "Eco",
            MODE_NIGHT: "Night",
        }
    )

    schema_dict[
        vol.Optional(
            CONF_PRESET_SCHEDULE_OFF,
            default=room_data.get(CONF_PRESET_SCHEDULE_OFF, MODE_ECO),
        )
    ] = vol.In(
        {
            MODE_ECO: "Eco",
            MODE_NIGHT: "Night",
            MODE_FROST_PROTECTION: "Frost Protection",
        }
    )

    return vol.Schema(schema_dict)


def build_room_control_schema(room_data: dict[str, Any]) -> vol.Schema:
    """Build schema for room control configuration."""
    return vol.Schema(
        {
            vol.Optional(
                CONF_PAUSE_DURATION_MINUTES,
                default=room_data.get(
                    CONF_PAUSE_DURATION_MINUTES, DEFAULT_PAUSE_DURATION
                ),
            ): vol.In(
                {
                    15: "15 minutes",
                    30: "30 minutes",
                    60: "1 heure",
                    120: "2 heures",
                    240: "4 heures",
                    480: "8 heures",
                }
            ),
            vol.Optional(
                CONF_PAUSE_INFINITE,
                default=room_data.get(CONF_PAUSE_INFINITE, DEFAULT_PAUSE_INFINITE),
            ): selector.BooleanSelector(),
        }
    )
