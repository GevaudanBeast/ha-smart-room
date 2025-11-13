"""Constants for the Smart Room Manager integration."""
from typing import Final

# Integration domain
DOMAIN: Final = "smart_room_manager"

# Configuration and options
CONF_ROOMS: Final = "rooms"
CONF_ROOM_NAME: Final = "room_name"
CONF_ROOM_ID: Final = "room_id"

# Sensor configuration
CONF_PRESENCE_SENSORS: Final = "presence_sensors"
CONF_DOOR_WINDOW_SENSORS: Final = "door_window_sensors"
CONF_LUMINOSITY_SENSOR: Final = "luminosity_sensor"
CONF_TEMPERATURE_SENSOR: Final = "temperature_sensor"
CONF_HUMIDITY_SENSOR: Final = "humidity_sensor"

# Actuator configuration
CONF_LIGHTS: Final = "lights"
CONF_CLIMATE_ENTITY: Final = "climate_entity"
CONF_HEATING_SWITCHES: Final = "heating_switches"
CONF_SOLAR_OPTIMIZER_SWITCH: Final = "solar_optimizer_switch"

# Light behavior configuration
CONF_LIGHT_LUX_THRESHOLD: Final = "light_lux_threshold"
CONF_LIGHT_TIMEOUT: Final = "light_timeout"
CONF_LIGHT_NIGHT_MODE: Final = "light_night_mode"
CONF_LIGHT_NIGHT_BRIGHTNESS: Final = "light_night_brightness"
CONF_LIGHT_DAY_BRIGHTNESS: Final = "light_day_brightness"

# Climate behavior configuration
CONF_TEMP_COMFORT: Final = "temp_comfort"
CONF_TEMP_ECO: Final = "temp_eco"
CONF_TEMP_NIGHT: Final = "temp_night"
CONF_TEMP_AWAY: Final = "temp_away"
CONF_TEMP_FROST_PROTECTION: Final = "temp_frost_protection"
CONF_CLIMATE_PRESENCE_REQUIRED: Final = "climate_presence_required"
CONF_CLIMATE_WINDOW_CHECK: Final = "climate_window_check"
CONF_CLIMATE_UNOCCUPIED_DELAY: Final = "climate_unoccupied_delay"

# Schedule configuration
CONF_MORNING_START: Final = "morning_start"
CONF_DAY_START: Final = "day_start"
CONF_EVENING_START: Final = "evening_start"
CONF_NIGHT_START: Final = "night_start"

# Global modes
CONF_GUEST_MODE_ENTITY: Final = "guest_mode_entity"
CONF_VACATION_MODE_ENTITY: Final = "vacation_mode_entity"
CONF_ALARM_ENTITY: Final = "alarm_entity"
CONF_SEASON_SENSOR: Final = "season_sensor"

# Default values
DEFAULT_LIGHT_LUX_THRESHOLD: Final = 50
DEFAULT_LIGHT_TIMEOUT: Final = 300  # 5 minutes
DEFAULT_LIGHT_NIGHT_BRIGHTNESS: Final = 20
DEFAULT_LIGHT_DAY_BRIGHTNESS: Final = 100
DEFAULT_TEMP_COMFORT: Final = 20.0
DEFAULT_TEMP_ECO: Final = 18.0
DEFAULT_TEMP_NIGHT: Final = 17.0
DEFAULT_TEMP_AWAY: Final = 16.0
DEFAULT_TEMP_FROST_PROTECTION: Final = 7.0
DEFAULT_CLIMATE_UNOCCUPIED_DELAY: Final = 1800  # 30 minutes
DEFAULT_MORNING_START: Final = "07:00:00"
DEFAULT_DAY_START: Final = "09:00:00"
DEFAULT_EVENING_START: Final = "18:00:00"
DEFAULT_NIGHT_START: Final = "22:00:00"

# Entity ID formats
SENSOR_FORMAT: Final = "sensor.smart_room_{room_id}_state"
BINARY_SENSOR_OCCUPIED_FORMAT: Final = "binary_sensor.smart_room_{room_id}_occupied"
BINARY_SENSOR_LIGHT_NEEDED_FORMAT: Final = "binary_sensor.smart_room_{room_id}_light_needed"
SWITCH_AUTOMATION_FORMAT: Final = "switch.smart_room_{room_id}_automation"

# Attributes
ATTR_ROOM_ID: Final = "room_id"
ATTR_ROOM_NAME: Final = "room_name"
ATTR_OCCUPIED: Final = "occupied"
ATTR_LUMINOSITY: Final = "luminosity"
ATTR_TEMPERATURE: Final = "temperature"
ATTR_HUMIDITY: Final = "humidity"
ATTR_LIGHT_STATE: Final = "light_state"
ATTR_CLIMATE_STATE: Final = "climate_state"
ATTR_CURRENT_MODE: Final = "current_mode"
ATTR_TARGET_TEMPERATURE: Final = "target_temperature"
ATTR_WINDOWS_OPEN: Final = "windows_open"

# Update intervals
UPDATE_INTERVAL: Final = 30  # seconds

# Time periods
TIME_PERIOD_MORNING: Final = "morning"
TIME_PERIOD_DAY: Final = "day"
TIME_PERIOD_EVENING: Final = "evening"
TIME_PERIOD_NIGHT: Final = "night"

# Modes
MODE_COMFORT: Final = "comfort"
MODE_ECO: Final = "eco"
MODE_NIGHT: Final = "night"
MODE_AWAY: Final = "away"
MODE_FROST_PROTECTION: Final = "frost_protection"
MODE_GUEST: Final = "guest"
