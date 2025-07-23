#!/usr/bin/env bash
set -e

# ANKI CONVERTER SETUP SCRIPT
# This script sets up the Python environment and dependencies for the UCalgary Anki Converter
# Compatible with macOS, Linux, and Windows (via Git Bash/WSL)

echo "🚀 Setting up UCalgary Anki Converter..."
echo "================================================"

# Detect OS for platform-specific setup
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS="windows"
fi

echo "🔍 Detected OS: $OS"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required system dependencies
echo "📋 Checking system requirements..."

# Check Python
if command_exists python3; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
elif command_exists python; then
    PYTHON_CMD="python"
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
else
    echo "❌ ERROR: Python not found. Please install Python 3.8+ first."
    echo "   Download from: https://www.python.org/downloads/"
    exit 1
fi

# Validate Python version
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 8 ]]; then
    echo "❌ ERROR: Python 3.8+ required. Found: $PYTHON_VERSION"
    echo "   Please upgrade Python: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Check pip
if command_exists pip3; then
    PIP_CMD="pip3"
elif command_exists pip; then
    PIP_CMD="pip"
else
    echo "❌ ERROR: pip not found. Installing pip..."
    if [[ $OS == "linux" ]]; then
        sudo apt update && sudo apt install -y python3-pip
    elif [[ $OS == "macos" ]]; then
        $PYTHON_CMD -m ensurepip --upgrade
    else
        echo "Please install pip manually: https://pip.pypa.io/en/stable/installation/"
        exit 1
    fi
    PIP_CMD="pip3"
fi

echo "✅ pip found"

# Check Git
if ! command_exists git; then
    echo "❌ ERROR: Git not found. Please install Git first."
    case $OS in
        "linux")
            echo "   Run: sudo apt install git"
            ;;
        "macos")
            echo "   Run: brew install git"
            echo "   Or install Xcode Command Line Tools"
            ;;
        "windows")
            echo "   Download from: https://git-scm.com/download/win"
            ;;
    esac
    exit 1
fi

echo "✅ Git found"

# Check Google Chrome
CHROME_FOUND=false
if command_exists google-chrome || command_exists google-chrome-stable; then
    CHROME_FOUND=true
elif command_exists "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; then
    CHROME_FOUND=true
elif [[ -f "/c/Program Files/Google/Chrome/Application/chrome.exe" ]] || [[ -f "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" ]]; then
    CHROME_FOUND=true
fi

if [[ $CHROME_FOUND == false ]]; then
    echo "⚠️  WARNING: Google Chrome not detected."
    echo "   The script requires Chrome for web automation."
    echo "   Download from: https://www.google.com/chrome/"
    echo "   You can continue setup, but install Chrome before running the converter."
else
    echo "✅ Google Chrome found"
fi

echo ""
echo "🔧 Setting up Python environment..."

# Remove existing venv if it exists and is corrupted
if [[ -d ".venv" ]]; then
    echo "📁 Found existing virtual environment"
    
    # Test if venv is working
    if source .venv/bin/activate 2>/dev/null && python --version >/dev/null 2>&1; then
        echo "✅ Existing virtual environment is working"
        deactivate 2>/dev/null || true
    else
        echo "🗑️  Removing corrupted virtual environment"
        rm -rf .venv
    fi
fi

# Create virtual environment if it doesn't exist
if [[ ! -d ".venv" ]]; then
    echo "📦 Creating new virtual environment..."
    $PYTHON_CMD -m venv .venv
    
    if [[ ! -d ".venv" ]]; then
        echo "❌ ERROR: Failed to create virtual environment"
        echo "   Try running: $PYTHON_CMD -m pip install --user virtualenv"
        exit 1
    fi
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
if [[ $OS == "windows" ]]; then
    source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
else
    source .venv/bin/activate
fi

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "❌ ERROR: Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"

# Upgrade pip and setuptools
echo "⬆️  Upgrading pip and setuptools..."
python -m pip install --upgrade pip setuptools wheel

# Install requirements
echo "📥 Installing Python dependencies..."
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed successfully"
else
    echo "❌ ERROR: requirements.txt not found"
    exit 1
fi

# Platform-specific security setup
echo ""
echo "🔐 Configuring security settings..."

case $OS in
    "macos")
        # Remove quarantine attributes that might block execution
        echo "🍎 Configuring macOS security..."
        xattr -d com.apple.quarantine . 2>/dev/null || true
        xattr -d com.apple.quarantine export_ucalgary_anki.py 2>/dev/null || true
        chmod +x export_ucalgary_anki.py
        ;;
    "linux")
        echo "� Configuring Linux permissions..."
        chmod +x export_ucalgary_anki.py
        chmod +x setup.sh
        ;;
    "windows")
        echo "🪟 Windows setup complete"
        echo "   Note: If you get execution policy errors, run in PowerShell as Admin:"
        echo "   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
        ;;
esac

# Create config directory with proper permissions
CONFIG_DIR="$HOME/.config/ucalgary_anki"
if [[ ! -d "$CONFIG_DIR" ]]; then
    mkdir -p "$CONFIG_DIR"
    chmod 700 "$CONFIG_DIR" 2>/dev/null || true
