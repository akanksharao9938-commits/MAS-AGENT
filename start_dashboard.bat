@echo off
cd /d "%~dp0"
echo Starting Multi-Agent AI Dashboard...
".venv\Scripts\python.exe" -m streamlit run dashboard.py
pause
