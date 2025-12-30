# Plan : Évolution Architecture Smart Room Manager

## 🎯 Objectif

Créer une architecture hybride avec :
- **1 automation centrale** : Gère la logique globale (alarme, planning, profils)
- **Blueprints par pièce** : Exécutent les décisions localement

## 📐 Architecture Proposée

```
Smart Room Manager Central (Automation)
├─ Input : alarm_control_panel.maison
├─ Input : calendar.planning (optionnel)
├─ Output : input_select.preset_chambre
├─ Output : input_select.preset_salon
└─ Output : input_select.preset_sdb

Blueprint Chambre
├─ Listen : input_select.preset_chambre
├─ Check : binary_sensor.fenetre_chambre
├─ Check : switch.solar_optimizer_chambre (bypass)
└─ Control : climate.chambre

Blueprint Salon
├─ Listen : input_select.preset_salon
├─ Check : binary_sensor.fenetre_salon
├─ Check : switch.solar_optimizer_salon (bypass)
└─ Control : climate.salon + light.salon
```

## ✅ Avantages

1. **Logique centralisée** : 1 endroit pour gérer alarme/planning
2. **Blueprints simplifiés** : Juste écoute + priorités locales
3. **Planning flexible** : Global ou par pièce selon besoin
4. **Règles inter-pièces** : Possibles dans l'automation centrale
5. **Migration progressive** : Peut cohabiter avec système actuel

## 📊 Comparaison avec Système Actuel

### Système Actuel (v0.2.4)
- ✅ Intégration Python complète
- ✅ UI de configuration
- ✅ Tout géré en code Python
- ❌ Modifications = rebuild de l'intégration
- ❌ Logique répartie dans plusieurs fichiers

### Nouveau Système Proposé
- ✅ Automation YAML = modifications faciles
- ✅ Blueprints = réutilisables
- ✅ Logique visible dans UI HA
- ❌ Pas de UI config intégrée
- ❌ Plus de fichiers à maintenir

## 🛠️ Options d'Implémentation

### Option A : MVP Simple (1-2h)
**Périmètre** :
- ✅ Automation centrale pour alarme armée/désarmée
- ✅ Input select par pièce (preset : comfort, eco, night, frost)
- ✅ Profils basiques : chambre, salon
- ❌ Pas de planning (juste alarme)
- ❌ Pas de calendrier

**Fichiers à créer** :
```
automations/
  smart_room_central.yaml
blueprints/
  smart_room_climate.yaml
  smart_room_lights.yaml
helpers/
  input_select_preset_chambre.yaml
  input_select_preset_salon.yaml
```

**Logique MVP** :
```yaml
# Automation centrale
trigger:
  - platform: state
    entity_id: alarm_control_panel.maison
action:
  - if alarme armed_away:
      set all presets to "frost_protection"
    else:
      set all presets to "eco"
```

### Option B : Complet (3-4h)
**Périmètre** :
- ✅ Alarme armée/désarmée
- ✅ Planning avec calendriers par pièce
- ✅ Profils de pièces (normal, corridor, bathroom)
- ✅ Migration de tous les blueprints
- ✅ Plages horaires confort

**Fichiers à créer** :
```
automations/
  smart_room_central.yaml
blueprints/
  smart_room_normal.yaml
  smart_room_corridor.yaml
  smart_room_bathroom.yaml
helpers/
  input_select_preset_*.yaml (toutes pièces)
  calendar.planning_*.yaml (optionnel)
scripts/
  migration_v0.2_to_v0.3.py
```

**Logique complète** :
```yaml
# Automation centrale
trigger:
  - platform: state
    entity_id: alarm_control_panel.maison
  - platform: time_pattern
    minutes: "/5"
action:
  - for each room:
      - check: alarme armed_away?
        → preset = frost_protection
      - check: in comfort time range?
        → preset = comfort
      - check: in night time?
        → preset = night
      - else:
        → preset = eco
```

### Option C : Attendre
**Raisons** :
- Tester d'abord système actuel v0.2.4
- Voir si vraiment besoin de cette refonte
- Collecter feedback utilisateurs
- Décider plus tard

## 🤔 Recommandation

**Je recommande : Option A (MVP Simple)**

**Pourquoi ?** :
1. **Validation du concept** : Tester l'approche avant investissement complet
2. **Cohabitation** : Peut fonctionner avec système actuel
3. **Apprentissage** : Voir si cette architecture convient mieux
4. **Rapide** : 1-2h pour avoir quelque chose de fonctionnel
5. **Évolutif** : Facile de passer à Option B si concluant

**Ensuite** :
- Si MVP concluant → Migration vers Option B
- Si MVP non concluant → Rester sur système actuel v0.2.4

## 📝 Questions à Clarifier

1. **Nomenclature** : Garder nom "Smart Room Manager" ou nouveau nom ?
2. **Cohabitation** : Nouveau système remplace ou complète l'actuel ?
3. **Migration** : Utilisateurs actuels doivent-ils migrer ?
4. **Version** : v0.3.0 ou projet séparé ?

## 🚀 Prochaines Étapes (si MVP)

1. Créer structure dossiers
2. Créer input_select helpers (2 pièces test)
3. Créer automation centrale (logique alarme)
4. Créer 1 blueprint simple (chambre)
5. Tester sur pièce test
6. Documenter résultats

## 📊 Métriques de Succès

- [ ] Automation centrale fonctionne avec alarme
- [ ] Presets changent selon alarme
- [ ] Blueprint réagit aux presets
- [ ] Bypass (fenêtre, SO) fonctionne
- [ ] Code plus simple que v0.2.4 ?
- [ ] Configuration plus facile ?
