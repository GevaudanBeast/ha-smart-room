# Smart Room Manager - Home Assistant Integration

**Version 1.1.0** - ⚡ **Nouveau** : Support de Solar Optimizer !

Une intégration Home Assistant complète pour gérer intelligemment chaque pièce de votre maison en automatisant les lumières et le chauffage selon la présence, la luminosité, les horaires et les modes globaux.

## 🆕 Nouveautés v1.1.0

- ⚡ **Solar Optimizer** : Compatibilité totale avec Solar Optimizer en mode prioritaire
- 🔄 Gestion automatique du switch Solar Optimizer par pièce
- 📝 Guide de migration depuis les blueprints HVAC
- 📖 Documentation complète Solar Optimizer

## 📋 Fonctionnalités

### Gestion intelligente des lumières
- ✅ Allumage automatique selon présence, luminosité et horaires
- ✅ Mode nuit avec luminosité réduite
- ✅ Extinction automatique avec délai configurable
- ✅ Respect des commandes manuelles (pas de "lutte" contre l'utilisateur)

### Gestion intelligente du chauffage
- ✅ Consignes de température variables selon :
  - Plages horaires (matin, journée, soirée, nuit)
  - Présence dans la pièce
  - Modes globaux (vacances, invité, alarme)
- ✅ Arrêt automatique si fenêtre ouverte
- ✅ Mode hors-gel en cas d'absence prolongée
- ✅ Délai d'inoccupation configurable avant réduction de consigne

### Modes globaux
- 🏠 **Mode Confort** : Températures confortables quand la pièce est occupée
- 🌱 **Mode Éco** : Températures réduites quand la pièce est inoccupée
- 🌙 **Mode Nuit** : Températures et luminosités adaptées la nuit
- 🏖️ **Mode Vacances** : Mode hors-gel, automatisations minimales
- 👥 **Mode Invité** : Comportements adaptés à la présence d'invités
- 🚨 **Mode Alarme** : Automatisations réduites quand l'alarme est armée

### Configuration UI complète
- ⚙️ Ajout/modification/suppression de pièces via l'interface
- 📊 Configuration des seuils, délais et températures par pièce
- 🕐 Programmation des plages horaires
- 🔄 Recharge automatique à chaque modification

## 🚀 Installation

### Méthode 1 : HACS (recommandé)
1. Ouvrez HACS dans Home Assistant
2. Allez dans "Intégrations"
3. Cliquez sur les 3 points en haut à droite > "Dépôts personnalisés"
4. Ajoutez l'URL de ce repository
5. Recherchez "Smart Room Manager" et installez

### Méthode 2 : Manuelle
1. Copiez le dossier `custom_components/smart_room_manager` dans votre dossier `config/custom_components/`
2. Redémarrez Home Assistant

## ⚙️ Configuration

### Configuration initiale

1. Allez dans **Configuration** > **Intégrations**
2. Cliquez sur **+ Ajouter une intégration**
3. Recherchez **Smart Room Manager**
4. Configurez les paramètres globaux (optionnels) :
   - Entité mode invité
   - Entité mode vacances
   - Entité alarme
   - Capteur de saison

### Ajout d'une pièce

1. Ouvrez l'intégration **Smart Room Manager**
2. Cliquez sur **Configurer**
3. Sélectionnez **Ajouter une pièce**
4. Suivez l'assistant de configuration :

#### Étape 1 : Nom de la pièce
- Donnez un nom à votre pièce (ex: "Salon", "Chambre", "Bureau")

#### Étape 2 : Capteurs
- **Capteurs de présence** : Détecteurs de mouvement (binary_sensor)
- **Capteurs de porte/fenêtre** : Détecteurs d'ouverture (binary_sensor)
- **Capteur de luminosité** : Mesure en lux (sensor)
- **Capteur de température** : Température actuelle (sensor)
- **Capteur d'humidité** : Humidité (sensor) - optionnel

#### Étape 3 : Actionneurs
- **Lumières** : Entités light.* ou switch.* à contrôler
- **Entité climat** : Thermostat ou système de chauffage (climate.*)
- **Interrupteurs de chauffage** : Switches pilotant le chauffage
- **⚡ Switch Solar Optimizer** : Switch d'action Solar Optimizer (optionnel - voir [SOLAR_OPTIMIZER.md](SOLAR_OPTIMIZER.md))

#### Étape 4 : Configuration des lumières
- **Seuil de luminosité** : En dessous de cette valeur (lux), les lumières s'allument
- **Délai d'extinction** : Temps avant extinction après fin de présence
- **Mode nuit activé** : Luminosité réduite la nuit
- **Luminosité de nuit** : Pourcentage de luminosité la nuit (1-100%)
- **Luminosité de jour** : Pourcentage de luminosité le jour (1-100%)

#### Étape 5 : Configuration du chauffage
- **Température confort** : Consigne quand la pièce est occupée
- **Température éco** : Consigne quand la pièce est inoccupée
- **Température nuit** : Consigne pendant la nuit
- **Température absence** : Consigne en mode absence/alarme
- **Température hors-gel** : Consigne en mode vacances
- **Présence requise** : Exiger la présence pour chauffer en mode confort
- **Vérifier les fenêtres** : Couper le chauffage si fenêtre ouverte
- **Délai d'inoccupation** : Temps avant passage en mode éco

#### Étape 6 : Horaires
- **Début du matin** : Heure de début de la période matinale
- **Début de journée** : Heure de début de la période de journée
- **Début de soirée** : Heure de début de la soirée
- **Début de nuit** : Heure de début de la nuit

## 📊 Entités créées

Pour chaque pièce configurée, l'intégration crée automatiquement :

### Sensors
- **sensor.smart_room_[nom]_state** : État général de la pièce
  - Valeur : Mode actuel (comfort, eco, night, away, frost_protection)
  - Attributs : occupation, luminosité, température, humidité, état lumières, état chauffage

### Binary Sensors
- **binary_sensor.smart_room_[nom]_occupied** : Occupation de la pièce
- **binary_sensor.smart_room_[nom]_light_needed** : Indique si les lumières doivent être allumées

### Switches
- **switch.smart_room_[nom]_automation** : Active/désactive l'automatisation pour cette pièce

## 🎯 Exemples d'utilisation

### Scénario 1 : Salon avec lumières et chauffage
- **Capteurs** : 1 détecteur de présence, capteur de luminosité, capteur de température
- **Actionneurs** : 3 lumières, 1 radiateur (climate)
- **Configuration** :
  - Seuil luminosité : 50 lux
  - Extinction après : 5 minutes
  - Confort : 20°C, Éco : 18°C, Nuit : 17°C

**Comportement** :
- Présence détectée + < 50 lux → Lumières ON
- Pas de présence pendant 5 min → Lumières OFF
- Pièce occupée → Chauffage 20°C
- Pièce inoccupée > 30 min → Chauffage 18°C

### Scénario 2 : Chambre avec mode nuit
- **Configuration** :
  - Mode nuit : Activé
  - Luminosité nuit : 20%
  - Luminosité jour : 100%
  - Nuit : 22h00 - 07h00

**Comportement** :
- Présence la nuit (22h-7h) → Lumières 20%
- Présence le jour → Lumières 100%
- Période nuit → Température 17°C

### Scénario 3 : Bureau avec présence obligatoire
- **Configuration** :
  - Présence requise pour chauffer : Activé
  - Vérifier fenêtres : Activé

**Comportement** :
- Présence → Chauffage mode confort
- Absence immédiate → Chauffage mode éco
- Fenêtre ouverte → Chauffage OFF

## 🔧 Automatisations avancées

Vous pouvez créer des automatisations basées sur les entités de l'intégration :

```yaml
# Exemple : Notification si fenêtre ouverte trop longtemps en hiver
automation:
  - alias: "Alerte fenêtre ouverte"
    trigger:
      - platform: state
        entity_id: sensor.smart_room_salon_state
        attribute: windows_open
        to: true
        for:
          minutes: 10
    condition:
      - condition: numeric_state
        entity_id: sensor.temperature_exterieure
        below: 10
    action:
      - service: notify.mobile_app
        data:
          message: "La fenêtre du salon est ouverte depuis 10 minutes et il fait froid dehors !"
```

## 📈 Intégration avec d'autres systèmes

### Alarmo
Configurez l'entité alarme dans les paramètres globaux pour adapter automatiquement les comportements quand l'alarme est armée.

### Solar Optimizer

✅ **Compatible dès maintenant !**

Smart Room Manager v1.1.0 supporte nativement Solar Optimizer en mode **prioritaire** :
- ⚡ Quand Solar Optimizer chauffe → Smart Room Manager se met en retrait
- 🔄 Quand Solar Optimizer s'arrête → Smart Room Manager reprend le contrôle
- 📋 Configuration simple : juste sélectionner le switch SO par pièce

**Documentation complète** : Voir [SOLAR_OPTIMIZER.md](SOLAR_OPTIMIZER.md)

### IPX800
Compatible avec tous les actionneurs gérés par IPX800 (X4FP, relais, etc.).

## 🐛 Dépannage

### Les lumières ne s'allument pas
- Vérifiez que le switch d'automatisation est activé
- Vérifiez les seuils de luminosité
- Consultez les logs : `Configuration` > `Logs` > Filtrer "smart_room_manager"

### Le chauffage ne change pas de consigne
- Vérifiez la compatibilité de votre entité climate
- Assurez-vous que les températures sont correctement configurées
- Vérifiez si une fenêtre est détectée ouverte

### L'intégration ne se charge pas
- Vérifiez les logs Home Assistant
- Redémarrez Home Assistant
- Vérifiez que tous les fichiers sont présents dans `custom_components/smart_room_manager/`

## 📝 Logs et débogage

Pour activer les logs détaillés, ajoutez dans `configuration.yaml` :

```yaml
logger:
  default: info
  logs:
    custom_components.smart_room_manager: debug
```

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Ouvrir une issue pour signaler un bug
- Proposer des améliorations
- Soumettre une pull request

## 📄 Licence

Ce projet est sous licence MIT.

## 🙏 Remerciements

Développé avec ❤️ pour la communauté Home Assistant.

## 📞 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- Consultez la documentation Home Assistant

---

**Version** : 1.0.0
**Auteur** : GevaudanBeast
**Compatibilité** : Home Assistant 2023.1+
