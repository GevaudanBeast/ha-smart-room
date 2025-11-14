# Changelog

All notable changes to Smart Room Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.2] - 2025-01-14

### Improved
- **Configuration optionnelle** : Les champs température/humidité et autres capteurs/actionneurs ne sont plus sauvegardés avec une valeur `None` lorsqu'ils ne sont pas configurés
  - Seuls les champs réellement configurés sont enregistrés dans la configuration
  - Configuration plus propre et minimale possible
  - Compatible avec des pièces minimalistes (juste un nom) jusqu'à des pièces ultra-équipées

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
  - Corridor: 5-minute auto-off timer (configurable)
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
