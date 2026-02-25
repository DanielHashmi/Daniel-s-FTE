@echo off
echo ========================================
echo   ONE-CLICK HACKATHON DEMO
echo ========================================
echo.
echo This will:
echo   1. Open the Dashboard (localhost:3000)
echo   2. Open the Demo Page (DEMO.html)
echo   3. Open Odoo (localhost:8069)
echo.

:: Open Demo HTML directly
start "" "%~dp0DEMO.html"

:: Open Dashboard
start "" "http://localhost:3000/dashboard"

:: Open Odoo
start "" "http://localhost:8069"

echo.
echo ========================================
echo   DEMO IS NOW OPEN IN YOUR BROWSER
echo ========================================
echo.
echo What to show judges:
echo   1. DEMO.html - Shows all Gold features checked
echo   2. Dashboard - Live data from your vault
echo   3. Odoo - Create invoice, see it sync
echo.
pause
