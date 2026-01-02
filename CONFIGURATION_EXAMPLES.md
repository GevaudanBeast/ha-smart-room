# 🏠 Configuration Examples

This document contains **ready-to-use** configuration examples for specific room types.

## 📋 Table of Contents

- [Simple Lights](#simple-lights)
- [Lights with Sensors](#lights-with-sensors)
- [Simple Heating](#simple-heating)
- [Global Entities](#global-entities)

---

## 🔧 Global Entities

Configure **once** in **Configuration → Integrations → Smart Room Manager → Configure → Global Settings**:

| Parameter | Entity | Comment |
|-----------|--------|---------|
| Alarm Entity | `alarm_control_panel.home` | ✅ Required |
| Season Calendar | `calendar.summer_winter` | ✅ Required |

---

## 💡 Simple Lights

### Ground Floor Corridor

**Characteristics**:
- Timer: 5 minutes
- Manual control
- No presence sensor

**Smart Room Manager Configuration**:

```yaml
Room Name: "Ground Floor Corridor"
Room Type: "Corridor"

# Sensors Step
Door/Window Sensors: (empty)
Temperature Sensor: (empty)
Humidity Sensor: (empty)

# Actuators Step
Lights:
  - light.corridor_light
Climate Entity: (empty)
Bypass Switch: (empty)
External Control Switch: (empty)

# Light Config Step
Light Timeout: 300s (5 minutes)

# Climate Config Step
(skip - no heating)

# Schedule Step
Night Start: 22:00
Comfort Time Ranges: (empty)

# Control Step
Pause Duration: 30 minutes
Infinite Pause: false
```

---

### Bathroom

**Characteristics**:
- Timer: 15 minutes
- Manual light control
- Heating controlled by radiator

**Smart Room Manager Configuration**:

```yaml
Room Name: "Bathroom"
Room Type: "Bathroom"

# Sensors Step
Door/Window Sensors: (empty)
Temperature Sensor: sensor.bathroom_temperature
Humidity Sensor: sensor.bathroom_humidity

# Actuators Step
Lights:
  - light.bathroom_light
Climate Entity: climate.bathroom_x4fp
Bypass Switch: (empty)
External Control Switch: (empty)

# Light Config Step
Light Timeout: 900s (15 minutes)

# Climate Config Step
Comfort Temperature: 21.0°C
Eco Temperature: 19.0°C
Night Temperature: 18.0°C
Frost Protection: 7.0°C
Cool Comfort: 25.0°C
Cool Eco: 27.0°C
Window Check: enabled
Window Open Delay: 2 minutes
Window Close Delay: 5 minutes
Summer Policy: "eco"

# Climate Advanced Step
External Control Preset: "comfort"
External Control Temp: 21.0°C
Allow External in Away: false
Preset Comfort: "comfort"
Preset Eco: "eco"
Preset Night: "eco"
Preset Away: "away"
Preset Window: "away"

# Schedule Step
Night Start: 22:00
Comfort Time Ranges: "06:30-08:30,18:00-22:00"

# Control Step
Pause Duration: 60 minutes
Infinite Pause: false
```

---

## 🌡️ Simple Heating

### Living Room (Thermostat)

**Characteristics**:
- Thermostat-based heating
- No automatic lights
- Temperature control

**Smart Room Manager Configuration**:

```yaml
Room Name: "Living Room"
Room Type: "Normal"

# Sensors Step
Door/Window Sensors:
  - binary_sensor.living_room_window
Temperature Sensor: sensor.living_room_temperature
Humidity Sensor: (empty)

# Actuators Step
Lights: (empty)
Climate Entity: climate.living_room_thermostat
Bypass Switch: input_boolean.living_room_bypass
External Control Switch: (empty)

# Climate Config Step
Comfort Temperature: 20.5°C
Eco Temperature: 19.0°C
Night Temperature: 18.0°C
Frost Protection: 7.0°C
Cool Comfort: 24.0°C
Cool Eco: 26.0°C
Window Check: enabled
Window Open Delay: 2 minutes
Window Close Delay: 5 minutes
Summer Policy: "off"

# Schedule Step
Night Start: 23:00
Comfort Time Ranges: "07:00-09:00,18:00-23:00"

# Control Step
Pause Duration: 120 minutes
Infinite Pause: false
```

---

### Master Bedroom (X4FP with Solar Optimizer)

**Characteristics**:
- X4FP fil pilote radiator
- Solar Optimizer integration
- Temperature-based hysteresis control
- Room calendar support

**Smart Room Manager Configuration**:

```yaml
Room Name: "Master Bedroom"
Room Type: "Normal"

# Sensors Step
Door/Window Sensors:
  - binary_sensor.master_window
Temperature Sensor: sensor.master_temperature
Humidity Sensor: (empty)

# Actuators Step
Lights: (empty)
Climate Entity: climate.master_x4fp
Bypass Switch: input_boolean.master_bypass
External Control Switch: switch.solar_optimizer_master

# Climate Config Step
Comfort Temperature: 19.0°C
Eco Temperature: 17.0°C
Night Temperature: 16.0°C
Frost Protection: 7.0°C
Cool Comfort: 25.0°C
Cool Eco: 27.0°C
Window Check: enabled
Window Open Delay: 3 minutes
Window Close Delay: 10 minutes
Summer Policy: "eco"

# Climate Advanced Step
Setpoint Input: input_number.master_setpoint
Hysteresis: 0.5°C
Min Setpoint: 15.0°C
Max Setpoint: 22.0°C
Preset Heat: "comfort"
Preset Idle: "eco"
External Control Preset: "comfort"
External Control Temp: 21.0°C
Allow External in Away: false
Preset Comfort: "comfort"
Preset Eco: "eco"
Preset Night: "eco"
Preset Away: "away"
Preset Window: "away"

# Schedule Step
Night Start: 22:30
Comfort Time Ranges: "06:30-08:00,18:00-22:30"
Schedule Entity: calendar.master_schedule
Preset Schedule ON: "comfort"
Preset Schedule OFF: "eco"

# Control Step
Pause Duration: 120 minutes
Infinite Pause: true
```

---

## 📝 Notes

- **Empty fields**: Leave empty if not used
- **Timers**: Only for corridor and bathroom room types
- **Solar Optimizer**: Use External Control Switch field
- **Hysteresis**: Only configure if you have a setpoint input entity
- **Calendars**: Optional per-room scheduling

For migration from existing automations, see [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md).
