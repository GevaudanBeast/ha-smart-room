# Release Notes v0.1.0

## 🎉 Smart Room Manager v0.1.0

Première version de l'intégration Home Assistant Smart Room Manager.

### ✨ Fonctionnalités

- ✅ Configuration 100% UI (config_flow, aucun YAML requis)
- ✅ Support Solar Optimizer (priorité absolue sur le chauffage)
- ✅ Gestion multi-modes : comfort, eco, night, away, frost_protection, guest
- ✅ Détection présence par pièce
- ✅ Gestion intelligente éclairage (seuil luminosité + présence)
- ✅ Intégration Alarmo pour modes automatiques
- ✅ Intégration calendrier (saison été/hiver)
- ✅ Entités par pièce : sensor (mode), binary_sensor (occupé, lumière), switch (automation)

### 📚 Documentation

- **README.md** : Documentation principale avec installation et configuration
- **MIGRATION_GUIDE.md** : Plan de migration progressif en 4 phases depuis automations YAML
- **CONFIGURATION_EXAMPLES.md** : Configurations prêtes à l'emploi pour toutes les pièces
- **SOLAR_OPTIMIZER.md** : Guide complet d'intégration Solar Optimizer

### 📦 Installation

**Via HACS (recommandé)** :
1. HACS → Intégrations → Menu (⋮) → Dépôts personnalisés
2. URL : `https://github.com/GevaudanBeast/HA-SMART`
3. Catégorie : Integration
4. Télécharger "Smart Room Manager"
5. Redémarrer Home Assistant

**Manuel** :
1. Télécharger `smart-room-manager-v0.1.0.zip`
2. Extraire le dossier `custom_components/smart_room_manager` dans `/config/custom_components/`
3. Redémarrer Home Assistant
4. Aller dans Paramètres → Appareils et services → Ajouter une intégration → "Smart Room Manager"

### 🔐 Vérification

**SHA256 Checksum** :
```
0a289b338b987c4ba0bd70d94348ec39194f78776227bfb41caccba0b46bf89c
```

Pour vérifier l'intégrité du fichier téléchargé :
```bash
sha256sum smart-room-manager-v0.1.0.zip
```

### 🧪 Migration

Consulter **MIGRATION_GUIDE.md** pour un plan de migration progressif en 4 phases :
- **Phase 1** : Pièces simples (WC, couloirs) - Semaine 1
- **Phase 2** : Lumières avec capteurs - Semaine 2
- **Phase 3** : Chauffage simple (Salon) - Semaines 3-4
- **Phase 4** : Pièces avec Solar Optimizer - Après validation

### 📝 Changelog

**Commits inclus** :
- `c86b94f` - feat: Add GitHub workflows and HACS integration
- `ddf8158` - chore: Update version numbering to v0.1.0
- `e05b104` - feat: Add Solar Optimizer support v1.1.0 + migration guides
- `e654d92` - feat: Add Smart Room Manager integration v1.0.0

### ⚙️ Compatibilité

- **Home Assistant** : 2023.1.0 ou supérieur
- **Python** : 3.11+
- **HACS** : Compatible

### 🐛 Problèmes connus

Aucun problème connu pour cette version initiale.

### 💬 Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub : https://github.com/GevaudanBeast/HA-SMART/issues
- Consulter la documentation complète dans le README.md

---

**Version complète** : v0.1.0
**Date de release** : 2025-11-13
**Taille de l'archive** : 24K
