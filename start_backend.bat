@echo off
echo Starting ProfileIQ Backend...
cd /d "%~dp0backend"
py -3.11 -m uvicorn main:app --reload --port 8001
