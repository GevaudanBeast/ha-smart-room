# Smart Room Manager v0.2.3 - Comprehensive Critical Fixes

## 🔧 Critical Fixes

This version fixes **multiple critical errors** affecting v0.2.1 and v0.2.2 users:

### 1. Missing DOMAIN Imports
**Problem:**
- `NameError: name 'DOMAIN' is not defined` in switch.py and binary_sensor.py
- Integration couldn't load switch and binary_sensor platforms

**Solution:**
- ✅ Added `from .const import DOMAIN` to switch.py and binary_sensor.py
- ✅ All entities (switches, binary sensors) now created successfully

### 2. Deprecated Warning (Home Assistant 2025.12)
**Problem:**
- Warning about explicit `config_entry` assignment in OptionsFlow
- Code not compatible with Home Assistant 2025.12+

**Solution:**
- ✅ Removed explicit assignment (automatically provided by parent class)
- ✅ Compatible with Home Assistant 2025.12 and future versions

### 3. "Entity None" - Comprehensive Fixes
**Problem:**
- Error `Entity None is neither a valid entity ID nor a valid UUID`
- Temperature/humidity sensors displaying "Entity None" in forms
- Configuration containing `None` values for optional fields

**Solution (3 combined fixes):**
- ✅ **Extended migration**: Automatic cleanup on startup of `None` values in:
  - `door_window_sensors` and `lights` (newly added)
  - `temperature_sensor`, `humidity_sensor`
  - `climate_entity`, `climate_bypass_switch`
- ✅ **Critical `.get()` fix**: 7 locations corrected from `.get(field, [])` to `.get(field) or []`
  - Reason: `.get(key, default)` returns `None` if key exists with value `None`
  - Files: config_flow.py, light_control.py, room_manager.py
- ✅ **Conditional schemas**: Forms rebuilt to not display "None" as default value

## 🚀 Installation / Update

### Via HACS (Recommended)

1. HACS → Integrations
2. Search for "Smart Room Manager"
3. Click "Update" (or reinstall)
4. **Restart Home Assistant**
5. ✅ Migration runs automatically!

### Manual

1. Download `smart_room_manager.zip` from this release
2. Extract to `/config/custom_components/smart_room_manager/`
3. **Restart Home Assistant**
4. ✅ Migration runs automatically!

## 📋 Verification

After restart, in **Settings → System → Logs**, you should see:

```
Cleaned None values from room configurations (v0.2.1 migration)
```

And the "Entity None" error should be gone! 🎉

## 📊 Version History

- **v0.2.3** : Automatic None values migration (this patch)
- **v0.2.2** : Improved optional configuration
- **v0.2.1** : Fixed ALARM_STATE_ARMED_AWAY import
- **v0.2.0** : Simplified architecture (breaking changes)

## 📚 For More Information

- [README](README.en.md) - Complete documentation
- [CHANGELOG](CHANGELOG.en.md) - Change history
- [Release Notes v0.2.0](RELEASE_NOTES_v0.2.0.en.md) - Main features

---

**Previous version** : [v0.2.2](https://github.com/GevaudanBeast/HA-SMART/releases/tag/v0.2.2)
