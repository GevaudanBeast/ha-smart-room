# ⚡ Solar Optimizer - Integration Guide

Smart Room Manager v0.3.0+ supports **Solar Optimizer** in **priority mode** through the External Control feature.

## 🎯 How It Works

Solar Optimizer manages heating to use solar energy surplus. When Solar Optimizer decides to heat a room, **it must have absolute priority** over all other logic.

### Smart Room Manager Behavior

```
┌─────────────────────────────────────────────────────┐
│  switch.solar_optimizer_xxx = ON                    │
│  ↓                                                   │
│  Solar Optimizer is actively heating                │
│  ↓                                                   │
│  Smart Room Manager STEPS BACK                      │
│  ↓                                                   │
│  No action from Smart Room Manager                  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  switch.solar_optimizer_xxx = OFF                   │
│  ↓                                                   │
│  Solar Optimizer not heating                        │
│  ↓                                                   │
│  Smart Room Manager RESUMES CONTROL                 │
│  ↓                                                   │
│  Normal logic (alarm, windows, schedule, etc.)      │
└─────────────────────────────────────────────────────┘
```

## 🏆 Priority System (v0.3.0)

Smart Room Manager uses a 7-level priority system:

```
Priority 1 (HIGHEST): Manual Pause
    ↓
Priority 2: Bypass Switch
    ↓
Priority 3: Window Open
    ↓
Priority 4: EXTERNAL CONTROL (Solar Optimizer) ⚡
    ↓
Priority 5: Away Mode (Alarm armed_away)
    ↓
Priority 6: Schedule/Calendar
    ↓
Priority 7 (LOWEST): Normal Mode (Comfort/Eco/Night)
```

**Key point**: External Control (Solar Optimizer) has **Priority 4** - it overrides normal operation but respects safety features (window open, bypass).

## ⚙️ Configuration

### Step 1: Enable Solar Optimizer

Ensure Solar Optimizer is correctly configured in Home Assistant:

```yaml
# Solar Optimizer Configuration (example)
solar_optimizer:
  devices:
    - name: "Master Bedroom Heating"
      entity_id: climate.x4fp_fp_2
      power: 1500  # Watts
      switch: switch.solar_optimizer_master_bedroom
```

### Step 2: Configure Smart Room Manager

#### Basic Configuration

1. **Add room** in Smart Room Manager
2. **Configure External Control**:

```yaml
Room Name: "Master Bedroom"
Room Type: "Normal"

# Sensors Step
Temperature Sensor: sensor.master_temperature
Door/Window Sensors:
  - binary_sensor.master_window

# Actuators Step
Climate Entity: climate.master_x4fp
External Control Switch: switch.solar_optimizer_master_bedroom
```

#### Advanced Configuration

In the **Climate Advanced** step:

```yaml
# External Control Configuration
External Control Preset: "comfort"
External Control Temp: 21.0°C
Allow External in Away: false
```

**Parameters explained**:

| Parameter | Description | Recommended Value |
|-----------|-------------|------------------|
| **External Control Preset** | X4FP preset when SO is active | `"comfort"` |
| **External Control Temp** | Target temperature for thermostats | `21.0°C` |
| **Allow External in Away** | Allow SO when alarm is armed_away | `false` (safety) |

## 🔍 Monitoring

### Debug Sensors (v0.3.0)

Smart Room Manager creates debug sensors for each room:

| Sensor | Purpose | Example Values |
|--------|---------|----------------|
| `sensor.ROOM_climate_priority` | Current active priority | `external_control`, `normal`, `away` |
| `sensor.ROOM_external_control` | External control state | `on`, `off` |
| `sensor.ROOM_climate_state` | Current climate mode | `comfort`, `eco`, `night`, `frost_protection` |
| `sensor.ROOM_target_temperature` | Current target temperature | `21.0`, `19.0`, `16.0`, `7.0` |

### Example Monitoring Card

```yaml
type: entities
title: Master Bedroom - Solar Optimizer
entities:
  - entity: switch.solar_optimizer_master_bedroom
    name: Solar Optimizer Switch
  - entity: sensor.master_climate_priority
    name: Current Priority
  - entity: sensor.master_external_control
    name: External Control Status
  - entity: sensor.master_target_temperature
    name: Target Temperature
  - entity: climate.master_x4fp
    name: Radiator
```

