# Smart Room Manager v0.2.1 - Critical Fix 🔧

**Release Date**: January 14, 2025

## 🐛 Critical Fix

This version fixes a **blocking bug** that prevented the integration from loading in Home Assistant.

### Fixed Error

```
ERROR (MainThread) [homeassistant.config_entries] Error occurred loading flow for integration smart_room_manager:
cannot import name 'ALARM_STATE_ARMED_AWAY' from 'homeassistant.const'
```

### Solution

- ✅ Fixed `ALARM_STATE_ARMED_AWAY` import
- ✅ Now imports from our own `const.py` instead of `homeassistant.const`
- ✅ Integration loads correctly

## 📦 Installation

### Via HACS (Recommended)
```
1. HACS > Integrations
2. Smart Room Manager > Redownload
3. Restart Home Assistant
```

### Manual
```
1. Download smart_room_manager.zip
2. Extract to config/custom_components/
3. Restart Home Assistant
```

## 🆕 What's New in v0.2.x (reminder)

If you're coming from v0.1.0, see [v0.2.0 release notes](RELEASE_NOTES_v0.2.0.en.md) for complete list of changes:

- 🔄 Simplified architecture (4 modes)
- 🏠 Room types (normal, corridor, bathroom)
- 🎛️ Generic bypass
- ⏰ Multiple comfort time ranges
- 🌡️ Summer/winter support

## 🔗 Useful Links

- 📖 [Complete README](https://github.com/GevaudanBeast/HA-SMART/blob/main/README.en.md)
- 📋 [Detailed CHANGELOG](https://github.com/GevaudanBeast/HA-SMART/blob/main/CHANGELOG.en.md)
- 📝 [v0.2.0 Notes](https://github.com/GevaudanBeast/HA-SMART/blob/main/RELEASE_NOTES_v0.2.0.en.md)
- 🐛 [Report a bug](https://github.com/GevaudanBeast/HA-SMART/issues)

---

**Developed with ❤️ for the Home Assistant community**
