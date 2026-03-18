#!/bin/bash

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
python3 -m pip install --upgrade pip

# Install package in editable mode
pip install -e .

echo "Setup complete. Activate with: source venv/bin/activate"
