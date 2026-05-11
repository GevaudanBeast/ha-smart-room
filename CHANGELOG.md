# Changelog

All notable changes to Smart Room Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

[English](#english) | [Français](#français)

---

# English

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
