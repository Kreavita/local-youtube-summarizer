@echo off

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python.exe -m pip install --upgrade pip

REM Install package in editable mode
python.exe -m pip install -e .

echo Setup complete. Activate with: venv\Scripts\activate
