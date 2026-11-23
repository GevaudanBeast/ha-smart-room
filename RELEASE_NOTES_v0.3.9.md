## Smart Room Manager v0.3.9

Reliability release, validated on a real installation (beta.1 to beta.7). **Requires Home Assistant 2024.11 or later.**

### 🐛 Bug fixes
- **B1 Pause switch**: the pause state is held by the room (the old lookup by entity_id never matched). Turning the pause off, or the end of a timed pause, gives control back. Pause and Automation switches are restored after a restart; a timed pause keeps its end time.
- **B2/B3 Presets re-read**: presets are read on every cycle, so a thermostat unavailable at startup works once it is back; `away` preset when away instead of `hvac off`; no command to an unavailable climate entity; "no preset for mode" warning logged once per mode.
- **B4 Hysteresis setpoint follows the mode**: eco and night use their temperatures; `setpoint_input` is only the comfort setpoint.
- **B6 Version** aligned with the manifest.
- **B7 External control (Wire Pilot)**: compares with the real preset (no redundant command, re-applies after a manual change).
- **B8 Minimum Home Assistant** 2024.11 (options flow).
- **B9 Timed pause timer** cancelled when the entity is removed.
- **B10 Window delays**: an opening shorter than the open delay no longer triggers frost protection; delays measured from the sensors' `last_changed`.
- **B11 Anomalies log**: written only when the list changes.
- **B12 Bathrooms**: light on = comfort, light off = calendar mode when a calendar is set (previously always eco).

### ✨ New
- **B5 Configuration diagnostics**: repair issues and an `Anomalies` sensor (missing entities, entities unavailable for more than 10 min, heating without actuator, actuator also driven by Solar Optimizer or another room, comfort setpoint below eco).
- **B13 Manual changes respected**: when a person changes the preset, HVAC mode or setpoint, SRM leaves the room alone for `manual_override_minutes` (room option, default 120, 0 = disabled). The priority sensor shows "Réglage manuel respecté jusqu'à HH:MM"; turning the Pause switch off resumes control.
- **B14 Heating blocked by a window**: when heating (or cooling) is wanted (calendar, manual change, Solar Optimizer) but an open window forces frost protection, the `Chauffage bloqué` binary sensor turns on and `smart_room_manager_heating_blocked` is fired (`_unblocked` when it ends). Eco is not a demand, nothing when away, the Pause switch bypasses everything. The window wins over a manual change, which is re-applied when the window closes.
- **B15 Notifications**: new "Notifications" options step. Types: heating blocked/unblocked, manual change detected/ended, configuration issues, frost protection. Targets: `notify` entities, legacy notify actions (with `data`), scripts (variables title, message, type, room_id, room_name, entities). Per-room targets (add or replace), quiet period with fallback targets, cooldown (default 10 min), French/English texts. The `smart_room_manager_notification` event is always fired; existing events are kept.

### 🧪 Tests
- 187 automated tests (pytest-homeassistant-custom-component), 92 % coverage.

### ⬆️ Upgrade
- Update through HACS / Marketplace and restart Home Assistant. No configuration change is required; new options keep their defaults (manual change 120 min, notifications without targets).

---

## Smart Room Manager v0.3.9 (FR)

Version de fiabilité validée sur une installation réelle. Home Assistant 2024.11 minimum.
Corrections : pause (B1), presets relus et `away` en absence (B2/B3), consigne selon le mode (B4), version (B6), contrôle externe Fil Pilote (B7), HA minimum (B8), timer de pause (B9), délais fenêtres (B10), journal des anomalies (B11), salles de bain et calendrier (B12).
Nouveautés : diagnostic de configuration (B5), réglages manuels respectés (B13), chauffage bloqué par une fenêtre (B14), notifications (B15).
Voir le [CHANGELOG](https://github.com/GevaudanBeast/ha-smart-room/blob/main/CHANGELOG.md).
