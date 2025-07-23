#!/usr/bin/env bash
set -e

# 1) Create venv (if it doesn't exist)
python3 -m venv .venv

# 2) Activate it
source .venv/bin/activate

# 3) Upgrade pip and install everything
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Virtualenv created and dependencies installed."
echo "👉 To start using the converter:"
echo "   source .venv/bin/activate"

echo "👉 After setup, run: python export_ucalgary_anki.py and follow the on-screen prompts to log in, choose your deck URL, and specify where to save the .apkg file."