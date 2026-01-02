# 📖 Migration Guide to Smart Room Manager

This guide explains how to progressively migrate your existing YAML automations to the Smart Room Manager integration.

## 🎯 Migration Principle

**IMPORTANT**: **Progressive** and **tested** migration, room by room.

### Recommended Order

1. ✅ Simple rooms first (corridor, WC, basement)
2. ✅ Rooms with simple heating next
3. ✅ Rooms with Solar Optimizer (special attention required)
4. ⚠️ **DO NOT migrate shutters** (too specific)

## 📋 Automation Inventory

### Lights to Migrate

| Room | Current Automation | Current Timer | Comments |
|------|-------------------|---------------|----------|
| Corridors (x3) | `Timer - corridors...` | 5 min | ✅ Simple |
| Ground Floor Bathroom | `Timer - corridors...` | 15 min | ✅ Simple |
| First Floor Bathroom | `Timer - corridors...` | 15 min | ✅ Simple |
| WC | `Timer - corridors...` | 5 min | ✅ Simple |
| Attic | `Timer - corridors...` | 15 min | ✅ Simple |
| Basement | `Timer - corridors...` | 15 min | ✅ Simple |
| Shed | `Timer - corridors...` | 15 min | ✅ Simple |
| Indoor Entrance | `Indoor entrance - Door open` | 5 min | ✅ Simple |
| Outdoor Entrance | `Outdoor entrance light` | IPX timer | ✅ Simple |
| Outdoor | `Outdoor - Complete management...` | N/A | ⚠️ Keep automation |
| Terrace | `Terrace - Smart management...` | N/A | ⚠️ Keep automation |

### Heating to Migrate

| Room | Type | Current Blueprint | Solar Optimizer | Priority |
|------|------|------------------|-----------------|----------|
| Living Room | Stove | `blueprint_hvac_thermostat_heat.yaml` | ❌ No | 1 |
| Master Suite | X4FP FP2 | `blueprint_hvac_X4FP_room.yaml` | ✅ Yes | 3 |
| Guest Room | X4FP FP1 | `blueprint_hvac_X4FP_room.yaml` | ✅ Yes | 3 |
| Ground Floor Bathroom | X4FP FP3 | `blueprint_hvac_X4FP_bathroom.yaml` | ✅ Yes | 3 |
| First Floor Bathroom | X4FP FP4 | `blueprint_hvac_X4FP_bathroom.yaml` | ✅ Yes | 3 |
| Thomas's Room | AC | `blueprint_hvac_room_thermostat.yaml` | ✅ Yes | 2 |
| Livia's Room | AC | `blueprint_hvac_room_thermostat.yaml` | ✅ Yes | 2 |

### Automations to KEEP in YAML

❌ **DO NOT migrate** (too specific logic):

- All shutters (VR) - too complex
- Outdoor lights - specific logic (sun, motion, etc.)
- Terrace - specific sensors and conditions
- Security/alarm - critical system
- Notifications - user-specific

## 🔄 Migration Process

### Step 1: Preparation

1. **Backup** your configuration:
```bash
# Backup automations.yaml
cp automations.yaml automations.yaml.backup

# Backup scripts if used
cp scripts.yaml scripts.yaml.backup
```

2. **Document** current behavior:
   - Note current timer values
   - Document special conditions
   - List all entities used

3. **Test environment** (if possible):
   - Test on development instance first
   - Or migrate one non-critical room first

### Step 2: First Migration (Simple Room)

**Example: Ground Floor Corridor**

1. **Add room** in Smart Room Manager:
   - Configuration → Integrations
   - Smart Room Manager → Configure
   - Options → Add a room

2. **Configure the room**:
```yaml
Room Name: "Ground Floor Corridor"
Room Type: "Corridor"
Lights:
  - light.corridor_light
Light Timeout: 300s (5 minutes)
```

