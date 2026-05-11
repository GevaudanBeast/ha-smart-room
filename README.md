# Smart Room Manager - Home Assistant Integration

[![Version](https://img.shields.io/badge/version-0.3.7-blue.svg)](https://github.com/GevaudanBeast/ha-smart-room/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.1+-blue.svg)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

**Version 0.3.7** - Summer mode now honored by Solar Optimizer / external control!

[English](#english) | [Français](#français)

---

## English

A comprehensive Home Assistant integration to intelligently manage each room in your home by automating lights and heating in a simple and effective way.

### 🆕 What's New

**v0.3.7** (Latest) - Critical Bug Fix:
- ☀️ **Summer mode + external control**: Solar Optimizer no longer forces `HEAT` in summer. Reversible AC units now switch to `COOL` with the cool comfort temperature; heater-only thermostats and Wire Pilot heaters are skipped during summer. Previously bedroom AC units kept reverting to heating each control cycle.

**v0.3.6** - Critical Bug Fixes:
- 🔥 **X4FP hysteresis fix**: Frost protection mode now bypasses hysteresis and correctly applies the away preset
- 🏠 **External control fix**: Solar Optimizer now only activates when you're away (inverted logic)
- ✏️ **Entity selector fix**: Clearing sensors/switches in config now works correctly
- 🗑️ **Room deletion fix**: Deleted rooms now properly removed from device registry
- 🧹 **Cleanup service**: Now also removes orphaned devices

**v0.3.5** - Wire Pilot/Thermostat Routing:
- 🔧 **Climate type detection fix**: Wire Pilot entities were incorrectly routed to the thermostat controller
- 🌍 **English translation**: "Fil Pilote" → "Wire Pilot"

**v0.3.4** - New Features & Bug Fixes:
- 🔥 **Wire Pilot**: X4FP renamed to "Wire Pilot" / "Fil Pilote" (clearer, more generic)
- 🎛️ **Thermostat control modes**:
  - `preset_only` (default, recommended): Uses thermostat presets only - you control temperatures in your thermostat app (Netatmo, Tado, etc.)
  - `temperature`: SRM controls temperatures directly (legacy behavior)
  - `preset_and_temp`: Uses both presets and temperatures
  - **Smart config flow**: Temperature settings only shown when needed (not in preset_only mode)
- 🌡️ **Wire Pilot hysteresis simplified**: Temperature sensor acts as a safeguard, setpoint_input optional
- 🪟 **Separate frost presets**: Different presets for away mode vs windows open
- 🌙 **Night period fix**: Now works correctly after midnight (22:00-06:00)
- 💨 **VMC multi-bathroom**: Fixed conflict when multiple bathrooms share one VMC
- 📊 **Priority alignment**: Display mode now matches actual heating action
- 🏠 **Ignore in away**: Schedule now respected when "ignore_in_away" option is checked
- 🔄 **Away→Disarmed transition**: Wire Pilot and thermostat presets now update correctly
- ⏸️ **Pause for lights**: Manual pause now also stops light automation

**v0.3.3** - VMC & Debug Sensors:
- 💨 **VMC Support**: Global VMC entity with configurable timer
- 🔍 **Activity Sensor**: Human-readable room status with emojis
- ⏱️ **Light Timer**: Countdown before auto-off
- 🧹 **Cleanup Service**: Remove orphaned entities

**v0.3.0** - Advanced Climate Control:
- 🌞 **External Control** : Solar Optimizer and other external control systems support
- 🌡️ **Hysteresis Fil Pilote** : Temperature-based control with hysteresis for Fil Pilote radiators
- 📅 **Room Calendars** : Per-room schedule/calendar support (Google Calendar, etc.)
- ⏸️ **Manual Pause** : Pause automation temporarily per room (15min to 8h)
- 🪟 **Window Delays** : Configurable delays before reacting to windows open/close
- 🎯 **Configurable Presets** : Customize Fil Pilote presets per room
- ☀️ **Summer Policy** : Choose "off" or "eco" for Fil Pilote in summer
- 🔍 **Debug Sensors** : Priority, external control, hysteresis state, schedule active
- 🎛️ **7-Level Priority System** : Paused, Bypass, Windows, External, Away, Schedule, Normal
- ✅ **Fully Configurable** : All features available in UI wizard (8 steps)

See [CHANGELOG.md](CHANGELOG.md) for complete details.

**Previous versions:**
- **v0.2.4**: Documentation improvements and MIT license
- **v0.2.3**: Critical fixes for None values and deprecated warnings
- **v0.2.2**: Cleaner configuration with optional fields
- **v0.2.1**: Fixed ALARM_STATE_ARMED_AWAY import
- **v0.2.0**: Simplified architecture (4 modes, alarm-based presence, manual lights)

### 📋 Features

#### Smart Light Management (v0.2.0 simplified)
- ✅ **Manual control** : You control your lights manually or via automations
- ✅ **Auto-off timer** : Only for corridors and bathrooms (configurable 60-1800s)
- ✅ **Bathroom special** : Light ON = comfort heating, OFF = eco heating

#### Smart Climate/Heating Management
- ✅ **4 adapted modes** :
  - **Comfort** : Present + configurable time ranges
  - **Eco** : Default mode outside comfort ranges
  - **Night** : Night period (configurable)
  - **Frost Protection** : Alarm armed_away or window open
- ✅ **Fil Pilote/Thermostat auto-detection** : Automatic control based on type
- ✅ **Summer/winter support** : Heat/cool temperatures via calendar
- ✅ **Generic bypass** : Switch to disable control (Solar Optimizer, etc.)
- ✅ **Open windows** : Automatic frost protection mode

#### Room Types
- 🏠 **Normal** (bedrooms) : No light timer
- 🚶 **Corridor** : Auto-off lights after 5 min (configurable)
- 🛁 **Bathroom** : 15 min timer + light controls heating (ON=comfort, OFF=eco)

#### Simplified Presence Detection
- 🚨 **Via alarm** : armed_away = absent, otherwise present
- ⏰ **Time ranges** : Comfort mode on configurable ranges if present
- 🌙 **Night mode** : Based on night start time

#### Complete UI Configuration
- ⚙️ Add/edit/delete rooms via interface
- 📊 Configure room types and behaviors
- 🕐 Multiple comfort time ranges (format: HH:MM-HH:MM,HH:MM-HH:MM)
- 🔄 Automatic reload on every change

### 🚀 Installation

#### Method 1: HACS (Recommended)
1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the 3-dot menu → "Custom repositories"
4. Add URL: `https://github.com/GevaudanBeast/HA-SMART`
5. Search for "Smart Room Manager" and install
6. Restart Home Assistant

#### Method 2: Manual
1. Download the latest release from [GitHub Releases](https://github.com/GevaudanBeast/HA-SMART/releases)
2. Extract `smart_room_manager.zip` to your `config/custom_components/` folder
3. Restart Home Assistant

### ⚙️ Configuration

#### Initial Setup

1. Go to **Settings** > **Devices & Services**
2. Click **+ Add Integration**
3. Search for **Smart Room Manager**
4. Configure global settings (optional):
   - **Alarm** : Detects presence (armed_away = absent)
   - **Summer calendar** : Switches heat/cool for A/C

#### Adding a Room

1. Open **Smart Room Manager** integration
2. Click **Configure** > **Add Room**
3. Follow the configuration wizard:

**Step 1: Basic Information**
- **Name** : Room name (required)
- **Type** : Normal / Corridor / Bathroom
- **Icon** : Custom icon (e.g., mdi:bed, mdi:desk)

**Step 2: Sensors (all optional)**
- **Window/door sensors** : Detect opening → frost protection
- **Temperature sensor** : Info only (displayed in attributes)
- **Humidity sensor** : Info only

**Step 3: Actuators (all optional)**
- **Lights** : light.* or switch.* entities
- **Climate entity** : Thermostat or Fil Pilote (auto-detection)
- **Bypass switch** : Disables climate control

**Step 4: Light Configuration** (if type = Corridor or Bathroom)
- **Timeout** : Delay before automatic turn-off (60-1800s)

**Step 5: Climate Configuration**

*Winter temperatures (heat)* :
- **Comfort** : Temperature when present + comfort time range (default: 20°C)
- **Eco** : Default temperature outside comfort ranges (default: 18°C)
- **Night** : Night period temperature (default: 17°C)
- **Frost Protection** : Temperature if alarm armed_away or window open (default: 12°C)

*Summer temperatures (cool)* :
- **Comfort** : A/C temperature if summer active (default: 24°C)
- **Eco** : A/C eco temperature summer (default: 26°C)

**Step 6: Schedule**
- **Night start** : Night period start time (e.g., 22:00)
- **Comfort ranges** : Format `HH:MM-HH:MM,HH:MM-HH:MM`
  - Example: `07:00-09:00,18:00-22:00` (morning + evening)

### 📊 Created Entities

For each configured room:

**Sensors**
- **sensor.smart_room_[name]_state** : Current mode (comfort / eco / night / frost_protection)

**Binary Sensors**
- **binary_sensor.smart_room_[name]_occupied** : Occupation (alarm-based)
- **binary_sensor.smart_room_[name]_light_needed** : Always False (manual control)

**Switches**
- **switch.smart_room_[name]_automation** : Enable/disable automation

### 🎯 Usage Examples

#### Scenario 1: Simple Bedroom
**Configuration** :
- Type: Normal (no timer)
- Climate: climate.bedroom
- Temperatures: Comfort 20°C, Eco 18°C, Night 17°C
- Night: 22:00
- Comfort ranges: `07:00-09:00`

**Behavior** :
- 7am-9am + present → Heating 20°C (comfort)
- 9am-10pm + present → Heating 18°C (eco)
- 10pm-7am → Heating 17°C (night)
- Alarm armed_away → Heating 12°C (frost protection)

#### Scenario 2: Bathroom
**Configuration** :
- Type: Bathroom
- Lights: light.bathroom
- Timer: 900s (15 min)
- Climate: climate.bathroom_radiator
- Temperatures: Comfort 22°C, Eco 17°C

**Behavior** :
- Light ON manually → Heating 22°C (comfort)
- Light OFF → Heating 17°C (eco)
- Light ON > 15 min → Automatic turn-off
- Turn-off → Heating back to 17°C

#### Scenario 3: Living Room with Bypass
**Configuration** :
- Type: Normal
- Climate: climate.living_room
- Bypass: switch.solar_optimizer_living
- Comfort ranges: `18:00-23:00`

**Behavior** :
- Bypass ON (Solar Optimizer active) → Smart Room Manager stands by
- Bypass OFF + 6pm-11pm + present → Comfort heating
- Bypass OFF + outside range → Eco heating

### 🔧 Solar Optimizer Integration

✅ **Compatible via generic bypass!**

**Configuration** :
1. Add Solar Optimizer switch in "Bypass switch"
2. When SO heats (ON) → Smart Room Manager stands by
3. When SO stops (OFF) → Smart Room Manager takes control

### 🐛 Troubleshooting

**Heating doesn't change**
- Check that automation switch is enabled
- Check that bypass isn't active
- Check `sensor.smart_room_*_state` to see current mode

**Lights don't turn off (corridor/bathroom)**
- Check room type (Normal has no timer)
- Check configured timeout

**"Entity None" error (v0.2.1/v0.2.2)**
- Update to v0.2.3 and restart Home Assistant
- Migration runs automatically

### 📝 Logs and Debugging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.smart_room_manager: debug
```

### 🔄 Migration from v0.1.0

**Major changes** :
- ❌ Presence sensors removed (use alarm)
- ❌ Interior luminosity sensors removed
- ❌ Guest/vacation modes removed
- ✅ Room types added
- ✅ Multiple comfort ranges instead of 4 periods

**Action required** : Reconfigure rooms via UI (old configs incompatible)

### 📞 Support

- 📖 [Complete documentation](https://github.com/GevaudanBeast/HA-SMART)
- 🐛 [GitHub Issues](https://github.com/GevaudanBeast/HA-SMART/issues)
- 💬 [Discussions](https://github.com/GevaudanBeast/HA-SMART/discussions)

---

## Français

Une intégration Home Assistant complète pour gérer intelligemment chaque pièce de votre maison en automatisant les lumières et le chauffage de manière simple et efficace.

### 🆕 Nouveautés

**v0.3.7** (Dernière) - Correction Critique :
- ☀️ **Mode été + contrôle externe** : Le contrôle externe (Solar Optimizer) ne force plus `HEAT` en été. Les thermostats réversibles passent en `COOL` avec `temp_cool_comfort` ; les thermostats chauffage seul et les Fil Pilote sont ignorés en été. Auparavant, les climatisations des chambres repassaient sans cesse en chauffage à chaque cycle.

**v0.3.6** - Corrections Critiques :
- 🔥 **Fix hystérésis X4FP** : Le mode hors-gel court-circuite maintenant l'hystérésis et applique le preset absence
- 🏠 **Fix contrôle externe** : Solar Optimizer ne s'active que quand vous êtes absent (logique inversée)
- ✏️ **Fix sélecteurs d'entités** : La suppression des capteurs/switches sauvegarde correctement
- 🗑️ **Fix suppression de pièce** : Les pièces supprimées disparaissent du device registry
- 🧹 **Service cleanup** : Supprime aussi les devices orphelins

**v0.3.5** - Routage Fil Pilote/Thermostat :
- 🔧 **Fix détection type climat** : Les entités Fil Pilote étaient envoyées au contrôleur thermostat, causant des erreurs `set_temperature`. Utilise désormais `climate_mode` configuré au lieu de l'auto-détection.

**v0.3.4** - Nouveautés & Corrections :
- 🔥 **Fil Pilote** : X4FP renommé en "Fil Pilote" (plus clair, plus générique)
- 🎛️ **Modes contrôle thermostat** :
  - `preset_only` (défaut, recommandé) : Utilise uniquement les presets - vous contrôlez les températures dans l'app du thermostat (Netatmo, Tado, etc.)
  - `temperature` : SRM contrôle les températures directement (ancien comportement)
  - `preset_and_temp` : Utilise presets et températures
  - **Config flow intelligent** : Les températures n'apparaissent que si nécessaire (pas en mode preset_only)
- 🌡️ **Hystérésis Fil Pilote simplifiée** : Le capteur de température sert de garde-fou, setpoint_input optionnel
- 🪟 **Presets hors-gel séparés** : Presets différents pour absence vs fenêtres ouvertes
- 🌙 **Période nuit** : Fonctionne maintenant après minuit (22:00-06:00)
- 💨 **VMC multi-SDB** : Corrige conflit quand plusieurs SDB partagent une VMC
- 📊 **Priorités alignées** : Le mode affiché correspond à l'action réelle
- 🏠 **Ignore in away** : Le schedule est respecté quand l'option est cochée
- 🔄 **Transition away→disarmed** : Les presets Fil Pilote et thermostat se mettent à jour
- ⏸️ **Pause lumières** : La pause manuelle arrête aussi l'automation des lumières

**v0.3.3** - VMC & Capteurs Debug :
- 💨 **Support VMC** : Entité VMC globale avec timer configurable
- 🔍 **Capteur Activité** : État pièce lisible avec emojis
- ⏱️ **Timer Lumière** : Countdown avant extinction auto
- 🧹 **Service Nettoyage** : Supprime entités orphelines

**v0.3.0** - Contrôle Climat Avancé :
- 🌞 **Contrôle externe** : Support Solar Optimizer
- 📅 **Calendriers** : Planning par pièce
- ⏸️ **Pause manuelle** : Pause temporaire par pièce
- 🔍 **Capteurs debug** : Priorité, hystérésis, etc.

**v0.2.0** - Architecture Simplifiée :
- 🔄 **Plus de capteurs de présence** : L'alarme détermine la présence (armed_away = absent)
- 💡 **Contrôle manuel des lumières** : Timer auto-off uniquement pour couloirs/salles de bain
- 🎛️ **Bypass générique** : Un seul switch pour désactiver le chauffage
- 📊 **4 modes au lieu de 6** : Confort, Eco, Nuit, Hors-gel
- ⏰ **Horaires simplifiés** : Période nuit + plages horaires confort configurables

### 📋 Fonctionnalités

#### Gestion intelligente des lumières (v0.2.0 simplifié)
- ✅ **Contrôle manuel** : Vous contrôlez vos lumières manuellement ou via automatisations
- ✅ **Timer auto-off** : Uniquement pour couloirs et salles de bain (60-1800s configurable)
- ✅ **Salle de bain spécial** : Lumière ON = chauffage confort, OFF = chauffage eco

#### Gestion intelligente du chauffage
- ✅ **4 modes adaptés** :
  - **Confort** : Présence + plages horaires configurables
  - **Eco** : Mode par défaut hors plages confort
  - **Nuit** : Période nocturne (configurable)
  - **Hors-gel** : Alarme armed_away ou fenêtre ouverte
- ✅ **Auto-détection Fil Pilote/Thermostat** : Contrôle automatique selon type
- ✅ **Support été/hiver** : Températures heat/cool via calendrier
- ✅ **Bypass générique** : Switch pour désactiver contrôle
- ✅ **Fenêtres ouvertes** : Passage automatique en hors-gel

#### Types de pièces
- 🏠 **Normal** (chambres) : Pas de timer lumière
- 🚶 **Couloir** : Auto-off lumières après 5 min (configurable)
- 🛁 **Salle de bain** : Timer 15 min + lumière contrôle chauffage (ON=confort, OFF=eco)

#### Détection de présence simplifiée
- 🚨 **Via alarme** : armed_away = absent, sinon présent
- ⏰ **Plages horaires** : Mode confort sur plages configurables si présent
- 🌙 **Mode nuit** : Basé sur heure de début nuit

#### Configuration UI complète
- ⚙️ Ajout/modification/suppression de pièces via l'interface
- 📊 Configuration des types de pièce et comportements
- 🕐 Plages horaires confort multiples (format HH:MM-HH:MM,HH:MM-HH:MM)
- 🔄 Recharge automatique à chaque modification

### 🚀 Installation

#### Méthode 1 : HACS (recommandé)
1. Ouvrez HACS dans Home Assistant
2. Allez dans "Intégrations"
3. Cliquez sur les 3 points > "Dépôts personnalisés"
4. Ajoutez l'URL : `https://github.com/GevaudanBeast/HA-SMART`
5. Recherchez "Smart Room Manager" et installez
6. Redémarrez Home Assistant

#### Méthode 2 : Manuelle
1. Téléchargez la dernière release depuis [GitHub Releases](https://github.com/GevaudanBeast/HA-SMART/releases)
2. Extrayez `smart_room_manager.zip` dans `config/custom_components/`
3. Redémarrez Home Assistant

### ⚙️ Configuration

#### Configuration initiale

1. Allez dans **Paramètres** > **Appareils et services**
2. Cliquez sur **+ Ajouter une intégration**
3. Recherchez **Smart Room Manager**
4. Configurez les paramètres globaux (optionnels) :
   - **Alarme** : Détecte présence (armed_away = absent)
   - **Calendrier été** : Bascule heat/cool pour climatisation

#### Ajout d'une pièce

1. Ouvrez l'intégration **Smart Room Manager**
2. Cliquez sur **Configurer** > **Ajouter une pièce**
3. Suivez l'assistant de configuration :

**Étape 1 : Informations de base**
- **Nom** : Nom de la pièce (requis)
- **Type** : Normal / Couloir / Salle de bain
- **Icône** : Icône personnalisée (ex: mdi:bed, mdi:desk)

**Étape 2 : Capteurs (tous optionnels)**
- **Capteurs fenêtre/porte** : Détecte ouverture → hors-gel
- **Capteur température** : Pour info seulement
- **Capteur humidité** : Pour info seulement

**Étape 3 : Actionneurs (tous optionnels)**
- **Lumières** : Entités light.* ou switch.*
- **Entité climat** : Thermostat ou Fil Pilote (auto-détection)
- **Switch bypass** : Désactive contrôle chauffage

**Étape 4 : Configuration lumières** (si type = Couloir ou Salle de bain)
- **Timeout** : Délai avant extinction automatique (60-1800s)

**Étape 5 : Configuration chauffage**

*Températures hiver (heat)* :
- **Confort** : Température quand présent + plage confort (défaut: 20°C)
- **Eco** : Température par défaut hors plages confort (défaut: 18°C)
- **Nuit** : Température période nocturne (défaut: 17°C)
- **Hors-gel** : Température si alarme armed_away ou fenêtre ouverte (défaut: 12°C)

*Températures été (cool)* :
- **Confort** : Température clim si été actif (défaut: 24°C)
- **Eco** : Température clim eco été (défaut: 26°C)

**Étape 6 : Horaires**
- **Début nuit** : Heure de début période nuit (ex: 22:00)
- **Plages confort** : Format `HH:MM-HH:MM,HH:MM-HH:MM`
  - Exemple : `07:00-09:00,18:00-22:00`

### 📊 Entités créées

Pour chaque pièce configurée :

**Sensors**
- **sensor.smart_room_[nom]_state** : Mode actuel (comfort / eco / night / frost_protection)

**Binary Sensors**
- **binary_sensor.smart_room_[nom]_occupied** : Occupation (basée sur alarme)
- **binary_sensor.smart_room_[nom]_light_needed** : Toujours False (contrôle manuel)

**Switches**
- **switch.smart_room_[nom]_automation** : Active/désactive l'automatisation

### 🎯 Exemples d'utilisation

#### Scénario 1 : Chambre simple
**Configuration** :
- Type : Normal (pas de timer)
- Climat : climate.chambre
- Températures : Confort 20°C, Eco 18°C, Nuit 17°C
- Nuit : 22:00
- Plages confort : `07:00-09:00`

**Comportement** :
- 7h-9h + présent → Chauffage 20°C (confort)
- 9h-22h + présent → Chauffage 18°C (eco)
- 22h-7h → Chauffage 17°C (nuit)
- Alarme armed_away → Chauffage 12°C (hors-gel)

#### Scénario 2 : Salle de bain
**Configuration** :
- Type : Salle de bain
- Lumières : light.salle_bain
- Timer : 900s (15 min)
- Climat : climate.radiateur_sdb
- Températures : Confort 22°C, Eco 17°C

**Comportement** :
- Lumière ON manuellement → Chauffage 22°C (confort)
- Lumière OFF → Chauffage 17°C (eco)
- Lumière ON > 15 min → Extinction automatique
- Extinction → Retour chauffage 17°C

#### Scénario 3 : Salon avec bypass
**Configuration** :
- Type : Normal
- Climat : climate.salon
- Bypass : switch.solar_optimizer_salon
- Plages confort : `18:00-23:00`

**Comportement** :
- Bypass ON (Solar Optimizer actif) → Smart Room Manager ne contrôle pas
- Bypass OFF + 18h-23h + présent → Chauffage confort
- Bypass OFF + hors plage → Chauffage eco

### 🔧 Intégration avec Solar Optimizer

✅ **Compatible via bypass générique !**

**Configuration** :
1. Ajoutez le switch Solar Optimizer dans "Switch bypass"
2. Quand SO chauffe (ON) → Smart Room Manager se met en retrait
3. Quand SO s'arrête (OFF) → Smart Room Manager reprend le contrôle

### 🐛 Dépannage

**Le chauffage ne change pas**
- Vérifiez que le switch d'automatisation est activé
- Vérifiez que le bypass n'est pas actif
- Consultez `sensor.smart_room_*_state` pour voir le mode actuel

**Les lumières ne s'éteignent pas (couloir/SdB)**
- Vérifiez le type de pièce (Normal n'a pas de timer)
- Vérifiez le timeout configuré

**Erreur "Entity None" (v0.2.1/v0.2.2)**
- Mettez à jour vers v0.2.3 et redémarrez Home Assistant
- La migration s'exécute automatiquement

### 📝 Logs et débogage

Ajoutez dans `configuration.yaml` :

```yaml
logger:
  default: info
  logs:
    custom_components.smart_room_manager: debug
```

### 🔄 Migration depuis v0.1.0

**Changements majeurs** :
- ❌ Capteurs de présence supprimés (utiliser alarme)
- ❌ Capteurs luminosité intérieurs supprimés
- ❌ Modes guest/vacation supprimés
- ✅ Types de pièces ajoutés
- ✅ Plages confort multiples au lieu de 4 périodes

**Action requise** : Reconfigurer les pièces via UI (anciennes configs incompatibles)

### 📞 Support

- 📖 [Documentation complète](https://github.com/GevaudanBeast/HA-SMART)
- 🐛 [Issues GitHub](https://github.com/GevaudanBeast/HA-SMART/issues)
- 💬 [Discussions](https://github.com/GevaudanBeast/HA-SMART/discussions)

---

**Version** : 0.3.4
**Author / Auteur** : GevaudanBeast
**Compatibility / Compatibilité** : Home Assistant 2023.1+

## 📄 License / Licence

This project is licensed under MIT License. / Ce projet est sous licence MIT.

## 🙏 Acknowledgments / Remerciements

Developed with ❤️ for the Home Assistant community. / Développé avec ❤️ pour la communauté Home Assistant.
