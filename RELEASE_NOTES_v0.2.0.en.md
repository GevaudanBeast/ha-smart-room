# Smart Room Manager v0.2.0 - Simplified Architecture 🎯

**Release Date**: January 14, 2025

## 🚀 Highlights

Major version with **complete architecture refactoring** for more simplicity and robustness:

- 🔄 **Alarm-based presence** : No more need for presence sensors
- 💡 **Manual light control** : Auto-off timer only for corridors/bathrooms
- 🎛️ **Generic bypass** : Single switch for all scenarios (Solar Optimizer, manual, etc.)
- 📊 **4 modes instead of 6** : Simplified architecture
- ⏰ **Comfort time ranges** : Flexible multi-range configuration

## ⚠️ Breaking Changes

**This version requires complete room reconfiguration via the interface.**

v0.1.0 configurations are **incompatible** with v0.2.0 due to major architectural changes.

### Removed Elements
- ❌ Presence sensors (replaced by alarm)
- ❌ Interior luminosity sensors
- ❌ Guest and vacation modes
- ❌ 4 time periods (morning, day, evening, night)
- ❌ Solar Optimizer specific configuration

### New Required Elements
- ✅ Alarm entity (armed_away = absent)
- ✅ Room type (normal, corridor, bathroom)
- ✅ Comfort time ranges (format HH:MM-HH:MM,HH:MM-HH:MM)
- ✅ Generic bypass switch (optional)
- ✅ Summer calendar (optional, for A/C)

## ✨ New Features

### 🏠 Room Types
Each room now has a type that determines its behavior:

- **Normal** (bedrooms, office):
  - No light timer
  - Full manual control
  - Heating mode based on time ranges

- **Corridor**:
  - Auto-off timer 5 minutes (configurable 60-1800s)
  - Automatic turn-off after timeout
  - Energy savings

- **Bathroom**:
  - Auto-off timer 15 minutes
  - **Light controls heating**: ON=comfort, OFF=eco
  - Automatic boost during use

### 🎛️ Generic Bypass
Single switch for all scenarios:
- ✅ Solar Optimizer (solar energy priority)
- ✅ Temporary manual control
- ✅ Maintenance mode
- ✅ Any other external control

**How it works**:
- Switch ON → Smart Room Manager stands by
- Switch OFF → Smart Room Manager takes control

### 🌡️ Summer/Winter Support
Separate temperature configuration:
- **Winter** (heat): Comfort 20°C, Eco 18°C
- **Summer** (cool): Comfort 24°C, Eco 26°C
- Automatic switching via calendar

### 🔧 X4FP Auto-detection
Automatic climate type detection:
- **X4FP (IPX800)**: Control via preset_mode (comfort, eco, away)
- **Thermostat**: Control via hvac_mode + temperature

### ⏰ Flexible Time Ranges
Configure **multiple comfort ranges** per day:
- Format: `HH:MM-HH:MM,HH:MM-HH:MM`
- Example: `07:00-09:00,18:00-22:00` (morning + evening)
- Eco mode by default outside ranges

### 🎨 Customization
- Customizable icons per room
- Simplified UI configuration
- Fewer wizard steps

## 🐛 Bug Fixes

### Security and Robustness
- ✅ Added all missing constants
- ✅ Required field validation
- ✅ Complete error handling (try/except)
- ✅ Secure data structure access

### Fixed Bugs
- 🔧 Incorrect season calendar access
- 🔧 Hard-coded versions "0.1.0"
- 🔧 Unsafe entity_id parsing
- 🔧 Imported but undefined constants
- 🔧 Code duplication (60+ lines)

### Code Improvements
- 📦 Created `SmartRoomEntity` base class
- 🔍 Complete code review
- 📝 Improved documentation
- ⚡ Performance optimizations

## 📋 Operating Modes (v0.2.0)

### 4 Simplified Modes

1. **Comfort** 🌟
   - When: Present (alarm disarmed) + comfort time range
   - Heating: Configured comfort temperature
   - Example: 7am-9am and 6pm-10pm, temperature 20°C

2. **Eco** 🌱
   - When: Present but outside comfort ranges
   - Heating: Configured eco temperature
   - Example: Working from home, temperature 18°C
   - **Default mode**

3. **Night** 🌙
   - When: Night period (configurable)
   - Heating: Configured night temperature
   - Example: 10pm-7am, temperature 17°C

4. **Frost Protection** ❄️
   - When: Alarm armed_away OR window open
   - Heating: Frost protection temperature
   - Example: Away, temperature 12°C

## 🔄 Migration from v0.1.0

### Required Steps

1. **Backup your current configuration** (screenshot)

2. **Remove v0.1.0 integration**:
   - Settings > Devices & Services
   - Smart Room Manager > Remove

3. **Update to v0.2.0** (HACS or manual)

4. **Restart Home Assistant**

5. **Reconfigure the integration**:
   - Add Smart Room Manager
   - Configure alarm + summer calendar (optional)
   - Recreate each room with new flow

### v0.1.0 → v0.2.0 Mapping

| v0.1.0 | v0.2.0 | Notes |
|--------|--------|-------|
| Presence sensor | Alarm | armed_away = absent |
| Luminosity sensor | - | Removed (manual control) |
| Guest mode | - | Removed |
| Vacation mode | Frost protection | Via alarm armed_away |
| 6 modes | 4 modes | Simplified |
| 4 periods | Night + comfort ranges | Flexible |
| Solar Optimizer switch | Bypass switch | Generic |
| - | Room type | Normal/Corridor/Bathroom |
| - | Room icon | Customizable |

## 📦 Installation

### Via HACS (Recommended)
```
1. HACS > Integrations
2. Menu (⋮) > Custom repositories
3. URL: https://github.com/GevaudanBeast/HA-SMART
4. Search "Smart Room Manager"
5. Install + Restart HA
```

### Manual
```
1. Download smart_room_manager.zip
2. Extract to config/custom_components/
3. Restart Home Assistant
4. Add via Settings > Integrations
```

## 🎯 Configuration Examples

### Simple Bedroom
```
Type: Normal
Climate: climate.bedroom
Temperatures: 20°C / 18°C / 17°C / 12°C
Night: 22:00
Comfort ranges: 07:00-09:00
```
**Result**: Comfort in morning, eco during day, night at night

### Bathroom with Light Control
```
Type: Bathroom
Lights: light.bathroom
Timeout: 900s (15 min)
Climate: climate.bathroom_radiator
Comfort/eco temperatures: 22°C / 17°C
```
**Result**: Light ON → 22°C, OFF → 17°C, auto-off after 15 min

### Living Room with Solar Optimizer
```
Type: Normal
Climate: climate.living_room
Bypass: switch.solar_optimizer_living
Comfort ranges: 18:00-23:00
```
**Result**: SO priority, Smart Room backup

## 🔗 Useful Links

- 📖 [Complete README](https://github.com/GevaudanBeast/HA-SMART/blob/main/README.md)
- 📋 [Detailed CHANGELOG](https://github.com/GevaudanBeast/HA-SMART/blob/main/CHANGELOG.md)
- 🐛 [Report a bug](https://github.com/GevaudanBeast/HA-SMART/issues)
- 💬 [Discussions](https://github.com/GevaudanBeast/HA-SMART/discussions)

## 🙏 Acknowledgments

Thanks to all v0.1.0 users for your feedback that made this refactoring possible!

---

**Developed with ❤️ for the Home Assistant community**
