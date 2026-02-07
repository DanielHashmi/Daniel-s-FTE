@echo off
echo Starting Daniel FTE Dashboard...
echo.

cd /d "%~dp0dashboard"

echo Installing dependencies if needed...
if not exist "node_modules" (
    call npm install
)

echo.
echo ========================================
echo   Dashboard starting on http://localhost:3000
echo   Password: danielsecurepassfornow
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

npm run dev
