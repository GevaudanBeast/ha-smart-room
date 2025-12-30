# Plan d'Évolution Smart Room Manager v0.3.0

## 🎯 Objectif

Remplacer complètement les blueprints chauffage par l'intégration Smart Room Manager en comblant tous les gaps fonctionnels.

---

## 📊 Architecture : 3 Types de Chauffage

### Type 1 : Thermostat Chauffage Seul (heat only)
**Caractéristiques** :
- HVAC mode : `heat` uniquement
- Température configurable par mode
- Été : `OFF`
- Exemple : Poêle du salon

**Blueprint actuel** : `blueprint_hvac_thermostat_heat.yaml`

**Status intégration** : ✅ Déjà supporté correctement

---

### Type 2 : Thermostat Réversible (heat/cool)
**Caractéristiques** :
- HVAC mode : `heat` (hiver) / `cool` (été)
- Températures différentes hiver/été
- Été comfort : COOL 24°C
- Été eco/night : COOL 26°C (ou OFF configurable)
- Exemple : Climatisations chambres enfants

**Blueprint actuel** : `blueprint_hvac_room_thermostat.yaml`

**Status intégration** : ⚠️ **Partiellement supporté**
- ✅ Hiver HEAT OK
- ✅ Été comfort COOL OK
- ❌ **Été eco/night → devrait être COOL 26°C, pas OFF**

---

### Type 3a : X4FP Sans Capteur Température
**Caractéristiques** :
- Contrôle par presets uniquement (comfort/eco/away/none)
- Pas de retour température
- Été : OFF ou eco configurable
- Exemple : Sèche-serviettes basiques

**Blueprint actuel** : `blueprint_hvac_X4FP_bathroom.yaml`

**Status intégration** : ✅ Déjà supporté (presets)
- ⚠️ Été : seulement OFF (pas configurable eco)

---

### Type 3b : X4FP Avec Capteur Température + Hystérésis
**Caractéristiques** :
- Contrôle par presets + régulation température
- Capteur température externe
- Consigne température configurable (input_number)
- Hystérésis : temp < setpoint - hyst → preset_heat
- Hystérésis : temp > setpoint + hyst → preset_idle
- Garde-fous min/max température
- Été : OFF
- Exemple : Chambres avec radiateurs pilote

**Blueprint actuel** : `blueprint_hvac_X4FP_room.yaml`

**Status intégration** : ❌ **PAS SUPPORTÉ**
- ❌ Pas de capteur température
- ❌ Pas de consigne configurable
- ❌ Pas d'hystérésis
- ❌ Pas de preset_heat vs preset_idle

---

## 🔧 Concepts Clés : Bypass vs External Control

L'intégration supporte **deux modes de contrôle externe** :

### 1. Bypass (déjà implémenté ✅)
**CONF_CLIMATE_BYPASS_SWITCH** = "climate_bypass_switch"

- **Comportement** : Quand ON → l'intégration **ne fait absolument rien**
- **Usage** : Désactivation complète du contrôle automatique
- **Exemple** : Switch manuel "Mode Manuel" pour reprendre le contrôle total
- **Priorité** : Absolue (PRIORITY 1)

```python
if bypass_switch == ON:
    return  # Arrêt complet, intégration désactivée
```

### 2. External Control (à implémenter ⭐⭐⭐)
**CONF_EXTERNAL_CONTROL_SWITCH** = "external_control_switch"

- **Comportement** : Quand actif → l'intégration **applique un mode spécifique**
- **Usage** : Contrôle externe avec priorité (Solar Optimizer, tarif EDF, etc.)
- **Exemple** : Solar Optimizer chauffe → force preset comfort
- **Priorité** : Haute (PRIORITY 3, après fenêtres)
- **Override Away** : Configurable via case à cocher

```python
if external_control_switch.is_active == True:
    if is_away and not allow_external_in_away:
        pass  # Continue vers away
    else:
        set_preset(external_control_preset)  # Applique mode externe
        return
```

### Tableau Comparatif

