# Changelog

All notable changes to Smart Room Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.5] - 2026-01-09

### 🐛 Corrections critiques

#### Fix : Détection du type de climat (Fil Pilote vs Thermostat)
- **Problème** : Les entités Fil Pilote (`climate.x4fp_fp_*`) étaient envoyées au contrôleur thermostat, qui appelait `set_temperature` (non supporté par Fil Pilote)
- **Cause** : Auto-détection basée sur les attributs de l'entité au lieu d'utiliser la configuration utilisateur
- **Fix** : Utilise désormais `CONF_CLIMATE_MODE` configuré par l'utilisateur
  - `fil_pilote` → `CLIMATE_TYPE_FIL_PILOTE` (utilise `set_preset_mode`)
  - `thermostat_heat/cool/heat_cool` → `CLIMATE_TYPE_THERMOSTAT` (utilise `set_temperature`)
- **Fallback** : Détection par attributs seulement si `climate_mode` n'est pas configuré

### 🌍 Traductions

#### Wire Pilot (terme technique anglais)
- **Renommé** : "Fil Pilote" → "Wire Pilot" dans toutes les traductions anglaises
- **Fichiers** : `strings.json`, `translations/en.json`
- **Note** : Le français conserve "Fil Pilote"

## [0.3.4] - 2026-01-09

### 🐛 Corrections critiques

#### Fix : Période nuit après minuit
- **Problème** : La période nuit ne fonctionnait qu'entre 22:00 et 23:59
- **Fix** : Ajout de `DEFAULT_DAY_START` (06:00), la nuit est maintenant 22:00-06:00
- **Logique** : `is_night = now >= 22:00 OR now < 06:00`

#### Fix : VMC multi-salles de bain
- **Problème** : Le timer VMC d'une salle de bain pouvait éteindre la VMC globale alors qu'une autre salle de bain était encore active
- **Fix** : Ajout de `_any_other_bathroom_active()` qui vérifie si d'autres salles de bain ont besoin de la VMC avant de l'éteindre

#### Fix : Priorités mode chauffage
- **Fix** : Alignement des priorités entre `room_manager` et `climate_control`
- **Fix** : Le calendrier a maintenant priorité sur la période nuit (config explicite)
- **Fix** : Les salles de bain utilisent la logique lumière avant le calendrier

#### Fix : Option ignore_in_away respectée
- **Problème** : Le schedule était ignoré même avec l'option "ignore_in_away" cochée
- **Fix** : Vérification de `ignore_in_away` dans la priorité away mode

#### Fix : Transition away → disarmed (X4FP et Thermostats)
- **Problème** : Passage de armed_away à disarmed ne changeait pas les presets
- **Fix X4FP** : Synchronisation avec l'état réel du preset avant comparaison
- **Fix Thermostat** : Support des presets "away" et "home" si le thermostat les supporte
- **Comportement** : X4FP away→eco/comfort, Thermostat away→home + heat/cool

#### Fix : Pause manuelle n'arrêtait pas les lumières
- **Problème** : Le switch pause n'arrêtait que le chauffage, pas le contrôle des lumières
- **Fix** : Ajout de la vérification `is_paused()` dans `light_control.py`

#### Fix : Sensor état incohérent avec priorités
- **Problème** : Le sensor d'état ignorait fenêtres ouvertes et ignore_in_away
- **Fix** : Alignement des priorités dans `room_manager._update_current_mode()`
- **Comportement** : Le sensor affiche maintenant le vrai mode appliqué

#### Fix : Presets hors-gel différenciés (away vs fenêtres)
- **Problème** : Le preset "fenêtre" était utilisé pour les deux cas (absence et fenêtres)
- **Fix** : Paramètre `reason` ajouté à `set_frost_protection()`
- **Comportement** : `CONF_PRESET_AWAY` pour absence, `CONF_PRESET_WINDOW` pour fenêtres

### ✨ Nouvelles fonctionnalités

