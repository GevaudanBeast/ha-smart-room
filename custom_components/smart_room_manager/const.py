"""Constants for the Smart Room Manager integration."""

from typing import Final

# Integration domain
DOMAIN: Final = "smart_room_manager"
VERSION: Final = "0.3.0"

# Configuration and options
CONF_ROOMS: Final = "rooms"
CONF_ROOM_NAME: Final = "room_name"
CONF_ROOM_ID: Final = "room_id"
CONF_ROOM_TYPE: Final = "room_type"
CONF_ROOM_ICON: Final = "room_icon"

# Room types
ROOM_TYPE_NORMAL: Final = "normal"  # Chambres - pas de timer lumière
ROOM_TYPE_CORRIDOR: Final = "corridor"  # Couloirs, WC - timer lumière
ROOM_TYPE_BATHROOM: Final = (
    "bathroom"  # Salles de bains - timer + lumière pilote chauffage
)

# Sensor configuration
CONF_DOOR_WINDOW_SENSORS: Final = "door_window_sensors"
CONF_TEMPERATURE_SENSOR: Final = "temperature_sensor"
CONF_HUMIDITY_SENSOR: Final = "humidity_sensor"

# Actuator configuration
CONF_LIGHTS: Final = "lights"
CONF_CLIMATE_ENTITY: Final = "climate_entity"
CONF_CLIMATE_BYPASS_SWITCH: Final = "climate_bypass_switch"

# X4FP Hysteresis configuration (Type 3b)
CONF_SETPOINT_INPUT: Final = "setpoint_input"  # input_number entity for setpoint
CONF_HYSTERESIS: Final = "hysteresis"  # Hysteresis value in °C
CONF_MIN_SETPOINT: Final = "min_setpoint"  # Minimum temperature setpoint
CONF_MAX_SETPOINT: Final = "max_setpoint"  # Maximum temperature setpoint
CONF_PRESET_HEAT: Final = "preset_heat"  # Preset when heating needed
CONF_PRESET_IDLE: Final = "preset_idle"  # Preset when temperature OK

# External Control configuration (Solar Optimizer, etc.)
CONF_EXTERNAL_CONTROL_SWITCH: Final = "external_control_switch"  # Switch/binary_sensor
CONF_EXTERNAL_CONTROL_PRESET: Final = "external_control_preset"  # X4FP preset
CONF_EXTERNAL_CONTROL_TEMP: Final = "external_control_temp"  # Thermostat temperature
CONF_ALLOW_EXTERNAL_IN_AWAY: Final = "allow_external_in_away"  # Boolean

# Schedule/Calendar configuration
CONF_SCHEDULE_ENTITY: Final = "schedule_entity"  # calendar entity
CONF_PRESET_SCHEDULE_ON: Final = "preset_schedule_on"  # Mode when event active
CONF_PRESET_SCHEDULE_OFF: Final = "preset_schedule_off"  # Mode when no event

# Manual Pause configuration
CONF_PAUSE_DURATION_MINUTES: Final = (
    "pause_duration_minutes"  # 15, 30, 60, 120, 240, 480
)
CONF_PAUSE_INFINITE: Final = "pause_infinite"  # Boolean

# Window delays (Priority 2)
CONF_WINDOW_DELAY_OPEN: Final = "window_delay_open"  # Minutes before reacting to open
CONF_WINDOW_DELAY_CLOSE: Final = (
    "window_delay_close"  # Minutes before resuming after close
)

# Configurable presets (Priority 2)
CONF_PRESET_COMFORT: Final = "preset_comfort"  # X4FP preset for comfort mode
CONF_PRESET_ECO: Final = "preset_eco"  # X4FP preset for eco mode
CONF_PRESET_NIGHT: Final = "preset_night"  # X4FP preset for night mode
CONF_PRESET_AWAY: Final = "preset_away"  # X4FP preset for away/frost protection
CONF_PRESET_WINDOW: Final = "preset_window"  # X4FP preset for windows open

# Summer policy (Priority 2)
CONF_SUMMER_POLICY: Final = "summer_policy"  # "off" or "eco" for X4FP in summer

# Tick configuration (Priority 2)
CONF_TICK_MINUTES: Final = "tick_minutes"  # 0, 5, 10, 15 (0 = disabled)

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
CONF_COMFORT_TIME_RANGES: Final = (
    "comfort_time_ranges"  # List of {"start": "HH:MM", "end": "HH:MM"}
)

# Global configuration
CONF_ALARM_ENTITY: Final = "alarm_entity"
CONF_SEASON_CALENDAR: Final = "season_calendar"

# X4FP preset modes (IPX800 fil pilote)
# Real preset names from IPX800: comfort, eco, away, none
X4FP_PRESET_COMFORT: Final = "comfort"
X4FP_PRESET_ECO: Final = "eco"
X4FP_PRESET_AWAY: Final = "away"  # Hors-gel/frost protection mode
X4FP_PRESET_OFF: Final = "none"

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

