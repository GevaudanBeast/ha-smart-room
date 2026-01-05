# Changelog

All notable changes to Smart Room Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.4] - 2026-01-04

### 🐛 Critical Bug Fixes

#### Fix: Night period after midnight
- **Problem**: Night period only worked between 22:00 and 23:59
- **Fix**: Added `DEFAULT_DAY_START` (06:00), night is now 22:00-06:00
- **Logic**: `is_night = now >= 22:00 OR now < 06:00`

#### Fix: VMC with multiple bathrooms
- **Problem**: One bathroom's VMC timer could turn off the global VMC while another bathroom was still active
- **Fix**: Added `_any_other_bathroom_active()` that checks if other bathrooms need the VMC before turning it off

#### Fix: Heating mode priorities
- **Fix**: Aligned priorities between `room_manager` and `climate_control`
- **Fix**: Schedule now has priority over night period (explicit user config)
- **Fix**: Bathrooms use light-based logic before schedule

#### Fix: Respect ignore_in_away option for schedule
- **Problem**: Schedule was ignored even with "ignore_in_away" option checked
- **Fix**: Check `ignore_in_away` in away mode priority

#### Fix: Away → disarmed transition (X4FP and Thermostats)
- **Problem**: Transitioning from armed_away to disarmed didn't change presets
- **X4FP Fix**: Sync with actual preset state before comparison
- **Thermostat Fix**: Support "away" and "home" presets if thermostat supports them
- **Behavior**: X4FP away→eco/comfort, Thermostat away→home + heat/cool

### 🔧 Refactoring

- **Consolidated**: VMC on/off methods into generic `_control_entity()`
- **Added**: `_get_entity_domain()` helper for domain extraction
- **Fixed**: Null check on `state.last_changed`
- **Unified**: All binary_sensors return `None` when no data available

## [0.3.3] - 2026-01-04

### ✨ UX Improvements - Contextual Configuration

#### New: Climate Mode Selection
- **Added**: Climate type selector in actuators:
  - None (corridors, etc.)
  - Wire Pilot / Fil Pilote (X4FP, IPX800...)
  - Thermostat (heat only)
  - Thermostat (cool only)
  - Thermostat (heat/cool)
- **Improved**: Contextual configuration based on selected mode

#### New: VMC (Ventilation) Support
- **Added**: Global VMC entity in general settings (switch or fan)
- **Added**: Configurable VMC timer (duration after light turns off)
- **Behavior**: VMC high speed activates when light turns on, timer starts when light turns off
- **Added**: VMC High Speed binary_sensor (shows countdown)

#### New: Debug and Tracing Sensors
- **Added**: Activity sensor for each room (human-readable log with emojis)
- **Added**: Light Timer binary_sensor (countdown before auto-off)
- **Added**: Clear descriptions for bypass vs external control

#### New: Cleanup Service
- **Added**: `smart_room_manager.cleanup_entities` service to remove orphaned entities
- **Behavior**: Automatically removes entities from rooms that no longer exist

#### Room Type Improvements
- **Renamed**: "Normal" → "Living space" (bedroom, living room, kitchen, office...)
- **Renamed**: "Corridor" → "Passage/utility" (corridor, attic, cellar, laundry...)
- **Renamed**: "Bathroom" → "Bathroom / WC" (light timer + VMC)

#### Smart Configuration Logic
- **Improved**: No climate entity → mode forced to "None", climate config skipped
- **Improved**: Fil Pilote + temp sensor → temperature setpoints shown
- **Improved**: Fil Pilote without temp sensor → temperatures hidden
- **Improved**: Bypass and external control ignored if no climate configured

### 🐛 Bug Fixes

#### Fix: SelectSelector Validation Error
- **Problem**: "unknown error" when creating/editing rooms
- **Cause**: SelectSelector for pause_duration used integers instead of strings
- **Fix**: Converted to string options ["15", "30", "60", "120", "240", "480"]

#### Fix: Line Length Errors (E501)
- **Fix**: All lines comply with 88 character limit for ruff/HACS

#### Fix: Unused Imports
- **Fix**: Removed F401 unused imports in multiple files

### ✅ Backward Compatibility
- Existing configurations remain functional
- New fields (VMC, climate_mode) are optional with default values
- No migration required

## [0.2.3] - 2025-01-14

### Fixed
- **Multiple critical errors** : Comprehensive fixes for v0.2.3
  - **Missing DOMAIN imports** : Added `from .const import DOMAIN` in switch.py and binary_sensor.py
    - Resolves: `NameError: name 'DOMAIN' is not defined`
  - **Deprecated warning** : Removed explicit config_entry assignment in OptionsFlow
    - Compatible with Home Assistant 2025.12
  - **"Entity None" in forms** : Multiple fixes
    - Extended migration: Cleanup of door_window_sensors and lights (in addition to temperature_sensor, humidity_sensor, climate_entity, climate_bypass_switch)
    - Fixed `.get(field, [])` to `.get(field) or []` in 7 locations (config_flow.py, light_control.py, room_manager.py)
    - Conditional form schemas to avoid None as default value
  - Completely resolves "Entity None is neither a valid entity ID nor a valid UUID" error
  - Transparent migration on startup, no user action required

## [0.2.2] - 2025-01-14