#### Thermostat : Mode de contrôle configurable
- **Nouveau** : Option `thermostat_control_mode` dans la configuration avancée
- **Modes disponibles** :
  - `preset_only` (défaut, recommandé) : Utilise uniquement les presets du thermostat, l'utilisateur contrôle les températures dans l'app native (Netatmo, Tado, etc.)
  - `temperature` : Contrôle direct de la température (ancien comportement)
  - `preset_and_temp` : Utilise les presets ET définit la température
- **Mapping automatique** : Modes SRM → presets thermostat avec fallbacks
  - Confort → comfort, home, boost
  - Eco → eco, home
  - Nuit → sleep, eco, home
  - Absence → away
- **Config Flow intelligent** : Les températures ne sont affichées que si `control_mode != preset_only`
  - Mode `preset_only` : Pas d'étape températures (l'utilisateur configure dans l'app thermostat)
  - Mode `temperature`/`both` : Nouvelle étape `thermostat_temperatures` avec toutes les consignes

#### Fil Pilote : Hystérésis simplifiée
- **Amélioration** : Ne nécessite plus qu'un capteur de température (pas de setpoint_input obligatoire)
- **Consigne automatique** : Utilise les températures configurées (confort, eco, nuit) selon le mode actif
- **Optionnel** : `setpoint_input` (input_number) reste disponible pour un contrôle dynamique
- **Garde-fou** : Le capteur de température fournit le retour pour arrêter à la bonne température

### 🔧 Refactoring

#### Renommage X4FP → Fil Pilote
- **Renommé** : `x4fp_controller.py` → `fil_pilote_controller.py`
- **Renommé** : Classe `X4FPController` → `FilPiloteController`
- **Nouvelles constantes** : `FP_PRESET_*` avec alias `X4FP_PRESET_*` pour rétro-compatibilité
- **Nouvelle constante** : `CLIMATE_TYPE_FIL_PILOTE` avec alias `CLIMATE_TYPE_X4FP`
- **Traductions** : "X4FP" remplacé par "Fil Pilote" (en, fr)
- **Note** : Le nom "Fil Pilote" est plus générique et clair pour les utilisateurs français (IPX800, Qubino, etc.)

#### Autres améliorations
- **Consolidé** : Méthodes VMC on/off en `_control_entity()` générique
- **Ajouté** : Helper `_get_entity_domain()` pour extraction du domaine
- **Corrigé** : Null check sur `state.last_changed`
- **Uniformisé** : Tous les binary_sensor retournent `None` quand pas de données

### ✅ Rétro-compatibilité
- Les configurations existantes restent fonctionnelles
- Les alias `X4FP_PRESET_*` et `CLIMATE_TYPE_X4FP` préservent la compatibilité
- Le mode `preset_only` est le défaut pour les thermostats (nouveau comportement recommandé)
- Les anciennes configurations avec `setpoint_input` continuent de fonctionner

## [0.3.3] - 2026-01-04

### ✨ Améliorations UX - Configuration contextuelle

#### Nouveau : Sélection du mode climat
- **Ajouté** : Sélecteur de type de chauffage dans les actionneurs :
  - Aucun (couloirs, etc.)
  - Fil Pilote (X4FP, IPX800...)
  - Thermostat (chauffage seul)
  - Thermostat (climatisation seule)
  - Thermostat (chaud/froid)
- **Amélioré** : Configuration contextuelle basée sur le mode sélectionné

#### Nouveau : Support VMC (Ventilation)
- **Ajouté** : Entité VMC globale dans paramètres généraux (switch ou fan)
- **Ajouté** : Timer VMC configurable (durée après extinction lumière)
- **Comportement** : VMC grande vitesse s'active à l'allumage, timer démarre à l'extinction
- **Ajouté** : binary_sensor VMC Grande Vitesse (affiche countdown)

#### Nouveau : Capteurs de debug et traçage
- **Ajouté** : sensor Activité pour chaque pièce (log lisible avec emojis)
- **Ajouté** : binary_sensor Timer Lumière (countdown avant extinction auto)
- **Ajouté** : Descriptions claires pour bypass vs contrôle externe

