# Smart Room Manager v0.2.3 - Correctifs Critiques Complets

## 🔧 Correctifs Critiques

Cette version corrige **plusieurs erreurs critiques** affectant les utilisateurs v0.2.1 et v0.2.2 :

### 1. Imports DOMAIN Manquants
**Problème :**
- `NameError: name 'DOMAIN' is not defined` dans switch.py et binary_sensor.py
- L'intégration ne pouvait pas charger les plateformes switch et binary_sensor

**Solution :**
- ✅ Ajout de `from .const import DOMAIN` dans switch.py et binary_sensor.py
- ✅ Toutes les entités (switches, capteurs binaires) sont maintenant créées correctement

### 2. Warning Deprecated (Home Assistant 2025.12)
**Problème :**
- Warning sur l'assignation explicite de `config_entry` dans OptionsFlow
- Code non compatible avec Home Assistant 2025.12+

**Solution :**
- ✅ Suppression de l'assignation explicite (fournie automatiquement par la classe parente)
- ✅ Compatible avec Home Assistant 2025.12 et versions futures

### 3. "Entity None" - Corrections Complètes
**Problème :**
- Erreur `Entity None is neither a valid entity ID nor a valid UUID`
- Capteurs de température/humidité affichant "Entity None" dans les formulaires
- Configuration contenant des valeurs `None` pour les champs optionnels

**Solution (3 corrections combinées) :**
- ✅ **Migration étendue** : Nettoyage automatique au démarrage des valeurs `None` dans :
  - `door_window_sensors` et `lights` (nouvellement ajoutés)
  - `temperature_sensor`, `humidity_sensor`
  - `climate_entity`, `climate_bypass_switch`
- ✅ **Correction `.get()` critique** : 7 emplacements corrigés de `.get(field, [])` vers `.get(field) or []`
  - Raison : `.get(key, default)` retourne `None` si la clé existe avec valeur `None`
  - Fichiers : config_flow.py, light_control.py, room_manager.py
- ✅ **Schémas conditionnels** : Formulaires reconstruits pour ne pas afficher "None" comme valeur par défaut

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
