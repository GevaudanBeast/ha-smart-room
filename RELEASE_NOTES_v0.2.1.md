# Smart Room Manager v0.2.1 - Correctif Critique 🔧

**Date de release** : 14 janvier 2025

## 🐛 Correctif Critique

Cette version corrige un **bug bloquant** qui empêchait l'intégration de se charger dans Home Assistant.

### Erreur Corrigée

```
ERROR (MainThread) [homeassistant.config_entries] Error occurred loading flow for integration smart_room_manager:
cannot import name 'ALARM_STATE_ARMED_AWAY' from 'homeassistant.const'
```

### Solution

- ✅ Correction de l'import `ALARM_STATE_ARMED_AWAY`
- ✅ Import maintenant depuis notre propre `const.py` au lieu de `homeassistant.const`
- ✅ L'intégration se charge correctement

## 📦 Installation

### Via HACS (Recommandé)
```
1. HACS > Intégrations
2. Smart Room Manager > Redownload
3. Redémarrer Home Assistant
```

### Manuelle
```
1. Télécharger smart_room_manager.zip
2. Extraire dans config/custom_components/
3. Redémarrer Home Assistant
```

## 🆕 Nouveautés v0.2.x (rappel)

Si vous venez de la v0.1.0, consultez les [notes de release v0.2.0](RELEASE_NOTES_v0.2.0.md) pour la liste complète des changements :

- 🔄 Architecture simplifiée (4 modes)
- 🏠 Types de pièces (normal, couloir, salle de bain)
- 🎛️ Bypass générique
- ⏰ Plages horaires confort multiples
- 🌡️ Support été/hiver

## 🔗 Liens Utiles

- 📖 [README complet](https://github.com/GevaudanBeast/HA-SMART/blob/main/README.md)
- 📋 [CHANGELOG détaillé](https://github.com/GevaudanBeast/HA-SMART/blob/main/CHANGELOG.md)
- 📝 [Notes v0.2.0](https://github.com/GevaudanBeast/HA-SMART/blob/main/RELEASE_NOTES_v0.2.0.md)
- 🐛 [Signaler un bug](https://github.com/GevaudanBeast/HA-SMART/issues)

---

**Développé avec ❤️ pour la communauté Home Assistant**
