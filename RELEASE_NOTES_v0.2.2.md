# Smart Room Manager v0.2.2 - Configuration Optionnelle

## 🎯 Améliorations

### Configuration Optionnelle Complète

Cette version améliore la gestion des champs optionnels dans la configuration :

- **Champs facultatifs vraiment facultatifs** : Les capteurs de température/humidité et autres équipements ne sont plus sauvegardés avec une valeur `None` lorsqu'ils ne sont pas configurés
- **Configuration plus propre** : Seuls les champs réellement configurés sont enregistrés
- **Flexibilité maximale** : Possibilité de créer des pièces minimalistes (juste un nom) jusqu'à des pièces ultra-équipées

### Champs concernés

Les champs suivants ne sont maintenant sauvegardés **que s'ils sont configurés** :
- `temperature_sensor` - Capteur de température
- `humidity_sensor` - Capteur d'humidité
- `climate_entity` - Entité de climatisation/chauffage
- `climate_bypass_switch` - Interrupteur de bypass (Solar Optimizer, contrôle manuel, etc.)

## 📋 Notes de compatibilité

- ✅ **Aucun changement breaking** : Les configurations existantes continuent de fonctionner
- ✅ **Mise à jour automatique** : Les anciennes configurations avec valeurs `None` sont gérées correctement
- ✅ **Rétro-compatible** : Compatible avec v0.2.0 et v0.2.1

## 🔧 Installation

### Via HACS (recommandé)

1. Téléchargez `smart_room_manager.zip` depuis cette release
2. Dans HACS, ajoutez le dépôt custom : `https://github.com/GevaudanBeast/HA-SMART`
3. Installez "Smart Room Manager"
4. Redémarrez Home Assistant

### Manuelle

1. Téléchargez `smart_room_manager.zip`
2. Extrayez dans `/config/custom_components/smart_room_manager/`
3. Redémarrez Home Assistant

## 📚 Pour plus d'informations

- [README](README.md) - Documentation complète
- [CHANGELOG](CHANGELOG.md) - Historique des changements
- [Release Notes v0.2.0](RELEASE_NOTES_v0.2.0.md) - Fonctionnalités principales de la v0.2.0

---

**Version précédente** : [v0.2.1](https://github.com/GevaudanBeast/HA-SMART/releases/tag/v0.2.1)
