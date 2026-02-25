#!/bin/bash
# Silver Tier Testing Script
# Run this to verify system readiness before testing

echo "=== Silver Tier System Check ==="
echo ""

# Check Python version
echo "1. Python Version:"
python3 --version
echo ""

# Check dependencies
echo "2. Key Dependencies:"
pip list | grep -E "playwright|google-api-python-client|pyyaml|watchdog|python-dotenv" || echo "⚠️  Some dependencies missing"
echo ""

# Check Playwright browsers
echo "3. Playwright Browsers:"
playwright --version 2>/dev/null || echo "⚠️  Playwright not installed"
echo ""

# Check PM2
echo "4. PM2:"
pm2 --version 2>/dev/null || echo "⚠️  PM2 not installed"
echo ""

# Check project structure
echo "5. Project Structure:"
for dir in src/lib src/watchers src/orchestration src/mcp tests AI_Employee_Vault; do
    if [ -d "$dir" ]; then
        echo "✓ $dir"
    else
        echo "✗ $dir (missing)"
    fi
done
echo ""

# Check vault structure
echo "6. Vault Structure:"
for dir in AI_Employee_Vault/Inbox AI_Employee_Vault/Needs_Action AI_Employee_Vault/Plans AI_Employee_Vault/Pending_Approval AI_Employee_Vault/Approved AI_Employee_Vault/Rejected AI_Employee_Vault/Done AI_Employee_Vault/Logs; do
    if [ -d "$dir" ]; then
        echo "✓ $dir"
    else
        echo "✗ $dir (missing)"
        mkdir -p "$dir" 2>/dev/null && echo "  → Created"
    fi
done
echo ""

echo "=== System Check Complete ==="
