@echo off
cd /d "%~dp0"

echo Installing dependencies...
pip install typer rich flask anthropic --quiet

echo Starting server...
start "" python web_ui.py

timeout /t 2 /nobreak >nul

start "" http://localhost:5050
