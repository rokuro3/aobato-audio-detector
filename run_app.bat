@echo off
setlocal
cd /d "%~dp0"
if not exist "python\python.exe" (
  echo Embedded Python is not installed. Double-click setup.bat first.
  pause
  exit /b 1
)
python\python.exe -m streamlit run app.py
pause