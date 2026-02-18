@echo off
setlocal

echo Starting the AI Brain (Cloud Drafter)...
set "AGENT_ROLE=cloud"
set "AGENT_ID=cloud-agent-001"
echo AGENT_ROLE=%AGENT_ROLE%
echo AGENT_ID=%AGENT_ID%

REM Prefer the locally-installed pythoncore runtime if present,
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