## 📋 Detailed Scenarios

### Scenario 1: Normal Solar Optimizer Operation

**Conditions**:
- Solar surplus available
- Room temperature < target
- No windows open
- Alarm not armed_away

**Behavior**:
1. Solar Optimizer activates: `switch.solar_optimizer_master = ON`
2. Smart Room Manager detects External Control active
3. Priority 4 activated (External Control)
4. Radiator set to External Control Preset (`comfort`)
5. Temperature target: External Control Temp (21.0°C)

**Sensors**:
```
sensor.master_climate_priority = "external_control"
sensor.master_external_control = "on"
sensor.master_target_temperature = 21.0
climate.master_x4fp.preset_mode = "comfort"
```

### Scenario 2: Window Opens During Solar Optimization

**Conditions**:
- Solar Optimizer active
- Window opens

**Behavior**:
1. Priority 3 (Window) overrides Priority 4 (External Control)
2. Radiator immediately set to Frost Protection
3. Solar Optimizer still running (but ineffective)

**Sensors**:
```
sensor.master_climate_priority = "window"
sensor.master_external_control = "on"  # SO still active
sensor.master_target_temperature = 7.0
climate.master_x4fp.preset_mode = "away"  # Frost protection
```

**When window closes**:
- If SO still ON → resume External Control (Priority 4)
- If SO turned OFF → resume Normal mode (Priority 7)

### Scenario 3: Alarm Armed During Solar Optimization

**Conditions**:
- Solar Optimizer active
- User arms alarm (armed_away)

**Behavior depends on** `Allow External in Away` setting:

**If `Allow External in Away = false`** (recommended):
1. Priority 5 (Away) overrides Priority 4 (External Control)
2. Radiator set to Frost Protection
3. Solar Optimizer disabled for safety

```
sensor.master_climate_priority = "away"
sensor.master_target_temperature = 7.0
```

**If `Allow External in Away = true`**:
1. Priority 4 (External Control) remains active
2. Solar Optimizer continues heating
3. Use only if you trust Solar Optimizer safety

### Scenario 4: Solar Optimizer Stops

**Conditions**:
- Solar Optimizer was active
- Solar surplus disappears
- Switch turns OFF

**Behavior**:
1. External Control deactivated (Priority 4 → OFF)
2. Smart Room Manager resumes normal control
3. Fallback to Priority 7 (Normal Mode)
4. Mode determined by schedule/time/alarm

**Example at 19:00 (comfort time)**:
```
sensor.master_climate_priority = "normal"
sensor.master_external_control = "off"
sensor.master_climate_state = "comfort"
sensor.master_target_temperature = 19.0
climate.master_x4fp.preset_mode = "comfort"
```

### Scenario 5: Manual Pause

**Conditions**:
- Solar Optimizer active
- User activates manual pause

**Behavior**:
1. Priority 1 (Pause) overrides all (including SO)
2. Automation completely paused
3. Radiator remains in last state
4. No automatic changes

```
sensor.master_climate_priority = "paused"
switch.master_pause = "on"
```

## 🎛️ Configuration Tips

### Recommended Settings

**For most rooms**:
```yaml
External Control Preset: "comfort"
External Control Temp: 21.0°C
Allow External in Away: false
```

**For less critical rooms** (guest room, etc.):
```yaml
External Control Preset: "eco"
External Control Temp: 19.0°C
Allow External in Away: false
```

**For advanced users** (if you trust SO safety):
```yaml
External Control Preset: "comfort"
External Control Temp: 21.0°C
Allow External in Away: true  # ⚠️ Use with caution
```

### Window Detection

Always configure window sensors for rooms with Solar Optimizer:

```yaml
Door/Window Sensors:
  - binary_sensor.master_window
```

**Why?**
- Safety: Prevents heating with window open
- Priority: Window (Priority 3) overrides SO (Priority 4)
- Energy: Avoids wasting solar surplus

### Summer Policy

Configure summer behavior for X4FP radiators:

```yaml
Summer Policy: "eco"  # or "off"
```

**Options**:
- `"off"`: Turn off X4FP completely in summer (saves energy)
- `"eco"`: Keep X4FP in eco mode (maintains minimal protection)

