#!/bin/bash
# Real-time System Monitor
# Watch the AI Employee system in action

cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

clear

echo "🔍 AI Employee System Monitor"
echo "=============================="
echo ""
echo "Press Ctrl+C to exit"
echo ""

while true; do
    clear
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🔍 AI EMPLOYEE SYSTEM MONITOR${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Timestamp
    echo -e "${YELLOW}⏰ $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""

    # PM2 Status
    echo -e "${GREEN}📊 PM2 Process Status${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if command -v pm2 &> /dev/null; then
        pm2 list 2>/dev/null | tail -n +2 || echo "No PM2 processes running"
    else
        echo "PM2 not installed"
    fi
    echo ""

    # Vault Status
    echo -e "${GREEN}📁 Vault Status${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "%-20s %s\n" "Needs_Action:" "$(ls -1 AI_Employee_Vault/Needs_Action/*.md 2>/dev/null | wc -l) files"
    printf "%-20s %s\n" "Plans:" "$(ls -1 AI_Employee_Vault/Plans/*.md 2>/dev/null | wc -l) files"
    printf "%-20s %s\n" "Pending_Approval:" "$(ls -1 AI_Employee_Vault/Pending_Approval/*.md 2>/dev/null | wc -l) files"
    printf "%-20s %s\n" "Approved:" "$(ls -1 AI_Employee_Vault/Approved/*.md 2>/dev/null | wc -l) files"
    printf "%-20s %s\n" "Rejected:" "$(ls -1 AI_Employee_Vault/Rejected/*.md 2>/dev/null | wc -l) files"
    printf "%-20s %s\n" "Done:" "$(ls -1 AI_Employee_Vault/Done/*.md 2>/dev/null | wc -l) files"
    echo ""

    # Recent Activity
    echo -e "${GREEN}📝 Recent Files (Last 5)${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    find AI_Employee_Vault -name "*.md" -type f -mmin -60 2>/dev/null | \
        xargs ls -lt 2>/dev/null | head -5 | \
        awk '{print $9}' | sed 's|AI_Employee_Vault/||' || echo "No recent activity"
    echo ""

    # Audit Log Stats
    echo -e "${GREEN}📊 Today's Activity${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    LOG_FILE="AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json"
    if [ -f "$LOG_FILE" ]; then
        TOTAL_ACTIONS=$(grep -c "action_type" "$LOG_FILE" 2>/dev/null || echo "0")
        printf "%-20s %s\n" "Total Actions:" "$TOTAL_ACTIONS"

        # Count by action type
        CREATE_PLAN=$(grep -c '"action_type": "create_plan"' "$LOG_FILE" 2>/dev/null || echo "0")
        CREATE_ACTION=$(grep -c '"action_type": "create_action_file"' "$LOG_FILE" 2>/dev/null || echo "0")
        APPROVALS=$(grep -c '"action_type": "approval_decision"' "$LOG_FILE" 2>/dev/null || echo "0")

        printf "%-20s %s\n" "Plans Created:" "$CREATE_PLAN"
        printf "%-20s %s\n" "Actions Created:" "$CREATE_ACTION"
        printf "%-20s %s\n" "Approvals:" "$APPROVALS"
    else
        echo "No activity today"
    fi
    echo ""

    # Latest Log Entry
    echo -e "${GREEN}📋 Latest Log Entry${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if [ -f "$LOG_FILE" ]; then
        tail -1 "$LOG_FILE" 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "No logs yet"
    else
        echo "No logs yet"
    fi
    echo ""

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "Refreshing in 3 seconds... (Ctrl+C to exit)"

    sleep 3
done
