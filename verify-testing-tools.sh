#!/bin/bash
# Verification Test - Ensures all testing tools work correctly

echo "🔧 Testing Tools Verification"
echo "=============================="
echo ""

cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $1"
        ((FAIL++))
    fi
}

echo "1. Checking test scripts exist..."
[ -f "test-system.sh" ] && check "test-system.sh exists" || check "test-system.sh missing"
[ -f "quick-test.sh" ] && check "quick-test.sh exists" || check "quick-test.sh missing"
[ -f "demo-workflow.sh" ] && check "demo-workflow.sh exists" || check "demo-workflow.sh missing"
[ -f "monitor.sh" ] && check "monitor.sh exists" || check "monitor.sh exists"
echo ""

echo "2. Checking test scripts are executable..."
[ -x "test-system.sh" ] && check "test-system.sh executable" || check "test-system.sh not executable"
[ -x "quick-test.sh" ] && check "quick-test.sh executable" || check "quick-test.sh not executable"
[ -x "demo-workflow.sh" ] && check "demo-workflow.sh executable" || check "demo-workflow.sh not executable"
[ -x "monitor.sh" ] && check "monitor.sh executable" || check "monitor.sh not executable"
echo ""

echo "3. Checking documentation..."
[ -f "TESTING_GUIDE.md" ] && check "TESTING_GUIDE.md exists" || check "TESTING_GUIDE.md missing"
[ -f "QUICK_START.md" ] && check "QUICK_START.md exists" || check "QUICK_START.md missing"
[ -f ".env.example" ] && check ".env.example exists" || check ".env.example missing"
echo ""

echo "4. Checking Python imports..."
python3 -c "import sys; sys.path.insert(0, '.'); from src.lib.vault import vault" 2>/dev/null && check "vault.py imports" || check "vault.py import failed"
python3 -c "import sys; sys.path.insert(0, '.'); from src.lib.logging import get_logger" 2>/dev/null && check "logging.py imports" || check "logging.py import failed"
python3 -c "import sys; sys.path.insert(0, '.'); from src.lib.config import config" 2>/dev/null && check "config.py imports" || check "config.py import failed"
echo ""

echo "5. Checking vault structure..."
for dir in AI_Employee_Vault/Inbox AI_Employee_Vault/Needs_Action AI_Employee_Vault/Plans AI_Employee_Vault/Pending_Approval AI_Employee_Vault/Done AI_Employee_Vault/Logs; do
    [ -d "$dir" ] && check "$dir exists" || check "$dir missing"
done
echo ""

echo "=============================="
echo "Summary:"
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All verification checks passed!${NC}"
    echo ""
    echo "You're ready to test! Try:"
    echo "  ./quick-test.sh       - Quick automated test"
    echo "  ./demo-workflow.sh    - Interactive demo"
    echo "  ./monitor.sh          - Real-time monitoring"
    echo ""
    echo "Or read:"
    echo "  QUICK_START.md        - Quick start guide"
    echo "  TESTING_GUIDE.md      - Comprehensive testing"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some checks failed. Review the output above.${NC}"
    exit 1
fi
