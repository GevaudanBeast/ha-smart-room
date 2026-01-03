#!/bin/bash

echo "======================================"
echo "🔍 Vérification des mises à jour"
echo "======================================"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Compteurs
PASS=0
FAIL=0

# Fonction de vérification
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $1"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL${NC}: $1"
        ((FAIL++))
    fi
}

# 1. Vérifier la branche
echo "📌 1. Vérification de la branche Git"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" = "claude/smart-room-manager-setup-sN3ra" ]; then
    check "Branche correcte: $CURRENT_BRANCH"
else
    echo -e "${YELLOW}⚠️  WARNING${NC}: Branche actuelle: $CURRENT_BRANCH (attendu: claude/smart-room-manager-setup-sN3ra)"
    ((FAIL++))
fi
echo ""

# 2. Vérifier les commits
echo "📌 2. Vérification des 8 commits de correction"
EXPECTED_COMMITS=(
    "6dda8ac"
    "a5937cf"
    "bcd72f6"
    "c442606"
    "ace1f64"
    "ed7a096"
    "af7a682"
    "9c3f417"
)

for commit in "${EXPECTED_COMMITS[@]}"; do
    if git log --oneline | grep -q "^$commit"; then
        check "Commit $commit présent"
    else
        echo -e "${RED}❌ FAIL${NC}: Commit $commit manquant"
        ((FAIL++))
    fi
done
echo ""

# 3. Vérifier les fichiers modifiés
echo "📌 3. Vérification des fichiers clés"

# Vérifier coordinator.py
if grep -q "def async_add_listener(self, \*args, \*\*kwargs)" custom_components/smart_room_manager/coordinator.py; then
    check "coordinator.py: async_add_listener avec *args, **kwargs"
else
    echo -e "${RED}❌ FAIL${NC}: coordinator.py: async_add_listener incorrect"
    ((FAIL++))
fi

# Vérifier strings.json
if grep -q '"schedule_entity": "Calendar entity (optional)"' custom_components/smart_room_manager/strings.json; then
    check "strings.json: schedule_entity traduit correctement"
else
    echo -e "${RED}❌ FAIL${NC}: strings.json: schedule_entity incorrect"
    ((FAIL++))
fi

# Vérifier fr.json
if grep -q '"schedule_entity": "Entité calendrier (optionnel)"' custom_components/smart_room_manager/translations/fr.json; then
    check "fr.json: schedule_entity traduit en français"
else
    echo -e "${RED}❌ FAIL${NC}: fr.json: schedule_entity incorrect"
    ((FAIL++))
fi

# Vérifier preset_schedule_on dans strings.json
if grep -q '"preset_schedule_on":' custom_components/smart_room_manager/strings.json; then
    check "strings.json: preset_schedule_on selector présent"
else
    echo -e "${RED}❌ FAIL${NC}: strings.json: preset_schedule_on selector manquant"
    ((FAIL++))
fi

# Vérifier config_flow.py validation
if grep -q "if preset_on in \[MODE_COMFORT, MODE_ECO, MODE_NIGHT\]:" custom_components/smart_room_manager/config_flow.py; then
    check "config_flow.py: validation stricte des presets"
else
    echo -e "${RED}❌ FAIL${NC}: config_flow.py: validation stricte manquante"
    ((FAIL++))
fi

# Vérifier CONF_IGNORE_IN_AWAY
if grep -q "CONF_IGNORE_IN_AWAY" custom_components/smart_room_manager/const.py; then
    check "const.py: CONF_IGNORE_IN_AWAY défini"
else
    echo -e "${RED}❌ FAIL${NC}: const.py: CONF_IGNORE_IN_AWAY manquant"
    ((FAIL++))
fi

echo ""

# 4. Vérifier l'état Git
echo "📌 4. Vérification de l'état Git"
if [ -z "$(git status --porcelain)" ]; then
    check "Working tree propre (pas de modifications non commitées)"
else
    echo -e "${YELLOW}⚠️  WARNING${NC}: Il y a des modifications non commitées"
    git status --short
fi
echo ""

# 5. Vérifier la synchronisation avec origin
echo "📌 5. Vérification de la synchronisation avec GitHub"
git fetch origin claude/smart-room-manager-setup-sN3ra 2>/dev/null
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ "$LOCAL" = "$REMOTE" ]; then
    check "Branche synchronisée avec origin"
else
    echo -e "${YELLOW}⚠️  WARNING${NC}: Branche locale différente de origin"
    echo "   Local:  $LOCAL"
    echo "   Remote: $REMOTE"
fi
echo ""

# 6. Résumé des derniers commits
echo "📌 6. Derniers commits (HEAD~7..HEAD)"
git log --oneline --graph --decorate -8
echo ""

# Résultat final
echo "======================================"
echo "📊 Résultat de la vérification"
echo "======================================"
echo -e "${GREEN}✅ Tests réussis: $PASS${NC}"
if [ $FAIL -gt 0 ]; then
    echo -e "${RED}❌ Tests échoués: $FAIL${NC}"
    echo ""
    echo -e "${RED}⚠️  ATTENTION: Des mises à jour semblent manquantes!${NC}"
    echo "Actions recommandées:"
    echo "1. git pull origin claude/smart-room-manager-setup-sN3ra"
    echo "2. Vérifier les logs: git log --oneline -10"
else
    echo -e "${GREEN}✅ Toutes les vérifications sont passées!${NC}"
    echo ""
    echo "✨ Votre installation est à jour!"
    echo ""
    echo "⚠️  IMPORTANT: Redémarrez Home Assistant pour charger les modifications"
    echo "   Paramètres → Système → Redémarrer"
fi
echo ""
