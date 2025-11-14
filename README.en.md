# Smart Room Manager - Home Assistant Integration

**Version 0.2.0** - 🎯 Simplified and Optimized Architecture!

A comprehensive Home Assistant integration to intelligently manage each room in your home by automating lights and heating in a simple and effective way.

## 🆕 What's New in v0.2.0

### Simplified Architecture
- 🔄 **No presence sensors** : Alarm determines presence (armed_away = absent)
- 💡 **Manual light control** : Auto-off timer only for corridors/bathrooms
- 🎛️ **Generic bypass** : Single switch to disable heating (Solar Optimizer, manual, etc.)
- 📊 **4 modes instead of 6** : Simplified architecture
- ⏰ **Simplified schedules** : Night period + configurable comfort time ranges

### New Features
- 🏠 **Room types** :
  - **Normal** (bedrooms) : No light timer
  - **Corridor** : Auto-off lights after 5 min (configurable)
  - **Bathroom** : 15 min timer + light controls heating (ON=comfort, OFF=eco)
- 🌡️ **Summer/winter support** : Separate cool/heat temperatures with calendar
- 🔧 **X4FP auto-detection** : Automatic detection of X4FP vs thermostat
- 🎨 **Customizable icons** : Choose icon for each room

## 📋 Features

### Smart Light Management (v0.2.0 simplified)
- ✅ **Manual control** : You control your lights manually or via automations
- ✅ **Auto-off timer** : Only for corridors and bathrooms (configurable)
- ✅ **Bathroom special** : Light ON = comfort heating, OFF = eco heating

### Smart Climate/Heating Management
- ✅ **4 adapted modes** :
  - **Comfort** : Present + configurable time ranges
  - **Eco** : Default mode outside comfort ranges
  - **Night** : Night period (configurable)
  - **Frost Protection** : Alarm armed_away or window open
- ✅ **X4FP/Thermostat auto-detection** : Automatic control based on type
- ✅ **Summer/winter support** : Heat/cool temperatures via calendar
- ✅ **Generic bypass** : Switch to disable control (Solar Optimizer, etc.)
- ✅ **Open windows** : Automatic frost protection mode

### Simplified Presence Detection
- 🚨 **Via alarm** : armed_away = absent, otherwise present
- ⏰ **Time ranges** : Comfort mode on configurable ranges if present
- 🌙 **Night mode** : Based on night start time

### Complete UI Configuration
- ⚙️ Add/edit/delete rooms via interface
- 📊 Configure room types and behaviors
- 🕐 Multiple comfort time ranges (format: HH:MM-HH:MM,HH:MM-HH:MM)
- 🔄 Automatic reload on every change

## 🚀 Installation

### Method 1: HACS (Recommended)
1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the 3-dot menu → "Custom repositories"
4. Add URL: `https://github.com/GevaudanBeast/HA-SMART`
5. Search for "Smart Room Manager" and install
6. Restart Home Assistant

