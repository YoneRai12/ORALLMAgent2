#!/usr/bin/env bash
# Setup script for Linux / WSL environments.
# Creates a virtual environment and installs dependencies.
set -e
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
