# 📖 Guide de migration vers Smart Room Manager

Ce guide explique comment migrer progressivement tes automatisations YAML existantes vers l'intégration Smart Room Manager.

## 🎯 Principe de migration

**IMPORTANT** : Migration **progressive** et **testée** pièce par pièce.

### Ordre recommandé

1. ✅ Pièces simples d'abord (couloir, WC, cave)
2. ✅ Pièces avec chauffage simple ensuite
3. ✅ Pièces avec Solar Optimizer (attention particulière)
4. ⚠️ **NE PAS migrer les volets** (trop spécifiques)

## 📋 Inventaire de tes automatisations

### Lumières à migrer

| Pièce | Automation actuelle | Timer actuel | Commentaires |
|-------|-------------------|--------------|--------------|
| Couloirs (x3) | `Timer - couloirs...` | 5 min | ✅ Simple |
| Salle d'eau RDC | `Timer - couloirs...` | 15 min | ✅ Simple |
| Salle de bain Et.1 | `Timer - couloirs...` | 15 min | ✅ Simple |
| WC | `Timer - couloirs...` | 5 min | ✅ Simple |
| Grenier | `Timer - couloirs...` | 15 min | ✅ Simple |
| Cave | `Timer - couloirs...` | 15 min | ✅ Simple |
| Abris | `Timer - couloirs...` | 15 min | ✅ Simple |
| Entrée intérieure | `Entrée intérieure - Ouverture de la porte` | 5 min | ✅ Simple |
| Entrée extérieure | `Lumière de l'entrée extérieure` | IPX timer | ✅ Simple |
| Extérieurs | `Extérieurs - Gestion complète...` | N/A | ⚠️ Garder automation |
| Terrasse | `Terrasse - Gestion intelligente...` | N/A | ⚠️ Garder automation |

### Chauffages à migrer

| Pièce | Type | Blueprint actuel | Solar Optimizer | Priorité |
|-------|------|------------------|-----------------|----------|
| Salon | Poêle | `blueprint_hvac_thermostat_heat.yaml` | ❌ Non | 1 |
| Suite parentale | X4FP FP2 | `blueprint_hvac_X4FP_room.yaml` | ✅ Oui | 3 |
| Chambre d'amis | X4FP FP1 | `blueprint_hvac_X4FP_room.yaml` | ✅ Oui | 3 |
| Salle d'eau RDC | X4FP FP3 | `blueprint_hvac_X4FP_bathroom.yaml` | ✅ Oui | 3 |
| Salle de bain Et.1 | X4FP FP4 | `blueprint_hvac_X4FP_bathroom.yaml` | ✅ Oui | 3 |
| Chambre Thomas | Clim | `blueprint_hvac_room_thermostat.yaml` | ✅ Oui | 2 |
| Chambre Livia | Clim | `blueprint_hvac_room_thermostat.yaml` | ✅ Oui | 2 |

### Automatisations à GARDER en YAML

❌ **Ne PAS migrer** (logiques trop spécifiques) :

- Tous les volets (VR) - trop complexes
- VMC grande vitesse
- Prises cuisine horaires
- Cinéma + volet
- Store anti-vent
- Caméras Frigate
- Alarme fumée
- Pompe inondation
- Sonnette avec snapshot

## 🚀 Migration étape par étape

### Phase 1 : Pièce simple (ex: Couloir RDC)

#### Étape 1.1 : Identifier les entités

```yaml
# Automation actuelle (extrait)
trigger:
  - entity_id: light.x8r_ndeg2_relais_6  # Couloir RDC
    from: 'off'
    to: 'on'
action:
  - delay: { minutes: 5 }
  - light.turn_off: light.x8r_ndeg2_relais_6
```

**Entités identifiées** :
- Lumière : `light.x8r_ndeg2_relais_6`
- Timer : 5 minutes
- Pas de capteur de présence (allumage manuel)
- Pas de capteur de luminosité

#### Étape 1.2 : Configuration dans Smart Room Manager

1. Ouvre **Configuration** → **Intégrations** → **Smart Room Manager**
2. Clique **Configurer** → **Ajouter une pièce**
3. Configure :

**Nom** : `Couloir RDC`

**Capteurs** :
- Capteurs de présence : (vide - pas de capteur)
- Capteur de luminosité : (vide)
- Autres : (vide)

**Actionneurs** :
- Lumières : `light.x8r_ndeg2_relais_6`
- Chauffage : (vide)

