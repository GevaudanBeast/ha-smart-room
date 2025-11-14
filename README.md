# Smart Room Manager - Home Assistant Integration

**Version 0.2.0** - 🎯 Architecture simplifiée et optimisée !

Une intégration Home Assistant complète pour gérer intelligemment chaque pièce de votre maison en automatisant les lumières et le chauffage de manière simple et efficace.

## 🆕 Nouveautés v0.2.0

### Architecture Simplifiée
- 🔄 **Plus de capteurs de présence** : L'alarme détermine la présence (armed_away = absent)
- 💡 **Contrôle manuel des lumières** : Timer auto-off uniquement pour couloirs/salles de bain
- 🎛️ **Bypass générique** : Un seul switch pour désactiver le chauffage (Solar Optimizer, manuel, etc.)
- 📊 **4 modes au lieu de 6** : Confort, Eco, Nuit, Hors-gel (suppression modes invité/vacances)
- ⏰ **Horaires simplifiés** : Période nuit + plages horaires confort configurables

### Nouvelles Fonctionnalités
- 🏠 **Types de pièces** :
  - **Normal** (chambres) : Pas de timer lumière
  - **Couloir** : Auto-off lumières après 5 min (configurable)
  - **Salle de bain** : Timer 15 min + lumière pilote chauffage (ON=confort, OFF=eco)
- 🌡️ **Support été/hiver** : Températures cool/heat séparées avec calendrier
- 🔧 **Auto-détection X4FP** : Détection automatique X4FP vs thermostat
- 🎨 **Icônes personnalisables** : Choisissez l'icône de chaque pièce

## 📋 Fonctionnalités

### Gestion intelligente des lumières (v0.2.0 simplifié)
- ✅ **Contrôle manuel** : Vous contrôlez vos lumières manuellement ou via automatisations
- ✅ **Timer auto-off** : Uniquement pour couloirs et salles de bain (configurable)
- ✅ **Salle de bain spécial** : Lumière ON = chauffage confort, OFF = chauffage eco

### Gestion intelligente du chauffage
- ✅ **4 modes adaptés** :
  - **Confort** : Présence + plages horaires configurables
  - **Eco** : Mode par défaut hors plages confort
  - **Nuit** : Période nocturne (configurable)
  - **Hors-gel** : Alarme armed_away ou fenêtre ouverte
- ✅ **Auto-détection X4FP/Thermostat** : Contrôle automatique selon type
- ✅ **Support été/hiver** : Températures heat/cool via calendrier
- ✅ **Bypass générique** : Switch pour désactiver contrôle (Solar Optimizer, etc.)
- ✅ **Fenêtres ouvertes** : Passage automatique en hors-gel

### Détection de présence simplifiée
- 🚨 **Via alarme** : armed_away = absent, sinon présent
- ⏰ **Plages horaires** : Mode confort sur plages configurables si présent
- 🌙 **Mode nuit** : Basé sur heure de début nuit

### Configuration UI complète
- ⚙️ Ajout/modification/suppression de pièces via l'interface
- 📊 Configuration des types de pièce et comportements
- 🕐 Plages horaires confort multiples (format HH:MM-HH:MM,HH:MM-HH:MM)
- 🔄 Recharge automatique à chaque modification

## 🚀 Installation

### Méthode 1 : HACS (recommandé)
1. Ouvrez HACS dans Home Assistant
2. Allez dans "Intégrations"
3. Cliquez sur les 3 points en haut à droite > "Dépôts personnalisés"
4. Ajoutez l'URL : `https://github.com/GevaudanBeast/HA-SMART`
5. Recherchez "Smart Room Manager" et installez
6. Redémarrez Home Assistant

