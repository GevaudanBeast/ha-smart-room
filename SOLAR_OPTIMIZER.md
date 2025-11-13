# ⚡ Solar Optimizer - Guide d'intégration

Smart Room Manager v0.1.0 supporte dès sa version initiale **Solar Optimizer** en mode **prioritaire**.

## 🎯 Principe de fonctionnement

Solar Optimizer gère le chauffage pour utiliser le surplus d'énergie solaire. Quand Solar Optimizer décide de chauffer une pièce, **il doit avoir la priorité absolue** sur toute autre logique.

### Comportement de Smart Room Manager

```
┌─────────────────────────────────────────────────────┐
│  switch.solar_optimizer_xxx = ON                    │
│  ↓                                                   │
│  Solar Optimizer chauffe activement                 │
│  ↓                                                   │
│  Smart Room Manager se met EN RETRAIT               │
│  ↓                                                   │
│  Aucune action de Smart Room Manager                │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  switch.solar_optimizer_xxx = OFF                   │
│  ↓                                                   │
│  Solar Optimizer ne chauffe pas                     │
│  ↓                                                   │
│  Smart Room Manager reprend le contrôle             │
│  ↓                                                   │
│  Logique normale (alarme, fenêtres, etc.)           │
└─────────────────────────────────────────────────────┘
```

## ⚙️ Configuration

### Étape 1 : Activer Solar Optimizer

Assure-toi que Solar Optimizer est correctement configuré dans Home Assistant :

```yaml
# Configuration Solar Optimizer (exemple)
solar_optimizer:
  devices:
    - name: "Chauffage Suite parentale"
      entity_id: climate.x4fp_fp_2
      power: 1500  # Watts
      switch: switch.solar_optimizer_chauffage_suite_parentale
```

### Étape 2 : Configurer Smart Room Manager

Lors de la configuration d'une pièce avec Solar Optimizer :

**Configuration → Intégrations → Smart Room Manager → Configurer → Ajouter/Modifier une pièce**

#### Étape "Actionneurs" :

| Champ | Valeur |
|-------|--------|
| Entité climat | `climate.x4fp_fp_2` |
| **Solar Optimizer switch** | `switch.solar_optimizer_chauffage_suite_parentale` |

⚠️ **Important** : Le switch Solar Optimizer est le **switch d'action** (pas l'enable switch). C'est le switch qui est **ON** quand SO chauffe activement.

## 📋 Exemples de configuration

### Suite parentale (X4FP avec SO)

```yaml
Nom: "Suite parentale"

# Capteurs
Capteurs porte/fenêtre:
  - binary_sensor.x24d_03_baie_vitree_sp
  - binary_sensor.x24d_04_fenetre_sp

# Actionneurs
Entité climat: climate.x4fp_fp_2
Solar Optimizer switch: switch.solar_optimizer_chauffage_suite_parentale

# Chauffage
Température confort: 20°C
Température éco: 18°C
Température nuit: 17°C
Température absence: 16°C
Vérifier fenêtres: ✅ Oui
```

### Chambre d'amis (X4FP avec SO)

```yaml
Nom: "Chambre d'amis"
Entité climat: climate.x4fp_fp_1
Solar Optimizer switch: switch.solar_optimizer_chauffage_chambre_d_amis
(reste identique à Suite parentale)
```

### Salle d'eau (Sèche-serviettes avec SO)

```yaml
Nom: "Salle d'eau RDC"
Entité climat: climate.x4fp_fp_3
Solar Optimizer switch: switch.solar_optimizer_seche_serviette_salle_d_eau
```

### Salle de bain (Sèche-serviettes avec SO)

```yaml
Nom: "Salle de bain Et.1"
Entité climat: climate.x4fp_fp_4
Solar Optimizer switch: switch.solar_optimizer_seche_serviette_salle_de_bain
```

### Chambre Thomas (Climatisation avec SO)

```yaml
Nom: "Chambre Thomas"
Entité climat: climate.clim_thomas
Solar Optimizer switch: switch.solar_optimizer_climatisation_thomas
```

### Chambre Livia (Climatisation avec SO)

```yaml
Nom: "Chambre Livia"
Entité climat: climate.clim_livia
Solar Optimizer switch: switch.solar_optimizer_climatisation_livia
```

## 🔍 Vérification du fonctionnement

### 1. Vérifier les logs

**Configuration → Logs → Filtrer "smart_room_manager"**

Quand Solar Optimizer est actif, tu dois voir :

```
[smart_room_manager.climate_control] ⚡ Solar Optimizer active (switch.solar_optimizer_chauffage_suite_parentale ON) in Suite parentale - Smart Room Manager in standby
```

### 2. Observer le comportement

#### Test 1 : Solar Optimizer actif

1. ✅ Vérifie que `switch.solar_optimizer_xxx` = **ON**
2. ✅ Smart Room Manager ne doit **PAS** modifier le chauffage
3. ✅ Les logs montrent "Solar Optimizer active... in standby"

#### Test 2 : Solar Optimizer inactif

1. ✅ Vérifie que `switch.solar_optimizer_xxx` = **OFF**
2. ✅ Smart Room Manager reprend le contrôle
3. ✅ Le chauffage suit les règles normales (alarme, fenêtres, etc.)

#### Test 3 : Transition SO → Smart Room Manager

1. ✅ Attends que Solar Optimizer finisse de chauffer (switch passe à OFF)
2. ✅ Dans les 30 secondes, Smart Room Manager reprend le contrôle
3. ✅ La température est ajustée selon le mode (confort/éco/away)