| Aspect | Bypass | External Control |
|--------|--------|------------------|
| **État** | ✅ Implémenté | ❌ À implémenter |
| **Intégration fait** | RIEN | Applique mode externe |
| **Utilisateur voit** | Aucun changement auto | Changements auto selon externe |
| **Override Away** | N/A | ☑️ Configurable |
| **Cas d'usage** | Mode manuel total | Solar Optimizer, tarif dynamique |
| **Générique** | Oui | Oui (tout switch avec is_active) |

---

## 🔥 Gaps Critiques par Priority

### Priority 1 : BLOQUANT (remplacer blueprints impossible sans ça)

#### 1.1 - X4FP avec Hystérésis Température ⭐⭐⭐
**Impact** : Chambres (X4FP) ne peuvent pas migrer
**Fichiers** : `climate_control.py`, `config_flow.py`, `const.py`

**Ajouts nécessaires** :
```python
# Config
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_SETPOINT_INPUT = "setpoint_input"  # input_number.xxx
CONF_HYSTERESIS = "hysteresis"  # 0.2-2.0°C, default 0.5
CONF_MIN_SETPOINT = "min_setpoint"  # default 17
CONF_MAX_SETPOINT = "max_setpoint"  # default 23

# Presets pour X4FP avec température
CONF_PRESET_HEAT = "preset_heat"  # default: comfort
CONF_PRESET_IDLE = "preset_idle"  # default: eco
```

**Logique** :
```python
def _control_x4fp_with_temp():
    # 1. Lire capteur température
    current_temp = get_sensor_temp(temperature_sensor)

    # 2. Lire consigne (depuis input_number)
    setpoint = get_setpoint(setpoint_input)
    setpoint = clamp(setpoint, min_setpoint, max_setpoint)

    # 3. Calculer avec hystérésis
    if current_temp <= setpoint - hysteresis:
        target_preset = preset_heat  # comfort
    elif current_temp >= setpoint + hysteresis:
        target_preset = preset_idle  # eco
    else:
        # Zone morte : garder preset actuel
        return

    # 4. Appliquer
    set_preset(target_preset)
```

---

#### 1.2 - Contrôle Externe Avancé (External Control) ⭐⭐⭐
**Impact** : Toutes les pièces avec contrôle externe (Solar Optimizer, etc.)
**Fichiers** : `climate_control.py`, `config_flow.py`