3. **Test** the integration:
   - Turn light on manually
   - Wait for timer
   - Verify automatic turn-off

4. **Disable** old automation:
   - **DO NOT DELETE** yet
   - Just disable it
   - Keep for 1 week minimum

5. **Monitor** for issues:
   - Check logs
   - Test edge cases
   - Verify expected behavior

### Step 3: Heating Migration (Without Solar Optimizer)

**Example: Living Room**

1. **Configure room** in Smart Room Manager:
```yaml
Room Name: "Living Room"
Room Type: "Normal"
Temperature Sensor: sensor.living_room_temperature
Climate Entity: climate.living_room_thermostat
Door/Window Sensors:
  - binary_sensor.living_room_window

# Climate Configuration
Comfort Temperature: 20.5°C
Eco Temperature: 19.0°C
Night Temperature: 18.0°C
Frost Protection: 7.0°C
Window Check: enabled

# Schedule
Night Start: 23:00
Comfort Time Ranges: "07:00-09:00,18:00-23:00"
```

2. **Test phases**:
   - ✅ Comfort mode during comfort hours
   - ✅ Eco mode outside comfort hours
   - ✅ Night mode after night start
   - ✅ Frost protection when alarm armed_away
   - ✅ Window open detection

3. **Disable** old blueprint automation

### Step 4: Solar Optimizer Integration

**Example: Master Bedroom with X4FP**

1. **Prerequisites**:
   - Solar Optimizer already configured
   - Switch entity exists (e.g., `switch.solar_optimizer_master`)

2. **Configure room**:
```yaml
Room Name: "Master Bedroom"
Room Type: "Normal"
Temperature Sensor: sensor.master_temperature
Climate Entity: climate.master_x4fp
Door/Window Sensors:
  - binary_sensor.master_window
External Control Switch: switch.solar_optimizer_master

# Climate Configuration
Comfort Temperature: 19.0°C
Eco Temperature: 17.0°C
Night Temperature: 16.0°C
Frost Protection: 7.0°C
Summer Policy: "eco"

# External Control Configuration
External Control Preset: "comfort"
External Control Temp: 21.0°C
Allow External in Away: false

# Priority Configuration
Preset Comfort: "comfort"
Preset Eco: "eco"
Preset Window: "away"
```

3. **Priority System**:
```
1. Manual Pause (highest priority)
2. Bypass Switch
3. Window Open → Frost Protection
4. External Control (Solar Optimizer)
5. Away Mode (Alarm)
6. Schedule/Calendar
7. Normal Mode (Comfort/Eco/Night)
```

4. **Test Solar Optimizer**:
   - ✅ When SO switch ON → radiator follows SO
   - ✅ When SO switch OFF → Smart Room Manager resumes control
   - ✅ Window open → interrupts SO
   - ✅ Away mode → overrides SO (unless "Allow External in Away")

### Step 5: Advanced Features

#### Hysteresis Control (X4FP Type 3b)

For temperature-based control without external thermostats:

```yaml
# Climate Advanced Step
Setpoint Input: input_number.master_setpoint
Hysteresis: 0.5°C
Min Setpoint: 15.0°C
Max Setpoint: 22.0°C
Preset Heat: "comfort"
Preset Idle: "eco"
```

**Behavior**:
- Temperature < (Setpoint - Hysteresis) → Heat (Comfort preset)
- Temperature > (Setpoint + Hysteresis) → Idle (Eco preset)

#### Room Calendar

For per-room schedule overrides:

```yaml
# Schedule Step
Schedule Entity: calendar.master_schedule
Preset Schedule ON: "comfort"
Preset Schedule OFF: "eco"
```

**Use case**: Google Calendar event → force comfort mode

#### Manual Pause

```yaml
# Control Step
Pause Duration: 120 minutes
Infinite Pause: true
```

**Usage**:
- Switch `switch.master_pause` → pause automation temporarily
- Infinite pause: requires manual un-pause

