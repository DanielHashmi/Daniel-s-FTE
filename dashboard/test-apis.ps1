#!/usr/bin/env pwsh
# Test Real Dashboard APIs

$BASE_URL = "http://localhost:3000"

Write-Host "🧪 Testing AI Employee Dashboard APIs..." -ForegroundColor Cyan
Write-Host ""

# Test 1: FTE Status
Write-Host "1️⃣ Testing FTE Status..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/fte/status" -Method Get
    Write-Host "✅ FTE Status: $($response.running)" -ForegroundColor Green
    Write-Host "   Services: $($response.services.Count)" -ForegroundColor Gray
} catch {
    Write-Host "❌ FTE Status failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 2: Approvals
Write-Host "2️⃣ Testing Approvals..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/approvals" -Method Get
    Write-Host "✅ Approvals: $($response.approvals.Count) pending" -ForegroundColor Green
    if ($response.approvals.Count -gt 0) {
        Write-Host "   First: $($response.approvals[0].title)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Approvals failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 3: Social Posts
Write-Host "3️⃣ Testing Social Posts..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/social/posts" -Method Get
    Write-Host "✅ Social Posts: $($response.posts.Count) total" -ForegroundColor Green
} catch {
    Write-Host "❌ Social Posts failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 4: Email Inbox
Write-Host "4️⃣ Testing Email Inbox..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/email/inbox" -Method Get
    Write-Host "✅ Emails: $($response.emails.Count) emails, $($response.drafts.Count) drafts" -ForegroundColor Green
} catch {
    Write-Host "❌ Email Inbox failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 5: Logs
Write-Host "5️⃣ Testing Logs..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/logs" -Method Get
    Write-Host "✅ Logs: $($response.logs.Count) entries" -ForegroundColor Green
} catch {
    Write-Host "❌ Logs failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 6: Settings
Write-Host "6️⃣ Testing Settings..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/settings" -Method Get
    Write-Host "✅ Settings:" -ForegroundColor Green
    Write-Host "   Dry Run: $($response.settings.dryRun)" -ForegroundColor Gray
    Write-Host "   HITL: $($response.settings.hitl)" -ForegroundColor Gray
    Write-Host "   Integrations: $($response.integrations.Count)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Settings failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 7: Briefing
Write-Host "7️⃣ Testing Briefing..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/briefing" -Method Get
    Write-Host "✅ Briefing Stats:" -ForegroundColor Green
    Write-Host "   Tasks: $($response.stats.tasksCompleted)" -ForegroundColor Gray
    Write-Host "   Emails: $($response.stats.emailsProcessed)" -ForegroundColor Gray
    Write-Host "   Social: $($response.stats.socialPosts)" -ForegroundColor Gray
    Write-Host "   Pending: $($response.stats.approvalsPending)" -ForegroundColor Gray
    Write-Host "   Time Saved: $($response.stats.timeSaved)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Briefing failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 8: Accounting
Write-Host "8️⃣ Testing Accounting..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/odoo/summary" -Method Get
    Write-Host "✅ Accounting:" -ForegroundColor Green
    Write-Host "   Revenue: `$$($response.stats.revenue)" -ForegroundColor Gray
    Write-Host "   Expenses: `$$($response.stats.expenses)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Accounting failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "✨ API Testing Complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Create a test social post from the UI"
Write-Host "   2. Try approving it"
Write-Host "   3. Start/stop the FTE from the control page"
Write-Host "   4. Check that files move in AI_Employee_Vault"
Write-Host ""