**Configuration lumières** :
- Seuil luminosité : 1000 lx (très élevé pour désactiver l'auto)
- Délai extinction : 300 secondes (5 min)
- Mode nuit : Désactivé
- Luminosité jour : 100%

**Chauffage** : (ignorer)

**Horaires** : (par défaut)

#### Étape 1.3 : Tester

1. ✅ Allume manuellement `light.x8r_ndeg2_relais_6`
2. ✅ Vérifie que `switch.smart_room_couloir_rdc_automation` est ON
3. ✅ Attends 5 minutes → lumière doit s'éteindre
4. ✅ Vérifie les logs : **Configuration** → **Logs** → Filtrer "smart_room"

#### Étape 1.4 : Désactiver l'ancienne automation

1. ✅ Va dans **Configuration** → **Automatisations**
2. ✅ Trouve `Timer - couloirs...`
3. ✅ **Désactive-la** (toggle OFF) - **NE PAS supprimer encore**
4. ✅ Teste pendant 1 semaine
5. ✅ Si OK : supprime l'automation

#### Étape 1.5 : Valider

✅ Critères de validation :
- Lumière s'éteint après 5 min d'allumage manuel
- Pas de conflit avec l'ancienne automation
- Logs propres (pas d'erreurs)

---

### Phase 2 : Pièce avec capteurs (ex: Entrée intérieure)

#### Étape 2.1 : Identifier les entités

```yaml
# Automation actuelle
trigger:
  - entity_id: binary_sensor.x24d_17_porte_rdc
    to: 'on'
action:
  - light.turn_on: light.x8r_ndeg2_relais_5
  - delay: { minutes: 5 }
  - light.turn_off: light.x8r_ndeg2_relais_5
```

**Entités** :
- Lumière : `light.x8r_ndeg2_relais_5`
- Capteur : `binary_sensor.x24d_17_porte_rdc` (porte)
- Timer : 5 minutes

#### Étape 2.2 : Configuration Smart Room Manager

**Nom** : `Entrée intérieure`

**Capteurs** :
- Capteurs de présence : `binary_sensor.x24d_17_porte_rdc`
- Capteur de luminosité : (vide - allume toujours)

**Actionneurs** :
- Lumières : `light.x8r_ndeg2_relais_5`

**Configuration lumières** :
- Seuil luminosité : 1000 lx (désactive l'auto lux)
- Délai extinction : 300 s (5 min)
- Mode nuit : Activé ✅
- Luminosité nuit : 100% (pas de variation)
- Luminosité jour : 100%

---

### Phase 3 : Chauffage sans Solar Optimizer (ex: Salon)

#### Étape 3.1 : Identifier les entités

```yaml
# Blueprint actuel : blueprint_hvac_thermostat_heat.yaml
input:
  room_name: Salon
  climate_entity: climate.salon_poele
  window_sensors:
    - binary_sensor.x24d_08_baie_vitree_2m_salon
    - binary_sensor.x24d_07_baie_vitree_3m_salon
    - binary_sensor.x24d_12_fenetre_pano_salon
    - binary_sensor.x24d_09_baie_vitree_cuisine
    - binary_sensor.x24d_10_fenetre_cuisine
  alarm_entity: alarm_control_panel.maison
  summer_entity: calendar.ete_hiver
  comfort_temp: 19.5
  eco_temp: 18
```

**Entités** :
- Chauffage : `climate.salon_poele`
- Fenêtres : 5 capteurs
- Alarme : `alarm_control_panel.maison`
- Été : `calendar.ete_hiver`

#### Étape 3.2 : Configuration Smart Room Manager

**Nom** : `Salon`

**Capteurs** :
- Capteurs de présence : (vide ou ajouter si tu as)
- Capteurs porte/fenêtre :
  - `binary_sensor.x24d_08_baie_vitree_2m_salon`
  - `binary_sensor.x24d_07_baie_vitree_3m_salon`
  - `binary_sensor.x24d_12_fenetre_pano_salon`
  - `binary_sensor.x24d_09_baie_vitree_cuisine`
  - `binary_sensor.x24d_10_fenetre_cuisine`
- Capteur température : (le poêle a déjà son capteur interne)

**Actionneurs** :
- Lumières : (à ajouter si tu veux gérer les lumières salon)
- Entité climat : `climate.salon_poele`

**Configuration chauffage** :
- Température confort : 19.5°C
- Température éco : 18°C
- Température nuit : 17°C
- Température absence : 16°C
- Température hors-gel : 7°C
- Présence requise : ❌ Non
- Vérifier fenêtres : ✅ Oui
- Délai inoccupation : 1800 s (30 min)

**Paramètres globaux** (dans configuration de l'intégration) :
- Entité mode invité : (vide)
- Entité mode vacances : (vide)
- Entité alarme : `alarm_control_panel.maison`
- Capteur de saison : `calendar.ete_hiver`

#### Étape 3.3 : Tester

1. ✅ Vérifie que le chauffage respecte confort/éco selon alarme
2. ✅ Ouvre une fenêtre → chauffage doit se couper
3. ✅ Arme l'alarme → température doit baisser (away)
4. ✅ Active `calendar.ete_hiver` → chauffage doit s'éteindre

#### Étape 3.4 : Désactiver le blueprint

1. ✅ Désactive automation `Chauffage - Salon (poêle)`
2. ✅ Teste pendant 1 semaine
3. ✅ Si OK : supprime l'automation

---

### Phase 4 : Chauffage AVEC Solar Optimizer (ATTENTION)

⚠️ **CRITIQUE** : Solar Optimizer doit rester **PRIORITAIRE**.

#### Contexte Solar Optimizer

Tes blueprints actuels surveillent le switch Solar Optimizer :
```yaml
solar_switch: switch.solar_optimizer_chauffage_suite_parentale
```

Quand ce switch est **ON**, Solar Optimizer est en train de chauffer activement.
→ Le blueprint se met en retrait et laisse SO piloter.

#### Étape 4.1 : Amélioration nécessaire

L'intégration Smart Room Manager actuelle **ne gère pas encore** cette logique SO.

**Deux options** :

**Option A : Garder les blueprints pour les pièces avec SO** (recommandé court terme)
- ✅ Pas de risque
- ✅ SO continue à fonctionner parfaitement
- ❌ Pas de migration complète

**Option B : Améliorer Smart Room Manager** (recommandé moyen terme)
- J'ajoute la logique SO dans l'intégration
- Même comportement que tes blueprints
- Migration complète possible

#### Recommandation

Pour l'instant, **garde les blueprints HVAC** pour les pièces avec Solar Optimizer :
- Suite parentale
- Chambre d'amis
- Salle d'eau RDC
- Salle de bain Et.1
- Chambre Thomas
- Chambre Livia

Je vais améliorer l'intégration pour supporter SO, puis tu pourras migrer ces pièces.

---

## 📊 Plan de migration complet

### Sprint 1 : Lumières simples (1 semaine)

1. ✅ Couloir RDC
2. ✅ Couloir Et.1
3. ✅ WC RDC
4. ✅ Cave
5. ✅ Grenier
6. ✅ Abris

**Test** : 1 semaine, validation complète

### Sprint 2 : Lumières avec capteurs (1 semaine)

1. ✅ Entrée intérieure
2. ✅ Entrée extérieure
3. ✅ Salle d'eau RDC (lumière uniquement)
4. ✅ Salle de bain Et.1 (lumière uniquement)

**Test** : 1 semaine, validation complète

### Sprint 3 : Chauffage sans SO (2 semaines)

1. ✅ Salon (poêle)

**Test** : 2 semaines, validation approfondie

### Sprint 4 : Amélioration Solar Optimizer (attendre mise à jour)

1. ⏳ J'améliore l'intégration pour supporter SO
2. ⏳ Tu testes sur une pièce pilote (ex: Chambre Thomas)
3. ⏳ Si OK, migration des autres pièces SO

---

## 🔧 Dépannage migration

### Problème : Lumière ne s'éteint pas

**Cause** : Ancienne automation toujours active

**Solution** :
1. Désactive l'ancienne automation
2. Redémarre Home Assistant
3. Vérifie les logs

### Problème : Chauffage ne suit pas l'alarme

**Cause** : Entité alarme non configurée dans paramètres globaux

**Solution** :
1. Configuration → Intégrations → Smart Room Manager
2. Configurer → Paramètres globaux
3. Ajoute `alarm_control_panel.maison`

### Problème : Conflit avec Solar Optimizer

**Cause** : SO et Smart Room Manager se battent

**Solution** :
1. **Désactive immédiatement** Smart Room Manager pour cette pièce
2. Réactive le blueprint d'origine
3. Attends la mise à jour de l'intégration avec support SO

---

## 📞 Support

Si tu rencontres des problèmes :

1. **Logs** : Configuration → Logs → Filtrer "smart_room_manager"
2. **État des entités** : Outils développeur → États
3. **GitHub** : Ouvre une issue sur le repository

---

**Version** : 1.0.0
**Dernière mise à jour** : 2025-01-13