#### Nouveau : Service de nettoyage
- **Ajouté** : Service `smart_room_manager.cleanup_entities` pour supprimer les entités orphelines
- **Comportement** : Supprime automatiquement les entités des pièces qui n'existent plus

#### Améliorations des types de pièces
- **Renommé** : "Normal" → "Pièce de vie" (chambre, salon, cuisine, bureau...)
- **Renommé** : "Couloir" → "Pièce de passage" (couloir, grenier, cave, buanderie...)
- **Renommé** : "Salle de bain" → "Salle de bain / WC" (timer lumière + VMC)

#### Logique de configuration intelligente
- **Amélioré** : Pas d'entité climat → mode forcé à "Aucun", config climat sautée
- **Amélioré** : Fil Pilote + capteur temp → températures de consigne affichées
- **Amélioré** : Fil Pilote sans capteur temp → températures masquées
- **Amélioré** : Bypass et contrôle externe ignorés si pas de climat configuré

### 🐛 Corrections

#### Fix : Erreur de validation SelectSelector
- **Problème** : "unknown error" lors de la création/édition de pièces
- **Cause** : SelectSelector pour pause_duration utilisait des entiers au lieu de chaînes
- **Fix** : Conversion en options string ["15", "30", "60", "120", "240", "480"]

#### Fix : Erreurs de longueur de ligne (E501)
- **Fix** : Toutes les lignes respectent la limite de 88 caractères pour ruff/HACS

#### Fix : Imports non utilisés
- **Fix** : Suppression des imports F401 dans plusieurs fichiers

### ✅ Compatibilité ascendante
- Les configurations existantes restent fonctionnelles
- Les nouveaux champs (VMC, climate_mode) sont optionnels avec valeurs par défaut
- Pas de migration nécessaire

### 🌍 Internationalization Improvements

#### Complete translation system for English and French
- **Added**: SelectSelector with translation_key for room types (Normal, Corridor, Bathroom)
- **Added**: SelectSelector with translation_key for summer policy (Off, Eco, Comfort)
- **Added**: SelectSelector with translation_key for pause duration (15min to 8h)
- **Fixed**: French translations for bypass and external control switches
- **Fixed**: Mixed French/English strings in room_control options
- **Updated**: All translation files (strings.json, en.json, fr.json) with new selectors

#### Simplified Schedule Configuration
- **Removed from UI**: `night_start` and `comfort_ranges` fields from schedule configuration step
- **Added**: `ignore_in_away` option to skip schedule when alarm is in away mode
- **Backward Compatibility**: Existing installations with `night_start` and `comfort_ranges` configured will continue to work with these values
- **Note**: New installations will use default values (night_start: 22:00, comfort_ranges: empty)

#### Technical Changes
- Marked `CONF_NIGHT_START` and `CONF_COMFORT_TIME_RANGES` as DEPRECATED in const.py
- Helper functions `parse_comfort_ranges()` and `format_comfort_ranges()` kept for backward compatibility
- Removed unused imports from config_flow.py

### ✅ Backward Compatibility Guarantees
- **Existing configurations**: All existing room configurations with `night_start` and `comfort_ranges` will continue to work
- **Runtime behavior**: RoomManager still uses these values if present in configuration
- **Default values**: New configurations use `DEFAULT_NIGHT_START = "22:00:00"` and empty comfort_ranges
- **No migration needed**: Upgrade is safe and non-breaking for existing users

## [0.3.2] - 2026-01-02

### 🐛 Critical Bug Fix - Module Import Conflict

#### Fix: config_flow module naming conflict
- **Problem**: Integration failed to load with "Invalid handler specified" error, no logs generated
- **Root Cause**: Both `config_flow.py` file AND `config_flow/` directory existed, creating Python import ambiguity
- **Impact**: Home Assistant could not load the integration at all in v0.3.0 and v0.3.1
- **Fix**: Removed `config_flow.py` file, consolidated all code into `config_flow/__init__.py` package
- **Files Changed**:
  - Deleted: `config_flow.py` (653 lines)
  - Updated: `config_flow/__init__.py` (now contains full config flow implementation)

