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

# 4) Clear macOS Gatekeeper quarantine flags (macOS only)
if command -v xattr >/dev/null 2>&1; then
  echo "🔓 Clearing macOS Gatekeeper quarantine flags..."
  xattr -dr com.apple.quarantine "$(pwd)"
  echo "✅ Quarantine flags cleared."
fi