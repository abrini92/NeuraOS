#!/bin/bash
# Fix Code Quality - Neura Top 0.1%
# Auto-fix Ruff issues

set -e

echo "🔧 NEURA CODE QUALITY FIX"
echo "=========================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Phase 1: Auto-fix Ruff issues${NC}"
echo "Fixing whitespace, imports, type annotations..."
poetry run ruff check --fix neura/ --select W293,W291,I001,UP007,UP006,UP035,UP015,F401,F541,E712

echo ""
echo -e "${YELLOW}Phase 2: Format code${NC}"
echo "Applying Black-compatible formatting..."
poetry run ruff format neura/

echo ""
echo -e "${YELLOW}Phase 3: Verify fixes${NC}"
echo "Checking remaining issues..."
REMAINING=$(poetry run ruff check neura/ --statistics 2>&1 | grep "Found" || echo "0 errors")
echo "Result: $REMAINING"

echo ""
echo -e "${GREEN}✅ Code quality fixes applied!${NC}"
echo ""
echo "Next steps:"
echo "1. Review changes: git diff"
echo "2. Run tests: poetry run pytest"
echo "3. Commit: git commit -am 'fix: code quality improvements'"