**⚠️ Users affected by v0.3.0/v0.3.1**: Please upgrade to v0.3.2 immediately. The previous versions were non-functional due to this module conflict.

### 📊 Verified Compatibility
- ✅ Home Assistant 2023.1+ through 2025.12+
- ✅ All fixes from v0.3.1 preserved (OptionsFlow and async_shutdown)

## [0.3.1] - 2025-12-31

### 🐛 Bug Fixes - Critical Compatibility Issues

#### Fix: Config Flow "Invalid handler specified" error (HA 2025.12 compatibility)
- **Problem**: Config flow failed to load with "Invalid handler specified" error in Home Assistant 2025.12+
- **Root Cause**: `OptionsFlow.__init__()` accepted `config_entry` parameter which is now deprecated
- **Fix**: Remove `config_entry` parameter from both `async_get_options_flow()` and `OptionsFlow.__init__()`
- **Impact**: Config flow now loads correctly on HA 2025.12+
- **File**: `config_flow.py:191, 197`
- **Change**:
  ```python
  # Before (deprecated)
  return SmartRoomManagerOptionsFlow(config_entry)
  def __init__(self, config_entry: config_entries.ConfigEntry) -> None:

  # After (HA 2025.12+ compatible)
  return SmartRoomManagerOptionsFlow()
  def __init__(self) -> None:
  ```

#### Fix: Home Assistant 2023.x compatibility for async_shutdown
- **Problem**: `AttributeError: 'super' object has no attribute 'async_shutdown'` on HA 2023.x
- **Root Cause**: `DataUpdateCoordinator.async_shutdown()` was added in HA 2024.x
- **Fix**: Check if method exists before calling using `hasattr()`
- **Impact**: Integration now works on both HA 2023.1+ and 2024.x+
- **File**: `coordinator.py:98`
- **Change**:
  ```python
  # Before (HA 2024.x only)
  await super().async_shutdown()

  # After (HA 2023.1+ compatible)
  if hasattr(super(), "async_shutdown"):
      await super().async_shutdown()
  ```

### 📊 Compatibility Matrix
- ✅ **Home Assistant 2023.1+** - Minimum supported (with async_shutdown check)
- ✅ **Home Assistant 2024.x** - Fully supported
- ✅ **Home Assistant 2025.12+** - Latest tested (with OptionsFlow fix)

### 🔄 Migration from v0.3.0
No configuration changes required. This is a compatibility patch release.

**Recommended actions:**
1. Update integration via HACS or manual installation
2. Restart Home Assistant completely
3. Clear Python cache if issues persist:
   ```bash
   cd /config/custom_components/smart_room_manager
   find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
   find . -name "*.pyc" -delete
   ha core restart
   ```

## [0.3.0] - 2025-01-31

### 🎯 Major Feature Release - Advanced Climate Control

#### Priority 1 Features Added

- **External Control (Solar Optimizer, etc.)**
  - Generic external control support via switch entity
  - `CONF_EXTERNAL_CONTROL_SWITCH`: Entity to monitor (input_boolean, switch)
  - `CONF_EXTERNAL_CONTROL_PRESET`: X4FP preset when active (default: comfort)
  - `CONF_EXTERNAL_CONTROL_TEMP`: Thermostat temperature when active (default: 20°C)
  - `CONF_ALLOW_EXTERNAL_IN_AWAY`: Allow external control override when away (default: false)
  - Priority: Higher than away mode, lower than windows open
  - Monitors `is_active` attribute or state ON

- **Hysteresis X4FP Type 3b**
  - Temperature-based control for X4FP radiators with hysteresis
  - `CONF_SETPOINT_INPUT`: Input number or sensor for target temperature
  - `CONF_HYSTERESIS`: Temperature deadband (default: 0.5°C)
  - `CONF_MIN_SETPOINT`, `CONF_MAX_SETPOINT`: Limits for setpoint clamping (17-23°C)
  - `CONF_PRESET_HEAT`: Preset when heating needed (default: comfort)
  - `CONF_PRESET_IDLE`: Preset when temperature reached (default: eco)
  - Three states: heating, idle, deadband (no change)
  - Hysteresis state available via debug sensor

