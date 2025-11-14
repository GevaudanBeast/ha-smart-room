# Smart Room Manager v0.2.3 - Automatic Migration

## 🔧 Critical Fix

### Automatic None Values Migration

This version automatically fixes an issue affecting users who installed v0.2.1 or v0.2.2:

**Problem resolved:**
- Error `Entity None is neither a valid entity ID nor a valid UUID`
- Temperature/humidity sensors displaying "Entity None"
- Configuration containing `None` values for optional fields

**Automatic solution:**
- ✅ **Transparent startup migration** : Automatic cleanup of `None` values
- ✅ **No action required** : Fix applies automatically on restart
- ✅ **Cleaned configuration** : Removes None values from:
  - `temperature_sensor`
  - `humidity_sensor`
  - `climate_entity`
  - `climate_bypass_switch`

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
