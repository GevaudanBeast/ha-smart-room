# Changelog

All notable changes to Smart Room Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/GevaudanBeast/HA-SMART/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/GevaudanBeast/HA-SMART/releases/tag/v0.1.0
