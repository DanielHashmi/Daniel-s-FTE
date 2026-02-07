@echo off
echo Starting Odoo 16 Local Environment...
docker-compose -f docker-compose-odoo.yml up -d
echo.
echo ========================================================
echo   Odoo is starting on http://localhost:8069
echo ========================================================
echo.
echo 1. Open http://localhost:8069 in your browser
echo 2. Create a new database with these EXACT details:
echo    - Master Password: admin (or whatever you set/it asks)
echo    - Database Name: odoo
echo    - Email: admin
echo    - Password: admin
echo    - Check "Demo data" (IMPORTANT for testing!)
echo.
echo 3. After login, go to Apps and install "Invoicing" (or Accounting)
echo.
pause
