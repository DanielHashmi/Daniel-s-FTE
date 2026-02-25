# Quick Start - Run Dashboard Locally

Write-Host "🚀 Starting Daniel FTE Dashboard..." -ForegroundColor Cyan

# Navigate to dashboard
Set-Location "$PSScriptRoot\..\dashboard"

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Start dev server
Write-Host ""
Write-Host "✅ Starting development server..." -ForegroundColor Green
Write-Host "🌐 Open http://localhost:3000 in your browser" -ForegroundColor Cyan
Write-Host "🔑 Password: danielsecurepassfornow" -ForegroundColor Yellow
Write-Host ""

npm run dev