## 🔧 Troubleshooting

### Issue: Solar Optimizer not working

**Symptoms**:
- SO switch ON but radiator doesn't respond
- Priority shows something other than "external_control"

**Check**:
1. External Control Switch is correctly configured
2. Window is not open (Priority 3 > Priority 4)
3. Alarm is not armed_away (if "Allow External in Away" = false)
4. Bypass switch is OFF (Priority 2 > Priority 4)
5. Manual pause is OFF (Priority 1 > Priority 4)

**Debug**:
```yaml
# Check these sensors
sensor.master_climate_priority  # Should be "external_control"
sensor.master_external_control  # Should be "on"
binary_sensor.master_window     # Should be "off"
switch.master_bypass            # Should be "off"
switch.master_pause             # Should be "off"
```

### Issue: Solar Optimizer continues after alarm armed

**Symptoms**:
- Alarm armed_away but SO still heating

**Solution**:
```yaml
# Set in Climate Advanced step
Allow External in Away: false
```

This ensures Away mode (Priority 5) overrides External Control (Priority 4).

### Issue: Conflict between Solar Optimizer and schedule

**Symptoms**:
- Unexpected mode changes when SO stops

**Explanation**:
- This is **normal behavior**
- When SO stops (Priority 4 OFF), Smart Room Manager resumes normal control (Priority 7)
- Normal mode follows schedule/time of day

**Example**:
```
# While SO active (14:00, comfort time)
Priority 4: External Control → Comfort mode (21°C)

# SO stops (16:00, eco time)
Priority 7: Normal Mode → Eco mode (17°C)
```

This is correct - Smart Room Manager adapts to current time period.

### Issue: Temperature target doesn't match

**Symptoms**:
- Target temperature unexpected during SO

**Check**:
```yaml
# Climate Advanced step
External Control Temp: 21.0°C  # Must match your expectation
```

**Note**: For X4FP radiators, temperature is controlled by presets:
- `External Control Temp` only applies to thermostats
- For X4FP, use `External Control Preset` instead

## 📊 Migration from Blueprints

If you're migrating from previous X4FP blueprints with Solar Optimizer:

### Old Configuration (Blueprint)
```yaml
blueprint:
  name: X4FP Room with Solar Optimizer
  inputs:
    solar_optimizer_switch: switch.solar_optimizer_master
    solar_priority: true
    # ...
```

### New Configuration (Smart Room Manager v0.3.0)
```yaml
# Actuators Step
External Control Switch: switch.solar_optimizer_master

# Climate Advanced Step
External Control Preset: "comfort"
External Control Temp: 21.0°C
Allow External in Away: false
```

**Benefits of new system**:
- ✅ Clearer priority hierarchy
- ✅ Better integration with other features
- ✅ Debug sensors for monitoring
- ✅ More flexible configuration
- ✅ Supports multiple external control sources

## 🎯 Best Practices

1. **Always configure window sensors** for safety
2. **Use `Allow External in Away: false`** unless you have specific needs
3. **Monitor debug sensors** during initial setup
4. **Test priority scenarios** before relying on automation:
   - Window open during SO
   - Alarm armed during SO
   - Manual pause during SO
5. **Keep External Control Preset = "comfort"** for most cases
6. **Document your configuration** for future reference

## 📚 Additional Resources

- [Configuration Examples](CONFIGURATION_EXAMPLES.md) - Ready-to-use configurations
- [Migration Guide](MIGRATION_GUIDE.md) - Migrating from YAML automations
- [Changelog](CHANGELOG.md) - Feature details and updates

## 💡 Advanced: Multiple External Control Sources

Smart Room Manager v0.3.0 supports any external control source, not just Solar Optimizer:

**Examples**:
- Solar Optimizer
- Dynamic pricing automation
- Grid load balancing
- Manual override switches
- External home automation systems

**Configuration is the same**:
```yaml
External Control Switch: switch.YOUR_EXTERNAL_SOURCE
External Control Preset: "comfort"
External Control Temp: 21.0°C
```

The switch state determines when external control is active. When ON, Priority 4 activates and your external system takes control.

Good luck with your Solar Optimizer integration! ☀️
