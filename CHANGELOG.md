# Changelog

All notable changes to Smart Room Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

[English](#english) | [Français](#français)

---

# English

## [0.3.9] - unreleased (branch fix/v0.3.9)

### 🐛 Bug Fixes

- **Pause switch now works** (B1): the pause state is held by the room. The previous lookup used `switch.smart_room_<room_id>_pause`, which never matched the real entity_id. Pause and Automation switches are restored after a restart; a timed pause keeps its end time.
- **Thermostat presets re-read** (B2/B3): presets are read on every cycle, so a thermostat that was unavailable at startup gets its presets (and the `away` preset when away, instead of `hvac off`). No command is sent to an unavailable climate entity. The "No preset for mode" warning is logged once per mode.
- **Hysteresis setpoint follows the mode** (B4): eco and night use their temperatures; `setpoint_input` is only used as the comfort setpoint.
- **External control (Wire Pilot)** (B7): compares with the real preset (no redundant command, re-applies after a manual change).
- **Timed pause timer** (B9): cancelled when the entity is removed (reload/unload).
- **Window delays** (B10): a window opened for less than the open delay no longer triggers frost protection (previously the close delay applied after any short opening). Delays are measured from the sensors' `last_changed`, not from the 30 s update loop.
- **Pause release** (B1e/B1f): turning the pause off, or its timer ending, gives control back to the room.
- **Anomalies log** (B11): the "configuration anomalies" warning is logged only when the list changes.
- **Bathrooms follow their calendar** (B12): light on = comfort; light off = calendar mode when a calendar is set (previously always eco).
- **Version** (B6): `VERSION` aligned with the manifest. **Minimum Home Assistant** (B8): 2024.11 (options flow).

### ✨ New

- **Configuration diagnostics** (B5): at startup and every 15 minutes, repair issues are created for missing entities, entities unavailable for more than 10 minutes, heating without actuator, actuators also driven by Solar Optimizer, and comfort setpoint below eco. New sensor `Anomalies`.

- **Manual change detection** (B13): when a person changes the preset, HVAC mode or setpoint of a room's climate entity (change carrying a `user_id`), SRM leaves that room alone for `manual_override_minutes` (room option, default 120 min, 0 = disabled), then resumes automatically. Reason shown as "réglage manuel" on the Pause switch and the priority sensor; turning the Pause switch off resumes control. Light timers are not affected.

### 🧪 Tests

- 141 automated tests (`tests/`, pytest-homeassistant-custom-component).

## [0.3.7] - 2026-05-11

### 🐛 Critical Bug Fixes

- **Summer mode external control fix**: External control (Solar Optimizer) no longer forces `HEAT` mode in summer. For reversible AC units it now switches to `COOL` with the configured cool comfort temperature; for heater-only thermostats and Wire Pilot heaters it is skipped during summer. Previously bedroom AC units kept reverting to heating each control cycle whenever external control was active.

## [0.3.6] - 2026-01-09

### 🐛 Critical Bug Fixes

- **X4FP hysteresis fix**: Frost protection mode now bypasses hysteresis and correctly applies the away preset
- **External control fix**: Solar Optimizer now only activates when you're away (inverted logic)
- **Entity selector fix**: Clearing sensors/switches in config now works correctly (conditional `default=`)
- **Room deletion fix**: Deleted rooms now properly removed from device registry
- **Cleanup service**: Now also removes orphaned devices

## [0.3.5] - 2026-01-09

### 🐛 Critical Bug Fixes

- **Climate type detection**: Wire Pilot entities now correctly use `set_preset_mode` instead of `set_temperature`
- **Translation**: "Fil Pilote" → "Wire Pilot" in English

## [0.3.4] - 2026-01-04

### 🐛 Bug Fixes

- Night period after midnight (22:00-06:00)
- VMC multi-bathroom conflict
- Heating mode priorities alignment
- ignore_in_away option respected
- Away → disarmed transition for X4FP and thermostats
- Manual pause now stops light control
- State sensor consistent with priorities

### ✨ New Features

- Thermostat control modes: `preset_only`, `temperature`, `preset_and_temp`
- Wire Pilot hysteresis simplified (temperature sensor as safeguard)

## [0.3.3] - 2026-01-04

- Climate mode selector (None, Wire Pilot, Thermostat heat/cool)
- VMC support with configurable timer
- Activity and Light Timer sensors
- Cleanup service for orphaned entities

## [0.3.0] - 2025-01-31

### Major Features

- External Control (Solar Optimizer support)
- Hysteresis for Wire Pilot (temperature-based control)
- Per-room schedule/calendar
- Manual pause switch (15min to 8h)
- Debug sensors (priority, hysteresis state, schedule active)
- Window open delays
- Configurable presets per room
- Summer policy (off/eco)

## [0.2.0] - 2025-01-14

- Simplified architecture (alarm-based presence)
- Room types (Normal, Corridor, Bathroom)
- Generic bypass switch
- Summer/winter mode

## [0.1.0] - 2025-01-13

- Initial release

---

# Français

## [0.3.7] - 2026-05-11

### 🐛 Corrections critiques

#### Fix : Mode été ignoré par le contrôle externe
- **Problème** : Quand le contrôle externe (Solar Optimizer) était actif, les climatisations des chambres repassaient sans cesse en mode chauffage, même en été. `_apply_external_control()` forçait `HVACMode.HEAT` à chaque cycle sans tenir compte du calendrier de saison.
- **Fix** : En mode été, les thermostats réversibles passent désormais en `COOL` avec la température `temp_cool_comfort`. Les thermostats non réversibles et les Fil Pilote (chauffage uniquement) sont ignorés par le contrôle externe en été plutôt que forcés en chauffage.

## [0.3.6] - 2026-01-09

### 🐛 Corrections critiques

#### Fix : X4FP hystérésis appliquait comfort au lieu de away
- **Problème** : En mode hystérésis avec Fil Pilote, le mode "absent" passait par la logique d'hystérésis
- **Fix** : `MODE_FROST_PROTECTION` bypass maintenant l'hystérésis

#### Fix : Contrôle externe actif quand présent
- **Problème** : Solar Optimizer était actif même quand l'utilisateur était présent
- **Fix** : `allow_in_away=True` signifie contrôle externe **uniquement** quand absent

#### Fix : Modifications d'entités qui revenaient
- **Problème** : Les sélecteurs d'entités ne sauvegardaient pas les suppressions
- **Fix** : `default=` conditionnel - défini uniquement si valeur existe

#### Fix : Suppression de pièce incomplète
- **Problème** : Pièce restait visible après suppression
- **Fix** : Suppression du device + entités manquantes (activity, light_timer, vmc_active)

### 🔧 Améliorations

- Service cleanup_entities supprime aussi les devices orphelins

## [0.3.5] - 2026-01-09

### 🐛 Corrections critiques

- **Détection Fil Pilote vs Thermostat** : Utilise `CONF_CLIMATE_MODE` configuré
- **Traduction** : "Fil Pilote" → "Wire Pilot" en anglais

## [0.3.4] - 2026-01-09

### 🐛 Corrections critiques

- Période nuit après minuit (22:00-06:00)
- VMC multi-salles de bain
- Priorités mode chauffage
- Option ignore_in_away respectée
- Transition away → disarmed
- Pause manuelle arrête les lumières
- Sensor état cohérent avec priorités
- Presets hors-gel différenciés (away vs fenêtres)

### ✨ Nouvelles fonctionnalités

- **Thermostat** : Mode de contrôle (`preset_only`, `temperature`, `preset_and_temp`)
- **Fil Pilote** : Hystérésis simplifiée (capteur temp comme garde-fou)

### 🔧 Refactoring

- Renommage X4FP → Fil Pilote
- `_control_entity()` générique pour VMC

## [0.3.3] - 2026-01-04

### ✨ Améliorations UX

- Sélection du mode climat (Aucun, Fil Pilote, Thermostat)
- Support VMC avec timer configurable
- Capteurs Activity et Timer Lumière
- Service de nettoyage des entités orphelines

## [0.3.0] - 2025-01-31

### 🎯 Fonctionnalités majeures

- Contrôle externe (Solar Optimizer)
- Hystérésis Fil Pilote (contrôle par température)
- Calendrier par pièce
- Switch pause manuelle (15min à 8h)
- Capteurs debug (priorité, hystérésis, schedule)
- Délais fenêtre ouverte
- Presets configurables par pièce
- Politique été (off/eco)

## [0.2.0] - 2025-01-14

- Architecture simplifiée (présence par alarme)
- Types de pièces (Normal, Couloir, Salle de bain)
- Switch bypass générique
- Mode été/hiver

## [0.1.0] - 2025-01-13

- Version initiale

---

[Unreleased]: https://github.com/GevaudanBeast/HA-SMART/compare/v0.3.7...HEAD
[0.3.7]: https://github.com/GevaudanBeast/HA-SMART/compare/v0.3.6...v0.3.7
[0.3.6]: https://github.com/GevaudanBeast/HA-SMART/compare/v0.3.5...v0.3.6
[0.3.5]: https://github.com/GevaudanBeast/HA-SMART/compare/v0.3.4...v0.3.5
[0.3.4]: https://github.com/GevaudanBeast/HA-SMART/compare/v0.3.3...v0.3.4
