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
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (  # v0.3.0 Priority 1 additions; v0.3.0 Priority 2 additions
    CONF_ALARM_ENTITY,
    CONF_ALLOW_EXTERNAL_IN_AWAY,
    CONF_CLIMATE_BYPASS_SWITCH,
    CONF_CLIMATE_ENTITY,
    CONF_CLIMATE_WINDOW_CHECK,
    CONF_COMFORT_TIME_RANGES,
    CONF_DOOR_WINDOW_SENSORS,
    CONF_EXTERNAL_CONTROL_PRESET,
    CONF_EXTERNAL_CONTROL_SWITCH,
    CONF_EXTERNAL_CONTROL_TEMP,
    CONF_HUMIDITY_SENSOR,
    CONF_HYSTERESIS,
    CONF_LIGHT_TIMEOUT,
    CONF_LIGHTS,
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
    CONF_WINDOW_DELAY_CLOSE,
    CONF_WINDOW_DELAY_OPEN,
    DEFAULT_ALLOW_EXTERNAL_IN_AWAY,
    DEFAULT_EXTERNAL_CONTROL_PRESET,
    DEFAULT_EXTERNAL_CONTROL_TEMP,
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
    DOMAIN,
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

_LOGGER = logging.getLogger(__name__)


# Helper functions for config flow


def parse_comfort_ranges(comfort_ranges_text: str) -> list[dict[str, str]]:
    """Parse comfort time ranges from text format.

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
                "description": "Configuration simplifiée v0.2.0 - Alarme détermine présence, pas de capteurs présence/luminosité"
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
        # Note: self.config_entry is automatically provided by OptionsFlow parent class (HA 2025.12+)
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
                    "rooms": "Aucune pièce configurée. Retournez au menu pour ajouter une pièce."
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
                "info": "Type normal: pas de timer. Couloir/SdB: timer auto-off."
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
                "info": "Tous optionnels. Fenêtres → hors-gel si ouvertes.",
            },
        )

    async def async_step_room_actuators(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure room actuators (v0.3.0)."""
        if user_input is not None:
            # Only save actuators that are actually configured (non-empty)
            update_data = {
                CONF_LIGHTS: user_input.get(CONF_LIGHTS, []),
            }

            # Add optional climate entity only if configured
            if user_input.get(CONF_CLIMATE_ENTITY):
                update_data[CONF_CLIMATE_ENTITY] = user_input.get(CONF_CLIMATE_ENTITY)

            # Add optional bypass switch only if configured
            if user_input.get(CONF_CLIMATE_BYPASS_SWITCH):
                update_data[CONF_CLIMATE_BYPASS_SWITCH] = user_input.get(
                    CONF_CLIMATE_BYPASS_SWITCH
                )

            # Add optional external control switch only if configured (v0.3.0)
            if user_input.get(CONF_EXTERNAL_CONTROL_SWITCH):
                update_data[CONF_EXTERNAL_CONTROL_SWITCH] = user_input.get(
                    CONF_EXTERNAL_CONTROL_SWITCH
                )

            self._current_room.update(update_data)
            return await self.async_step_room_light_config()

        return self.async_show_form(
            step_id="room_actuators",
            data_schema=build_room_actuators_schema(self._current_room),
            description_placeholders={
                "room_name": self._current_room[CONF_ROOM_NAME],
                "info": "Bypass: désactive tout contrôle. External Control: Solar Optimizer, etc. (priorité haute)",
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
                    "info": f"Type {room_type}: auto-off après timeout",
                },
            )
        else:
            # Skip light config for normal rooms (no timer)
            return await self.async_step_room_climate_config()

    async def async_step_room_climate_config(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure climate behavior (v0.3.0 - 4 modes, summer/winter, window delays, summer policy)."""
        if user_input is not None:
            self._current_room.update(
                {
                    CONF_TEMP_COMFORT: user_input.get(
                        CONF_TEMP_COMFORT, DEFAULT_TEMP_COMFORT
                    ),
                    CONF_TEMP_ECO: user_input.get(CONF_TEMP_ECO, DEFAULT_TEMP_ECO),
                    CONF_TEMP_NIGHT: user_input.get(
                        CONF_TEMP_NIGHT, DEFAULT_TEMP_NIGHT
                    ),
                    CONF_TEMP_FROST_PROTECTION: user_input.get(
                        CONF_TEMP_FROST_PROTECTION, DEFAULT_TEMP_FROST_PROTECTION
                    ),
                    CONF_TEMP_COOL_COMFORT: user_input.get(
                        CONF_TEMP_COOL_COMFORT, DEFAULT_TEMP_COOL_COMFORT
                    ),
                    CONF_TEMP_COOL_ECO: user_input.get(
                        CONF_TEMP_COOL_ECO, DEFAULT_TEMP_COOL_ECO
                    ),
                    CONF_CLIMATE_WINDOW_CHECK: user_input.get(
                        CONF_CLIMATE_WINDOW_CHECK, True
                    ),
                    # v0.3.0 Priority 2 additions
                    CONF_WINDOW_DELAY_OPEN: user_input.get(
                        CONF_WINDOW_DELAY_OPEN, DEFAULT_WINDOW_DELAY_OPEN
                    ),
                    CONF_WINDOW_DELAY_CLOSE: user_input.get(
                        CONF_WINDOW_DELAY_CLOSE, DEFAULT_WINDOW_DELAY_CLOSE
                    ),
                    CONF_SUMMER_POLICY: user_input.get(
                        CONF_SUMMER_POLICY, DEFAULT_SUMMER_POLICY
                    ),
                }
            )
            return await self.async_step_room_climate_advanced()

        return self.async_show_form(
            step_id="room_climate_config",
            data_schema=build_climate_config_schema(self._current_room),
            description_placeholders={
                "room_name": self._current_room[CONF_ROOM_NAME],
                "info": "Températures hiver/été. Window delays: temps avant réaction fenêtres. Summer policy: X4FP en été.",
            },
        )

    async def async_step_room_climate_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure advanced climate features (v0.3.0 - Hysteresis, External Control, X4FP Presets)."""
        if user_input is not None:
            # Save optional advanced config
            update_data = {}

            # Hysteresis configuration (only if both temp sensor and setpoint are configured)
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

            # External Control configuration
            update_data[CONF_EXTERNAL_CONTROL_PRESET] = user_input.get(
                CONF_EXTERNAL_CONTROL_PRESET, DEFAULT_EXTERNAL_CONTROL_PRESET
            )
            update_data[CONF_EXTERNAL_CONTROL_TEMP] = user_input.get(
                CONF_EXTERNAL_CONTROL_TEMP, DEFAULT_EXTERNAL_CONTROL_TEMP
            )
            update_data[CONF_ALLOW_EXTERNAL_IN_AWAY] = user_input.get(
                CONF_ALLOW_EXTERNAL_IN_AWAY, DEFAULT_ALLOW_EXTERNAL_IN_AWAY
            )

            # X4FP Configurable Presets (Priority 2)
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

            self._current_room.update(update_data)
            return await self.async_step_room_schedule()

        return self.async_show_form(
            step_id="room_climate_advanced",
            data_schema=build_climate_advanced_schema(self._current_room),
            description_placeholders={
                "room_name": self._current_room[CONF_ROOM_NAME],
                "info": "Hysteresis: contrôle X4FP via temp (setpoint requis). External Control: config Solar Optimizer. Presets: personnaliser X4FP.",
            },
        )

    async def async_step_room_schedule(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure room schedule (v0.3.0 - night_start, comfort_time_ranges, calendar, presets)."""
        if user_input is not None:
            # Save night start
            self._current_room[CONF_NIGHT_START] = user_input.get(
                CONF_NIGHT_START, DEFAULT_NIGHT_START
            )

            # Parse comfort time ranges using helper
            comfort_ranges_text = user_input.get("comfort_ranges", "")
            comfort_ranges = parse_comfort_ranges(comfort_ranges_text)
            self._current_room[CONF_COMFORT_TIME_RANGES] = comfort_ranges

            # v0.3.0 - Schedule entity (calendar) support
            if user_input.get(CONF_SCHEDULE_ENTITY):
                self._current_room[CONF_SCHEDULE_ENTITY] = user_input.get(
                    CONF_SCHEDULE_ENTITY
                )

                # Presets for schedule on/off
                if user_input.get(CONF_PRESET_SCHEDULE_ON):
                    self._current_room[CONF_PRESET_SCHEDULE_ON] = user_input.get(
                        CONF_PRESET_SCHEDULE_ON
                    )
                if user_input.get(CONF_PRESET_SCHEDULE_OFF):
                    self._current_room[CONF_PRESET_SCHEDULE_OFF] = user_input.get(
                        CONF_PRESET_SCHEDULE_OFF
                    )

            return await self.async_step_room_control()

        return self.async_show_form(
            step_id="room_schedule",
            data_schema=build_schedule_schema(self._current_room),
            description_placeholders={
                "room_name": self._current_room[CONF_ROOM_NAME],
                "info": "Night start + comfort ranges (time-based). Calendar: externe (Google, etc.). Presets: mode si calendar ON/OFF",
            },
        )

    async def async_step_room_control(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure room control options (v0.3.0 - Manual pause configuration)."""
        if user_input is not None:
            # Save pause configuration
            self._current_room[CONF_PAUSE_DURATION_MINUTES] = user_input.get(
                CONF_PAUSE_DURATION_MINUTES, DEFAULT_PAUSE_DURATION
            )
            self._current_room[CONF_PAUSE_INFINITE] = user_input.get(
                CONF_PAUSE_INFINITE, DEFAULT_PAUSE_INFINITE
            )

            # Save the room
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

        return self.async_show_form(
            step_id="room_control",
            data_schema=build_room_control_schema(self._current_room),
            description_placeholders={
                "room_name": self._current_room[CONF_ROOM_NAME],
                "info": "Pause manuelle: durée par défaut du switch pause. Infinite: pause sans limite de temps.",
            },
        )

    async def async_step_delete_room(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Confirm room deletion."""
        rooms = list(self.config_entry.options.get(CONF_ROOMS, []))
        room_name = rooms[self._room_index].get(CONF_ROOM_NAME, "Unknown")

        if user_input is not None:
            if user_input.get("confirm"):
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

    async def async_step_global_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure global settings (v0.2.0 - alarm + season calendar)."""
        if user_input is not None:
            # Update entry data (not options) for global settings
            # Note: This requires updating entry.data which is normally immutable
            # We create a new data dict
            new_data = {
                **self.config_entry.data,
                CONF_ALARM_ENTITY: user_input.get(CONF_ALARM_ENTITY),
                CONF_SEASON_CALENDAR: user_input.get(CONF_SEASON_CALENDAR),
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
                "info": "Alarme: armed_away → hors-gel. Calendrier été: clim cool, hiver: heat.",
            },
        )
