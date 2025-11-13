# 🏠 Exemples de configuration pour ton installation

Ce document contient des exemples de configuration **prêts à l'emploi** pour tes pièces spécifiques.

## 📋 Table des matières

- [Lumières simples](#lumières-simples)
- [Lumières avec capteurs](#lumières-avec-capteurs)
- [Chauffage simple](#chauffage-simple)
- [Entités globales](#entités-globales)

---

## 🔧 Entités globales

À configurer **une seule fois** dans **Configuration → Intégrations → Smart Room Manager → Configurer → Paramètres globaux** :

| Paramètre | Entité | Commentaire |
|-----------|--------|-------------|
| Entité mode invité | (vide) | Pas encore configuré |
| Entité mode vacances | (vide) | Pas encore configuré |
| Entité alarme | `alarm_control_panel.maison` | ✅ Obligatoire |
| Capteur de saison | `calendar.ete_hiver` | ✅ Obligatoire |

---

## 💡 Lumières simples

### Couloir RDC

**Caractéristiques** :
- Timer : 5 minutes
- Allumage manuel
- Pas de capteur de présence

**Configuration Smart Room Manager** :

```yaml
Nom de la pièce: "Couloir RDC"

# Étape Capteurs
Capteurs de présence: (vide)
Capteurs porte/fenêtre: (vide)
Capteur de luminosité: (vide)
Capteur de température: (vide)
Capteur d'humidité: (vide)

# Étape Actionneurs
Lumières:
  - light.x8r_ndeg2_relais_6
Entité climat: (vide)
Interrupteurs de chauffage: (vide)

# Étape Configuration lumières
Seuil de luminosité: 1000 lx  # Très élevé pour désactiver l'auto
Délai d'extinction: 300 s  # 5 minutes
Mode nuit: ❌ Non
Luminosité de nuit: 20%
Luminosité de jour: 100%

# Étape Configuration chauffage
(ignorer - pas de chauffage)

# Étape Horaires
Début du matin: 07:00
Début de journée: 09:00
Début de soirée: 18:00
Début de nuit: 22:00
```

**Automation à désactiver** : `Timer - couloirs, Sdb, WC, grenier, cave, abris, entrée extérieure`

---

### WC RDC

**Caractéristiques** :
- Timer : 5 minutes
- Même configuration que couloir

**Configuration** :

```yaml
Nom: "WC RDC"
Lumières: light.x8r_ndeg0_relais_7
Délai: 300 s
(reste identique à Couloir RDC)
```

---

### Salle d'eau RDC (lumière uniquement)

**Caractéristiques** :
- Timer : 15 minutes
- Lumière : `light.x8r_ndeg0_relais_5`
- Chauffage géré séparément (blueprint avec SO)

**Configuration** :

```yaml
Nom: "Salle d'eau RDC"

# Capteurs
Capteurs de présence: (vide)
Capteurs porte/fenêtre:
  - binary_sensor.x24d_15_fenetre_sdb_rdc
Capteur de luminosité: (vide)
Capteur de température: (vide)
Capteur d'humidité: (vide)

# Actionneurs
Lumières:
  - light.x8r_ndeg0_relais_5
Entité climat: (vide)  # ⚠️ GARDER BLUEPRINT POUR LE CHAUFFAGE

# Lumières
Seuil de luminosité: 1000 lx
Délai d'extinction: 900 s  # 15 minutes
Mode nuit: ✅ Oui
Luminosité de nuit: 30%
Luminosité de jour: 100%

# Chauffage
(ignorer - géré par blueprint)
```

**Automation à désactiver** : `Timer - couloirs...` (partie salle d'eau uniquement)
**Automation à GARDER** : `Chauffage - Salle d'eau` (blueprint avec SO)

---

### Salle de bain Et.1 (lumière uniquement)

**Configuration** :

```yaml
Nom: "Salle de bain Et.1"

# Capteurs
Capteurs porte/fenêtre:
  - binary_sensor.x24d_16_fenetre_sdb_et1

# Actionneurs
Lumières:
  - light.x8r_ndeg1_relais_6

# Lumières
Délai d'extinction: 900 s  # 15 minutes
Mode nuit: ✅ Oui
Luminosité de nuit: 30%

# Chauffage
(ignorer - géré par blueprint)
```

---

### Cave

**Configuration** :

```yaml
Nom: "Cave"
Lumières: light.x8r_ndeg2_relais_4
Délai: 900 s  # 15 minutes
```

---

### Grenier

**Configuration** :

```yaml
Nom: "Grenier"
Lumières: light.x8r_ndeg2_relais_8
Délai: 900 s  # 15 minutes
```

---

### Abris

**Configuration** :

```yaml
Nom: "Abris"
Lumières: switch.lumiere_abris
Délai: 900 s  # 15 minutes
```

---

## 🚪 Lumières avec capteurs

### Entrée intérieure

**Caractéristiques** :
- Capteur : Porte RDC
- Timer : 5 minutes
- Allumage automatique à l'ouverture

**Configuration** :

```yaml
Nom: "Entrée intérieure"

# Capteurs
Capteurs de présence:
  - binary_sensor.x24d_17_porte_rdc  # Porte = présence
Capteurs porte/fenêtre: (vide)  # On met la porte en "présence" pour déclencher l'allumage
Capteur de luminosité: (vide)
Capteur de température: (vide)
Capteur d'humidité: (vide)

# Actionneurs
Lumières:
  - light.x8r_ndeg2_relais_5

# Lumières
Seuil de luminosité: 1000 lx  # Désactive l'auto lux
Délai d'extinction: 300 s  # 5 minutes
Mode nuit: ✅ Oui
Luminosité de nuit: 100%  # Pas de variation
Luminosité de jour: 100%

# Horaires
(par défaut)
```

**Automation à désactiver** : `Entrée intérieure - Ouverture de la porte`

**Comportement attendu** :
- Porte s'ouvre → Lumière ON
- 5 minutes après fermeture → Lumière OFF
- Fonctionne jour ET nuit (seuil lux élevé)

---

### Entrée extérieure

**Caractéristiques** :
- Capteur : Porte RDC
- Timer : géré par IPX (pas de timer dans Smart Room Manager)
- Allumage uniquement la nuit

**Configuration** :

```yaml
Nom: "Entrée extérieure"

# Capteurs
Capteurs de présence:
  - binary_sensor.x24d_17_porte_rdc
Capteur de luminosité: (vide)

# Actionneurs
Lumières:
  - light.x8r_ndeg2_relais_3

# Lumières
Seuil de luminosité: 50 lx  # Allume seulement la nuit
Délai d'extinction: 600 s  # 10 minutes (timer IPX)
Mode nuit: ✅ Oui
Luminosité de nuit: 100%
Luminosité de jour: 100%

# Horaires
Début de nuit: 22:00  # Période "nuit" où la lumière s'allume
Début du matin: 07:00
```

**Automation à désactiver** : `Lumière de l'entrée extérieure`

---

## 🌡️ Chauffage simple (sans Solar Optimizer)

### Salon (Poêle)

**Caractéristiques** :
- Poêle à granulés
- 5 capteurs de fenêtres/baies
- Gestion alarme (confort/away)
- Pas de Solar Optimizer

**Configuration** :

```yaml
Nom: "Salon"

# Capteurs
Capteurs de présence: (vide)  # Pas de capteur de présence pour le chauffage
Capteurs porte/fenêtre:
  - binary_sensor.x24d_08_baie_vitree_2m_salon
  - binary_sensor.x24d_07_baie_vitree_3m_salon
  - binary_sensor.x24d_12_fenetre_pano_salon
  - binary_sensor.x24d_09_baie_vitree_cuisine
  - binary_sensor.x24d_10_fenetre_cuisine
Capteur de luminosité: sensor.xthl_1_luminance  # Pour les lumières
Capteur de température: (vide)  # Le poêle a son capteur interne
Capteur d'humidité: (vide)

# Actionneurs
Lumières:
  - light.xdimmer_ndeg0_sortie_1
  - light.xdimmer_ndeg0_sortie_2
  - light.xdimmer_ndeg0_sortie_3
Entité climat: climate.salon_poele
Interrupteurs de chauffage: (vide)

# Lumières
Seuil de luminosité: 50 lx
Délai d'extinction: 300 s  # 5 minutes
Mode nuit: ✅ Oui
Luminosité de nuit: 20%
Luminosité de jour: 100%

# Chauffage
Température confort: 19.5°C
Température éco: 18.0°C
Température nuit: 17.0°C
Température absence: 16.0°C
Température hors-gel: 7.0°C
Présence requise pour chauffer: ❌ Non
Vérifier l'ouverture des fenêtres: ✅ Oui
Délai d'inoccupation: 1800 s  # 30 minutes

# Horaires
Début du matin: 07:00
Début de journée: 09:00
Début de soirée: 18:00
Début de nuit: 22:00
```

**Paramètres globaux requis** :
- Entité alarme : `alarm_control_panel.maison`
- Capteur de saison : `calendar.ete_hiver`

**Automation à désactiver** : `Chauffage - Salon (poêle)`

**Comportement attendu** :

| Condition | Mode | Consigne |
|-----------|------|----------|
| Alarme désarmée | Confort | 19.5°C |
| Alarme armée | Away | 16°C |
| Été (calendar.ete_hiver = on) | OFF | - |
| Fenêtre ouverte | Pause | - |
| Nuit (22h-7h) | Nuit | 17°C |

---

## ⚠️ Pièces avec Solar Optimizer (À NE PAS migrer pour l'instant)

Ces pièces utilisent Solar Optimizer et doivent **GARDER leurs blueprints actuels** :

### Suite parentale
- Blueprint : `Chauffage - Suite parentale`
- SO : `switch.solar_optimizer_chauffage_suite_parentale`
- ⏳ Attendre mise à jour Smart Room Manager

### Chambre d'amis
- Blueprint : `Chauffage - Chambre d'amis`
- SO : `switch.solar_optimizer_chauffage_chambre_d_amis`
- ⏳ Attendre mise à jour

### Salle d'eau RDC (chauffage)
- Blueprint : `Chauffage - Salle d'eau`
- SO : `switch.solar_optimizer_seche_serviette_salle_d_eau`
- ⏳ Attendre mise à jour

### Salle de bain Et.1 (chauffage)
- Blueprint : `Chauffage - Salle de bain`
- SO : `switch.solar_optimizer_seche_serviette_salle_de_bain`
- ⏳ Attendre mise à jour

### Chambre Thomas (climatisation)
- Blueprint : `Climatisation Thomas`
- SO : `switch.solar_optimizer_climatisation_thomas`
- ⏳ Attendre mise à jour

### Chambre Livia (climatisation)
- Blueprint : `Climatisation Livia`
- SO : `switch.solar_optimizer_climatisation_livia`
- ⏳ Attendre mise à jour

---

## 🔄 Ordre de migration recommandé

### Phase 1 : Lumières simples (semaine 1)

1. ✅ WC RDC
2. ✅ Couloir RDC
3. ✅ Cave
4. ✅ Grenier

**Test 3-4 jours**

### Phase 2 : Lumières simples (suite) (semaine 2)

5. ✅ Abris
6. ✅ Salle d'eau RDC (lumière uniquement)
7. ✅ Salle de bain Et.1 (lumière uniquement)

**Test 3-4 jours**

### Phase 3 : Lumières avec capteurs (semaine 3)

8. ✅ Entrée intérieure
9. ✅ Entrée extérieure

**Test 4-5 jours**

### Phase 4 : Chauffage simple (semaines 4-5)

10. ✅ Salon (poêle + lumières)

**Test 2 semaines** (important pour le chauffage)

### Phase 5 : Attendre mise à jour Solar Optimizer

11. ⏳ Suite parentale
12. ⏳ Chambre d'amis
13. ⏳ Salle d'eau (chauffage)
14. ⏳ Salle de bain (chauffage)
15. ⏳ Chambre Thomas
16. ⏳ Chambre Livia

---

## 📝 Notes importantes

### Automatisations à NE JAMAIS migrer

❌ **Garder en YAML** (trop spécifiques) :
- Tous les volets (VR)
- VMC grande vitesse
- Prises cuisine
- Cinéma + volet
- Store anti-vent
- Caméras Frigate
- Alarme fumée
- Pompe inondation
- Sonnette
- Piscine (filtration)

### Configuration VMC

La VMC est liée aux lumières mais doit **rester en automation YAML** :
```yaml
# Automation à GARDER
- alias: VMC - Grande vitesse avec extinction automatique
  trigger:
    - entity_id:
      - light.x8r_ndeg0_relais_5  # SdB RDC
      - light.x8r_ndeg0_relais_2  # SdB autre
      - light.x8r_ndeg0_relais_8  # Salle d'eau
      - light.x8r_ndeg1_relais_6  # SdB Et.1
```

→ Cette automation fonctionne **en parallèle** de Smart Room Manager sans conflit.

---

## 🆘 Support

En cas de problème :

1. **Vérifier les logs** : Configuration → Logs → Filtrer "smart_room_manager"
2. **Vérifier les entités** : Outils développeur → États
3. **Désactiver temporairement** : `switch.smart_room_[nom]_automation` → OFF
4. **Réactiver l'ancienne automation** si problème

---

**Version** : 0.1.0
**Dernière mise à jour** : 2025-01-13