**Concept** : Système **générique** pour tout contrôle externe (Solar Optimizer aujourd'hui, autre intégration demain)

**Différence avec Bypass** :
- **Bypass** (déjà présent) = Désactivation complète → intégration ne fait RIEN
- **External Control** (nouveau) = Contrôle externe prioritaire → intégration applique un mode spécifique

**Ajouts nécessaires** :
```python
# Config
CONF_EXTERNAL_CONTROL_SWITCH = "external_control_switch"  # Switch générique (Solar Optimizer, etc.)
CONF_EXTERNAL_CONTROL_PRESET = "external_control_preset"  # comfort/eco/etc. (X4FP)
CONF_EXTERNAL_CONTROL_TEMP = "external_control_temp"  # Température (thermostat)
CONF_ALLOW_EXTERNAL_IN_AWAY = "allow_external_in_away"  # Boolean (case à cocher)
```

**Interface utilisateur** :
```yaml
External Control Switch:
  - Label: "External Control Switch (Solar Optimizer, etc.)"
  - Description: "Switch indicating an external system is actively controlling heating"
  - Optional: true
  - Selector: entity (switch/binary_sensor domain)

External Control Preset (X4FP):
  - Label: "Preset when external control active"
  - Options: comfort, eco, comfort-1, comfort-2, boost, none
  - Default: comfort

External Control Temperature (Thermostat):
  - Label: "Temperature when external control active"
  - Default: 20°C

☑️ Allow external control to override Away mode:
  - Description: "When checked, external control can heat even when alarm is armed (away)"
  - Default: false
```

**Logique priorité** :
```python
# PRIORITY 1: Bypass (déjà existant) → si ON, arrêter tout
if bypass_switch == ON:
    return

# PRIORITY 2: Fenêtres (déjà existant)
if windows_open:
    frost_protection()
    return

# PRIORITY 3: External Control actif → NOUVEAU
if external_control_switch:
    # Vérifier is_active attribute OU state
    is_active = (
        state_attr(external_control_switch, 'is_active') or
        state(external_control_switch).lower() == 'on'
    )

    if is_active:
        # Override away si autorisé (case cochée)
        if is_away and not allow_external_in_away:
            pass  # Continue vers away mode
        else:
            # Appliquer preset/temp configuré
            if X4FP:
                set_preset(external_control_preset)
            else:
                set_temperature(external_control_temp)
            return

# PRIORITY 4: Away mode
if is_away:
    frost_protection()
    return

# PRIORITY 5: Reste de la logique normale...
```

**Cas d'usage** :
- Solar Optimizer : chauffe avec surplus solaire
- Future intégration : chauffage base tarif EDF
- Future intégration : gestionnaire d'énergie tiers
- Tout switch/binary_sensor avec attribut `is_active`

---

#### 1.3 - Calendrier par Pièce (schedule_entity) ⭐⭐
**Impact** : Salles de bain, chambres avec planning spécifique
**Fichiers** : `room_manager.py`, `climate_control.py`, `config_flow.py`

**Ajouts nécessaires** :
```python
# Config
CONF_SCHEDULE_ENTITY = "schedule_entity"  # calendar.xxx
CONF_PRESET_SCHEDULE_ON = "preset_schedule_on"  # comfort
CONF_PRESET_SCHEDULE_OFF = "preset_schedule_off"  # eco
CONF_SCHEDULE_BLOCKS_LIGHT = "schedule_blocks_light"  # Boolean
```

**Logique** :
```python
# Dans room_manager._update_current_mode()
# PRIORITY après Away, avant time ranges

if schedule_entity:
    event_active = is_state(schedule_entity, 'on')

    if event_active:
        # Calendrier actif → force mode
        self._current_mode = MODE_COMFORT  # ou preset_schedule_on
        return
    else:
        # Pas d'event → force eco
        self._current_mode = MODE_ECO  # ou preset_schedule_off

        # Bloquer lumières si configuré (salles de bain)
        if schedule_blocks_light:
            self.light_controller.block_automation = True

        return
```

---

#### 1.4 - Été pour Thermostats Réversibles ⭐⭐
**Impact** : Climatisations (Livia, Thomas)
**Fichiers** : `climate_control.py`

**Problème actuel** :
```python
# climate_control.py ligne 209-222
if is_summer:
    if mode == MODE_FROST_PROTECTION:
        target_hvac = OFF
    elif mode == MODE_COMFORT:
        target_hvac = COOL
        target_temp = temp_cool_comfort  # 24°C
    else:  # eco, night
        target_hvac = OFF  # ❌ MAUVAIS
        target_temp = None
```

**Correction nécessaire** :
```python
if is_summer:
    if mode == MODE_FROST_PROTECTION:
        target_hvac = OFF
        target_temp = None
    elif mode == MODE_COMFORT:
        target_hvac = COOL
        target_temp = temp_cool_comfort  # 24°C
    else:  # eco, night
        # ✅ COOL à température plus haute
        target_hvac = COOL
        target_temp = temp_cool_eco  # 26°C
```

---

### Priority 2 : IMPORTANT (améliore flexibilité)

#### 2.1 - Délais Fenêtres (delay_open/close) ⭐
**Impact** : Évite réactions intempestives
**Fichiers** : `room_manager.py`, `config_flow.py`

**Ajouts** :
```python
CONF_WINDOW_DELAY_OPEN = "window_delay_open"  # minutes, default 2
CONF_WINDOW_DELAY_CLOSE = "window_delay_close"  # minutes, default 2
```

**Logique** : Utiliser `trigger.for` ou tracking temporel interne

---

#### 2.2 - Presets Configurables ⭐
**Impact** : Flexibilité utilisateur
**Fichiers** : `const.py`, `config_flow.py`, `climate_control.py`

**Ajouts** :
```python
# Au lieu de hardcoder comfort/eco/away
CONF_PRESET_COMFORT = "preset_comfort"  # user peut choisir comfort, comfort-1, etc.
CONF_PRESET_ECO = "preset_eco"
CONF_PRESET_NIGHT = "preset_night"
CONF_PRESET_AWAY = "preset_away"
CONF_PRESET_WINDOW = "preset_window"
```

---

#### 2.3 - Summer Policy Configurable ⭐
**Impact** : X4FP peuvent rester en eco au lieu de OFF
**Fichiers** : `config_flow.py`, `climate_control.py`

**Ajouts** :
```python
CONF_SUMMER_POLICY = "summer_policy"  # "off" ou "eco"
```

**Logique X4FP été** :
```python
if is_summer:
    if mode == MODE_FROST_PROTECTION:
        target_preset = AWAY
    elif summer_policy == "off":
        target_preset = OFF
    else:  # "eco"
        target_preset = ECO
```

---

#### 2.4 - Tick Configurable ⭐
**Impact** : Réapplication périodique
**Fichiers** : `coordinator.py`, `config_flow.py`

**Ajouts** :
```python
CONF_TICK_MINUTES = "tick_minutes"  # 0, 5, 10, 15 (0 = disabled)
```

---

### Priority 3 : BONUS (wizard, extensions)

#### 3.1 - Wizard d'Installation Intelligent ⭐⭐⭐
**Fichiers** : `config_flow.py`, `translations/fr.json`, `translations/en.json`

**Concept** : Détecter les zones HA existantes et pré-remplir la configuration

**Fonctionnalités** :

**1. Détection Zones (Areas)**
```python
from homeassistant.helpers import area_registry as ar

async def detect_existing_areas(hass):
    """Détecte toutes les zones configurées dans HA."""
    area_registry = ar.async_get(hass)
    areas = area_registry.async_list_areas()

    return [
        {
            "area_id": area.id,
            "name": area.name,  # "Salon", "Cuisine", etc.
            "aliases": area.aliases,
        }
        for area in areas
    ]
```

**2. Scan Entités par Zone**
```python
from homeassistant.helpers import entity_registry as er, device_registry as dr

async def scan_area_entities(hass, area_id):
    """Scan entités dans une zone."""
    entity_reg = er.async_get(hass)
    device_reg = dr.async_get(hass)

    # Trouver tous les devices dans cette area
    devices = dr.async_entries_for_area(device_reg, area_id)
    device_ids = {device.id for device in devices}

    # Trouver toutes les entités de ces devices
    entities = {
        "climate": [],
        "lights": [],
        "window_sensors": [],
        "temperature_sensors": [],
        "humidity_sensors": [],
    }

    for entity in entity_reg.entities.values():
        if entity.device_id in device_ids or entity.area_id == area_id:
            # Climate entities
            if entity.domain == "climate":
                entities["climate"].append(entity.entity_id)

            # Light entities
            elif entity.domain in ["light", "switch"]:
                if "light" in entity.entity_id or "lumiere" in entity.entity_id:
                    entities["lights"].append(entity.entity_id)

            # Binary sensors (windows, doors)
            elif entity.domain == "binary_sensor":
                if any(x in entity.entity_id.lower() for x in ["fenetre", "window", "porte", "door", "baie"]):
                    entities["window_sensors"].append(entity.entity_id)

            # Temperature sensors
            elif entity.domain == "sensor":
                if entity.original_device_class == "temperature":
                    entities["temperature_sensors"].append(entity.entity_id)
                elif entity.original_device_class == "humidity":
                    entities["humidity_sensors"].append(entity.entity_id)

    return entities
```

**3. Détection Type de Pièce**
```python
def detect_room_type(area_name: str, entities: dict) -> str:
    """Devine le type de pièce selon le nom."""
    area_lower = area_name.lower()

    # Bathroom detection
    if any(x in area_lower for x in ["bain", "bath", "sdb", "douche", "shower", "wc", "toilette"]):
        return "bathroom"

    # Corridor detection
    if any(x in area_lower for x in ["couloir", "corridor", "hall", "entree", "entry", "passage"]):
        return "corridor"

    # Normal room (default)
    return "normal"
```

**4. Détection Type de Chauffage**
```python
def detect_climate_type(hass, climate_entity: str) -> dict:
    """Détecte le type et capacités du chauffage."""
    state = hass.states.get(climate_entity)
    if not state:
        return None

    preset_modes = state.attributes.get("preset_modes", [])
    hvac_modes = state.attributes.get("hvac_modes", [])

    # X4FP detection
    is_x4fp = "comfort" in preset_modes or "eco" in preset_modes

    # Reversible detection
    is_reversible = "heat" in hvac_modes and "cool" in hvac_modes

    return {
        "type": "x4fp" if is_x4fp else "thermostat",
        "reversible": is_reversible,
        "presets": preset_modes,
        "hvac_modes": hvac_modes,
    }
```

**5. Interface Wizard** (Détection SANS auto-validation)
```yaml
┌─ Smart Room Manager - Configuration Assistée ────────────┐
│                                                           │
│ 🏠 Détection des zones Home Assistant                    │
│                                                           │
│ J'ai trouvé 12 zones configurées. Cochez celles que      │
│ vous souhaitez configurer (vous vérifierez ensuite) :    │
│                                                           │
│ ☐ Salon                         [Détails ▼]              │
│    └─ Type proposé: Normal                                │
│    └─ Chauffage détecté: climate.salon_poele             │
│    └─ Lumières: 3 détectées                              │
│    └─ Fenêtres: 4 capteurs détectés                      │
│                                                           │
│ ☐ Chambre d'amis                [Détails ▼]              │
│    └─ Type proposé: Normal                                │
│    └─ Chauffage détecté: climate.x4fp_fp_1 (X4FP)        │
│    └─ Température: sensor.temperature_chambre_d_amis     │
│    └─ Fenêtres: 2 capteurs détectés                      │
│                                                           │
│ ☐ Salle de bain                 [Détails ▼]              │
│    └─ Type proposé: Bathroom                              │
│    └─ Chauffage détecté: climate.x4fp_fp_4 (X4FP)        │
│    └─ Lumière confort: light.x8r_ndeg1_relais_6          │
│                                                           │
│ ☐ Grenier                       [Détails ▼]              │
│    └─ Aucun chauffage détecté                             │
│                                                           │
│ ⚠️ Rien n'est configuré automatiquement. Vous            │
│    devrez vérifier chaque pièce à l'étape suivante.      │
│                                                           │
│ [Tout cocher] [Tout décocher]                            │
│                                                           │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ ⚙️ Options globales (optionnel)                      │ │
│ │                                                       │ │
│ │ Alarme: [Aucun                                 ▼]    │ │
│ │ Calendrier été/hiver: [Aucun                   ▼]    │ │
│ │                                                       │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                           │
│      [Annuler]  [Suivant : Vérifier les pièces]          │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

**6. Écran de Vérification par Pièce** (L'utilisateur DOIT vérifier)
```yaml
┌─ Vérification : Salon (Pièce 1/3) ────────────────────────┐
│                                                           │
│ ⚠️ Configuration PROPOSÉE - Vérifiez tous les champs     │
│                                                           │
│ 📋 Informations de base                                  │
│    Nom: [Salon                                      ]    │
│         └─ ✏️ Modifiable                                 │
│    Type: [Normal                                 ▼]    │
│         └─ 💡 Normal / Corridor / Bathroom               │
│    Icône: [mdi:sofa                               ]    │
│         └─ ✏️ Optionnel                                  │
│                                                           │
│ 🌡️ Chauffage                                             │
│    Entité: [climate.salon_poele                  ▼]    │
│           └─ 🔍 Type détecté: Thermostat (heat only)     │
│    💡 Vous pouvez changer l'entité si détection fausse   │
│                                                           │
│    Températures (vérifiez les valeurs) :                 │
│       Confort: [20°C]  Eco: [18°C]  Nuit: [17°C]         │
│       Hors-gel: [12°C]                                    │
│                                                           │
│ 🪟 Fenêtres/Portes (vérifiez la sélection)              │
│    [✓] binary_sensor.x24d_10_fenetre_cuisine             │
│    [✓] binary_sensor.x24d_09_baie_vitree_cuisine         │
│    [✓] binary_sensor.x24d_08_baie_vitree_2m_salon        │
│    [✓] binary_sensor.x24d_07_baie_vitree_3m_salon        │
│    💡 Décochez si erreur de détection                    │
│                                                           │
│ 🔌 Contrôle Externe (optionnel)                          │
│    Switch: [Aucun                                 ▼]    │
│    💡 Ex: Solar Optimizer, tarif dynamique               │
│                                                           │
│ ⏰ Plages Horaires (modifiables)                         │
│    Début nuit: [22:00]                                    │
│    Plages confort: [07:00-09:00,18:00-22:00       ]    │
│                                                           │
│ ┌─────────────────────────────────────────────────────┐  │
│ │ ⚠️ IMPORTANT : Cette configuration est une          │  │
│ │    PROPOSITION basée sur la détection automatique.  │  │
│ │    Vérifiez TOUS les champs avant de valider !      │  │
│ └─────────────────────────────────────────────────────┘  │
│                                                           │
│   [Ignorer cette pièce]  [Valider et Suivant]            │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

**7. Flow du Wizard** (SANS auto-validation)
```
Étape 1: Choix mode
  ├─ "Configuration assistée (recommandé)" - détecte et propose
  └─ "Configuration manuelle" - saisie complète

Étape 2: Détection zones (si assistée)
  ├─ Scan toutes les areas HA (2 sec)
  ├─ Scan entités par area
  ├─ Détection types
  └─ Affichage liste avec checkboxes (TOUTES DÉCOCHÉES par défaut)
      💡 L'utilisateur coche manuellement ce qu'il veut configurer

Étape 3: Configuration globale
  ├─ Alarme (optionnel)
  └─ Calendrier été/hiver (optionnel)

Étape 4: Validation MANUELLE par pièce (pour CHAQUE cochée)
  ├─ Afficher config PROPOSÉE (pas validée)
  ├─ L'utilisateur DOIT vérifier chaque champ
  ├─ L'utilisateur peut modifier tout ce qu'il veut
  ├─ Boutons : [Ignorer] [Valider] [Suivant]
  └─ ⚠️ Aucune validation automatique, tout est proposition

Étape 5: Résumé
  ├─ X pièces configurées (celles validées par l'utilisateur)
  ├─ Y entités climate gérées
  └─ [Terminer]

POST-INSTALLATION:
  ├─ Via "Options" : Ajouter d'autres pièces
  ├─ Via "Options" : Modifier pièces existantes
  └─ Via "Options" : Supprimer pièces
```

**Important** : Le wizard est une **assistance**, pas une auto-configuration. L'utilisateur garde le contrôle total.

**Principes Importants** :
- ⚠️ **JAMAIS d'auto-validation** : Le wizard détecte et propose, l'utilisateur DOIT valider
- ✅ Chaque pièce doit être vérifiée manuellement
- ✅ L'utilisateur peut tout modifier (entités, températures, types)
- ✅ L'utilisateur peut ignorer des pièces détectées
- ✅ Configuration modifiable après coup (via options)
- ✅ Ajout de pièces ultérieur possible

**Avantages** :
- ✅ Configuration facilitée (5 min au lieu de 30 min)
- ✅ Pas d'erreur de saisie (entités déjà existantes)
- ✅ Détection intelligente des types (mais utilisateur valide)
- ✅ Contrôle total de l'utilisateur
- ✅ Fallback mode manuel si besoin
- ✅ Non intrusif (proposition, pas imposition)

#### 3.2 - Type "VMC"
**Pour ventilation automatique**

#### 3.3 - Type "Utility"
**Pour prises/appareils horaires**

---

## 📁 Fichiers à Modifier

### Critiques (Priority 1)
1. ✅ **const.py** - Ajouter toutes les nouvelles constantes
2. ✅ **config_flow.py** - Ajouter champs configuration
3. ✅ **climate_control.py** - Logique hystérésis + External Control avancé + été
4. ✅ **room_manager.py** - Logique calendrier

### Importants (Priority 2)
5. ⚠️ **coordinator.py** - Tick configurable
6. ⚠️ **climate_control.py** - Presets configurables + summer policy

### Bonus (Priority 3)
7. 🔵 **translations/fr.json** - Traductions
8. 🔵 **translations/en.json** - Traductions
9. 🔵 **config_flow.py** - Wizard complet

---

## 🗺️ Architecture Proposée

### Nouvelle Structure climate_control.py

```python
class ClimateController:
    async def async_update(self):
        # PRIORITY 0: Détection type
        if self._climate_type is None:
            self._detect_climate_type()

        # PRIORITY 1: Bypass (contrôle externe complet = intégration OFF)
        if self._is_bypass_active():
            return

        # PRIORITY 2: Fenêtres ouvertes (avec délai)
        if self._is_windows_open_delayed():
            await self._set_frost_protection()
            return

        # PRIORITY 3: External Control actif (Solar Optimizer, etc.)
        if self._is_external_control_active():
            await self._apply_external_control()
            return

        # PRIORITY 4: Away mode (alarme)
        if self._is_away_mode():
            await self._set_frost_protection()
            return

        # PRIORITY 5: Calendrier pièce
        if self._has_schedule():
            mode = self._get_schedule_mode()
            await self._apply_mode(mode)
            return

        # PRIORITY 6: Logique normale
        mode = self.room_manager.get_current_mode()
        is_summer = self._is_summer_mode()

        if self._climate_type == CLIMATE_TYPE_X4FP:
            if self._has_temperature_control():
                await self._control_x4fp_with_hysteresis(mode, is_summer)
            else:
                await self._control_x4fp_preset_only(mode, is_summer)
        else:
            await self._control_thermostat(mode, is_summer)

    def _control_x4fp_with_hysteresis(self, mode, is_summer):
        """X4FP Type 3b : avec capteur température + hystérésis"""
        if is_summer:
            # Été → OFF ou eco selon summer_policy
            return

        # Lire température + consigne
        current_temp = self._get_current_temperature()
        setpoint = self._get_setpoint()
        hysteresis = self.room_config.get(CONF_HYSTERESIS, 0.5)

        # Logique hystérésis
        if current_temp <= setpoint - hysteresis:
            target_preset = self.room_config.get(CONF_PRESET_HEAT, "comfort")
        elif current_temp >= setpoint + hysteresis:
            target_preset = self.room_config.get(CONF_PRESET_IDLE, "eco")
        else:
            # Zone morte
            return

        await self._set_x4fp_preset(target_preset)

    def _control_x4fp_preset_only(self, mode, is_summer):
        """X4FP Type 3a : sans capteur, juste presets"""
        # Code actuel, fonctionne déjà
        pass

    def _control_thermostat(self, mode, is_summer):
        """Thermostats Type 1 & 2"""
        if is_summer:
            # Type 1 (heat only) → OFF
            # Type 2 (heat/cool) → COOL avec temp selon mode
            if self._is_reversible():
                if mode == MODE_COMFORT:
                    await self._set_hvac_mode_temp(COOL, temp_cool_comfort)
                else:  # eco, night
                    await self._set_hvac_mode_temp(COOL, temp_cool_eco)
            else:
                await self._set_hvac_mode(OFF)
        else:
            # Hiver → HEAT
            temp = self._get_target_temperature(mode)
            await self._set_hvac_mode_temp(HEAT, temp)
```

---

## ✅ Checklist Migration Blueprints → Intégration

### Chambre d'amis (X4FP + temp + external control)
- [ ] Ajouter capteur température
- [ ] Ajouter consigne (input_number)
- [ ] Configurer hystérésis
- [ ] Configurer External Control (switch.solar_optimizer_xxx)
- [ ] ☑️ Cocher "Allow external control in away" si souhaité
- [ ] Tester hystérésis fonctionne
- [ ] Tester External Control override

### Suite parentale (X4FP + temp + external control + schedule)
- [ ] Ajouter capteur température
- [ ] Ajouter consigne (input_number)
- [ ] Configurer hystérésis
- [ ] Ajouter calendrier pièce
- [ ] Configurer External Control (switch.solar_optimizer_xxx)
- [ ] ☑️ Cocher "Allow external control in away" si souhaité
- [ ] Tester planning fonctionne

### Sèche-serviettes SdB (X4FP + light + external control + schedule)
- [ ] Lumière → confort (déjà OK)
- [ ] Ajouter calendrier
- [ ] Configurer External Control (switch.solar_optimizer_xxx)
- [ ] Tester calendrier bloque lumières

### Poêle salon (Thermostat heat only)
- [ ] Déjà OK, juste configurer fenêtres

### Clim Livia (Thermostat heat/cool + external control + schedule)
- [ ] Corriger été eco → COOL 26°C
- [ ] Ajouter calendrier
- [ ] Configurer External Control (switch.solar_optimizer_xxx)
- [ ] ☑️ Cocher "Allow external control in away" si souhaité
- [ ] Tester été fonctionne

### Clim Thomas (Thermostat heat/cool + external control + schedule)
- [ ] Corriger été eco → COOL 26°C
- [ ] Ajouter calendrier
- [ ] Configurer External Control (switch.solar_optimizer_xxx)
- [ ] ☑️ Cocher "Allow external control in away" si souhaité
- [ ] Tester été fonctionne

---

## 🚀 Plan d'Implémentation

### Phase 1 : Gaps Critiques (Priority 1) - 6-8h
1. ✅ Hystérésis X4FP (2h)
2. ✅ External Control avancé (2h)
3. ✅ Calendrier par pièce (1h)
4. ✅ Été thermostats réversibles (1h)
5. ✅ Tests sur 1 pièce de chaque type (2h)

### Phase 2 : Améliorations (Priority 2) - 3-4h
1. ⚠️ Délais fenêtres (1h)
2. ⚠️ Presets configurables (1h)
3. ⚠️ Summer policy (30min)
4. ⚠️ Tick configurable (30min)
5. ⚠️ Tests complets (1h)

### Phase 3 : Wizard & Extensions (Priority 3) - 4-6h
1. 🔵 Traductions FR/EN (1h)
2. 🔵 Wizard installation intelligent (3h)
   - Détection zones HA (areas)
   - Scan entités par zone
   - Pré-remplissage configuration (PROPOSITION)
   - Interface vérification/modification obligatoire
   - Ajout/modification ultérieure via Options
3. 🔵 Documentation (1h)

**Total estimé : 13-18h**

---

## ❓ Questions Validation

1. **Ordre des priorités OK ?**
   - Phase 1 d'abord → remplacer blueprints
   - Phase 2 ensuite → améliorer
   - Phase 3 → wizard

2. **Architecture 3 types de chauffage OK ?**
   - Type 1 : Thermostat heat only
   - Type 2 : Thermostat heat/cool
   - Type 3a : X4FP sans capteur
   - Type 3b : X4FP avec capteur + hystérésis

3. **Logique priorités External Control OK ?**
   - Bypass ON → arrêt total (intégration ne fait rien)
   - External Control actif → override (sauf away si case non cochée)
   - Détection via is_active attribute OU state ON
   - Générique (Solar Optimizer, future intégration, etc.)

4. **Migration progressive ?**
   - Pièce par pièce ?
   - Ou tout d'un coup après tests ?

5. **Calendrier bloque lumières ?**
   - Uniquement pour salles de bain ?
   - Ou option générale ?

6. **VMC & Prises → intégration ou automations ?**
   - Phase 3 vraiment utile ?
   - Ou on se concentre sur chauffage ?