## 🐛 Troubleshooting

### Issue: Lights don't turn off

**Check**:
1. Room type is "Corridor" or "Bathroom" (timer only for these types)
2. Light timeout is configured
3. Check logs for errors

**Solution**:
```yaml
# Ensure correct room type
Room Type: "Corridor"  # or "Bathroom"
Light Timeout: 300s
```

### Issue: Heating doesn't respond

**Check**:
1. Climate entity is responding manually
2. Check bypass switch is OFF
3. Check window sensors
4. Verify alarm state

**Debug sensors**:
- `sensor.ROOM_climate_priority` → shows current priority
- `sensor.ROOM_climate_state` → shows current state
- `sensor.ROOM_target_temperature` → shows target temp

### Issue: Solar Optimizer conflicts

**Check**:
1. External Control Switch is correctly configured
2. Priority is respected (use debug sensors)
3. "Allow External in Away" setting

**Solution**:
```yaml
# Ensure SO switch is configured
External Control Switch: switch.solar_optimizer_room
External Control Preset: "comfort"
Allow External in Away: false  # SO disabled when away
```

### Issue: Configuration not saving

**Check**:
1. Home Assistant logs for errors
2. Verify entity IDs exist
3. Check for None values

**Solution**:
- Only configure fields you actually use
- Leave optional fields empty, don't use None

## 📊 Migration Checklist

### Before Migration
- [ ] Backup `automations.yaml`
- [ ] Document current behavior
- [ ] List all entities used
- [ ] Identify Solar Optimizer rooms

### During Migration
- [ ] Add room to Smart Room Manager
- [ ] Configure all necessary fields
- [ ] Test basic functionality
- [ ] Test edge cases (window, away, etc.)
- [ ] Disable (don't delete) old automation

### After Migration
- [ ] Monitor for 1 week minimum
- [ ] Check logs for errors
- [ ] Verify all scenarios work
- [ ] Compare energy usage (if applicable)
- [ ] Delete old automation after confirmation

### Per Room Type

**Simple Lights**:
- [ ] Room name and type
- [ ] Light entities
- [ ] Timer value (corridor/bathroom only)
- [ ] Test on/off cycle

**Heating Only**:
- [ ] Temperature sensor
- [ ] Climate entity
- [ ] Window sensors
- [ ] Temperature setpoints
- [ ] Schedule/comfort ranges
- [ ] Test all modes

**With Solar Optimizer**:
- [ ] All heating items above
- [ ] External control switch
- [ ] External control preset
- [ ] Allow external in away setting
- [ ] Test SO priority
- [ ] Test normal mode fallback

**With Advanced Features**:
- [ ] Hysteresis configuration (if applicable)
- [ ] Room calendar (if applicable)
- [ ] Manual pause settings
- [ ] Debug sensors working

## 🎯 Success Criteria

A successful migration means:
- ✅ All expected behaviors work
- ✅ No errors in logs
- ✅ Energy usage similar or better
- ✅ Response times acceptable
- ✅ Edge cases handled (window, away, etc.)
- ✅ Manual controls work (pause, bypass)

## 📚 Additional Resources

- [Configuration Examples](CONFIGURATION_EXAMPLES.md) - Ready-to-use configurations
- [Solar Optimizer Guide](SOLAR_OPTIMIZER.md) - Detailed SO integration
- [Changelog](CHANGELOG.md) - Feature details and updates
- [README](README.md) - Full feature list

## 💡 Tips

1. **Start simple**: Migrate easiest rooms first
2. **Test thoroughly**: Don't rush, test all scenarios
3. **Monitor logs**: Check for warnings/errors
4. **Keep backups**: Don't delete old automations immediately
5. **One at a time**: Don't migrate multiple rooms simultaneously
6. **Document**: Note any special configurations
7. **Ask for help**: Check GitHub issues if stuck

Good luck with your migration! 🚀