# Default values - Hysteresis
DEFAULT_HYSTERESIS: Final = 0.5  # °C
DEFAULT_MIN_SETPOINT: Final = 17.0  # °C
DEFAULT_MAX_SETPOINT: Final = 23.0  # °C
DEFAULT_PRESET_HEAT: Final = X4FP_PRESET_COMFORT
DEFAULT_PRESET_IDLE: Final = X4FP_PRESET_ECO

# Default values - External Control
DEFAULT_EXTERNAL_CONTROL_PRESET: Final = X4FP_PRESET_COMFORT
DEFAULT_EXTERNAL_CONTROL_TEMP: Final = 20.0  # °C
DEFAULT_ALLOW_EXTERNAL_IN_AWAY: Final = False

# Default values - Manual Pause
DEFAULT_PAUSE_DURATION: Final = 30  # minutes
DEFAULT_PAUSE_INFINITE: Final = False

# Default values - Window delays (Priority 2)
DEFAULT_WINDOW_DELAY_OPEN: Final = 2  # minutes
DEFAULT_WINDOW_DELAY_CLOSE: Final = 2  # minutes

# Default values - Configurable presets (Priority 2)
# These default to standard X4FP presets, but can be overridden per room
DEFAULT_PRESET_COMFORT: Final = X4FP_PRESET_COMFORT
DEFAULT_PRESET_ECO: Final = X4FP_PRESET_ECO
DEFAULT_PRESET_NIGHT: Final = X4FP_PRESET_ECO  # Often same as eco
DEFAULT_PRESET_AWAY: Final = X4FP_PRESET_AWAY
DEFAULT_PRESET_WINDOW: Final = X4FP_PRESET_AWAY  # Frost protection when windows open

# Default values - Summer policy (Priority 2)
DEFAULT_SUMMER_POLICY: Final = "off"  # "off" or "eco"

# Default values - Tick (Priority 2)
DEFAULT_TICK_MINUTES: Final = 0  # 0 = disabled

# Entity ID formats
SENSOR_FORMAT: Final = "sensor.smart_room_{room_id}_state"
BINARY_SENSOR_NIGHT_FORMAT: Final = "binary_sensor.smart_room_{room_id}_night"
BINARY_SENSOR_BYPASS_FORMAT: Final = "binary_sensor.smart_room_{room_id}_climate_bypass"
SWITCH_AUTOMATION_FORMAT: Final = "switch.smart_room_{room_id}_automation"
SWITCH_PAUSE_FORMAT: Final = "switch.smart_room_{room_id}_pause"

# Debug sensor formats
SENSOR_PRIORITY_FORMAT: Final = "sensor.smart_room_{room_id}_current_priority"
BINARY_SENSOR_EXTERNAL_CONTROL_FORMAT: Final = (
    "binary_sensor.smart_room_{room_id}_external_control_active"
)
SENSOR_HYSTERESIS_FORMAT: Final = "sensor.smart_room_{room_id}_hysteresis_state"
BINARY_SENSOR_SCHEDULE_FORMAT: Final = (
    "binary_sensor.smart_room_{room_id}_schedule_active"
)

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
# Debug attributes (v0.3.0)
ATTR_CURRENT_PRIORITY: Final = "current_priority"
ATTR_EXTERNAL_CONTROL_ACTIVE: Final = "external_control_active"
ATTR_HYSTERESIS_STATE: Final = "hysteresis_state"
ATTR_SCHEDULE_ACTIVE: Final = "schedule_active"
ATTR_PAUSE_ACTIVE: Final = "pause_active"
ATTR_PAUSE_UNTIL: Final = "pause_until"
ATTR_REMAINING_MINUTES: Final = "remaining_minutes"

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

# Priority states (for debug sensor)
PRIORITY_PAUSED: Final = "paused"
PRIORITY_BYPASS: Final = "bypass"
PRIORITY_WINDOWS_OPEN: Final = "windows_open"
PRIORITY_EXTERNAL_CONTROL: Final = "external_control"
PRIORITY_AWAY: Final = "away"
PRIORITY_SCHEDULE: Final = "schedule"
PRIORITY_NORMAL: Final = "normal"

# Hysteresis states (for debug sensor)
HYSTERESIS_HEATING: Final = "heating"
HYSTERESIS_IDLE: Final = "idle"
HYSTERESIS_DEADBAND: Final = "deadband"

# Climate types
CLIMATE_TYPE_X4FP: Final = "x4fp"
CLIMATE_TYPE_THERMOSTAT: Final = "thermostat"

# Alarm states
ALARM_STATE_DISARMED: Final = "disarmed"
ALARM_STATE_ARMED_AWAY: Final = "armed_away"
ALARM_STATE_ARMED_NIGHT: Final = "armed_night"

# Platforms
PLATFORMS: Final = ["sensor", "binary_sensor", "switch"]
