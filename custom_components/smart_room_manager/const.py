"""Constants for the Smart Room Manager integration."""
from typing import Final

# Integration domain
DOMAIN: Final = "smart_room_manager"
VERSION: Final = "0.2.3"

# Configuration and options
CONF_ROOMS: Final = "rooms"
CONF_ROOM_NAME: Final = "room_name"
CONF_ROOM_ID: Final = "room_id"
CONF_ROOM_TYPE: Final = "room_type"
CONF_ROOM_ICON: Final = "room_icon"

# Room types
ROOM_TYPE_NORMAL: Final = "normal"  # Chambres - pas de timer lumière
ROOM_TYPE_CORRIDOR: Final = "corridor"  # Couloirs, WC - timer lumière
ROOM_TYPE_BATHROOM: Final = "bathroom"  # Salles de bains - timer + lumière pilote chauffage

# Sensor configuration
CONF_DOOR_WINDOW_SENSORS: Final = "door_window_sensors"
CONF_TEMPERATURE_SENSOR: Final = "temperature_sensor"
CONF_HUMIDITY_SENSOR: Final = "humidity_sensor"

# Actuator configuration
CONF_LIGHTS: Final = "lights"
CONF_CLIMATE_ENTITY: Final = "climate_entity"
CONF_CLIMATE_BYPASS_SWITCH: Final = "climate_bypass_switch"

# Light behavior configuration
CONF_LIGHT_TIMEOUT: Final = "light_timeout"
CONF_LIGHT_NIGHT_MODE: Final = "light_night_mode"
CONF_LIGHT_NIGHT_BRIGHTNESS: Final = "light_night_brightness"
CONF_LIGHT_DAY_BRIGHTNESS: Final = "light_day_brightness"

# Climate behavior configuration
CONF_TEMP_COMFORT: Final = "temp_comfort"
CONF_TEMP_ECO: Final = "temp_eco"
CONF_TEMP_NIGHT: Final = "temp_night"
CONF_TEMP_FROST_PROTECTION: Final = "temp_frost_protection"
CONF_CLIMATE_WINDOW_CHECK: Final = "climate_window_check"

# Clim specific (summer mode)
CONF_TEMP_COOL_COMFORT: Final = "temp_cool_comfort"
CONF_TEMP_COOL_ECO: Final = "temp_cool_eco"

# Schedule configuration
CONF_NIGHT_START: Final = "night_start"
CONF_COMFORT_TIME_RANGES: Final = "comfort_time_ranges"  # List of {"start": "HH:MM", "end": "HH:MM"}

# Global configuration
CONF_ALARM_ENTITY: Final = "alarm_entity"
CONF_SEASON_CALENDAR: Final = "season_calendar"

# Default values - Heating
DEFAULT_TEMP_COMFORT: Final = 20.0
DEFAULT_TEMP_ECO: Final = 18.0
DEFAULT_TEMP_NIGHT: Final = 17.0
DEFAULT_TEMP_FROST_PROTECTION: Final = 7.0

# Default values - Cooling (summer)
DEFAULT_TEMP_COOL_COMFORT: Final = 24.0
DEFAULT_TEMP_COOL_ECO: Final = 26.0

# Default values - Lights
DEFAULT_LIGHT_TIMEOUT: Final = 300  # 5 minutes
DEFAULT_LIGHT_TIMEOUT_BATHROOM: Final = 900  # 15 minutes
DEFAULT_LIGHT_NIGHT_BRIGHTNESS: Final = 50
DEFAULT_LIGHT_DAY_BRIGHTNESS: Final = 100

# Default values - Schedule
DEFAULT_NIGHT_START: Final = "22:00:00"

# Entity ID formats
SENSOR_FORMAT: Final = "sensor.smart_room_{room_id}_state"
BINARY_SENSOR_NIGHT_FORMAT: Final = "binary_sensor.smart_room_{room_id}_night"
BINARY_SENSOR_BYPASS_FORMAT: Final = "binary_sensor.smart_room_{room_id}_climate_bypass"
SWITCH_AUTOMATION_FORMAT: Final = "switch.smart_room_{room_id}_automation"

# Attributes
ATTR_ROOM_ID: Final = "room_id"
ATTR_ROOM_NAME: Final = "room_name"
ATTR_ROOM_TYPE: Final = "room_type"
ATTR_IS_NIGHT: Final = "is_night"
ATTR_WINDOWS_OPEN: Final = "windows_open"
ATTR_CLIMATE_BYPASS_ACTIVE: Final = "climate_bypass_active"
ATTR_ALARM_STATE: Final = "alarm_state"
ATTR_LIGHT_ON: Final = "light_on"
ATTR_TARGET_TEMPERATURE: Final = "target_temperature"
ATTR_CLIMATE_TYPE: Final = "climate_type"
ATTR_SUMMER_MODE: Final = "summer_mode"
ATTR_CURRENT_MODE: Final = "current_mode"
# State data attributes
ATTR_LIGHT_STATE: Final = "light_state"
ATTR_CLIMATE_STATE: Final = "climate_state"
ATTR_TIME_PERIOD: Final = "time_period"
ATTR_AUTOMATION_ENABLED: Final = "automation_enabled"
# Optional sensors (not used in v0.2.0 simplified logic)
ATTR_TEMPERATURE: Final = "temperature"
ATTR_HUMIDITY: Final = "humidity"
ATTR_LUMINOSITY: Final = "luminosity"
ATTR_OCCUPIED: Final = "occupied"

# Update intervals
UPDATE_INTERVAL: Final = 30  # seconds

# Time periods (simplified)
TIME_PERIOD_DAY: Final = "day"
TIME_PERIOD_NIGHT: Final = "night"

# Modes (simplified - 4 modes only)
MODE_COMFORT: Final = "comfort"
MODE_ECO: Final = "eco"
MODE_NIGHT: Final = "night"
MODE_FROST_PROTECTION: Final = "frost_protection"

# Climate types
CLIMATE_TYPE_X4FP: Final = "x4fp"
CLIMATE_TYPE_THERMOSTAT: Final = "thermostat"

# X4FP preset modes (IPX800 fil pilote)
# Real preset names from IPX800: comfort, eco, away, none
X4FP_PRESET_COMFORT: Final = "comfort"
X4FP_PRESET_ECO: Final = "eco"
X4FP_PRESET_AWAY: Final = "away"  # Hors-gel/frost protection mode
X4FP_PRESET_OFF: Final = "none"

# Alarm states
ALARM_STATE_DISARMED: Final = "disarmed"
ALARM_STATE_ARMED_AWAY: Final = "armed_away"
ALARM_STATE_ARMED_NIGHT: Final = "armed_night"

# Platforms
PLATFORMS: Final = ["sensor", "binary_sensor", "switch"]
