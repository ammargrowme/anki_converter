#!/usr/bin/env bash
set -e

# ANKI CONVERTER SETUP SCRIPT
# This script sets up the Python environment and dependencies for the UCalgary Anki Converter
# Compatible with macOS, Linux, and Windows (via Git Bash/WSL)

echo "🚀 Setting up UCalgary Anki Converter..."
echo "======        echo "🐧 Configuring Linux permissions..."
        chmod +x main.py 2>/dev/null || true
        chmod +x export_ucalgary_anki.py 2>/dev/null || true
        chmod +x export_ucalgary_anki_debug.py 2>/dev/null || true
        chmod +x setup.sh======================================="

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

# macOS-specific: Check and install Homebrew if needed
if [[ $OS == "macos" ]]; then
    if ! command_exists brew; then
        echo "📦 Homebrew not found. Installing Homebrew..."
        echo "   This will make installing dependencies much easier!"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for this session
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            export PATH="/opt/homebrew/bin:$PATH"
        elif [[ -f "/usr/local/bin/brew" ]]; then
            export PATH="/usr/local/bin:$PATH"
        fi
        
        if command_exists brew; then
            echo "✅ Homebrew installed successfully"
        else
            echo "⚠️  Homebrew installation may have failed"
            echo "   You may need to restart Terminal and re-run this script"
        fi
    else
        echo "✅ Homebrew found"
    fi
fi

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
        echo "   Installing pip via apt..."
        sudo apt update && sudo apt install -y python3-pip
    elif [[ $OS == "macos" ]]; then
        echo "   Installing pip..."
        if command_exists brew; then
            echo "   Using Homebrew to ensure pip is available..."
            brew install python3 2>/dev/null || true
        fi
        $PYTHON_CMD -m ensurepip --upgrade
    else
        echo "   Please install pip manually: https://pip.pypa.io/en/stable/installation/"
        exit 1
    fi
    PIP_CMD="pip3"
fi

echo "✅ pip found"

# Check Git
if ! command_exists git; then
    echo "❌ ERROR: Git not found. Installing Git..."
    case $OS in
        "linux")
            echo "   Installing Git via apt..."
            if sudo apt update && sudo apt install -y git; then
                echo "✅ Git installed successfully"
            else
                echo "   ❌ Failed to install Git automatically"
                echo "   Please run: sudo apt install git"
                exit 1
            fi
            ;;
        "macos")
            if command_exists brew; then
                echo "   Installing Git via Homebrew..."
                if brew install git; then
                    echo "✅ Git installed successfully"
                else
                    echo "   ❌ Failed to install Git via Homebrew"
                    echo "   Try: xcode-select --install"
                    exit 1
                fi
            else
                echo "   Installing Xcode Command Line Tools (includes Git)..."
                echo "   A dialog will appear - click 'Install'"
                xcode-select --install
                echo "   After installation completes, re-run this script"
                exit 0
            fi
            ;;
        "windows")
            echo "   Please download Git from: https://git-scm.com/download/win"
            echo "   After installation, re-run this script"
            exit 1
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
    
    # Attempt automatic installation
    case $OS in
        "macos")
            if command_exists brew; then
                echo "   Attempting to install Chrome via Homebrew..."
                if brew install --cask google-chrome 2>/dev/null; then
                    echo "✅ Google Chrome installed successfully!"
                    CHROME_FOUND=true
                else
                    echo "   ❌ Automatic installation failed"
                    echo "   Download manually from: https://www.google.com/chrome/"
                fi
            else
                echo "   Download from: https://www.google.com/chrome/"
            fi
            ;;
        "linux")
            echo "   Attempting to install Chrome via package manager..."
            if command_exists apt; then
                # Add Google's APT repository and install Chrome
                if wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add - 2>/dev/null && \
                   echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list >/dev/null && \
                   sudo apt update 2>/dev/null && \
                   sudo apt install -y google-chrome-stable 2>/dev/null; then
                    echo "✅ Google Chrome installed successfully!"
                    CHROME_FOUND=true
                else
                    echo "   ❌ Automatic installation failed"
                    echo "   Download from: https://www.google.com/chrome/"
                fi
            else
                echo "   Download from: https://www.google.com/chrome/"
            fi
            ;;
        "windows")
            echo "   Download from: https://www.google.com/chrome/"
            ;;
    esac
    
    if [[ $CHROME_FOUND == false ]]; then
        echo "   You can continue setup, but install Chrome before running the converter."
    fi
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
        xattr -d com.apple.quarantine main.py 2>/dev/null || true
        xattr -d com.apple.quarantine export_ucalgary_anki.py 2>/dev/null || true
        xattr -d com.apple.quarantine export_ucalgary_anki_debug.py 2>/dev/null || true
        chmod +x main.py 2>/dev/null || true
        chmod +x export_ucalgary_anki.py 2>/dev/null || true
        chmod +x export_ucalgary_anki_debug.py 2>/dev/null || true
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
        echo "   Attempting to install GUI support for macOS..."
        if command_exists brew; then
            echo "   Installing python-tk via Homebrew..."
            brew install python-tk 2>/dev/null || true
            # Test again after installation
            if python -c "import tkinter" 2>/dev/null; then
                echo "✅ GUI support successfully installed!"
                GUI_SUPPORT=true
            else
                echo "   ⚠️  Could not install GUI support automatically"
                echo "   Try: brew install python-tk"
                echo "   Or reinstall Python with GUI support"
            fi
        else
            echo "   GUI support should be available on macOS by default"
            echo "   You may need to reinstall Python with GUI support"
            echo "   Or install Homebrew and run: brew install python-tk"
        fi
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
echo "🚀 Choose your version:"
echo "   python main.py               # Modular (recommended)"
echo "   python export_ucalgary_anki_debug.py  # Debug version"
EOF
chmod +x activate.sh

