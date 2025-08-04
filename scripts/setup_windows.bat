@echo off
rem Setup script for Windows CMD
python -m venv .venv
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
playwright install