### Method 2: Manual
1. Download the latest release from [GitHub Releases](https://github.com/GevaudanBeast/HA-SMART/releases)
2. Extract `smart_room_manager.zip` to your `config/custom_components/` folder
3. Restart Home Assistant

## ⚙️ Configuration

### Initial Setup

1. Go to **Settings** > **Devices & Services**
2. Click **+ Add Integration**
3. Search for **Smart Room Manager**
4. Configure global settings (optional):
   - **Alarm** : Detects presence (armed_away = absent)
   - **Summer calendar** : Switches heat/cool for A/C

### Adding a Room

1. Open **Smart Room Manager** integration
2. Click **Configure** > **Add Room**
3. Follow the configuration wizard:

#### Step 1: Basic Information
- **Name** : Room name (e.g., "Living Room", "Bedroom")
- **Type** :
  - **Normal** : Bedrooms, office (no light timer)
  - **Corridor** : Auto-off lights after 5 min
  - **Bathroom** : 15 min timer + light controls heating
- **Icon** : Custom icon (e.g., mdi:bed, mdi:desk)

#### Step 2: Sensors (all optional)
- **Window/door sensors** : Detect opening → frost protection
- **Temperature sensor** : Info only (displayed in attributes)
- **Humidity sensor** : Info only

#### Step 3: Actuators
- **Lights** : light.* or switch.* entities (manual control + timer if corridor/bathroom type)
- **Climate entity** : Thermostat or X4FP (auto-detection)
- **Bypass switch** : Disables climate control (Solar Optimizer, manual, etc.)

#### Step 4: Light Configuration
- Shown only if type = Corridor or Bathroom
- **Timeout** : Delay before automatic turn-off (60-1800s)

#### Step 5: Climate Configuration
**Winter temperatures (heat)** :
- **Comfort** : Temperature when present + comfort time range (default: 20°C)
- **Eco** : Default temperature outside comfort ranges (default: 18°C)
- **Night** : Night period temperature (default: 17°C)
- **Frost Protection** : Temperature if alarm armed_away or window open (default: 12°C)

**Summer temperatures (cool)** :
- **Comfort** : A/C temperature if summer active (default: 24°C)
- **Eco** : A/C eco temperature summer (default: 26°C)

**Options** :
- **Check windows** : Enable frost protection if window open

#### Step 6: Schedule
- **Night start** : Night period start time (e.g., 22:00)
- **Comfort ranges** : Format `HH:MM-HH:MM,HH:MM-HH:MM`
  - Example: `07:00-09:00,18:00-22:00` (morning + evening)
  - Empty = never in comfort mode (always eco)

## 📊 Created Entities

For each configured room:

### Sensors
- **sensor.smart_room_[name]_state** : Current mode
  - Values: `comfort`, `eco`, `night`, `frost_protection`
  - Attributes: occupation, windows, temperature, humidity, light state, climate state

### Binary Sensors
- **binary_sensor.smart_room_[name]_occupied** : Occupation (alarm-based)
- **binary_sensor.smart_room_[name]_light_needed** : Indicates if lights needed (always False in v0.2.0 - manual control)

### Switches
- **switch.smart_room_[name]_automation** : Enable/disable automation

## 🎯 Usage Examples

### Scenario 1: Simple Bedroom
**Configuration** :
- Type: Normal (no timer)
- Climate entity: climate.bedroom
- Temperatures: Comfort 20°C, Eco 18°C, Night 17°C
- Night schedule: 22:00
- Comfort ranges: `07:00-09:00` (morning only)

**Behavior** :
- 7am-9am + present (alarm disarmed) → Heating 20°C (comfort)
- 9am-10pm + present → Heating 18°C (eco)
- 10pm-7am → Heating 17°C (night)
- Alarm armed_away → Heating 12°C (frost protection)

### Scenario 2: Bathroom
**Configuration** :
- Type: Bathroom
- Lights: light.bathroom
- Light timer: 900s (15 min)
- Climate: climate.bathroom_radiator
- Temperatures: Comfort 22°C, Eco 17°C

**Behavior** :
- Light turned on manually → Heating 22°C (comfort)
- Light off → Heating 17°C (eco)
- Light ON > 15 min → Automatic turn-off
- Turn-off → Heating back to 17°C

### Scenario 3: Living Room with Bypass
**Configuration** :
- Type: Normal
- Climate: climate.living_room
- Bypass: switch.solar_optimizer_living
- Comfort ranges: `18:00-23:00`

**Behavior** :
- Bypass ON (Solar Optimizer active) → Smart Room Manager stands by
- Bypass OFF + 6pm-11pm + present → Comfort heating
- Bypass OFF + outside range → Eco heating

### Scenario 4: Office with Summer/Winter
**Configuration** :
- Summer calendar: calendar.summer (ON in summer)
- Heat temperatures: Comfort 20°C, Eco 18°C
- Cool temperatures: Comfort 24°C, Eco 26°C

**Behavior** :
- Winter (calendar OFF) → hvac_mode: heat, temperature per mode
- Summer (calendar ON) → hvac_mode: cool, temperature per mode

## 🔧 Solar Optimizer Integration

✅ **Compatible via generic bypass!**

**Configuration** :
1. Add Solar Optimizer switch in "Bypass switch"
2. When SO heats (ON) → Smart Room Manager stands by
3. When SO stops (OFF) → Smart Room Manager takes control

**Benefits** :
- ⚡ Priority to Solar Optimizer (free energy)
- 🔄 Automatic control takeover
- 📋 Simple configuration (single switch)

## 🐛 Troubleshooting

### Heating doesn't change
- Check that automation switch is enabled
- Check that bypass isn't active
- Check `sensor.smart_room_*_state` to see current mode
- Logs: `Settings` > `System` > `Logs` > Filter "smart_room_manager"

### Lights don't turn off (corridor/bathroom)
- Check room type (Normal has no timer)
- Check configured timeout
- Lights must be ON for > timeout

### X4FP auto-detection doesn't work
- Check that climate entity has preset_modes: comfort, eco, away
- If classic thermostat: control via hvac_mode + temperature

## 📝 Logs and Debugging

Detailed configuration in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.smart_room_manager: debug
```

## 🔄 Migration from v0.1.0

**Major changes** :
- ❌ Presence sensors removed (use alarm)
- ❌ Interior luminosity sensors removed
- ❌ Guest/vacation modes removed
- ✅ Room types added
- ✅ Multiple comfort ranges instead of 4 periods
- ✅ Generic bypass instead of Solar Optimizer specific

**Action required** : Reconfigure rooms via UI (old configs incompatible)

## 🤝 Contributing

Contributions are welcome!
- 🐛 [Report a bug](https://github.com/GevaudanBeast/HA-SMART/issues)
- 💡 Suggest improvements
- 🔧 Submit a pull request

## 📄 License

This project is licensed under MIT License.

## 🙏 Acknowledgments

Developed with ❤️ for the Home Assistant community.

## 📞 Support

- 📖 [Complete documentation](https://github.com/GevaudanBeast/HA-SMART)
- 🐛 [GitHub Issues](https://github.com/GevaudanBeast/HA-SMART/issues)
- 💬 [Discussions](https://github.com/GevaudanBeast/HA-SMART/discussions)

---

**Version** : 0.2.0
**Author** : GevaudanBeast
**Compatibility** : Home Assistant 2023.1+