- **Schedule/Calendar per Room**
  - Per-room calendar/schedule entity support
  - `CONF_SCHEDULE_ENTITY`: Calendar or schedule entity
  - `CONF_PRESET_SCHEDULE_ON`: Mode when calendar event active (default: comfort)
  - `CONF_PRESET_SCHEDULE_OFF`: Mode when no event (default: eco)
  - Priority: Higher than normal mode, lower than away
  - Overrides time-based comfort ranges when configured
  - Schedule active status via debug sensor

- **Manual Pause Switch**
  - Per-room pause switch to temporarily disable automation
  - `CONF_PAUSE_DURATION_MINUTES`: Auto-resume duration (15, 30, 60, 120, 240, 480 minutes)
  - `CONF_PAUSE_INFINITE`: Enable infinite pause (no auto-resume)
  - Highest priority (paused = 0.5, above bypass)
  - Switch entity: `switch.smart_room_{room_id}_pause`
  - Attributes: duration_minutes, infinite_enabled, pause_until, remaining_minutes
  - Auto-turn off after duration or manual turn off

- **Debug Sensors**
  - `sensor.smart_room_{room_id}_current_priority`: Current priority level (paused, bypass, windows_open, external_control, away, schedule, normal)
  - `binary_sensor.smart_room_{room_id}_external_control_active`: External control status
  - `sensor.smart_room_{room_id}_hysteresis_state`: Hysteresis state (heating, idle, deadband)
  - `binary_sensor.smart_room_{room_id}_schedule_active`: Schedule active status
  - Detailed hysteresis attributes: current_temp, setpoint, hysteresis_value, lower/upper thresholds

#### Priority 2 Features Added

- **Window Delays**
  - Configurable delays before reacting to windows open/close
  - `CONF_WINDOW_DELAY_OPEN`: Minutes before setting frost protection (default: 2)
  - `CONF_WINDOW_DELAY_CLOSE`: Minutes before resuming after close (default: 2)
  - Prevents false reactions to brief window openings
  - Timestamp-based tracking with `is_windows_open_delayed()` method

- **Configurable X4FP Presets**
  - Customize X4FP presets per room
  - `CONF_PRESET_COMFORT`: Preset for comfort mode (default: comfort)
  - `CONF_PRESET_ECO`: Preset for eco mode (default: eco)
  - `CONF_PRESET_NIGHT`: Preset for night mode (default: eco)
  - `CONF_PRESET_AWAY`: Preset for away/frost protection (default: away)
  - `CONF_PRESET_WINDOW`: Preset for windows open (default: away)
  - Adapts to different radiator types

- **Summer Policy**
  - Configurable X4FP behavior in summer mode
  - `CONF_SUMMER_POLICY`: "off" or "eco" (default: "off")
  - "off": Turn off radiators completely in summer
  - "eco": Keep radiators on eco preset in summer
  - Applied in both normal and hysteresis control modes

#### Priority System (v0.3.0)

New 7-level priority hierarchy (0.5 = highest, 6 = lowest):
1. **Priority 0.5 - Paused**: Manual pause active
2. **Priority 1 - Bypass**: Climate bypass switch ON
3. **Priority 2 - Windows Open**: Windows detected open (with delay)
4. **Priority 3 - External Control**: Solar Optimizer or similar active
5. **Priority 4 - Away**: Alarm armed_away
6. **Priority 5 - Schedule**: Calendar event active
7. **Priority 6 - Normal**: Time-based or default mode

#### Config Flow Updated

- Wizard updated from v0.2.0 to v0.3.0 (6 → 8 steps)
- **Step 3 (Actuators)**: Added external_control_switch field
- **Step 5 (Climate Config)**: Added window_delay_open, window_delay_close, summer_policy
- **Step 6 (Climate Advanced)**: NEW - Hysteresis, External Control config, X4FP Presets
- **Step 7 (Schedule)**: Added schedule_entity, preset_schedule_on, preset_schedule_off
- **Step 8 (Room Control)**: NEW - Pause duration, pause infinite
- All features configurable via UI
- Sensible defaults for all optional features

