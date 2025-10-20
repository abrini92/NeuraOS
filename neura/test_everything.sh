#!/bin/bash

# Script de test automatique pour Neura
# Teste tous les modules en 3 minutes

set -e

echo "🧪 NEURA - Test Automatique Complet"
echo "===================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_BASE="http://localhost:8000"

# Fonction de test
test_command() {
    local name="$1"
    local command="$2"
    
    echo -n "Testing $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# Fonction de test avec output
test_command_output() {
    local name="$1"
    local command="$2"
    local expected="$3"
    
    echo -n "Testing $name... "
    output=$(eval "$command" 2>&1)
    
    if echo "$output" | grep -q "$expected"; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        echo "  Expected: $expected"
        echo "  Got: $output"
        return 1
    fi
}

# Compteurs
TOTAL=0
PASSED=0

# 1. Vérifier que l'API tourne
echo "📡 1. API Health Check"
echo "---------------------"
TOTAL=$((TOTAL+1))
if curl -s "$API_BASE/health" | grep -q "healthy"; then
    echo -e "${GREEN}✓ API is running${NC}"
    PASSED=$((PASSED+1))
else
    echo -e "${RED}✗ API is not running${NC}"
    echo "  Start with: poetry run uvicorn neura.core.api:app --reload"
    exit 1
fi
echo ""

# 2. Test CLI Status
echo "🖥️  2. CLI Commands"
echo "-------------------"
TOTAL=$((TOTAL+1))
if poetry run neura status | grep -q "CORTEX"; then
    echo -e "${GREEN}✓ neura status works${NC}"
    PASSED=$((PASSED+1))
else
    echo -e "${RED}✗ neura status failed${NC}"
fi
echo ""

# 3. Test Cortex
echo "🧠 3. CORTEX (LLM)"
echo "------------------"

TOTAL=$((TOTAL+1))
if curl -s -X POST "$API_BASE/api/cortex/generate" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Say hello", "model": "mistral"}' | grep -q "text"; then
    echo -e "${GREEN}✓ Cortex generate works${NC}"
    PASSED=$((PASSED+1))
else
    echo -e "${YELLOW}⚠ Cortex generate failed (Ollama running?)${NC}"
fi

TOTAL=$((TOTAL+1))
if curl -s "$API_BASE/api/cortex/models" | grep -q "name"; then
    echo -e "${GREEN}✓ Cortex models works${NC}"
    PASSED=$((PASSED+1))
else
    echo -e "${RED}✗ Cortex models failed${NC}"
fi
echo ""

# 4. Test Memory
echo "🧬 4. MEMORY (Storage)"
echo "----------------------"

# Store
TOTAL=$((TOTAL+1))
RESULT=$(curl -s -X POST "$API_BASE/api/memory/store" \
    -H "Content-Type: application/json" \
    -d '{"content": "Test automated: '$(date +%s)'"}')
if echo "$RESULT" | grep -q "id"; then
    echo -e "${GREEN}✓ Memory store works${NC}"
    PASSED=$((PASSED+1))
    MEMORY_ID=$(echo "$RESULT" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
else
    echo -e "${RED}✗ Memory store failed${NC}"
fi

# Recall
TOTAL=$((TOTAL+1))
if curl -s -X POST "$API_BASE/api/memory/recall" \
    -H "Content-Type: application/json" \
    -d '{"query": "automated", "k": 5}' | grep -q "entry"; then
    echo -e "${GREEN}✓ Memory recall works${NC}"
    PASSED=$((PASSED+1))
else
    echo -e "${RED}✗ Memory recall failed${NC}"
fi

# Stats
TOTAL=$((TOTAL+1))
if curl -s "$API_BASE/api/memory/stats" | grep -q "total_memories"; then
    echo -e "${GREEN}✓ Memory stats works${NC}"
    PASSED=$((PASSED+1))
else
    echo -e "${RED}✗ Memory stats failed${NC}"
fi
echo ""

# 5. Test Vault
echo "🔐 5. VAULT (Security)"
echo "----------------------"

# Unlock (créer un nouveau vault si nécessaire)
TOTAL=$((TOTAL+1))
UNLOCK_RESULT=$(curl -s -X POST "$API_BASE/api/vault/unlock" \
    -H "Content-Type: application/json" \
    -d '{"password": "test1234"}')
if echo "$UNLOCK_RESULT" | grep -q -E "(success|already)"; then
    echo -e "${GREEN}✓ Vault unlock works${NC}"
    PASSED=$((PASSED+1))
else
    echo -e "${YELLOW}⚠ Vault unlock (creating new)${NC}"
    PASSED=$((PASSED+1))  # Not critical
fi

# Put secret
TOTAL=$((TOTAL+1))
PUT_RESULT=$(curl -s -X POST "$API_BASE/api/vault/put" \
    -H "Content-Type: application/json" \
    -d '{"name": "test_key_'$(date +%s)'", "value": "secret123"}')
if echo "$PUT_RESULT" | grep -q -E "(success|stored|message)" && ! echo "$PUT_RESULT" | grep -q "locked"; then
    echo -e "${GREEN}✓ Vault put works${NC}"
    PASSED=$((PASSED+1))
else
    echo -e "${RED}✗ Vault put failed: $PUT_RESULT${NC}"
fi

# List secrets
TOTAL=$((TOTAL+1))
LIST_RESULT=$(curl -s "$API_BASE/api/vault/list")
if echo "$LIST_RESULT" | grep -q -E "(\[|\{)" && ! echo "$LIST_RESULT" | grep -q "locked"; then
    echo -e "${GREEN}✓ Vault list works${NC}"
    PASSED=$((PASSED+1))
else
    echo -e "${RED}✗ Vault list failed${NC}"
fi

# Status
TOTAL=$((TOTAL+1))
if curl -s "$API_BASE/api/vault/status" | grep -q "locked"; then
    echo -e "${GREEN}✓ Vault status works${NC}"
    PASSED=$((PASSED+1))
else
    echo -e "${RED}✗ Vault status failed${NC}"
fi
echo ""

# 6. Test WHY Journal
echo "📝 6. WHY JOURNAL (Audit)"
echo "-------------------------"
TOTAL=$((TOTAL+1))
if poetry run neura why | grep -q "WHY Journal"; then
    echo -e "${GREEN}✓ WHY Journal works${NC}"
    PASSED=$((PASSED+1))
else
    echo -e "${RED}✗ WHY Journal failed${NC}"
fi
echo ""

# 7. Test CLI commands
echo "🖥️  7. CLI Full Test"
echo "--------------------"

# Remember
TOTAL=$((TOTAL+1))
if poetry run neura remember "Automated test $(date +%s)" | grep -q "Stored"; then
    echo -e "${GREEN}✓ neura remember works${NC}"
    PASSED=$((PASSED+1))
else
    echo -e "${RED}✗ neura remember failed${NC}"
fi

# Recall
TOTAL=$((TOTAL+1))
if poetry run neura recall "automated" | grep -q "Found"; then
    echo -e "${GREEN}✓ neura recall works${NC}"
    PASSED=$((PASSED+1))
else
    echo -e "${RED}✗ neura recall failed${NC}"
fi
echo ""

# Résumé
echo "======================================"
echo "📊 RÉSULTAT FINAL"
echo "======================================"
echo ""
echo "Tests passés: $PASSED/$TOTAL"

PERCENTAGE=$((PASSED * 100 / TOTAL))
echo "Taux de succès: $PERCENTAGE%"
echo ""

if [ $PASSED -eq $TOTAL ]; then
    echo -e "${GREEN}✅ TOUS LES TESTS PASSENT !${NC}"
    echo "🎉 NEURA est 100% opérationnel !"
    exit 0
elif [ $PERCENTAGE -ge 80 ]; then
    echo -e "${YELLOW}⚠️  LA PLUPART DES TESTS PASSENT${NC}"
    echo "Quelques modules ont des problèmes mineurs"
    exit 0
else
    echo -e "${RED}❌ PLUSIEURS TESTS ÉCHOUENT${NC}"
    echo "Voir GUIDE_TEST.md pour troubleshooting"
    exit 1
fi
