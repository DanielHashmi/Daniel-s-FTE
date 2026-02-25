@echo off
echo Starting the AI Brain (Orchestrator)...
echo Mode: Local orchestrator (watchers + HITL approvals + execution)

REM Prefer the locally-installed pythoncore runtime if present (common on this machine),
REM otherwise fall back to `python` (must be on PATH).
set "PYTHON_EXE="
for /d %%D in ("%LOCALAPPDATA%\Python\pythoncore-*") do (
    if exist "%%D\python.exe" (
        set "PYTHON_EXE=%%D\python.exe"
    )
)
if not defined PYTHON_EXE (
    set "PYTHON_EXE=python"
)

echo Using Python: %PYTHON_EXE%
"%PYTHON_EXE%" -m src.orchestration.orchestrator
pause
