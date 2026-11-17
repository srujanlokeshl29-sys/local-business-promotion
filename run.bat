@echo off
cd /d "%~dp0"
echo ===================================================
echo Starting LocalBiz Portal...
echo ===================================================
venv\Scripts\python.exe app.py
pause