#### Technical Improvements

- **Code Refactoring**: Modularized codebase for better maintainability
  - `config_flow.py`: Reduced from 1223 to 654 lines (-47%) by extracting schemas and helpers
  - `climate_control.py`: Reduced from 768 to 392 lines (-49%) by extracting specialized controllers
  - Created `config_flow/` module: schemas.py (715 lines), helpers.py (70 lines)
  - Created `climate/` module: x4fp_controller.py (337 lines), thermostat_controller.py (201 lines)
  - Improved testability and separation of concerns
  - Lazy-loaded controllers for better performance
- Fixed forward reference bug in const.py (X4FP_PRESET_* used before definition)
- Proper timestamp tracking for window states
- Improved logging with emojis for better visibility
- Comprehensive state tracking for debug purposes
- All features have proper defaults and validation

### Migration from v0.2.x

No breaking changes. All new features are optional with sensible defaults.
Existing configurations continue to work without modification.
Reconfigure rooms via UI to enable new v0.3.0 features.

## [0.2.4] - 2025-11-16

### Added
- MIT License file
- Badges to README (Version, License, Home Assistant compatibility, HACS)

### Changed
- Version bump to 0.2.4
- Improved documentation

## [0.2.3] - 2025-01-14

### Fixed
- **Erreurs critiques multiples** : Corrections complètes pour v0.2.3
  - **Import DOMAIN manquant** : Ajout de `from .const import DOMAIN` dans switch.py et binary_sensor.py
    - Résout : `NameError: name 'DOMAIN' is not defined`
  - **Warning deprecated** : Suppression de l'assignment explicite de config_entry dans OptionsFlow
    - Compatible avec Home Assistant 2025.12
  - **"Entity None" dans formulaires** : Corrections multiples
    - Migration étendue : Nettoyage de door_window_sensors et lights (en plus de temperature_sensor, humidity_sensor, climate_entity, climate_bypass_switch)
    - Correction de `.get(field, [])` en `.get(field) or []` dans 7 emplacements (config_flow.py, light_control.py, room_manager.py)
    - Schémas de formulaires conditionnels pour ne pas afficher None comme valeur par défaut
  - Résout complètement l'erreur "Entity None is neither a valid entity ID nor a valid UUID"
  - Migration transparente au démarrage, aucune action utilisateur requise

## [0.2.2] - 2025-01-14

### Improved
- **Configuration optionnelle** : Les champs température/humidité et autres capteurs/actionneurs ne sont plus sauvegardés avec une valeur `None` lorsqu'ils ne sont pas configurés
  - Seuls les champs réellement configurés sont enregistrés dans la configuration
  - Configuration plus propre et minimale possible
  - Compatible avec des pièces minimalistes (juste un nom) jusqu'à des pièces ultra-équipées

## [0.2.1] - 2025-01-14

