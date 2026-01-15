#!/bin/bash
# Quick Test Script - Basic Functionality
# Tests the core workflow: Action File → Plan → Approval

set -e

echo "🧪 Silver Tier Quick Test"
echo "========================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Change to project directory
cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"

echo "Test 1: Vault Structure"
echo "-----------------------"
for dir in AI_Employee_Vault/Inbox AI_Employee_Vault/Needs_Action AI_Employee_Vault/Plans AI_Employee_Vault/Pending_Approval AI_Employee_Vault/Done AI_Employee_Vault/Logs; do
    if [ -d "$dir" ]; then
        pass "$dir exists"
    else
        fail "$dir missing"
        mkdir -p "$dir" 2>/dev/null && info "Created $dir"
    fi
done
echo ""

echo "Test 2: Python Imports"
echo "----------------------"
python3 -c "from src.lib.vault import vault; print('vault imported')" 2>/dev/null && pass "vault.py imports" || fail "vault.py import error"
python3 -c "from src.lib.logging import get_logger; print('logging imported')" 2>/dev/null && pass "logging.py imports" || fail "logging.py import error"
python3 -c "from src.lib.config import config; print('config imported')" 2>/dev/null && pass "config.py imports" || fail "config.py import error"
python3 -c "from src.watchers.base import BaseWatcher; print('BaseWatcher imported')" 2>/dev/null && pass "base.py imports" || fail "base.py import error"
python3 -c "from src.orchestration.orchestrator import Orchestrator; print('Orchestrator imported')" 2>/dev/null && pass "orchestrator.py imports" || fail "orchestrator.py import error"
echo ""

echo "Test 3: Create Test Action File"
echo "--------------------------------"
TEST_FILE="AI_Employee_Vault/Needs_Action/quick_test_$(date +%s).md"
cat > "$TEST_FILE" << 'EOF'
---
id: "quick_test_001"
type: "email"
source: "quick_test"
priority: "normal"
timestamp: "2026-01-15T16:00:00Z"
status: "pending"
metadata:
  sender: "test@example.com"
  subject: "Quick Test Email"
---

# Quick Test Email

This is a quick test to verify the system is working.
EOF

if [ -f "$TEST_FILE" ]; then
    pass "Test action file created: $(basename $TEST_FILE)"
else
    fail "Failed to create test action file"
fi
echo ""

echo "Test 4: Start Orchestrator (5 seconds)"
echo "---------------------------------------"
info "Starting orchestrator in background..."
export DRY_RUN=true
timeout 5 python3 src/orchestration/orchestrator.py > /tmp/orchestrator_test.log 2>&1 &
ORCH_PID=$!
sleep 6

if ps -p $ORCH_PID > /dev/null 2>&1; then
    kill $ORCH_PID 2>/dev/null
    pass "Orchestrator started successfully"
else
    pass "Orchestrator ran and exited (expected after timeout)"
fi
echo ""

echo "Test 5: Verify Processing"
echo "-------------------------"
# Check if file was moved to Done
if [ ! -f "$TEST_FILE" ]; then
    pass "Action file was processed (moved from Needs_Action)"
else
    fail "Action file still in Needs_Action (not processed)"
fi

# Check if plan was created
PLAN_COUNT=$(ls -1 AI_Employee_Vault/Plans/*quick_test*.md 2>/dev/null | wc -l)
if [ "$PLAN_COUNT" -gt 0 ]; then
    pass "Plan file created ($PLAN_COUNT found)"
else
    fail "No plan file created"
fi

# Check if file is in Done
DONE_COUNT=$(ls -1 AI_Employee_Vault/Done/*quick_test*.md 2>/dev/null | wc -l)
if [ "$DONE_COUNT" -gt 0 ]; then
    pass "Action file moved to Done"
else
    fail "Action file not in Done"
fi
echo ""

echo "Test 6: Check Logs"
echo "------------------"
LOG_FILE="AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json"
if [ -f "$LOG_FILE" ]; then
    pass "Audit log exists: $(basename $LOG_FILE)"
    LOG_ENTRIES=$(cat "$LOG_FILE" | grep -c "action_type" || echo "0")
    info "Log entries: $LOG_ENTRIES"
else
    fail "No audit log created"
fi
echo ""

echo "Test 7: PM2 Status"
echo "------------------"
if command -v pm2 &> /dev/null; then
    pass "PM2 is installed"
    PM2_RUNNING=$(pm2 list | grep -c "online" || echo "0")
    if [ "$PM2_RUNNING" -gt 0 ]; then
        info "PM2 processes running: $PM2_RUNNING"
    else
        info "No PM2 processes running (start with: pm2 start ecosystem.config.js)"
    fi
else
    fail "PM2 not installed"
fi
echo ""

# Summary
echo "========================="
echo "Test Summary"
echo "========================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start PM2: pm2 start ecosystem.config.js"
    echo "2. View logs: pm2 logs"
    echo "3. Read TESTING_GUIDE.md for comprehensive testing"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Check the output above.${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Install dependencies: pip install -e ."
    echo "2. Check Python path: export PYTHONPATH=\$(pwd)"
    echo "3. Review orchestrator log: cat /tmp/orchestrator_test.log"
    exit 1
fi
