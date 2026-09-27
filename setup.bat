@echo off
setlocal
cd /d "%~dp0"

echo Setting up embedded Python and required packages...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_embedded_python.ps1"
if errorlevel 1 (
  echo.
  echo Setup failed. Please check the messages above.
  pause
  exit /b 1
)

echo.
echo Setup completed successfully.
pause