### Fixed
- **Critical import error** : Fixed ALARM_STATE_ARMED_AWAY import from homeassistant.const (doesn't exist)
  - Now correctly imports from our own const.py
  - This was preventing the integration from loading in Home Assistant
  - Error: `cannot import name 'ALARM_STATE_ARMED_AWAY' from 'homeassistant.const'`

## [0.2.0] - 2025-01-14

### 🎯 Major Refactoring - Simplified Architecture

#### Removed (Breaking Changes)
- **Presence sensors** : Replaced by alarm-based presence detection (armed_away = absent)
- **Interior luminosity sensors** : Manual light control only, auto-off timer for corridors/bathrooms
- **Guest mode and vacation mode** : Simplified to 4 modes (removed 2 modes)
- **6 time periods** : Reduced to night period + multiple configurable comfort time ranges
- **Solar Optimizer specific field** : Replaced with generic bypass switch

#### Added
- **Room types** system:
  - Normal (bedrooms): No light timer
  - Corridor: 5-minute auto-off timer (configurable)
  - Bathroom: 15-minute timer + light controls heating (ON=comfort, OFF=eco)
- **Generic bypass switch** : Single switch to disable climate control (Solar Optimizer, manual, etc.)
- **Summer/winter mode** : Separate cool/heat temperatures with calendar-based season detection
- **X4FP auto-detection** : Automatic detection of X4FP vs thermostat control
- **Multiple comfort time ranges** : Configure multiple daily time ranges (format: HH:MM-HH:MM,HH:MM-HH:MM)
- **Room icon customization** : Choose custom icon for each room
- **SmartRoomEntity base class** : Factored device_info to eliminate code duplication

#### Changed
- **Default mode** : Changed from comfort to eco
- **Modes** : 6 modes → 4 modes (comfort, eco, night, frost_protection)
- **Light control** : Manual control with optional timer (corridor/bathroom types only)
- **Presence detection** : Alarm armed_away determines absence instead of sensors
- **Config flow** : Complete rewrite matching v0.2.0 architecture
- **X4FP control** : Uses correct preset names from IPX800 (away instead of frost_protection)

#### Fixed
- **Missing constants** : Added ATTR_LUMINOSITY, ATTR_OCCUPIED, and other missing constants
- **Season calendar access** : Fixed incorrect data structure access
- **Version consistency** : All files now use VERSION constant instead of hard-coded "0.1.0"
- **Error handling** : Added try/except to _set_frost_protection and other service calls
- **Entity ID parsing** : Using split_entity_id() instead of unsafe string checking
- **Data validation** : Added validation for required room_config fields (room_id, room_name)
- **Code duplication** : Created SmartRoomEntity base class (eliminated ~60 lines of duplicated code)

#### Technical Improvements
- Comprehensive code review improvements (security, robustness, validation)
- Better error handling throughout
- Proper data structure access patterns
- Factored common code into base classes
- Added comments and documentation where needed

### Migration from v0.1.0
**Action Required**: Rooms must be reconfigured via UI. Old v0.1.0 configurations are incompatible with v0.2.0 architecture.

See [Migration Guide](MIGRATION_GUIDE.md) for detailed instructions.

## [0.1.0] - 2025-01-13

### Added
- Initial release of Smart Room Manager
- Complete UI-based configuration (config_flow + options_flow)
- Smart light management:
  - Automatic control based on presence, luminosity, and time
  - Night mode with reduced brightness
  - Configurable timeout per room
  - Manual control override support
- Smart climate/heating management:
  - Variable temperature setpoints (comfort, eco, night, away, frost protection)
  - Window detection (heating pause)
  - Alarm integration (away mode)
  - Season detection (summer/winter)
  - Unoccupied delay configuration
- **Solar Optimizer support** (PRIORITY MODE):
  - When SO switch is ON → Smart Room Manager stands by
  - When SO switch is OFF → Smart Room Manager takes control
  - Per-room SO switch configuration
  - Compatible with existing Solar Optimizer setups
- Global modes:
  - Guest mode
  - Vacation mode (frost protection)
  - Alarm modes (away/home)
  - Season-based behavior
- Entity exposure per room:
  - `sensor.smart_room_*_state`: Overall room state and mode
  - `binary_sensor.smart_room_*_occupied`: Room occupation status
  - `binary_sensor.smart_room_*_light_needed`: Light requirement indicator
  - `switch.smart_room_*_automation`: Enable/disable room automation
- Multi-language support (EN/FR)
- IPX800 V5 compatibility (X4FP, X8R, XDimmer, etc.)
- Complete documentation:
  - Installation and configuration guide
  - Migration guide from YAML automations
  - Solar Optimizer integration guide
  - Room-specific configuration examples

### Technical Details
- DataUpdateCoordinator for centralized state management
- Modular architecture with separate controllers (light, climate)
- Async/await best practices
- Proper error handling and logging
- Home Assistant 2023.1+ compatibility

[Unreleased]: https://github.com/GevaudanBeast/HA-SMART/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/GevaudanBeast/HA-SMART/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/GevaudanBeast/HA-SMART/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/GevaudanBeast/HA-SMART/releases/tag/v0.1.0
