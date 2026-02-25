@echo off
setlocal

set "EDGE_EXE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE_EXE%" set "EDGE_EXE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE_EXE%" (
  echo Could not find Microsoft Edge executable.
  exit /b 1
)

set "USER_DATA_DIR=%LOCALAPPDATA%\Microsoft\Edge\User Data"
set "PROFILE_NAME=Profile 1"
set "CDP_PORT=9222"

echo.
echo Starting Edge with remote debugging on port %CDP_PORT% using profile "%PROFILE_NAME%".
echo If normal Edge windows are already open, close them first so debug mode can bind successfully.
echo.

start "" "%EDGE_EXE%" --remote-debugging-port=%CDP_PORT% --user-data-dir="%USER_DATA_DIR%" --profile-directory="%PROFILE_NAME%" http://localhost:3000/dashboard/social

echo Edge launch command sent.
echo Keep this Edge window running while Instagram approvals execute.
echo.

endlocal