### Improved
- **Optional configuration** : Temperature/humidity sensors and other actuators are no longer saved with `None` value when not configured
  - Only actually configured fields are stored in the configuration
  - Cleaner and more minimal configuration possible
  - Compatible with minimalist rooms (just a name) to fully-equipped rooms

## [0.2.1] - 2025-01-14

### Fixed
- **Critical import error** : Fixed ALARM_STATE_ARMED_AWAY import from homeassistant.const (doesn't exist)
  - Now correctly imports from our own const.py
  - This was preventing the integration from loading in Home Assistant
  - Error: `cannot import name 'ALARM_STATE_ARMED_AWAY' from 'homeassistant.const'`

## [0.2.0] - 2025-01-14

### 🎯 Major Refactoring - Simplified Architecture

#### Removed (Breaking Changes)
- **Presence sensors** : Replaced by alarm-based presence detection (armed_away = absent)
- **Interior luminosity sensors** : Manual light control only, auto-off timer for corridors/bathrooms
- **Guest mode and vacation mode** : Simplified to 4 modes (removed 2 modes)
- **6 time periods** : Reduced to night period + multiple configurable comfort time ranges
- **Solar Optimizer specific field** : Replaced with generic bypass switch

#### Added
- **Room types** system:
  - Normal (bedrooms): No light timer
  - Corridor: 5-minute auto-off timer (configurable 60-1800s)
  - Bathroom: 15-minute timer + light controls heating (ON=comfort, OFF=eco)
- **Generic bypass switch** : Single switch to disable climate control (Solar Optimizer, manual, etc.)
- **Summer/winter mode** : Separate cool/heat temperatures with calendar-based season detection
- **X4FP auto-detection** : Automatic detection of X4FP vs thermostat control
- **Multiple comfort time ranges** : Configure multiple daily time ranges (format: HH:MM-HH:MM,HH:MM-HH:MM)
- **Room icon customization** : Choose custom icon for each room
- **SmartRoomEntity base class** : Factored device_info to eliminate code duplication

#### Changed
- **Default mode** : Changed from comfort to eco
- **Modes** : 6 modes → 4 modes (comfort, eco, night, frost_protection)
- **Light control** : Manual control with optional timer (corridor/bathroom types only)
- **Presence detection** : Alarm armed_away determines absence instead of sensors
- **Config flow** : Complete rewrite matching v0.2.0 architecture
- **X4FP control** : Uses correct preset names from IPX800 (away instead of frost_protection)

#### Fixed
- **Missing constants** : Added ATTR_LUMINOSITY, ATTR_OCCUPIED, and other missing constants
- **Season calendar access** : Fixed incorrect data structure access
- **Version consistency** : All files now use VERSION constant instead of hard-coded "0.1.0"
- **Error handling** : Added try/except to _set_frost_protection and other service calls
- **Entity ID parsing** : Using split_entity_id() instead of unsafe string checking
- **Data validation** : Added validation for required room_config fields (room_id, room_name)
- **Code duplication** : Created SmartRoomEntity base class (eliminated ~60 lines of duplicated code)

#### Technical Improvements
- Comprehensive code review improvements (security, robustness, validation)
- Better error handling throughout
- Proper data structure access patterns
- Factored common code into base classes
- Added comments and documentation where needed

### Migration from v0.1.0
**Action Required**: Rooms must be reconfigured via UI. Old v0.1.0 configurations are incompatible with v0.2.0 architecture.

See [Migration Guide](MIGRATION_GUIDE.md) for detailed instructions.

## [0.1.0] - 2025-01-13

### Added
- Initial release of Smart Room Manager
- Complete UI-based configuration (config_flow + options_flow)
- Smart light management:
  - Automatic control based on presence, luminosity, and time
  - Night mode with reduced brightness
  - Configurable timeout per room
  - Manual control override support
- Smart climate/heating management:
  - Variable temperature setpoints (comfort, eco, night, away, frost protection)
  - Window detection (heating pause)
  - Alarm integration (away mode)
  - Season detection (summer/winter)
  - Unoccupied delay configuration
- **Solar Optimizer support** (PRIORITY MODE):
  - When SO switch is ON → Smart Room Manager stands by
  - When SO switch is OFF → Smart Room Manager takes control
  - Per-room SO switch configuration
  - Compatible with existing Solar Optimizer setups
- Global modes:
  - Guest mode
  - Vacation mode (frost protection)
  - Alarm modes (away/home)
  - Season-based behavior
- Entity exposure per room:
  - `sensor.smart_room_*_state`: Overall room state and mode
  - `binary_sensor.smart_room_*_occupied`: Room occupation status
  - `binary_sensor.smart_room_*_light_needed`: Light requirement indicator
  - `switch.smart_room_*_automation`: Enable/disable room automation
- Multi-language support (EN/FR)
- IPX800 V5 compatibility (X4FP, X8R, XDimmer, etc.)
- Complete documentation:
  - Installation and configuration guide
  - Migration guide from YAML automations
  - Solar Optimizer integration guide
  - Room-specific configuration examples

### Technical Details
- DataUpdateCoordinator for centralized state management
- Modular architecture with separate controllers (light, climate)
- Async/await best practices
- Proper error handling and logging
- Home Assistant 2023.1+ compatibility

[Unreleased]: https://github.com/GevaudanBeast/HA-SMART/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/GevaudanBeast/HA-SMART/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/GevaudanBeast/HA-SMART/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/GevaudanBeast/HA-SMART/releases/tag/v0.1.0
