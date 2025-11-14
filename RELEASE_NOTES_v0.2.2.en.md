# Smart Room Manager v0.2.2 - Optional Configuration

## 🎯 Improvements

### Complete Optional Configuration

This version improves the handling of optional fields in the configuration:

- **Truly optional fields** : Temperature/humidity sensors and other equipment are no longer saved with a `None` value when not configured
- **Cleaner configuration** : Only actually configured fields are stored
- **Maximum flexibility** : Ability to create minimalist rooms (just a name) to fully-equipped rooms

### Affected Fields

The following fields are now saved **only if configured**:
- `temperature_sensor` - Temperature sensor
- `humidity_sensor` - Humidity sensor
- `climate_entity` - Climate/heating entity
- `climate_bypass_switch` - Bypass switch (Solar Optimizer, manual control, etc.)

## 📋 Compatibility Notes

- ✅ **No breaking changes** : Existing configurations continue to work
- ✅ **Automatic update** : Old configurations with `None` values are handled correctly
- ✅ **Backward compatible** : Compatible with v0.2.0 and v0.2.1

## 🔧 Installation

### Via HACS (Recommended)

1. Download `smart_room_manager.zip` from this release
2. In HACS, add the custom repository: `https://github.com/GevaudanBeast/HA-SMART`
3. Install "Smart Room Manager"
4. Restart Home Assistant

### Manual

1. Download `smart_room_manager.zip`
2. Extract to `/config/custom_components/smart_room_manager/`
3. Restart Home Assistant

## 📚 For More Information

- [README](README.en.md) - Complete documentation
- [CHANGELOG](CHANGELOG.en.md) - Change history
- [Release Notes v0.2.0](RELEASE_NOTES_v0.2.0.en.md) - Main features of v0.2.0

---

**Previous version** : [v0.2.1](https://github.com/GevaudanBeast/HA-SMART/releases/tag/v0.2.1)
