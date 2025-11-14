# Smart Room Manager v0.2.0 - Architecture Simplifiée 🎯

**Date de release** : 14 janvier 2025

## 🚀 Highlights

Version majeure avec **refactoring complet** de l'architecture pour plus de simplicité et de robustesse :

- 🔄 **Présence basée sur alarme** : Plus besoin de capteurs de présence
- 💡 **Contrôle manuel des lumières** : Timer auto-off uniquement pour couloirs/salles de bain
- 🎛️ **Bypass générique** : Un seul switch pour tous les scénarios (Solar Optimizer, manuel, etc.)
- 📊 **4 modes au lieu de 6** : Architecture simplifiée
- ⏰ **Plages horaires confort** : Configuration flexible multi-plages

## ⚠️ Breaking Changes

**Cette version nécessite une reconfiguration complète des pièces via l'interface.**

Les configurations v0.1.0 sont **incompatibles** avec v0.2.0 en raison des changements architecturaux majeurs.

### Éléments supprimés
- ❌ Capteurs de présence (remplacé par alarme)
- ❌ Capteurs de luminosité intérieurs
- ❌ Modes invité et vacances
- ❌ 4 périodes horaires (matin, jour, soirée, nuit)
- ❌ Configuration Solar Optimizer spécifique

### Nouveaux éléments requis
- ✅ Entité alarme (armed_away = absent)
- ✅ Type de pièce (normal, couloir, salle de bain)
- ✅ Plages horaires confort (format HH:MM-HH:MM,HH:MM-HH:MM)
- ✅ Switch bypass générique (optionnel)
- ✅ Calendrier été (optionnel, pour clim)

## ✨ Nouvelles Fonctionnalités

### 🏠 Types de Pièces
Chaque pièce a maintenant un type qui détermine son comportement :

- **Normal** (chambres, bureau) :
  - Pas de timer lumière
  - Contrôle manuel complet
  - Mode chauffage selon plages horaires

- **Couloir** :
  - Timer auto-off 5 minutes (configurable)
  - Extinction automatique après timeout
  - Économie d'énergie

- **Salle de bain** :
  - Timer auto-off 15 minutes
  - **Lumière pilote chauffage** : ON=confort, OFF=eco
  - Boost automatique pendant utilisation

### 🎛️ Bypass Générique
Un seul switch pour tous les scénarios :
- ✅ Solar Optimizer (priorité énergie solaire)
- ✅ Contrôle manuel temporaire
- ✅ Mode maintenance
- ✅ Tout autre contrôle externe

**Fonctionnement** :
- Switch ON → Smart Room Manager se met en retrait
- Switch OFF → Smart Room Manager reprend le contrôle

### 🌡️ Support Été/Hiver
Configuration séparée des températures :
- **Hiver** (heat) : Confort 20°C, Eco 18°C
- **Été** (cool) : Confort 24°C, Eco 26°C
- Basculement automatique via calendrier

### 🔧 Auto-détection X4FP
Détection automatique du type de climat :
- **X4FP (IPX800)** : Contrôle via preset_mode (comfort, eco, away)
- **Thermostat** : Contrôle via hvac_mode + température

### ⏰ Plages Horaires Flexibles
Configuration de **plusieurs plages confort** par jour :
- Format : `HH:MM-HH:MM,HH:MM-HH:MM`
- Exemple : `07:00-09:00,18:00-22:00` (matin + soirée)
- Mode eco par défaut hors plages

### 🎨 Personnalisation
- Icônes personnalisables par pièce
- Configuration simplifiée via UI
- Moins d'étapes dans l'assistant

## 🐛 Corrections

### Sécurité et Robustesse
- ✅ Ajout de toutes les constantes manquantes
- ✅ Validation des champs requis
- ✅ Gestion d'erreurs complète (try/except)
- ✅ Accès sécurisé aux structures de données

### Bugs Corrigés
- 🔧 Accès incorrect au calendrier saison
- 🔧 Versions hard-codées "0.1.0"
- 🔧 Parsing entity_id non sécurisé
- 🔧 Constantes importées mais non définies
- 🔧 Duplication de code (60+ lignes)

### Amélioration du Code
- 📦 Création classe base `SmartRoomEntity`
- 🔍 Review de code complet
- 📝 Documentation améliorée
- ⚡ Optimisations performance

