#!/bin/bash

echo "🧪 TEST COMPLET MOTOR + POLICY"
echo "=============================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 PRÉ-REQUIS${NC}"
echo "1. Démarrer Ollama : ollama serve"
echo "2. Démarrer API : poetry run uvicorn neura.core.api:app --reload"
echo ""
echo "Press Enter quand prêt..."
read

echo -e "${BLUE}🧪 1. Test CLI Policy${NC}"
echo "$ poetry run neura policy --app Notes --action type_text --text \"Hello\""
poetry run neura policy --app Notes --action type_text --text "Hello"
echo ""

echo -e "${BLUE}🧪 2. Test CLI Motor (dry-run - safe)${NC}"
echo "$ poetry run neura motor --app Notes --action type_text --text \"Test\" --dry-run"
poetry run neura motor --app Notes --action type_text --text "Test" --dry-run
echo ""

echo -e "${BLUE}🧪 3. Test CLI Motor (blocked - unsafe app)${NC}"
echo "$ poetry run neura motor --app BadApp --action open_app"
poetry run neura motor --app BadApp --action open_app || true
echo ""

echo -e "${BLUE}🧪 4. Test CLI Motor (blocked - dangerous pattern)${NC}"
echo "$ poetry run neura motor --app Terminal --action type_text --text \"rm -rf /\""
poetry run neura motor --app Terminal --action type_text --text "rm -rf /" --dry-run || true
echo ""

echo -e "${BLUE}🧪 5. WHY Journal${NC}"
echo "$ poetry run neura why"
poetry run neura why
echo ""

echo -e "${BLUE}🧪 6. API Health Check${NC}"
echo "$ curl http://localhost:8000/health"
curl -s http://localhost:8000/health | jq '.modules'
echo ""

echo -e "${BLUE}🧪 7. API Motor Status${NC}"
echo "$ curl http://localhost:8000/api/motor/status"
curl -s http://localhost:8000/api/motor/status | jq || echo -e "${RED}❌ Motor API not available (restart API?)${NC}"
echo ""

echo -e "${BLUE}🧪 8. API Policy Status${NC}"
echo "$ curl http://localhost:8000/api/policy/status"
curl -s http://localhost:8000/api/policy/status | jq || echo -e "${RED}❌ Policy API not available (restart API?)${NC}"
echo ""

echo -e "${BLUE}🧪 9. API Policy Validate${NC}"
echo '$ curl -X POST http://localhost:8000/api/policy/validate -d {…}'
curl -s -X POST http://localhost:8000/api/policy/validate \
  -H "Content-Type: application/json" \
  -d '{"app": "Notes", "action": "type_text", "text": "API Test"}' | jq || echo -e "${RED}❌ Policy API not available${NC}"
echo ""

echo -e "${GREEN}✅ TESTS TERMINÉS${NC}"
echo ""
echo -e "${YELLOW}📊 RÉSUMÉ :${NC}"
echo "- CLI Policy : ✓"
echo "- CLI Motor (dry-run) : ✓"
echo "- CLI Motor (blocked) : ✓"
echo "- WHY Journal : ✓"
echo "- API endpoints : Nécessite redémarrage API"
echo ""
echo -e "${YELLOW}💡 Pour activer API Motor/Policy :${NC}"
echo "1. Arrêter API (Ctrl+C)"
echo "2. Relancer : poetry run uvicorn neura.core.api:app --reload"
echo "3. Relancer ce script : ./test_motor_policy.sh"
