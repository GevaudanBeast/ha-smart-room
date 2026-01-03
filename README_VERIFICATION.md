# ✅ Script de vérification des mises à jour

## Utilisation

```bash
cd /home/user/ha-smart-room
./verify_updates.sh
```

## Ce que le script vérifie

### 1. Branche Git
- ✅ Branche actuelle: `claude/smart-room-manager-setup-sN3ra`

### 2. Les 8 commits de correction
- `6dda8ac` - Validation stricte des presets
- `a5937cf` - Sauvegarde systématique des presets
- `bcd72f6` - Compatibilité async_add_listener (HA 2023.x et 2025.x+)
- `c442606` - SelectSelector pour presets calendrier
- `ace1f64` - Calendrier HA uniquement (domain="calendar")
- `ed7a096` - Documentation compatibilité ascendante
- `af7a682` - SelectSelector pour tous les champs
- `9c3f417` - Système de traduction EN/FR complet

### 3. Fichiers critiques
- ✅ `coordinator.py`: async_add_listener avec *args, **kwargs
- ✅ `strings.json`: Traductions anglaises complètes
- ✅ `translations/fr.json`: Traductions françaises complètes
- ✅ `config_flow.py`: Validation stricte des presets
- ✅ `const.py`: CONF_IGNORE_IN_AWAY défini

### 4. Synchronisation Git
- ✅ Pas de modifications non commitées
- ✅ Branche synchronisée avec GitHub

## Résultat attendu

```
✅ Tests réussis: 17
✅ Toutes les vérifications sont passées!

✨ Votre installation est à jour!

⚠️  IMPORTANT: Redémarrez Home Assistant pour charger les modifications
   Paramètres → Système → Redémarrer
```

## En cas d'échec

Si des tests échouent :

1. **Mettre à jour depuis GitHub**:
   ```bash
   git pull origin claude/smart-room-manager-setup-sN3ra
   ```

2. **Vérifier les logs**:
   ```bash
   git log --oneline -10
   ```

3. **Relancer la vérification**:
   ```bash
   ./verify_updates.sh
   ```

## Après vérification réussie

**REDÉMARRER Home Assistant** est obligatoire pour que les modifications soient chargées :

1. Paramètres → Système → **Redémarrer**
2. Attendre 2-3 minutes
3. Vérifier que les traductions sont chargées (voir "Entité calendrier (optionnel)" au lieu de "Entité calendrier/horaire")
4. Tester la création/modification de pièces

## Support

Si l'erreur "Unknown error occurred" persiste après redémarrage de HA :

1. Aller dans Paramètres → Système → Logs
2. Chercher "smart_room" ou "config_flow"
3. Copier le message d'erreur complet (avec traceback)
4. Partager les logs pour diagnostic
