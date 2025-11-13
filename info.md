# Smart Room Manager

**Version 0.1.0** - Gestion intelligente de pièces pour Home Assistant

## ⚡ Fonctionnalités principales

### Lumières intelligentes
- Contrôle automatique selon présence, luminosité et horaires
- Mode nuit avec luminosité réduite
- Extinction automatique avec délai configurable
- Respect des commandes manuelles

### Chauffage intelligent
- Consignes variables selon contexte (confort, éco, nuit, absence)
- Arrêt automatique si fenêtre ouverte
- Intégration alarme (mode away)
- Gestion saisonnière (été/hiver)
- **Compatible Solar Optimizer en mode prioritaire** ⚡

### Configuration UI complète
- Aucun YAML requis
- Ajout/modification de pièces via l'interface
- Configuration des seuils et délais par pièce
- Paramètres globaux (alarme, saison, modes)

## 📦 Installation

### Via HACS (recommandé)
1. HACS → Intégrations
2. Menu ︙ → Dépôts personnalisés
3. Ajoutez l'URL du repository
4. Recherchez "Smart Room Manager"
5. Installez et redémarrez Home Assistant

### Installation manuelle
1. Copiez `custom_components/smart_room_manager` dans votre dossier config
2. Redémarrez Home Assistant
3. Configuration → Intégrations → Ajouter Smart Room Manager

## 📚 Documentation

- [Guide complet](https://github.com/GevaudanBeast/HA-SMART/blob/main/README.md)
- [Guide de migration YAML → Smart Room Manager](https://github.com/GevaudanBeast/HA-SMART/blob/main/MIGRATION_GUIDE.md)
- [Exemples de configuration](https://github.com/GevaudanBeast/HA-SMART/blob/main/CONFIGURATION_EXAMPLES.md)
- [Guide Solar Optimizer](https://github.com/GevaudanBeast/HA-SMART/blob/main/SOLAR_OPTIMIZER.md)

## 🔗 Liens

- [GitHub Repository](https://github.com/GevaudanBeast/HA-SMART)
- [Issues](https://github.com/GevaudanBeast/HA-SMART/issues)
- [Changelog](https://github.com/GevaudanBeast/HA-SMART/blob/main/CHANGELOG.md)

## ⚙️ Compatibilité

- Home Assistant 2023.1+
- IPX800 V5 (X4FP, X8R, XDimmer, X4VR, X24D)
- Solar Optimizer
- Alarmo
- Calendriers Home Assistant