## 🔄 Migration depuis les blueprints

Si tu utilisais les blueprints HVAC avec Solar Optimizer, voici comment migrer :

### Avant (blueprint)

```yaml
- id: chauffage_suite_parentale
  alias: Chauffage - Suite parentale
  use_blueprint:
    path: blueprint_hvac_X4FP_room.yaml
    input:
      room_name: Suite parentale
      climate_entity: climate.x4fp_fp_2
      solar_enable: switch.solar_optimizer_chauffage_suite_parentale
      solar_behavior: force_comfort
```

### Après (Smart Room Manager)

1. Configure la pièce dans Smart Room Manager avec le switch SO
2. Désactive le blueprint
3. Teste pendant 1 semaine
4. Supprime le blueprint si tout fonctionne

### Comparaison des comportements

| Condition | Blueprint | Smart Room Manager | Identique ? |
|-----------|-----------|-------------------|-------------|
| SO switch = ON | Blueprint en retrait | SRM en retrait | ✅ Oui |
| SO switch = OFF | Logique blueprint | Logique SRM | ✅ Oui |
| Fenêtre ouverte | Pause chauffage | Pause chauffage | ✅ Oui |
| Alarme armée | Mode away | Mode away | ✅ Oui |
| Été (calendar) | OFF | OFF | ✅ Oui |

## ⚠️ Points d'attention

### 1. Switch Solar Optimizer correct

**✅ BON** : `switch.solar_optimizer_chauffage_suite_parentale`
- C'est le switch qui est ON quand SO chauffe

**❌ MAUVAIS** : `input_boolean.solar_optimizer_enable`
- Ce n'est PAS le switch d'action

### 2. Ordre de priorité

Smart Room Manager respecte cet ordre :

1. ⚡ **Solar Optimizer actif** (switch ON) → Priorité absolue
2. ☀️ **Été** (calendar) → Chauffage OFF
3. 🪟 **Fenêtre ouverte** → Pause
4. 🔒 **Alarme armée** → Mode away
5. 🌡️ **Logique normale** → Confort/Éco/Nuit

### 3. Pas de conflit

Si le switch SO n'est pas configuré, Smart Room Manager fonctionne normalement (comme avant).

## 📊 Scénarios d'usage

### Scénario 1 : Journée ensoleillée

```
09:00 - SO détecte surplus solaire
      → switch.solar_optimizer_xxx = ON
      → Smart Room Manager se met en retrait
      → SO chauffe à fond pour stocker l'énergie

14:00 - SO a fini de chauffer
      → switch.solar_optimizer_xxx = OFF
      → Smart Room Manager reprend le contrôle
      → Température maintenue selon mode (confort/éco)
```

### Scénario 2 : Nuit + alarme armée

```
22:00 - Alarme armée (away)
      → SO ne chauffe pas (pas de soleil)
      → Smart Room Manager applique mode away (16°C)

03:00 - Toujours nuit
      → SO toujours inactif
      → Smart Room Manager maintient 16°C
```

### Scénario 3 : Fenêtre ouverte pendant SO

```
11:00 - SO chauffe (switch ON)
      → Smart Room Manager en retrait

11:30 - Tu ouvres la fenêtre
      → Smart Room Manager détecte l'ouverture
      → ⚠️ SO continue de chauffer (il a la priorité)
      → Tu dois désactiver SO manuellement ou attendre qu'il finisse

11:45 - SO finit de chauffer (switch OFF)
      → Smart Room Manager reprend le contrôle
      → Détecte fenêtre ouverte
      → Coupe le chauffage immédiatement
```

⚠️ **Note** : Quand SO est actif, même une fenêtre ouverte ne coupe PAS le chauffage. C'est voulu : SO doit pouvoir finir son cycle.

## 🆘 Dépannage

### Problème : SO et Smart Room Manager se battent

**Symptôme** : Le chauffage change constamment de consigne

**Cause** : Le switch SO n'est pas le bon

**Solution** :
1. Vérifie le nom exact du switch dans Solar Optimizer
2. C'est le switch qui est ON quand SO chauffe activement
3. Reconfigure Smart Room Manager avec le bon switch

### Problème : Smart Room Manager ne reprend pas le contrôle après SO

**Symptôme** : Après que SO ait fini, la température ne s'ajuste pas

**Cause** : Switch toujours détecté comme ON

**Solution** :
1. Vérifie l'état réel du switch : Outils développeur → États
2. Si le switch est bloqué ON, redémarre Solar Optimizer
3. Vérifie les logs de Solar Optimizer

### Problème : SO ne chauffe plus

**Symptôme** : SO était fonctionnel, il ne chauffe plus

**Cause** : Smart Room Manager interfère (rare mais possible)

**Solution** :
1. Désactive temporairement Smart Room Manager : `switch.smart_room_xxx_automation` → OFF
2. Teste Solar Optimizer seul
3. Si SO fonctionne, le switch configuré n'est pas le bon
4. Reconfigure avec le bon switch

## 📞 Support

Si tu rencontres des problèmes avec Solar Optimizer :

1. **Vérifier les switchs** : Outils développeur → États → Rechercher "solar_optimizer"
2. **Vérifier les logs** : Configuration → Logs → Filtrer "smart_room_manager" ET "solar_optimizer"
3. **Tester manuellement** : Désactive Smart Room Manager et teste SO seul
4. **GitHub** : Ouvre une issue avec les logs

---

**Version** : 0.1.0
**Dernière mise à jour** : 2025-01-13
**Auteur** : GevaudanBeast