## 📋 Modes de Fonctionnement (v0.2.0)

### 4 Modes Simplifiés

1. **Confort** 🌟
   - Quand : Présent (alarme désarmée) + plage horaire confort
   - Chauffage : Température confort configurée
   - Exemple : 7h-9h et 18h-22h, température 20°C

2. **Eco** 🌱
   - Quand : Présent mais hors plages confort
   - Chauffage : Température eco configurée
   - Exemple : Journée en télétravail, température 18°C
   - **Mode par défaut**

3. **Nuit** 🌙
   - Quand : Période nocturne (configurable)
   - Chauffage : Température nuit configurée
   - Exemple : 22h-7h, température 17°C

4. **Hors-gel** ❄️
   - Quand : Alarme armed_away OU fenêtre ouverte
   - Chauffage : Température hors-gel
   - Exemple : Absence, température 12°C

## 🔄 Migration depuis v0.1.0

### Étapes Requises

1. **Sauvegardez votre configuration actuelle** (capture d'écran)

2. **Supprimez l'intégration v0.1.0** :
   - Paramètres > Appareils et services
   - Smart Room Manager > Supprimer

3. **Mettez à jour vers v0.2.0** (HACS ou manuel)

4. **Redémarrez Home Assistant**

5. **Reconfigurez l'intégration** :
   - Ajoutez Smart Room Manager
   - Configurez alarme + calendrier été (optionnel)
   - Recréez chaque pièce avec nouveau flow

### Correspondances v0.1.0 → v0.2.0

| v0.1.0 | v0.2.0 | Notes |
|--------|--------|-------|
| Capteur présence | Alarme | armed_away = absent |
| Capteur luminosité | - | Supprimé (contrôle manuel) |
| Mode invité | - | Supprimé |
| Mode vacances | Hors-gel | Via alarme armed_away |
| 6 modes | 4 modes | Simplifié |
| 4 périodes | Nuit + plages confort | Flexible |
| Switch Solar Optimizer | Switch bypass | Générique |
| - | Type pièce | Normal/Couloir/SdB |
| - | Icône pièce | Personnalisable |

## 📦 Installation

### Via HACS (Recommandé)
```
1. HACS > Intégrations
2. Menu (⋮) > Dépôts personnalisés
3. URL : https://github.com/GevaudanBeast/HA-SMART
4. Rechercher "Smart Room Manager"
5. Installer + Redémarrer HA
```

### Manuelle
```
1. Télécharger smart_room_manager.zip
2. Extraire dans config/custom_components/
3. Redémarrer Home Assistant
4. Ajouter via Paramètres > Intégrations
```

## 🎯 Exemples de Configuration

### Chambre Simple
```
Type : Normal
Climat : climate.chambre
Températures : 20°C / 18°C / 17°C / 12°C
Nuit : 22:00
Plages confort : 07:00-09:00
```
**Résultat** : Confort le matin, eco la journée, nuit la nuit

### Salle de Bain avec Lumière Pilote
```
Type : Salle de bain
Lumières : light.sdb
Timeout : 900s (15 min)
Climat : climate.radiateur_sdb
Températures confort/eco : 22°C / 17°C
```
**Résultat** : Lumière ON → 22°C, OFF → 17°C, auto-off après 15 min

### Salon avec Solar Optimizer
```
Type : Normal
Climat : climate.salon
Bypass : switch.solar_optimizer_salon
Plages confort : 18:00-23:00
```
**Résultat** : SO prioritaire, Smart Room backup

## 🔗 Liens Utiles

- 📖 [README complet](https://github.com/GevaudanBeast/HA-SMART/blob/main/README.md)
- 📋 [CHANGELOG détaillé](https://github.com/GevaudanBeast/HA-SMART/blob/main/CHANGELOG.md)
- 🐛 [Signaler un bug](https://github.com/GevaudanBeast/HA-SMART/issues)
- 💬 [Discussions](https://github.com/GevaudanBeast/HA-SMART/discussions)

## 🙏 Remerciements

Merci à tous les utilisateurs de la v0.1.0 pour vos retours qui ont permis cette refactorisation !

---

**Développé avec ❤️ pour la communauté Home Assistant**
