# Smart Room Manager v0.2.3 - Migration Automatique

## 🔧 Correctif Critique

### Migration Automatique des Valeurs None

Cette version corrige automatiquement un problème affectant les utilisateurs ayant installé la v0.2.1 ou v0.2.2 :

**Problème résolu :**
- Erreur `Entity None is neither a valid entity ID nor a valid UUID`
- Capteurs de température/humidité affichant "Entity None"
- Configuration contenant des valeurs `None` pour les champs optionnels

**Solution automatique :**
- ✅ **Migration transparente au démarrage** : Nettoyage automatique des valeurs `None`
- ✅ **Aucune action requise** : La correction s'applique automatiquement lors du redémarrage
- ✅ **Configuration nettoyée** : Suppression des valeurs None dans :
  - `temperature_sensor`
  - `humidity_sensor`
  - `climate_entity`
  - `climate_bypass_switch`

## 🚀 Installation / Mise à jour

### Via HACS (recommandé)

1. HACS → Intégrations
2. Recherchez "Smart Room Manager"
3. Cliquez sur "Mettre à jour" (ou réinstallez)
4. **Redémarrez Home Assistant**
5. ✅ La migration s'exécute automatiquement !

### Manuelle

1. Téléchargez `smart_room_manager.zip` depuis cette release
2. Extrayez dans `/config/custom_components/smart_room_manager/`
3. **Redémarrez Home Assistant**
4. ✅ La migration s'exécute automatiquement !

## 📋 Vérification

Après le redémarrage, dans **Paramètres → Système → Journaux**, vous devriez voir :

```
Cleaned None values from room configurations (v0.2.1 migration)
```

Et l'erreur "Entity None" devrait avoir disparu ! 🎉

## 📊 Historique des versions

- **v0.2.3** : Migration automatique des valeurs None (ce patch)
- **v0.2.2** : Configuration optionnelle améliorée
- **v0.2.1** : Correction import ALARM_STATE_ARMED_AWAY
- **v0.2.0** : Architecture simplifiée (breaking changes)

## 📚 Pour plus d'informations

- [README](README.md) - Documentation complète
- [CHANGELOG](CHANGELOG.md) - Historique des changements
- [Release Notes v0.2.0](RELEASE_NOTES_v0.2.0.md) - Fonctionnalités principales

---

**Version précédente** : [v0.2.2](https://github.com/GevaudanBeast/HA-SMART/releases/tag/v0.2.2)