# Create Windows activation script
cat > activate.bat << 'EOF'
@echo off
echo Activating Python virtual environment...
call .venv\Scripts\activate.bat
echo.
echo Virtual environment activated
echo Run your preferred version:
echo   python main.py               # Modular (recommended)
echo   python export_ucalgary_anki_debug.py  # Debug version
echo.
echo This window will stay open so you can run commands.
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
Write-Host "🚀 Choose your version:" -ForegroundColor Yellow
Write-Host "   python main.py               # Modular (recommended)" -ForegroundColor Yellow
Write-Host "   python export_ucalgary_anki_debug.py  # Debug version" -ForegroundColor Yellow
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
echo "   # Choose your preferred version:"
echo "   "
echo "   # Modular version (recommended):"
echo "   python main.py"
echo "   "
echo "   # Debug version (for troubleshooting):"
echo "   python export_ucalgary_anki_debug.py"
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
echo "💡 Optional: Test your setup first with: python test_setup.py"
echo ""
echo "📁 Files created:"
echo "   • .venv/          - Python virtual environment"
echo "   • activate.sh     - Quick activation script (Unix)"
echo "   • activate.bat    - Quick activation script (Windows Command Prompt)"
echo "   • activate.ps1    - Quick activation script (Windows PowerShell)"
echo "   • test_setup.py   - System verification script"
echo ""
echo "🔒 Security notes:"
echo "   • Credentials saved in: ~/.uc_anki_config.json"
echo "   • Delete this file to reset saved login"
echo "   • Virtual environment isolates dependencies"
if [[ $GUI_SUPPORT == true ]]; then
    echo "   • GUI file dialogs provide secure file selection"
fi
echo ""

# Final comprehensive system check
echo "🔍 Final System Verification:"
echo "================================================"

# Check all critical components
SYSTEM_READY=true

# Check Python
if python --version >/dev/null 2>&1; then
    echo "✅ Python: $(python --version 2>&1)"
else
    echo "❌ Python: Not working"
    SYSTEM_READY=false
fi

# Check virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "✅ Virtual Environment: Active ($VIRTUAL_ENV)"
else
    echo "❌ Virtual Environment: Not active"
    SYSTEM_READY=false
fi

# Check critical packages
if python -c "import selenium" 2>/dev/null; then
    echo "✅ Selenium: Available"
else
    echo "❌ Selenium: Missing"
    SYSTEM_READY=false
fi

if python -c "import genanki" 2>/dev/null; then
    echo "✅ Genanki: Available"
else
    echo "❌ Genanki: Missing"
    SYSTEM_READY=false
fi

# Check GUI support
if python -c "import tkinter" 2>/dev/null; then
    echo "✅ GUI Support: Available"
else
    echo "⚠️  GUI Support: Command line only"
fi

# Check Chrome
if [[ $CHROME_FOUND == true ]]; then
    echo "✅ Google Chrome: Found"
else
    echo "⚠️  Google Chrome: Not found (install before running)"
fi

# Check main script
MAIN_SCRIPT_READY=false
if [[ -f "main.py" ]]; then
    echo "✅ Main Script (Modular): Ready"
    MAIN_SCRIPT_READY=true
elif [[ -f "export_ucalgary_anki.py" ]]; then
    echo "✅ Main Script (Modular): Ready"
    MAIN_SCRIPT_READY=true
fi

if [[ -f "export_ucalgary_anki_debug.py" ]]; then
    echo "✅ Debug Script: Ready"
else
    echo "⚠️  Debug Script: Missing"
fi

if [[ $MAIN_SCRIPT_READY == false ]]; then
    echo "❌ Main Script: Missing (need main.py or export_ucalgary_anki.py)"
    SYSTEM_READY=false
fi

echo "================================================"

if [[ $SYSTEM_READY == true ]]; then
    echo "🎉 System is fully ready!"
else
    echo "⚠️  System has some issues - check the items marked with ❌ above"
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