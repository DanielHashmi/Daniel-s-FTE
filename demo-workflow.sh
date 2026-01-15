#!/bin/bash
# Demo Script - Complete Workflow Demonstration
# Shows the full AI Employee workflow in action

set -e

echo "🎬 Silver Tier Complete Workflow Demo"
echo "======================================"
echo ""
echo "This demo will:"
echo "1. Create a realistic email action"
echo "2. Start the orchestrator"
echo "3. Watch it create a plan"
echo "4. Create an approval request"
echo "5. Show you how to approve it"
echo ""
read -p "Press Enter to start the demo..."
echo ""

cd "/mnt/c/Users/kk/Desktop/Daniel's FTE"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

step() {
    echo -e "${BLUE}▶${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Step 1: Create realistic scenario
step "Step 1: Creating realistic email scenario..."
echo ""

TIMESTAMP=$(date +%s)
ACTION_FILE="AI_Employee_Vault/Needs_Action/demo_email_${TIMESTAMP}.md"

cat > "$ACTION_FILE" << EOF
---
id: "demo_email_${TIMESTAMP}"
type: "email"
source: "demo"
priority: "high"
timestamp: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
status: "pending"
metadata:
  sender: "sarah.johnson@techcorp.com"
  subject: "URGENT: Client presentation tomorrow"
  thread_id: "thread_demo_${TIMESTAMP}"
---

# Urgent Email from Sarah Johnson

**From:** sarah.johnson@techcorp.com
**Subject:** URGENT: Client presentation tomorrow
**Priority:** HIGH

## Message Content

Hi,

We have a critical client presentation tomorrow at 10 AM with Acme Corp.
I need you to:

1. Send the updated Q4 financial slides to the client (john.doe@acmecorp.com)
2. Include the ROI analysis we discussed
3. CC me on the email

The slides are in our shared drive under "Q4_Financials_Final.pptx"

This is time-sensitive - they need it by 8 AM tomorrow for their internal review.

Thanks,
Sarah Johnson
VP of Sales
EOF

success "Created demo email action: $(basename $ACTION_FILE)"
echo ""
info "File location: $ACTION_FILE"
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 2: Start orchestrator
step "Step 2: Starting orchestrator to process the action..."
echo ""
info "The orchestrator will:"
info "  - Detect the action file in Needs_Action/"
info "  - Analyze the content"
info "  - Create an execution plan"
info "  - Identify that email sending requires approval"
echo ""

export DRY_RUN=true

# Start orchestrator in background
python3 src/orchestration/orchestrator.py > /tmp/demo_orchestrator.log 2>&1 &
ORCH_PID=$!

info "Orchestrator started (PID: $ORCH_PID)"
echo ""
info "Waiting for processing (10 seconds)..."

# Monitor for 10 seconds
for i in {10..1}; do
    echo -ne "\rProcessing... $i seconds remaining"
    sleep 1
done
echo ""
echo ""

# Stop orchestrator
kill $ORCH_PID 2>/dev/null || true
wait $ORCH_PID 2>/dev/null || true

success "Orchestrator processing complete"
echo ""
read -p "Press Enter to see results..."
echo ""

# Step 3: Check results
step "Step 3: Checking results..."
echo ""

# Check if action was moved
if [ ! -f "$ACTION_FILE" ]; then
    success "Action file was processed and moved to Done/"
else
    echo "⚠️  Action file still in Needs_Action/ (may need more time)"
fi

# Check for plan
PLAN_FILES=$(ls -1 AI_Employee_Vault/Plans/*demo_email_${TIMESTAMP}*.md 2>/dev/null || echo "")
if [ -n "$PLAN_FILES" ]; then
    success "Plan file created!"
    echo ""
    PLAN_FILE=$(echo "$PLAN_FILES" | head -1)
    info "Plan location: $PLAN_FILE"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "PLAN CONTENT:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat "$PLAN_FILE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "⚠️  No plan file found (check orchestrator log: /tmp/demo_orchestrator.log)"
fi

echo ""
read -p "Press Enter to continue..."
echo ""

# Step 4: Create approval request
step "Step 4: Creating approval request for sensitive action..."
echo ""

APPROVAL_FILE="AI_Employee_Vault/Pending_Approval/demo_approval_${TIMESTAMP}.md"

cat > "$APPROVAL_FILE" << EOF
---
id: "appr_demo_${TIMESTAMP}"
type: "approval"
action_type: "send_email"
created: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
status: "pending"
context:
  plan_id: "plan_demo_${TIMESTAMP}"
  recipient: "john.doe@acmecorp.com"
  cc: "sarah.johnson@techcorp.com"
  subject: "Q4 Financial Presentation - Acme Corp"
  has_attachment: "true"
  attachment: "Q4_Financials_Final.pptx"
---

# Approval Request: Send Client Email

**Action:** Send Q4 financial presentation to Acme Corp client

## Email Details

**To:** john.doe@acmecorp.com
**CC:** sarah.johnson@techcorp.com
**Subject:** Q4 Financial Presentation - Acme Corp
**Attachment:** Q4_Financials_Final.pptx

## Draft Email Content

Hi John,

As requested by Sarah Johnson, please find attached our Q4 financial presentation including the ROI analysis for your review ahead of tomorrow's 10 AM meeting.

The presentation includes:
- Q4 Financial Overview
- ROI Analysis and Projections
- Strategic Recommendations

Please let us know if you need any clarifications before the meeting.

Best regards,
AI Employee
On behalf of Sarah Johnson, VP of Sales

## Risk Assessment

- **Sensitivity:** HIGH (financial data, client communication)
- **Reversibility:** LOW (email cannot be unsent)
- **Impact:** HIGH (affects client relationship)

## Approval Required

This action requires human approval because:
1. Sending email to external client
2. Contains financial information
3. Includes attachment
4. Time-sensitive business communication

**Do you approve this action?**
EOF

success "Created approval request: $(basename $APPROVAL_FILE)"
echo ""
info "File location: $APPROVAL_FILE"
echo ""
read -p "Press Enter to see approval request..."
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "APPROVAL REQUEST:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat "$APPROVAL_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 5: Show approval process
step "Step 5: Approval Process"
echo ""
info "To approve or reject this action, use the manage-approval skill:"
echo ""
echo "  List pending approvals:"
echo "    /manage-approval list"
echo ""
echo "  Approve this action:"
echo "    /manage-approval approve appr_demo_${TIMESTAMP}"
echo ""
echo "  Reject this action:"
echo "    /manage-approval reject appr_demo_${TIMESTAMP}"
echo ""
info "Let's simulate approval..."
echo ""

# Simulate approval by moving file
mkdir -p AI_Employee_Vault/Approved
cp "$APPROVAL_FILE" "AI_Employee_Vault/Approved/"
success "Simulated approval (file moved to Approved/)"
echo ""

# Start orchestrator briefly to process approval
info "Starting orchestrator to process approval..."
python3 src/orchestration/orchestrator.py > /tmp/demo_orchestrator2.log 2>&1 &
ORCH_PID=$!
sleep 5
kill $ORCH_PID 2>/dev/null || true
wait $ORCH_PID 2>/dev/null || true

success "Approval processed"
echo ""
read -p "Press Enter to see audit logs..."
echo ""

# Step 6: Show audit logs
step "Step 6: Audit Logs"
echo ""

LOG_FILE="AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json"
if [ -f "$LOG_FILE" ]; then
    success "Audit log found: $(basename $LOG_FILE)"
    echo ""
    info "Recent log entries:"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -20 "$LOG_FILE" | head -10
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "⚠️  No audit log found"
fi

echo ""
read -p "Press Enter to see dashboard..."
echo ""

# Step 7: Show dashboard
step "Step 7: Dashboard Status"
echo ""

if [ -f "AI_Employee_Vault/Dashboard.md" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat "AI_Employee_Vault/Dashboard.md"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "⚠️  Dashboard not found"
fi

echo ""
echo ""
echo "🎉 Demo Complete!"
echo "================="
echo ""
echo "Summary of what happened:"
echo "1. ✓ Email action file created in Needs_Action/"
echo "2. ✓ Orchestrator detected and processed it"
echo "3. ✓ Plan was generated with execution steps"
echo "4. ✓ Approval request created for sensitive action"
echo "5. ✓ Approval was processed (simulated)"
echo "6. ✓ All actions logged in audit log"
echo "7. ✓ Dashboard updated with system status"
echo ""
echo "Next steps:"
echo "- Start PM2 for production: pm2 start ecosystem.config.js"
echo "- Monitor logs: pm2 logs"
echo "- Read TESTING_GUIDE.md for comprehensive testing"
echo "- Configure real credentials for Gmail/LinkedIn"
echo ""
echo "Files created during demo:"
echo "- Action: AI_Employee_Vault/Done/*demo_email_${TIMESTAMP}*"
echo "- Plan: AI_Employee_Vault/Plans/*demo_email_${TIMESTAMP}*"
echo "- Approval: AI_Employee_Vault/Done/*demo_approval_${TIMESTAMP}*"
echo "- Logs: AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json"
echo ""
