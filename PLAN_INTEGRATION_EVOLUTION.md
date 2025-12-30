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

#### 1.2 - Solar Optimizer Avancé ⭐⭐⭐
**Impact** : Toutes les pièces avec SO
**Fichiers** : `climate_control.py`, `config_flow.py`

**Ajouts nécessaires** :
```python
# Config
CONF_SOLAR_SWITCH = "solar_switch"  # Déjà présent (bypass)
CONF_SOLAR_PRESET = "solar_preset"  # comfort/eco/etc. (X4FP)
CONF_SOLAR_TEMP = "solar_temp"  # Température (thermostat)
CONF_ALLOW_SOLAR_IN_AWAY = "allow_solar_in_away"  # Boolean
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

# PRIORITY 3: Solar Optimizer actif → NOUVEAU
if solar_is_heating():
    # Vérifier is_active attribute ou state
    is_active = state_attr(solar_switch, 'is_active') or state(solar_switch) == 'on'

    if is_active:
        # Override away si autorisé
        if is_away and not allow_solar_in_away:
            pass  # Continue vers away
        else:
            # Appliquer preset/temp solar
            if X4FP:
                set_preset(solar_preset)
            else:
                set_temperature(solar_temp)
            return

# PRIORITY 4: Away mode
if is_away:
    frost_protection()
    return

# PRIORITY 5: Reste de la logique normale...
```

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

#### 3.1 - Wizard d'Installation FR/EN
**Fichiers** : `config_flow.py`, `translations/`

#### 3.2 - Détection Automatique Entités
**Lors de l'ajout** : proposer toutes les entités détectées

#### 3.3 - Type "VMC"
**Pour ventilation automatique**

#### 3.4 - Type "Utility"
**Pour prises/appareils horaires**

---

## 📁 Fichiers à Modifier

### Critiques (Priority 1)
1. ✅ **const.py** - Ajouter toutes les nouvelles constantes
2. ✅ **config_flow.py** - Ajouter champs configuration
3. ✅ **climate_control.py** - Logique hystérésis + Solar avancé + été
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

        # PRIORITY 1: Bypass (Solar Optimizer OFF = contrôle externe)
        if self._is_bypass_active():
            return

        # PRIORITY 2: Fenêtres ouvertes (avec délai)
        if self._is_windows_open_delayed():
            await self._set_frost_protection()
            return

        # PRIORITY 3: Solar Optimizer actif
        if self._is_solar_heating():
            await self._apply_solar_control()
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

### Chambre d'amis (X4FP + temp + solar)
- [ ] Ajouter capteur température
- [ ] Ajouter consigne (input_number)
- [ ] Configurer hystérésis
- [ ] Configurer Solar Optimizer (is_active)
- [ ] Tester hystérésis fonctionne
- [ ] Tester Solar override

### Suite parentale (X4FP + temp + solar + schedule)
- [ ] Ajouter capteur température
- [ ] Ajouter consigne (input_number)
- [ ] Configurer hystérésis
- [ ] Ajouter calendrier pièce
- [ ] Configurer Solar Optimizer
- [ ] Tester planning fonctionne

### Sèche-serviettes SdB (X4FP + light + solar + schedule)
- [ ] Lumière → confort (déjà OK)
- [ ] Ajouter calendrier
- [ ] Configurer Solar Optimizer
- [ ] Tester calendrier bloque lumières

### Poêle salon (Thermostat heat only)
- [ ] Déjà OK, juste configurer fenêtres

### Clim Livia (Thermostat heat/cool + solar + schedule)
- [ ] Corriger été eco → COOL 26°C
- [ ] Ajouter calendrier
- [ ] Configurer Solar Optimizer
- [ ] Tester été fonctionne

### Clim Thomas (Thermostat heat/cool + solar + schedule)
- [ ] Corriger été eco → COOL 26°C
- [ ] Ajouter calendrier
- [ ] Configurer Solar Optimizer
- [ ] Tester été fonctionne

---

## 🚀 Plan d'Implémentation

### Phase 1 : Gaps Critiques (Priority 1) - 6-8h
1. ✅ Hystérésis X4FP (2h)
2. ✅ Solar Optimizer avancé (2h)
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
2. 🔵 Wizard installation (2h)
3. 🔵 Détection auto entités (1h)
4. 🔵 Documentation (1h)

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

3. **Logique priorités Solar Optimizer OK ?**
   - Bypass ON → arrêt total
   - Solar actif → override (sauf away si non autorisé)
   - Détection via is_active attribute

4. **Migration progressive ?**
   - Pièce par pièce ?
   - Ou tout d'un coup après tests ?

5. **Calendrier bloque lumières ?**
   - Uniquement pour salles de bain ?
   - Ou option générale ?

6. **VMC & Prises → intégration ou automations ?**
   - Phase 3 vraiment utile ?
   - Ou on se concentre sur chauffage ?
