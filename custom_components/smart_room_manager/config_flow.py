"""Config flow for Smart Room Manager integration."""
from __future__ import annotations

import logging
from typing import Any
import uuid

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
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_ALARM_ENTITY,
    CONF_CLIMATE_ENTITY,
    CONF_CLIMATE_PRESENCE_REQUIRED,
    CONF_CLIMATE_UNOCCUPIED_DELAY,
    CONF_CLIMATE_WINDOW_CHECK,
    CONF_DAY_START,
    CONF_DOOR_WINDOW_SENSORS,
    CONF_EVENING_START,
    CONF_GUEST_MODE_ENTITY,
    CONF_HEATING_SWITCHES,
    CONF_HUMIDITY_SENSOR,
    CONF_LIGHTS,
    CONF_LIGHT_DAY_BRIGHTNESS,
    CONF_LIGHT_LUX_THRESHOLD,
    CONF_LIGHT_NIGHT_BRIGHTNESS,
    CONF_LIGHT_NIGHT_MODE,
    CONF_LIGHT_TIMEOUT,
    CONF_LUMINOSITY_SENSOR,
    CONF_MORNING_START,
    CONF_NIGHT_START,
    CONF_PRESENCE_SENSORS,
    CONF_ROOM_ID,
    CONF_ROOM_NAME,
    CONF_ROOMS,
    CONF_SEASON_SENSOR,
    CONF_TEMPERATURE_SENSOR,
    CONF_TEMP_AWAY,
    CONF_TEMP_COMFORT,
    CONF_TEMP_ECO,
    CONF_TEMP_FROST_PROTECTION,
    CONF_TEMP_NIGHT,
    CONF_VACATION_MODE_ENTITY,
    DEFAULT_CLIMATE_UNOCCUPIED_DELAY,
    DEFAULT_DAY_START,
    DEFAULT_EVENING_START,
    DEFAULT_LIGHT_DAY_BRIGHTNESS,
    DEFAULT_LIGHT_LUX_THRESHOLD,
    DEFAULT_LIGHT_NIGHT_BRIGHTNESS,
    DEFAULT_LIGHT_TIMEOUT,
    DEFAULT_MORNING_START,
    DEFAULT_NIGHT_START,
    DEFAULT_TEMP_AWAY,
    DEFAULT_TEMP_COMFORT,
    DEFAULT_TEMP_ECO,
    DEFAULT_TEMP_FROST_PROTECTION,
    DEFAULT_TEMP_NIGHT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class SmartRoomManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Room Manager."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            # Store configuration
            return self.async_create_entry(
                title="Smart Room Manager",
                data={
                    CONF_NAME: user_input.get(CONF_NAME, "Smart Room Manager"),
                },
                options={
                    CONF_ROOMS: [],
                    # Global settings
                    CONF_GUEST_MODE_ENTITY: user_input.get(CONF_GUEST_MODE_ENTITY),
                    CONF_VACATION_MODE_ENTITY: user_input.get(CONF_VACATION_MODE_ENTITY),
                    CONF_ALARM_ENTITY: user_input.get(CONF_ALARM_ENTITY),
                    CONF_SEASON_SENSOR: user_input.get(CONF_SEASON_SENSOR),
                },
            )

        # Show form
        data_schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default="Smart Room Manager"): cv.string,
                vol.Optional(CONF_GUEST_MODE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["input_boolean", "binary_sensor"],
                    )
                ),
                vol.Optional(CONF_VACATION_MODE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["input_boolean", "binary_sensor"],
                    )
                ),
                vol.Optional(CONF_ALARM_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["alarm_control_panel"],
                    )
                ),
                vol.Optional(CONF_SEASON_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=[SENSOR_DOMAIN],
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SmartRoomManagerOptionsFlow:
        """Get the options flow for this handler."""
        return SmartRoomManagerOptionsFlow(config_entry)


class SmartRoomManagerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Smart Room Manager."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
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
                description_placeholders={"rooms": "Aucune pièce configurée."},
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
                return await self.async_step_edit_room()
            elif action == "delete":
                return await self.async_step_delete_room()

        # Build room list for selection
        room_choices = {}
        for idx, room in enumerate(rooms):
            room_name = room.get(CONF_ROOM_NAME, f"Room {idx + 1}")
            room_choices[f"edit_{idx}"] = f"✏️ Modifier: {room_name}"
            room_choices[f"delete_{idx}"] = f"🗑️ Supprimer: {room_name}"
        room_choices["back"] = "⬅️ Retour"

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
        """Add a new room - step 1: basic info."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._current_room = {
                CONF_ROOM_ID: str(uuid.uuid4())[:8],
                CONF_ROOM_NAME: user_input[CONF_ROOM_NAME],
            }
            return await self.async_step_room_sensors()

        return self.async_show_form(
            step_id="add_room",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ROOM_NAME): cv.string,
                }
            ),
            errors=errors,
        )

    async def async_step_edit_room(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Edit room - step 1: basic info."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._current_room[CONF_ROOM_NAME] = user_input[CONF_ROOM_NAME]
            return await self.async_step_room_sensors()

        return self.async_show_form(
            step_id="edit_room",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ROOM_NAME,
                        default=self._current_room.get(CONF_ROOM_NAME, ""),
                    ): cv.string,
                }
            ),
            errors=errors,
        )

    async def async_step_room_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure room sensors."""
        if user_input is not None:
            self._current_room.update(
                {
                    CONF_PRESENCE_SENSORS: user_input.get(CONF_PRESENCE_SENSORS, []),
                    CONF_DOOR_WINDOW_SENSORS: user_input.get(CONF_DOOR_WINDOW_SENSORS, []),
                    CONF_LUMINOSITY_SENSOR: user_input.get(CONF_LUMINOSITY_SENSOR),
                    CONF_TEMPERATURE_SENSOR: user_input.get(CONF_TEMPERATURE_SENSOR),
                    CONF_HUMIDITY_SENSOR: user_input.get(CONF_HUMIDITY_SENSOR),
                }
            )
            return await self.async_step_room_actuators()

        return self.async_show_form(
            step_id="room_sensors",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_PRESENCE_SENSORS,
                        default=self._current_room.get(CONF_PRESENCE_SENSORS, []),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=[BINARY_SENSOR_DOMAIN],
                            multiple=True,
                        )
                    ),
                    vol.Optional(
                        CONF_DOOR_WINDOW_SENSORS,
                        default=self._current_room.get(CONF_DOOR_WINDOW_SENSORS, []),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=[BINARY_SENSOR_DOMAIN],
                            multiple=True,
                        )
                    ),
                    vol.Optional(
                        CONF_LUMINOSITY_SENSOR,
                        default=self._current_room.get(CONF_LUMINOSITY_SENSOR),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=[SENSOR_DOMAIN],
                        )
                    ),
                    vol.Optional(
                        CONF_TEMPERATURE_SENSOR,
                        default=self._current_room.get(CONF_TEMPERATURE_SENSOR),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=[SENSOR_DOMAIN],
                        )
                    ),
                    vol.Optional(
                        CONF_HUMIDITY_SENSOR,
                        default=self._current_room.get(CONF_HUMIDITY_SENSOR),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=[SENSOR_DOMAIN],
                        )
                    ),
                }
            ),
            description_placeholders={"room_name": self._current_room[CONF_ROOM_NAME]},
        )

    async def async_step_room_actuators(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure room actuators."""
        if user_input is not None:
            self._current_room.update(
                {
                    CONF_LIGHTS: user_input.get(CONF_LIGHTS, []),
                    CONF_CLIMATE_ENTITY: user_input.get(CONF_CLIMATE_ENTITY),
                    CONF_HEATING_SWITCHES: user_input.get(CONF_HEATING_SWITCHES, []),
                }
            )
            return await self.async_step_room_light_config()

        return self.async_show_form(
            step_id="room_actuators",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_LIGHTS,
                        default=self._current_room.get(CONF_LIGHTS, []),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=[LIGHT_DOMAIN, SWITCH_DOMAIN],
                            multiple=True,
                        )
                    ),
                    vol.Optional(
                        CONF_CLIMATE_ENTITY,
                        default=self._current_room.get(CONF_CLIMATE_ENTITY),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=[CLIMATE_DOMAIN],
                        )
                    ),
                    vol.Optional(
                        CONF_HEATING_SWITCHES,
                        default=self._current_room.get(CONF_HEATING_SWITCHES, []),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=[SWITCH_DOMAIN],
                            multiple=True,
                        )
                    ),
                }
            ),
            description_placeholders={"room_name": self._current_room[CONF_ROOM_NAME]},
        )

    async def async_step_room_light_config(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure light behavior."""
        if user_input is not None:
            self._current_room.update(
                {
                    CONF_LIGHT_LUX_THRESHOLD: user_input.get(
                        CONF_LIGHT_LUX_THRESHOLD, DEFAULT_LIGHT_LUX_THRESHOLD
                    ),
                    CONF_LIGHT_TIMEOUT: user_input.get(
                        CONF_LIGHT_TIMEOUT, DEFAULT_LIGHT_TIMEOUT
                    ),
                    CONF_LIGHT_NIGHT_MODE: user_input.get(CONF_LIGHT_NIGHT_MODE, True),
                    CONF_LIGHT_NIGHT_BRIGHTNESS: user_input.get(
                        CONF_LIGHT_NIGHT_BRIGHTNESS, DEFAULT_LIGHT_NIGHT_BRIGHTNESS
                    ),
                    CONF_LIGHT_DAY_BRIGHTNESS: user_input.get(
                        CONF_LIGHT_DAY_BRIGHTNESS, DEFAULT_LIGHT_DAY_BRIGHTNESS
                    ),
                }
            )
            return await self.async_step_room_climate_config()

        return self.async_show_form(
            step_id="room_light_config",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_LIGHT_LUX_THRESHOLD,
                        default=self._current_room.get(
                            CONF_LIGHT_LUX_THRESHOLD, DEFAULT_LIGHT_LUX_THRESHOLD
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=1000,
                            step=10,
                            mode=selector.NumberSelectorMode.SLIDER,
                            unit_of_measurement="lx",
                        )
                    ),
                    vol.Optional(
                        CONF_LIGHT_TIMEOUT,
                        default=self._current_room.get(
                            CONF_LIGHT_TIMEOUT, DEFAULT_LIGHT_TIMEOUT
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=60,
                            max=3600,
                            step=30,
                            mode=selector.NumberSelectorMode.SLIDER,
                            unit_of_measurement="s",
                        )
                    ),
                    vol.Optional(
                        CONF_LIGHT_NIGHT_MODE,
                        default=self._current_room.get(CONF_LIGHT_NIGHT_MODE, True),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_LIGHT_NIGHT_BRIGHTNESS,
                        default=self._current_room.get(
                            CONF_LIGHT_NIGHT_BRIGHTNESS, DEFAULT_LIGHT_NIGHT_BRIGHTNESS
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=100,
                            step=1,
                            mode=selector.NumberSelectorMode.SLIDER,
                            unit_of_measurement="%",
                        )
                    ),
                    vol.Optional(
                        CONF_LIGHT_DAY_BRIGHTNESS,
                        default=self._current_room.get(
                            CONF_LIGHT_DAY_BRIGHTNESS, DEFAULT_LIGHT_DAY_BRIGHTNESS
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=100,
                            step=1,
                            mode=selector.NumberSelectorMode.SLIDER,
                            unit_of_measurement="%",
                        )
                    ),
                }
            ),
            description_placeholders={"room_name": self._current_room[CONF_ROOM_NAME]},
        )

    async def async_step_room_climate_config(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure climate behavior."""
        if user_input is not None:
            self._current_room.update(
                {
                    CONF_TEMP_COMFORT: user_input.get(
                        CONF_TEMP_COMFORT, DEFAULT_TEMP_COMFORT
                    ),
                    CONF_TEMP_ECO: user_input.get(CONF_TEMP_ECO, DEFAULT_TEMP_ECO),
                    CONF_TEMP_NIGHT: user_input.get(CONF_TEMP_NIGHT, DEFAULT_TEMP_NIGHT),
                    CONF_TEMP_AWAY: user_input.get(CONF_TEMP_AWAY, DEFAULT_TEMP_AWAY),
                    CONF_TEMP_FROST_PROTECTION: user_input.get(
                        CONF_TEMP_FROST_PROTECTION, DEFAULT_TEMP_FROST_PROTECTION
                    ),
                    CONF_CLIMATE_PRESENCE_REQUIRED: user_input.get(
                        CONF_CLIMATE_PRESENCE_REQUIRED, False
                    ),
                    CONF_CLIMATE_WINDOW_CHECK: user_input.get(
                        CONF_CLIMATE_WINDOW_CHECK, True
                    ),
                    CONF_CLIMATE_UNOCCUPIED_DELAY: user_input.get(
                        CONF_CLIMATE_UNOCCUPIED_DELAY,
                        DEFAULT_CLIMATE_UNOCCUPIED_DELAY,
                    ),
                }
            )
            return await self.async_step_room_schedule()

        return self.async_show_form(
            step_id="room_climate_config",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_TEMP_COMFORT,
                        default=self._current_room.get(
                            CONF_TEMP_COMFORT, DEFAULT_TEMP_COMFORT
                        ),
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
                        default=self._current_room.get(CONF_TEMP_ECO, DEFAULT_TEMP_ECO),
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
                        default=self._current_room.get(
                            CONF_TEMP_NIGHT, DEFAULT_TEMP_NIGHT
                        ),
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
                        CONF_TEMP_AWAY,
                        default=self._current_room.get(
                            CONF_TEMP_AWAY, DEFAULT_TEMP_AWAY
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=10,
                            max=20,
                            step=0.5,
                            mode=selector.NumberSelectorMode.SLIDER,
                            unit_of_measurement="°C",
                        )
                    ),
                    vol.Optional(
                        CONF_TEMP_FROST_PROTECTION,
                        default=self._current_room.get(
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
                        CONF_CLIMATE_PRESENCE_REQUIRED,
                        default=self._current_room.get(
                            CONF_CLIMATE_PRESENCE_REQUIRED, False
                        ),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_CLIMATE_WINDOW_CHECK,
                        default=self._current_room.get(CONF_CLIMATE_WINDOW_CHECK, True),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_CLIMATE_UNOCCUPIED_DELAY,
                        default=self._current_room.get(
                            CONF_CLIMATE_UNOCCUPIED_DELAY,
                            DEFAULT_CLIMATE_UNOCCUPIED_DELAY,
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=300,
                            max=7200,
                            step=300,
                            mode=selector.NumberSelectorMode.SLIDER,
                            unit_of_measurement="s",
                        )
                    ),
                }
            ),
            description_placeholders={"room_name": self._current_room[CONF_ROOM_NAME]},
        )

    async def async_step_room_schedule(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure room schedule."""
        if user_input is not None:
            self._current_room.update(
                {
                    CONF_MORNING_START: user_input.get(
                        CONF_MORNING_START, DEFAULT_MORNING_START
                    ),
                    CONF_DAY_START: user_input.get(CONF_DAY_START, DEFAULT_DAY_START),
                    CONF_EVENING_START: user_input.get(
                        CONF_EVENING_START, DEFAULT_EVENING_START
                    ),
                    CONF_NIGHT_START: user_input.get(
                        CONF_NIGHT_START, DEFAULT_NIGHT_START
                    ),
                }
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
            step_id="room_schedule",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_MORNING_START,
                        default=self._current_room.get(
                            CONF_MORNING_START, DEFAULT_MORNING_START
                        ),
                    ): selector.TimeSelector(),
                    vol.Optional(
                        CONF_DAY_START,
                        default=self._current_room.get(
                            CONF_DAY_START, DEFAULT_DAY_START
                        ),
                    ): selector.TimeSelector(),
                    vol.Optional(
                        CONF_EVENING_START,
                        default=self._current_room.get(
                            CONF_EVENING_START, DEFAULT_EVENING_START
                        ),
                    ): selector.TimeSelector(),
                    vol.Optional(
                        CONF_NIGHT_START,
                        default=self._current_room.get(
                            CONF_NIGHT_START, DEFAULT_NIGHT_START
                        ),
                    ): selector.TimeSelector(),
                }
            ),
            description_placeholders={"room_name": self._current_room[CONF_ROOM_NAME]},
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
        """Configure global settings."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    **self.config_entry.options,
                    CONF_GUEST_MODE_ENTITY: user_input.get(CONF_GUEST_MODE_ENTITY),
                    CONF_VACATION_MODE_ENTITY: user_input.get(CONF_VACATION_MODE_ENTITY),
                    CONF_ALARM_ENTITY: user_input.get(CONF_ALARM_ENTITY),
                    CONF_SEASON_SENSOR: user_input.get(CONF_SEASON_SENSOR),
                },
            )

        return self.async_show_form(
            step_id="global_settings",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_GUEST_MODE_ENTITY,
                        default=self.config_entry.options.get(CONF_GUEST_MODE_ENTITY),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["input_boolean", "binary_sensor"],
                        )
                    ),
                    vol.Optional(
                        CONF_VACATION_MODE_ENTITY,
                        default=self.config_entry.options.get(
                            CONF_VACATION_MODE_ENTITY
                        ),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["input_boolean", "binary_sensor"],
                        )
                    ),
                    vol.Optional(
                        CONF_ALARM_ENTITY,
                        default=self.config_entry.options.get(CONF_ALARM_ENTITY),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["alarm_control_panel"],
                        )
                    ),
                    vol.Optional(
                        CONF_SEASON_SENSOR,
                        default=self.config_entry.options.get(CONF_SEASON_SENSOR),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=[SENSOR_DOMAIN],
                        )
                    ),
                }
            ),
        )
