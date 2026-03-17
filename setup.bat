@echo off

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
pip install --upgrade pip

REM Install package in editable mode
pip install -e .

echo Setup complete. Activate with: venv\Scripts\activate.bat