### Méthode 2 : Manuelle
1. Téléchargez la dernière release depuis [GitHub Releases](https://github.com/GevaudanBeast/HA-SMART/releases)
2. Extrayez `smart_room_manager.zip` dans votre dossier `config/custom_components/`
3. Redémarrez Home Assistant

## ⚙️ Configuration

### Configuration initiale

1. Allez dans **Paramètres** > **Appareils et services**
2. Cliquez sur **+ Ajouter une intégration**
3. Recherchez **Smart Room Manager**
4. Configurez les paramètres globaux (optionnels) :
   - **Alarme** : Détecte présence (armed_away = absent)
   - **Calendrier été** : Bascule heat/cool pour climatisation

### Ajout d'une pièce

1. Ouvrez l'intégration **Smart Room Manager**
2. Cliquez sur **Configurer** > **Ajouter une pièce**
3. Suivez l'assistant de configuration :

#### Étape 1 : Informations de base
- **Nom** : Nom de la pièce (ex: "Salon", "Chambre")
- **Type** :
  - **Normal** : Chambres, bureau (pas de timer lumière)
  - **Couloir** : Auto-off lumières après 5 min
  - **Salle de bain** : Timer 15 min + lumière contrôle chauffage
- **Icône** : Icône personnalisée (ex: mdi:bed, mdi:desk)

#### Étape 2 : Capteurs (tous optionnels)
- **Capteurs fenêtre/porte** : Pour détecter ouverture → hors-gel
- **Capteur température** : Pour info seulement (affiché dans attributs)
- **Capteur humidité** : Pour info seulement

#### Étape 3 : Actionneurs
- **Lumières** : Entités light.* ou switch.* (contrôle manuel + timer si type couloir/SdB)
- **Entité climat** : Thermostat ou X4FP (auto-détection)
- **Switch bypass** : Désactive contrôle chauffage (Solar Optimizer, manuel, etc.)

#### Étape 4 : Configuration lumières
- Affiché uniquement si type = Couloir ou Salle de bain
- **Timeout** : Délai avant extinction automatique (60-1800s)

#### Étape 5 : Configuration chauffage
**Températures hiver (heat)** :
- **Confort** : Température quand présent + plage horaire confort (défaut: 20°C)
- **Eco** : Température par défaut hors plages confort (défaut: 18°C)
- **Nuit** : Température période nocturne (défaut: 17°C)
- **Hors-gel** : Température si alarme armed_away ou fenêtre ouverte (défaut: 12°C)

**Températures été (cool)** :
- **Confort** : Température clim si été actif (défaut: 24°C)
- **Eco** : Température clim eco été (défaut: 26°C)

**Options** :
- **Vérifier fenêtres** : Activer hors-gel si fenêtre ouverte

#### Étape 6 : Horaires
- **Début nuit** : Heure de début période nuit (ex: 22:00)
- **Plages confort** : Format `HH:MM-HH:MM,HH:MM-HH:MM`
  - Exemple : `07:00-09:00,18:00-22:00` (matin + soirée)
  - Vide = jamais en mode confort (toujours eco)

## 📊 Entités créées

Pour chaque pièce configurée :

### Sensors
- **sensor.smart_room_[nom]_state** : Mode actuel
  - Valeurs : `comfort`, `eco`, `night`, `frost_protection`
  - Attributs : occupation, fenêtres, température, humidité, état lumières, état chauffage

### Binary Sensors
- **binary_sensor.smart_room_[nom]_occupied** : Occupation (basée sur alarme)
- **binary_sensor.smart_room_[nom]_light_needed** : Indique si lumières nécessaires (toujours False en v0.2.0 - contrôle manuel)

### Switches
- **switch.smart_room_[nom]_automation** : Active/désactive l'automatisation

## 🎯 Exemples d'utilisation

### Scénario 1 : Chambre simple
**Configuration** :
- Type : Normal (pas de timer)
- Entité climat : climate.chambre
- Températures : Confort 20°C, Eco 18°C, Nuit 17°C
- Horaires nuit : 22:00
- Plages confort : `07:00-09:00` (matin uniquement)

**Comportement** :
- 7h-9h + présent (alarme désarmée) → Chauffage 20°C (confort)
- 9h-22h + présent → Chauffage 18°C (eco)
- 22h-7h → Chauffage 17°C (nuit)
- Alarme armed_away → Chauffage 12°C (hors-gel)

### Scénario 2 : Salle de bain
**Configuration** :
- Type : Salle de bain
- Lumières : light.salle_bain
- Timer lumière : 900s (15 min)
- Climat : climate.radiateur_sdb
- Températures : Confort 22°C, Eco 17°C

**Comportement** :
- Lumière allumée manuellement → Chauffage 22°C (confort)
- Lumière éteinte → Chauffage 17°C (eco)
- Lumière ON > 15 min → Extinction automatique
- Extinction → Retour chauffage 17°C

### Scénario 3 : Salon avec bypass
**Configuration** :
- Type : Normal
- Climat : climate.salon
- Bypass : switch.solar_optimizer_salon
- Plages confort : `18:00-23:00`

**Comportement** :
- Bypass ON (Solar Optimizer actif) → Smart Room Manager ne contrôle pas
- Bypass OFF + 18h-23h + présent → Chauffage confort
- Bypass OFF + hors plage → Chauffage eco

### Scénario 4 : Bureau avec été/hiver
**Configuration** :
- Calendrier été : calendar.ete (ON en été)
- Températures heat : Confort 20°C, Eco 18°C
- Températures cool : Confort 24°C, Eco 26°C

**Comportement** :
- Hiver (calendrier OFF) → hvac_mode: heat, température selon mode
- Été (calendrier ON) → hvac_mode: cool, température selon mode

## 🔧 Intégration avec Solar Optimizer

✅ **Compatible via bypass générique !**

**Configuration** :
1. Ajoutez le switch Solar Optimizer dans "Switch bypass"
2. Quand SO chauffe (ON) → Smart Room Manager se met en retrait
3. Quand SO s'arrête (OFF) → Smart Room Manager reprend le contrôle

**Avantages** :
- ⚡ Priorité à Solar Optimizer (énergie gratuite)
- 🔄 Reprise automatique du contrôle
- 📋 Configuration simple (un seul switch)

## 🐛 Dépannage

### Le chauffage ne change pas
- Vérifiez que le switch d'automatisation est activé
- Vérifiez que le bypass n'est pas actif
- Consultez `sensor.smart_room_*_state` pour voir le mode actuel
- Logs : `Paramètres` > `Système` > `Logs` > Filtrer "smart_room_manager"

### Les lumières ne s'éteignent pas (couloir/SdB)
- Vérifiez le type de pièce (Normal n'a pas de timer)
- Vérifiez le timeout configuré
- Les lumières doivent être ON depuis > timeout

### L'auto-détection X4FP ne fonctionne pas
- Vérifiez que l'entité climate a les preset_modes: comfort, eco, away
- Si thermostat classique : contrôle par hvac_mode + température

## 📝 Logs et débogage

Configuration détaillée dans `configuration.yaml` :

```yaml
logger:
  default: info
  logs:
    custom_components.smart_room_manager: debug
```

## 🔄 Migration depuis v0.1.0

**Changements majeurs** :
- ❌ Capteurs de présence supprimés (utiliser alarme)
- ❌ Capteurs luminosité intérieurs supprimés
- ❌ Modes guest/vacation supprimés
- ✅ Types de pièces ajoutés
- ✅ Plages confort multiples au lieu de 4 périodes
- ✅ Bypass générique au lieu de Solar Optimizer spécifique

**Action requise** : Reconfigurer les pièces via UI (anciennes configs incompatibles)

## 🤝 Contribution

Les contributions sont bienvenues !
- 🐛 [Signaler un bug](https://github.com/GevaudanBeast/HA-SMART/issues)
- 💡 Proposer des améliorations
- 🔧 Soumettre une pull request

## 📄 Licence

Ce projet est sous licence MIT.

## 🙏 Remerciements

Développé avec ❤️ pour la communauté Home Assistant.

## 📞 Support

- 📖 [Documentation complète](https://github.com/GevaudanBeast/HA-SMART)
- 🐛 [Issues GitHub](https://github.com/GevaudanBeast/HA-SMART/issues)
- 💬 [Discussions](https://github.com/GevaudanBeast/HA-SMART/discussions)

---

**Version** : 0.2.0
**Auteur** : GevaudanBeast
**Compatibilité** : Home Assistant 2023.1+