fi

# Verify installation
echo ""
echo "🧪 Verifying installation..."

# Test imports
if python -c "import selenium, genanki, requests, tqdm; print('All modules imported successfully')" 2>/dev/null; then
    echo "✅ All Python packages verified"
else
    echo "❌ ERROR: Some packages failed to import"
    echo "   Try running: pip install -r requirements.txt --force-reinstall"
    exit 1
fi

# Test GUI support (tkinter)
echo "🖥️  Checking GUI support..."
if python -c "import tkinter; print('GUI support available')" 2>/dev/null; then
    echo "✅ GUI file dialogs will be available"
    GUI_SUPPORT=true
else
    echo "⚠️  GUI support not available - will use command line dialogs"
    GUI_SUPPORT=false
    
    if [[ $OS == "linux" ]]; then
        echo "   To enable GUI dialogs on Linux, install tkinter:"
        echo "   sudo apt install python3-tk"
        echo "   Then re-run this setup script"
    elif [[ $OS == "macos" ]]; then
        echo "   GUI support should be available on macOS by default"
        echo "   You may need to reinstall Python with GUI support"
    elif [[ $OS == "windows" ]]; then
        echo "   GUI support should be available on Windows by default"
        echo "   You may need to reinstall Python with full features"
    fi
fi

# Create activation helper script
cat > activate.sh << 'EOF'
#!/bin/bash
# This script should be sourced, not executed directly
# Usage: source activate.sh

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "⚠️  This script should be sourced, not executed directly!"
    echo "✅ Use: source activate.sh"
    echo "   or: . activate.sh"
    exit 1
fi

source .venv/bin/activate
echo "✅ Virtual environment activated"
echo "🚀 Run: python export_ucalgary_anki.py"
EOF
chmod +x activate.sh

# Create Windows activation script
cat > activate.bat << 'EOF'
@echo off
echo Activating Python virtual environment...
call .venv\Scripts\activate.bat
echo.
echo Virtual environment activated
echo Run: python export_ucalgary_anki.py
echo.
echo This window will stay open so you can run commands.
echo To run the converter, type: python export_ucalgary_anki.py
echo To exit, type: exit
echo.
cmd /k
EOF

# Create PowerShell activation script for Windows
cat > activate.ps1 << 'EOF'
Write-Host "🔌 Activating Python virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1
Write-Host ""
Write-Host "✅ Virtual environment activated" -ForegroundColor Green  
Write-Host "🚀 Run: python export_ucalgary_anki.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "This PowerShell window will stay open for you to run commands." -ForegroundColor Cyan
Write-Host "Type 'exit' to close when done." -ForegroundColor Cyan
EOF

echo ""
echo "🎉 Setup completed successfully!"
echo "================================================"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1️⃣  Activate the environment:"
if [[ $OS == "windows" ]]; then
    echo "   Windows CMD:      Double-click activate.bat"
    echo "   Windows PowerShell: Right-click activate.ps1 → Run with PowerShell"
    echo "   Or manually:      .venv\\Scripts\\activate"
else
    echo "   macOS/Linux:  source .venv/bin/activate"
    echo "               or: source activate.sh"
    echo "               or: . activate.sh"
    echo ""
    echo "   ⚠️  NOTE: Use 'source' or '.' - do NOT run './activate.sh'"
    echo "       Running with './' won't activate the environment in your current shell"
fi
echo ""
echo "2️⃣  Run the converter:"
echo "   python export_ucalgary_anki.py"
echo ""
echo "3️⃣  Follow the prompts to:"
echo "   • Enter your UCalgary credentials (saved securely)"
echo "   • Provide the deck URL"
if [[ $GUI_SUPPORT == true ]]; then
    echo "   • Use the file dialog to choose where to save your .apkg file"
else
    echo "   • Type the path where you want to save your .apkg file"
fi
echo ""
echo "📁 Files created:"
echo "   • .venv/          - Python virtual environment"
echo "   • activate.sh     - Quick activation script (Unix)"
echo "   • activate.bat    - Quick activation script (Windows Command Prompt)"
echo "   • activate.ps1    - Quick activation script (Windows PowerShell)"
echo ""
echo "🔒 Security notes:"
echo "   • Credentials saved in: ~/.uc_anki_config.json"
echo "   • Delete this file to reset saved login"
echo "   • Virtual environment isolates dependencies"
if [[ $GUI_SUPPORT == true ]]; then
    echo "   • GUI file dialogs provide secure file selection"
fi
echo ""
if [[ $CHROME_FOUND == false ]]; then
    echo "⚠️  REMINDER: Install Google Chrome before running the converter"
    echo "   Download: https://www.google.com/chrome/"
    echo ""
fi
if [[ $GUI_SUPPORT == true ]]; then
    echo "🎯 Ready to convert UCalgary Cards to Anki decks with GUI dialogs!"
else
    echo "🎯 Ready to convert UCalgary Cards to Anki decks!"
    echo "   (Command line interface - consider installing GUI support for better experience)"
fi