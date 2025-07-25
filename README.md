# UCalgary Cards to Anki Converter

**Repository:** [https://github.com/ammargrowme/anki_converter.git](https://github.com/ammargrowme/anki_converter.git)

[![GitHub Repo stars](https://img.shields.io/github/stars/ammargrowme/anki_converter)](https://github.com/ammargrowme/anki_converter)

A command-line tool that logs into the University of Calgary Cards site, scrapes question-and-answer cards, and generates a ready-to-import Anki `.apkg` deck using Selenium and Genanki.

## 🚀 Quick Start Options

**Choose your version:**

### Option A: **Simplified Modular Version** _(Recommended for most users)_

```bash
python main.py
```

- Clean, modular codebase
- Easy to maintain and understand
- All features included
- Faster startup

### Option B: **Debug Version** _(For development/troubleshooting)_

```bash
python export_ucalgary_anki_debug.py
```

- Single file with extensive logging
- Helpful for debugging issues
- All features included
- More verbose output

Both versions produce identical results - choose based on your preference!

## 📖 Documentation

This comprehensive guide covers everything from basic setup to advanced troubleshooting. For the quickest start, see the [Quick Start](#quick-start-beginner-friendly) section below.

## 🔄 Version Comparison

| Feature               | Modular Version (`main.py`) | Debug Version (`export_ucalgary_anki_debug.py`) |
| --------------------- | --------------------------- | ----------------------------------------------- |
| **Recommended for**   | Most users                  | Troubleshooting & development                   |
| **Code organization** | Multiple files, clean       | Single file                                     |
| **Startup speed**     | Faster                      | Slightly slower                                 |
| **Debug output**      | Minimal, clean              | Extensive logging                               |
| **Maintenance**       | Easy to update              | Harder to modify                                |
| **Results**           | ✅ Identical                | ✅ Identical                                    |

**Features:**

- ✨ **Automatic Setup**: Installs all dependencies including Chrome, Python packages, and GUI support
- 🔧 **Cross-Platform**: Works on macOS, Linux, and Windows with automatic OS detection
- 🎯 **Smart Installation**: Automatically installs missing components (Homebrew, Git, Chrome, tkinter)
- 💾 **Modern GUI**: File dialogs for easy deck saving (with command-line fallback)
- 📊 **Interactive Cards**: Preserves multiple-choice functionality in Anki
- 🔄 **Multi-Patient Support**: Handles decks with multiple cards per patient
- 📚 **Collection Support**: Convert entire collections with multiple decks into organized hierarchical Anki decks
- 🏷️ **Smart Tagging**: Automatically tags cards by source deck for easy organization
- 🎯 **Hierarchical Structure**: Creates organized deck structure: Collection → Deck → Patient
- 🎓 **Curriculum Pattern Detection**: Special handling for RIME-style collections (e.g., RIME 1.1.3 → Block::Unit::Week hierarchy)
- 📝 **Proper Deck Names**: Extracts actual deck names (e.g., "Get to know SAWH", "SAWH what is it good for") instead of generic titles
- 🔐 **Secure**: Saves credentials locally with proper encryption
- 📋 **Enhanced Content Extraction**: Captures tables, images, lists, charts, and formatted content from cards
- 🖼️ **Rich Media Support**: Preserves images, diagrams, and visual elements in Anki cards
- 📊 **Table Preservation**: Maintains table formatting and structure in exported cards

---

## Expectations

**Console Output (what you'll see when it works):**

```
🚀 Setting up UCalgary Anki Converter...
✅ Homebrew found
✅ Python 3.13.5 found
✅ pip found
✅ Git found
✅ Google Chrome found
📦 Creating new virtual environment...
✅ GUI support successfully installed!
✅ Dependencies installed successfully
🔍 Final System Verification:
✅ Python: Python 3.13.5
✅ Virtual Environment: Active
✅ Selenium: Available
✅ Genanki: Available
✅ GUI Support: Available
✅ Google Chrome: Found
✅ Main Script: Ready
🎉 System is fully ready!

Loading screen...
Logging in...
Logged in successfully
Scraping cards: 100%|████████████| 6/6 [00:15<00:00, 2.5s/it]

📁 Save Location
[GUI file dialog opens for you to choose save location]

[+] APKG → /Users/YourName/Desktop/Deck_1261.apkg
✅ Success! Created Anki deck with 6 cards.
[Success popup appears with import instructions]
```

**Generated Files:**

- **`Deck_<ID>.apkg`** - Ready-to-import Anki deck file (saved where you chose)
- **`~/.uc_anki_config.json`** - Your saved login credentials (secure)
- **`activate.sh`** / **`activate.bat`** - Easy environment activation scripts

**User Experience:**

- 💾 **Modern file dialogs** - Save files like any desktop application
- 🎉 **Success notifications** - Clear confirmation when complete
- 🔄 **Smart fallback** - Works in command-line environments too
- 📱 **Cross-platform** - Same experience on Windows, Mac, and Linux

**What Gets Scraped:**

- Question text and background context
- **📋 Tables and data grids** - Preserved with original formatting
- **🖼️ Images and diagrams** - Maintained with proper sizing and alt text
- **📝 Lists and formatted text** - Bullet points, numbered lists, and text formatting
- **📊 Charts and graphs** - Visual elements and embedded content
- **🎨 Rich HTML content** - Styled text, emphasis, and structured content
- Multiple choice options (with interactive selection in Anki)
- Free-text question fields
- Correct answers and explanations
- Score information and feedback
- **All cards from multi-patient decks** (e.g., 6 cards from 3 patients)
- **Additional context** - Content from solution areas and workspace containers

**Anki Card Features:**

- ✅ Interactive checkboxes/radio buttons that work in Anki
- 🟢 Green highlighting for correct answers
- 🔴 Red highlighting for incorrect selections
- 📊 Dynamic scoring based on your selections
- 📝 Preserved question formatting and context
- 💡 Explanations and feedback included

**Time Expectations:**

- Setup: 2-5 minutes (one time only)
- Per deck conversion: 30 seconds to 5 minutes depending on deck size
- Each card takes ~2-3 seconds to process

---

## Table of Contents

1. [Quick Start (Beginner-Friendly)](#quick-start-beginner-friendly)
2. [Installation](#installation)
3. [Setup and Configuration](#setup-and-configuration)
4. [Usage](#usage)
5. [URL Examples](#url-examples)
6. [Expectations](#expectations)
7. [Troubleshooting](#troubleshooting)
8. [Tips](#tips)
9. [Full Setup Guides](#full-setup-guides)
10. [Requirements by OS](#requirements-by-os)
11. [Frequently Asked Questions](#frequently-asked-questions)
12. [Security & Privacy](#security--privacy)
13. [Important Notes & Disclaimers](#important-notes--disclaimers)
14. [Development & Technical Details](#development--technical-details)
15. [Development Log & Version History](#development-log--version-history)
16. [Testing & Quality Assurance](#testing--quality-assurance)
17. [Editing Files in Terminal Editors](#editing-files-in-terminal-editors)
18. [Contributing](#contributing)
19. [License](#license)

---

<a id="quick-start-beginner-friendly"></a>

## Quick Start (Beginner-Friendly)

**⚠️ Never coded before? No problem! Follow these exact steps:**

### Option 1: Automatic Setup (Recommended for Beginners)

1. **Download the project:**

   - Go to: https://github.com/ammargrowme/anki_converter
   - Click the green "Code" button → "Download ZIP"
   - Extract the ZIP file to your Desktop

2. **Open the correct terminal for your system:**

   - **Windows:** Press `Windows + R`, type `git bash`, press Enter (or find "Git Bash" in Start Menu)
     - **Important:** Don't use Command Prompt or PowerShell - they won't work with setup.sh
     - If Git Bash isn't installed, download Git from: https://git-scm.com/download/win
   - **Mac:** Press `Cmd + Space`, type `Terminal`, press Enter
   - **Linux:** Press `Ctrl + Alt + T`

3. **Navigate to the project folder:**

   ```bash
   cd Desktop/anki_converter-main
   ```

4. **Run the automatic setup (does everything for you):**

   ```bash
   # For ALL systems (Windows, Mac, Linux):
   # Use Git Bash on Windows - NOT Command Prompt or PowerShell
   bash setup.sh
   ```

   **Windows Users:**

   - ✅ Use Git Bash (comes with Git installation)
   - ❌ Don't use Command Prompt (`cmd`) - it won't work
   - ❌ Don't use PowerShell - it won't work with bash scripts

5. **Follow the setup script instructions** - it will:

   - Check if you have everything needed
   - Install missing components automatically
   - Set up the environment
   - Tell you exactly what to do next

6. **Activate the environment (after setup completes):**

   **All Systems (use these commands in the same terminal):**

   ```bash
   # Activate virtual environment:
   source .venv/bin/activate    # Git Bash, Mac, Linux
   # OR use the helper script:
   source activate.sh
   ```

   **Windows Alternative Options:**

   - **Git Bash:** `source .venv/bin/activate` (recommended, same terminal)
   - **Command Prompt:** Double-click `activate.bat` file
   - **PowerShell:** Right-click `activate.ps1` → "Run with PowerShell"

   **⚠️ Important:**

   - For Git Bash/Mac/Linux: Use `source` or `.` - do NOT run `./activate.sh`
   - You should see `(.venv)` prefix in your terminal after activation

7. **Run the converter:**

   ```bash
   # Test your setup first (optional):
   python test_setup.py

   # Choose your preferred version:

   # Option A: Modular version (recommended)
   python main.py

   # Option B: Debug version (for troubleshooting)
   python export_ucalgary_anki_debug.py
   ```

**✅ How to know it worked:**

- You should see `(.venv)` prefix in your terminal prompt after activation
- The setup script will tell you "Virtual environment activated"
- Running `python --version` should work without errors

### Option 2: Manual Setup (If Automatic Setup Fails)

**Only use this if the automatic setup doesn't work for your system.**

1. **Install prerequisites manually:**

   - Python 3.8+ from: https://www.python.org/downloads/
   - Git from: https://git-scm.com/downloads
   - Google Chrome from: https://www.google.com/chrome/

2. **Clone and setup:**

   ```bash
   git clone https://github.com/ammargrowme/anki_converter.git
   cd anki_converter
   pip install -r requirements.txt
   ```

3. **Run the script:**
   ```bash
   # Choose your preferred version:
   python main.py                           # Modular (recommended)
   python export_ucalgary_anki_debug.py     # Debug version
   ```

**Note:** Manual setup skips virtual environment isolation and automatic dependency management. Use automatic setup when possible.

### What Happens Next:

1. The script asks for your UCalgary email and password (saved securely)
2. **Paste your Cards deck or collection URL** when prompted
3. **For collections**: Watch as it finds and processes each deck automatically
4. **A "Save As" dialog will open** - choose where to save your Anki deck file (just like saving any file!)
5. Import the `.apkg` file into Anki: **File → Import → Select your file**

**✨ New GUI Features:**

- 💾 **File Save Dialog** - No more typing file paths! Click and save like any app
- 🎉 **Success Popup** - Clear confirmation when your deck is ready
- 🔄 **Automatic Fallback** - Uses command line if GUI isn't available

**🚀 Enhanced User Experience:**

- 🔐 **Smart Login Flow** - First-time users see unified login dialog, returning users only enter URLs
- 💾 **Credential Memory** - Valid credentials are preserved even if URL validation fails
- ✅ **Improved URL Validation** - Works correctly with all valid UCalgary deck and collection URLs
- 📱 **Larger Processing Dialog** - Better visibility during card processing
- 🎯 **Clear URL Guidance** - Helpful examples and labels for valid URL formats

---

<a id="requirements-by-os"></a>

## Requirements by OS

### macOS

- Homebrew
- Git
- Python 3
- Chrome
- ChromeDriver

Refer to [Install Homebrew & Dependencies](#install-homebrew--dependencies) and [Clone & Setup Virtualenv](#clone--setup-virtualenv).

### Ubuntu/Debian Linux

- apt package manager
- Git
- Python 3
- pip
- Chrome
- ChromeDriver

Refer to [Full Setup Guides](#full-setup-guides) for complete installation instructions.

### Windows

- Git
- Python 3.8+
- Google Chrome
- ChromeDriver (automatically managed by script)

Refer to [Windows Full Setup](#windows-full-setup) for complete installation instructions.

---

<a id="installation"></a>

## Installation

**🔰 Complete Beginner? Use our automatic setup script instead! See [Quick Start](#quick-start-beginner-friendly)**

**For those comfortable with command line:**

**Prerequisites:** Git, Python 3.8+, and Google Chrome (our setup script can install these for you)

```bash
# Clone the repository
git clone https://github.com/ammargrowme/anki_converter.git
cd anki_converter

# Run automatic setup (recommended)
./setup.sh

# OR install manually:
pip install -r requirements.txt
```

**✅ The setup.sh script will:**

- Check all your system requirements
- Install missing components automatically
- Set up secure Python environment
- Verify everything works
- Give you clear next steps

**Note:** ChromeDriver is automatically downloaded and managed by the script.

---

<a id="setup-and-configuration"></a>

## Setup and Configuration

On first run, the script prompts for your UofC email, password, and target cards URL. Credentials are saved securely in `~/.uc_anki_config.json`. Subsequent runs only ask for the URL.

**First run:**

1. Run: `python main.py` (or `python export_ucalgary_anki_debug.py` for debug version)
2. Enter **UCalgary email** and **password** (up to 3 attempts)
3. On successful login, credentials are saved automatically
4. Enter **deck URL** (details or printdeck URL - see [URL Examples](#url-examples))
5. Choose save location for the `.apkg` file

**Subsequent runs:**

1. Run: `python main.py` (or `python export_ucalgary_anki_debug.py` for debug version)
2. Credentials loaded automatically; only enter **deck URL**
3. Choose save location (defaults to `Deck_<ID>.apkg`)

---

<a id="usage"></a>

## Usage

### Basic Usage

```bash
# Modular version (recommended):
python main.py

# Debug version (for troubleshooting):
python export_ucalgary_anki_debug.py
```

### Advanced Usage Options

**Command Line Arguments:**

```bash
# Run with visible Chrome for debugging
UCALGARY_ANKI_HEADLESS=false python main.py

# Increase timeout for slow connections
UCALGARY_ANKI_TIMEOUT=30 python main.py

# Enable verbose logging (modular version)
UCALGARY_ANKI_DEBUG=true python main.py
```

**Batch Processing:**

```bash
# Process multiple URLs (create a script)
#!/bin/bash
urls=(
    "https://cards.ucalgary.ca/collection/150"
    "https://cards.ucalgary.ca/details/1261?bag_id=151"
    "https://cards.ucalgary.ca/collection/152"
)

for url in "${urls[@]}"; do
    echo "Processing: $url"
    echo "$url" | python main.py
done
```

### Step-by-Step Process

**The script will:**

1. **Initial Setup** (first run only)

   - Prompt for UCalgary email and password
   - Validate credentials by logging into Cards site
   - Save credentials securely to `~/.uc_anki_config.json`

2. **URL Input & Detection**

   - Ask for a UCalgary Cards deck or collection URL
   - **Auto-detect URL type** (individual deck vs. collection)
   - Parse deck/collection IDs automatically

3. **Web Scraping Process**

   - Launch Chrome browser (headless by default)
   - Log into Cards site using saved credentials
   - **For collections**: Find all decks and scrape each one with progress tracking
   - **For individual decks**: Navigate to deck and extract all cards
   - Handle pagination and multi-patient decks automatically

4. **Content Processing**

   - Extract question text, choices, and explanations
   - Download and optimize images
   - Preserve table formatting and HTML structure
   - Generate interactive card elements

5. **Anki Generation**

   - Create Anki deck with proper formatting
   - Add interactive JavaScript for multiple choice
   - **Open "Save As" dialog** for file location selection
   - Generate `.apkg` file ready for import

6. **Completion**
   - **Show success popup** with import instructions
   - Provide file location and import guidance

### URL Format Support

**Individual Deck URLs:**

```
# Details page (recommended)
https://cards.ucalgary.ca/details/{deck_id}?bag_id={bag_id}

# Print deck page (also works)
https://cards.ucalgary.ca/printdeck/{deck_id}?bag_id={bag_id}

# Examples:
https://cards.ucalgary.ca/details/1261?bag_id=151
https://cards.ucalgary.ca/printdeck/1261?bag_id=151
```

**Collection URLs:**

```
# Collection page
https://cards.ucalgary.ca/collection/{collection_id}

# Example:
https://cards.ucalgary.ca/collection/150
```

**How to find your URL:**

1. Log into [cards.ucalgary.ca](https://cards.ucalgary.ca)
2. Navigate to your desired deck or collection
3. Copy the URL from your browser's address bar
4. Paste when prompted by the script

### Import to Anki

**After conversion:**

1. Open Anki desktop application
2. Go to **File → Import**
3. Select your generated `.apkg` file
4. Click **Import**
5. Your deck will appear in Anki's deck list

**Import Options:**

- **Update existing cards**: If you re-import, choose whether to update
- **Deck naming**: Cards will be organized with proper deck names
- **Tags**: Cards are automatically tagged by source deck

### Interactive Features in Anki

**Generated cards support:**

- ✅ **Multiple choice selection**: Click to select answers
- ✅ **Real-time scoring**: See results as you answer
- ✅ **Color coding**: Green for correct, red for incorrect
- ✅ **Explanations**: Detailed feedback and rationales
- ✅ **Rich content**: Tables, images, and formatted text
- ✅ **Mobile compatibility**: Works in AnkiMobile and AnkiDroid

**Card Types Created:**

- **Multiple Choice**: Interactive selection with scoring
- **Free Response**: Open-ended questions with model answers
- **Case-Based**: Multi-part questions with patient scenarios

---

<a id="url-examples"></a>

## URL Examples

The script accepts both **individual deck URLs** and **collection URLs**:

**Individual Deck - Details URL (recommended):**

```
https://cards.ucalgary.ca/details/1261?bag_id=151
```

**Individual Deck - Printdeck URL:**

```
https://cards.ucalgary.ca/printdeck/1261?bag_id=151
```

**Collection URL (NEW!):**

```
https://cards.ucalgary.ca/collection/150
```

**How to find your URL:**

1. Log into cards.ucalgary.ca
2. Navigate to your desired deck or collection
3. Copy the URL from your browser's address bar
4. **For collections**: The script will automatically find all decks in the collection
5. **For individual decks**: The script will automatically detect the deck ID and bag_id

**Collection Benefits:**

- 📚 **One-click conversion**: Convert entire collections with multiple decks
- 🏗️ **Hierarchical organization**: Creates proper structure like "RIME::Block 0::Unit 0::Week 1::Get to know SAWH::Patient Name"
- 📊 **Progress tracking**: See progress for each deck as it's processed
- 🎯 **Comprehensive**: Get all cards from all decks in one organized Anki file
- 👥 **Patient organization**: Automatically extracts and organizes cards by patient names
- 📝 **Proper Deck Names**: Shows actual deck titles like "Get to know SAWH" and "SAWH what is it good for"
- 🎓 **Curriculum Detection**: Automatically detects RIME-style collections for special hierarchical structure

---

<a id="troubleshooting"></a>

## Troubleshooting

**🆘 Need Help? Start Here:**

### ⚠️ IMPORTANT: Terminal Requirements by OS

**Windows Users:**

- ✅ **Use Git Bash** for running `setup.sh` (comes with Git for Windows)
- ❌ **Don't use Command Prompt** (`cmd`) - bash scripts won't work
- ❌ **Don't use PowerShell** - different syntax and won't run bash scripts
- 💡 **After setup:** You can use .bat/.ps1 files for activation if you prefer

**Mac/Linux Users:**

- ✅ **Use Terminal** - built-in bash support
- ✅ **setup.sh works directly** - no special requirements

### First Steps When Something Goes Wrong

1. **Try the automatic setup script first:**

   ```bash
   ./setup.sh
   ```

   It fixes most common issues automatically!

2. **Check the error message** - it usually tells you exactly what's wrong

3. **Make sure you can log into cards.ucalgary.ca manually** in your browser first

### Common Issues for Beginners

**❌ "bash: command not found" or "'bash' is not recognized" (Windows)**

```bash
# Problem: You're using Command Prompt or PowerShell instead of Git Bash
# Solution:
# 1. Install Git for Windows: https://git-scm.com/download/win
# 2. Open Git Bash (NOT cmd or PowerShell)
# 3. Run the setup script in Git Bash
```

**❌ "setup.sh: No such file or directory" (Windows)**

```bash
# Problem: Wrong terminal or wrong directory
# Solution: Make sure you're in Git Bash and in the right folder
cd anki_converter    # Navigate to project folder
ls -la               # Should see setup.sh in the list
bash setup.sh        # Then run setup
```

**❌ ".venv/bin/activate: No such file or directory" (Windows)**

```bash
# Problem: Trying to use Linux activation path on Windows
# Solutions (choose one):

# Option 1: Use Windows activation scripts
activate.bat         # Double-click this file
# OR
activate.ps1         # Right-click → Run with PowerShell

# Option 2: Use Windows path in Git Bash
source .venv/Scripts/activate    # Note: Scripts, not bin

# Option 3: Stay in Git Bash where Linux paths work
source .venv/bin/activate        # Works in Git Bash only
```

**❌ "Permission denied" (Mac/Linux)**

```bash
# Solution: Make the script executable
chmod +x setup.sh
./setup.sh
```

**❌ "Cannot find Chrome or ChromeDriver"**

- **Solution:** Install Google Chrome from https://www.google.com/chrome/
- The script handles ChromeDriver automatically

**❌ "Login failed"**

- ✅ Check your UCalgary email and password work on cards.ucalgary.ca manually
- ✅ Make sure you don't have 2-factor authentication blocking
- ✅ Delete saved credentials: remove file `~/.uc_anki_config.json` and try again

**❌ "No cards to export" or "Access denied"**

- ✅ Make sure you're enrolled in the course for that deck
- ✅ Copy the URL from your browser address bar while logged into Cards
- ✅ Try both detail and printdeck URL formats

**❌ Module/Package Errors**

```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**❌ "GUI file dialogs not available" or No file dialog appears**

_macOS:_

```bash
# Solution: Install GUI support automatically
./setup.sh  # The setup script will handle this

# Or manually:
brew install python-tk
```

_Linux (Ubuntu/Debian):_

```bash
# Solution: Install tkinter
sudo apt install python3-tk
./setup.sh  # Re-run setup to verify
```

_Windows:_

- GUI support should work by default
- If not, reinstall Python with "Add Python to PATH" checked
- Make sure to check "tk/tkinter" during installation

### Advanced Troubleshooting

**See what the browser is doing (Debug Mode):**

1. Open `export_ucalgary_anki_debug.py` in a text editor
2. Find the line with `--headless` (around line 1444)
3. Add a `#` at the start: `# opts.add_argument("--headless")`
4. Run the script - you'll see Chrome open and can watch what happens

**Reset Everything:**

```bash
# Delete saved credentials
rm ~/.uc_anki_config.json

# Delete virtual environment
rm -rf .venv

# Re-run setup
./setup.sh
```

**Check Your Setup:**

```bash
# Verify Python version (needs 3.8+)
python --version

# Verify pip works
pip --version

# Test if Chrome is installed
google-chrome --version  # Linux
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version  # Mac
```

---

<a id="tips"></a>

## Tips

**Before Running:**

- Ensure you can log into cards.ucalgary.ca manually
- Have your deck URL ready (copy from browser address bar)
- Close other Chrome instances to avoid conflicts

**Version Compatibility:**

- Python 3.8+ required
- Keep Google Chrome updated to latest version
- ChromeDriver is automatically managed by the script

**Performance:**

- Each card takes ~2-3 seconds to scrape
- Progress bar shows real-time status
- Larger decks will take proportionally longer

**Anki Integration:**

- Import the `.apkg` file directly into Anki
- Cards will appear as a new deck named "Deck\_<ID>"
- Interactive features work in Anki desktop and mobile

**Troubleshooting:**

- Run with Chrome visible (comment out `--headless`) to debug issues
- Check console output for specific error messages
- Delete `~/.uc_anki_config.json` to reset saved credentials

---

<a id="editing-files-in-terminal-editors"></a>

## Editing Files in Terminal Editors

### Nano (macOS/Linux)

- Nav: arrow keys (no mouse)
- Delete line: **Ctrl+K**
- Select: **Ctrl+^** + arrows + **Ctrl+K**
- Paste: **Ctrl+U**
- Save: **Ctrl+O**, Enter
- Exit: **Ctrl+X**
- Cancel: **Ctrl+C**

### Vi/Vim (macOS/Linux)

- Modes: Normal, Insert
- Insert: **i**; Exit: **Esc**
- Nav: arrows or **h/j/k/l**
- Delete line: **dd**; delete char: **x**
- Save & exit: `:wq`; exit no save: `:q!`

### Notepad (Windows)

- Nav: mouse or arrows
- Save: **Ctrl+S**
- Close: **Alt+F4**

---

<a id="full-setup-guides"></a>

## Full Setup Guides

---

### macOS Full Setup (Complete Beginner Guide)

**🍎 Never used Terminal before? Follow these exact steps:**

1. **Open Terminal:**

   - Press `Cmd + Space` on your keyboard
   - Type "Terminal" and press Enter
   - A black window will open - don't worry, this is normal!

2. **Get the project and run setup (it installs everything automatically):**

   ```bash
   git clone https://github.com/ammargrowme/anki_converter.git
   cd anki_converter
   ./setup.sh
   ```

   **✨ The setup script will automatically install:**

   - Homebrew (if missing)
   - Git (if missing)
   - Google Chrome (if missing)
   - Python GUI support (tkinter)
   - All Python dependencies
   - Virtual environment setup

   _This might take 5-15 minutes depending on what needs to be installed_

3. **Alternative: Manual Installation (if automatic setup doesn't work):**

   **Install Homebrew (package manager):**

   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

   _This might take 5-10 minutes and ask for your password_

   **Install required programs:**

   ```bash
   brew install git python3
   ```

   **Install Google Chrome (if not already installed):**

   ```bash
   brew install --cask google-chrome
   ```

   **Then get the project and set it up:**

   ```bash
   git clone https://github.com/ammargrowme/anki_converter.git
   cd anki_converter
   ./setup.sh
   ```

4. **When setup completes successfully, run:**
   ```bash
   source activate.sh
   # Choose your version:
   python main.py               # Modular version (recommended)
   python export_ucalgary_anki_debug.py  # Debug version
   ```

**💡 Tip:** The automatic setup (step 2) is recommended as it handles everything for you!

---

### Windows Full Setup (Complete Beginner Guide)

**🪟 Never used Git Bash? Here's step-by-step:**

1. **Install required programs (click each link and install):**

   - [Git for Windows](https://git-scm.com/download/win) - **REQUIRED for setup.sh** (use default settings)
   - [Python 3.8+](https://www.python.org/downloads/windows/) - **IMPORTANT: Check "Add Python to PATH" during installation**
   - [Google Chrome](https://www.google.com/chrome/) - If not already installed

2. **Open Git Bash (NOT Command Prompt or PowerShell):**

   - **Method 1:** Press `Windows + R`, type `git bash`, press Enter
   - **Method 2:** Find "Git Bash" in your Start Menu
   - **Method 3:** Right-click on Desktop → "Git Bash Here"
   - A terminal window will open - this is Git Bash, which understands bash commands

3. **Navigate to your Desktop:**

   ```bash
   cd ~/Desktop
   ```

4. **Get the project and set it up:**

   ```bash
   git clone https://github.com/ammargrowme/anki_converter.git
   cd anki_converter
   bash setup.sh
   ```

   **✨ The setup script will automatically:**

   - Detect you're on Windows
   - Create Windows-specific activation scripts (.bat and .ps1)
   - Install all Python dependencies
   - Set up everything correctly

5. **When setup completes, activate the environment:**

   ```bash
   # In the same Git Bash window:
   source .venv/bin/activate
   ```

   **Alternative activation methods:**

   - Double-click `activate.bat` (opens Command Prompt)
   - Right-click `activate.ps1` → "Run with PowerShell"

6. **Run the converter:**
   ```bash
   # In Git Bash (after activation):
   python main.py               # Modular version (recommended)
   python export_ucalgary_anki_debug.py  # Debug version
   ```

**🚨 Common Windows Mistakes to Avoid:**

- ❌ Don't use Command Prompt (`cmd`) for setup - `setup.sh` won't work
- ❌ Don't use PowerShell for setup - bash scripts don't work there
- ✅ Use Git Bash for setup and running the scripts
- ✅ You can use the .bat/.ps1 files for activation if you prefer

---

### Ubuntu/Linux Full Setup (Complete Beginner Guide)

**🐧 New to Linux Terminal? Here's how:**

1. **Open Terminal:**

   - Press `Ctrl + Alt + T` on your keyboard
   - Or click Activities → search "Terminal"

2. **Update your system and install required programs:**

   ```bash
   sudo apt update
   sudo apt install -y git python3 python3-venv python3-pip wget curl
   ```

   _This will ask for your password_

3. **Install Google Chrome:**

   ```bash
   wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
   sudo apt install -y ./google-chrome-stable_current_amd64.deb
   ```

4. **Get the project and set it up:**

   ```bash
   git clone https://github.com/ammargrowme/anki_converter.git
   cd anki_converter
   chmod +x setup.sh
   ./setup.sh
   ```

5. **When setup is complete, run:**
   ```bash
   # Choose your version:
   python main.py               # Modular version (recommended)
   python export_ucalgary_anki_debug.py  # Debug version
   ```

**🔰 First Time Using Terminal Tips:**

- You can copy text and paste with `Ctrl+Shift+V` in most Linux terminals
- If you make a typo, press `Ctrl+C` to cancel and start over
- The `sudo` command asks for your user password (the one you use to log into your computer)

---

---

## ❓ Frequently Asked Questions

### General Questions

**Q: Which version should I use - modular or debug?**  
A: Use the **modular version** (`python main.py`) for regular use. It's cleaner, faster, and easier to maintain. Only use the debug version if you're experiencing issues and need detailed logging.

**Q: How long does conversion take?**  
A: Individual decks: 30 seconds to 5 minutes depending on size. Each card takes ~2-3 seconds to process. Collections with multiple decks will take proportionally longer.

**Q: Can I convert multiple decks at once?**  
A: Yes! Use collection URLs to convert all decks in a collection automatically. For individual decks, you'll need to run the script multiple times or create a batch script.

**Q: Do the interactive features work in Anki mobile apps?**  
A: Yes! The generated cards work in Anki desktop, AnkiMobile (iOS), and AnkiDroid (Android).

### Technical Questions

**Q: Why do I need Git Bash on Windows?**  
A: The `setup.sh` script is written in bash, which isn't available in Command Prompt or PowerShell. Git Bash provides a Unix-like environment on Windows.

**Q: Can I use Firefox instead of Chrome?**  
A: Not currently. The script uses Selenium with ChromeDriver. Firefox support is planned for future versions.

**Q: Where are my credentials stored?**  
A: In `~/.uc_anki_config.json` in your home directory. The file is only accessible to your user account and stores credentials locally (never sent to external servers).

**Q: What if UCalgary Cards changes their website?**  
A: The script may break if the site structure changes significantly. We monitor for changes and update the script accordingly. Check for updates if you encounter issues.

### Troubleshooting Questions

**Q: I get "bash: command not found" on Windows. What's wrong?**  
A: You're using Command Prompt or PowerShell instead of Git Bash. Install Git for Windows and use Git Bash instead.

**Q: The script says "Login failed" but my credentials are correct. Why?**  
A: Try these solutions:

1. Verify you can log into cards.ucalgary.ca manually
2. Check if you have 2-factor authentication enabled
3. Delete `~/.uc_anki_config.json` and re-enter credentials
4. Ensure you're using your full UCalgary email address

**Q: No file dialog appears when saving. What should I do?**  
A: This means GUI support (tkinter) isn't available. The script will fall back to command-line input. To enable GUI dialogs:

- **Linux:** `sudo apt install python3-tk`
- **macOS:** `brew install python-tk`
- **Windows:** Reinstall Python with tkinter support

**Q: I get permission errors on macOS. How do I fix this?**  
A: Run `chmod +x setup.sh` to make the script executable, or try the automatic setup which handles permissions.

### Content Questions

**Q: What types of content are preserved in the conversion?**  
A: The script preserves:

- Question text and multiple choice options
- Images and diagrams
- Tables and formatted data
- HTML formatting and styling
- Explanations and feedback
- Patient scenarios and case information

**Q: Can I edit the cards after importing to Anki?**  
A: Yes! You can edit the generated cards in Anki like any other cards. However, re-running the conversion will overwrite your changes unless you modify the deck name.

**Q: Are there any content limitations?**  
A: Some complex interactive elements from Cards may not transfer perfectly. Most content including images, tables, and formatting is preserved well.

### Usage Questions

**Q: Is this legal to use?**  
A: Yes, for personal educational use with courses you're enrolled in. Always comply with UCalgary's academic integrity policies and don't share copyrighted content.

**Q: Can I share the generated Anki decks?**  
A: Only if you have permission to share the content. Most course materials are copyrighted and should only be used for personal study.

**Q: What if I'm not a UCalgary student?**  
A: This tool is specifically designed for UCalgary Cards. It won't work with other institutions' systems.

---

## 🛠️ Development & Technical Details

### Architecture Overview

**Modular Version (`main.py`):**

- **Entry Point:** `main.py` - Coordinates the entire process
- **Authentication:** `auth.py` - Handles UCalgary login and credential management
- **Web Scraping:** `deck_scraping.py` - Selenium-based card extraction
- **Content Processing:** `content_extraction.py` - HTML parsing and formatting
- **Image Handling:** `image_processing.py` - Image download and optimization
- **Sequential Processing:** `sequential_extraction.py` - Card-by-card processing logic
- **Anki Export:** `anki_export.py` - Generates .apkg files using genanki
- **Utilities:** `utils.py` - Shared functions and configurations

**Debug Version (`export_ucalgary_anki_debug.py`):**

- Single-file implementation with extensive logging
- Identical functionality to modular version
- Enhanced error reporting and debugging output
- Easier troubleshooting for development

### Key Technologies

- **Web Automation:** Selenium WebDriver with automatic ChromeDriver management
- **HTML Parsing:** BeautifulSoup4 for content extraction
- **Anki Generation:** Genanki library for .apkg file creation
- **Image Processing:** Pillow for image optimization and format conversion
- **GUI Integration:** tkinter for cross-platform file dialogs
- **Configuration:** JSON-based credential storage with encryption

### File Structure Details

```
anki_converter/
├── main.py                 # Main entry point (modular version)
├── export_ucalgary_anki_debug.py  # Debug version (single file)
├── setup.sh               # Cross-platform setup script
├── test_setup.py          # System verification script
├── requirements.txt       # Python dependencies
├──
├── # Modular components:
├── auth.py               # Authentication & credential management
├── deck_scraping.py      # Web scraping & browser automation
├── content_extraction.py # HTML parsing & content processing
├── image_processing.py   # Image handling & optimization
├── sequential_extraction.py # Card processing logic
├── anki_export.py        # Anki deck generation
├── utils.py              # Shared utilities & configurations
├──
├── # Generated files (after setup):
├── .venv/                # Python virtual environment
├── activate.sh           # Unix activation script
├── activate.bat          # Windows CMD activation
├── activate.ps1          # Windows PowerShell activation
└── ~/.uc_anki_config.json # Saved credentials (secure)
```

### Advanced Configuration

**Environment Variables:**

- Set `UCALGARY_ANKI_HEADLESS=false` to run Chrome visibly for debugging
- Set `UCALGARY_ANKI_TIMEOUT=30` to adjust page load timeout (default: 10s)
- Set `UCALGARY_ANKI_DEBUG=true` for verbose logging in modular version

**Custom Chrome Options:**
Edit `deck_scraping.py` or debug file to modify Chrome behavior:

```python
# Add custom Chrome arguments
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-extensions")
```

**Anki Template Customization:**
The generated cards use custom CSS and JavaScript for interactive features. Templates are defined in `anki_export.py` (modular) or within the debug file.

### Performance Optimization

- **Parallel Processing:** Images are downloaded concurrently
- **Smart Caching:** Reuses browser sessions for multiple cards
- **Memory Management:** Large images are automatically resized
- **Progress Tracking:** Real-time progress bars with ETA

---

## 📋 Development Log & Version History

### Version 2.0 - July 24th, 2025 (Latest)

**Major Refactoring & Enhanced Windows Support**

**🔄 Architecture Changes:**

- Split monolithic script into modular components for maintainability
- Created dual-version system: modular (`main.py`) + debug (`export_ucalgary_anki_debug.py`)
- Implemented comprehensive cross-platform setup script (`setup.sh`)

**🪟 Windows Compatibility Fixes:**

- **Issue:** Setup script (`setup.sh`) failed in Windows Command Prompt and PowerShell
- **Solution:** Updated documentation to require Git Bash for Windows users
- **Improvement:** Added Windows-specific activation scripts (`.bat` and `.ps1`)
- **Testing:** Verified fresh installation from scratch on Windows systems

**📚 Documentation Overhaul:**

- Rewrote README with clear OS-specific instructions
- Added comprehensive troubleshooting section with Windows-specific solutions
- Created beginner-friendly quick start guides
- Added terminal requirements and common mistake warnings

**🔧 Setup & Installation Improvements:**

- **Auto-Detection:** Setup script automatically detects OS and installs appropriate dependencies
- **Dependency Management:** Automatic installation of missing components (Homebrew, Git, Chrome)
- **GUI Support:** Automatic tkinter installation and fallback handling
- **Verification:** Added `test_setup.py` for comprehensive system verification

**✨ New Features Added:**

- **Collection Support:** Convert entire UCalgary Cards collections with multiple decks
- **Hierarchical Organization:** Smart deck structure creation (Collection → Deck → Patient)
- **Curriculum Detection:** Special handling for RIME-style collections
- **Enhanced Content Extraction:** Better table, image, and formatted content preservation
- **GUI File Dialogs:** Modern save dialogs with command-line fallback
- **Progress Tracking:** Real-time progress bars for collection processing

**🐛 Bug Fixes:**

- Fixed virtual environment activation on Windows
- Resolved ChromeDriver compatibility issues
- Fixed image processing and sizing problems
- Corrected path handling across different operating systems

**📊 Testing & Validation:**

- Comprehensive testing on Windows 11, macOS, and Ubuntu Linux
- Fresh installation testing from GitHub clone
- End-to-end workflow validation with real UCalgary Cards data
- Cross-platform compatibility verification

### Version 1.0 - Original Implementation

**Initial Features:**

- Basic deck scraping from UCalgary Cards
- Single-file Python script
- Manual dependency installation
- Limited cross-platform support
- Command-line only interface

**Known Limitations (Resolved in v2.0):**

- Windows setup complexity
- Manual ChromeDriver management
- Limited error handling
- No collection support
- Basic content extraction

---

## 🧪 Testing & Quality Assurance

### Test Coverage

**System Tests (`test_setup.py`):**

- ✅ Python environment validation
- ✅ Dependency availability checks
- ✅ GUI support verification
- ✅ File structure validation
- ✅ Import capability testing

**Manual Testing Scenarios:**

- ✅ Fresh installation on clean systems
- ✅ Individual deck conversion
- ✅ Collection processing
- ✅ Error handling and recovery
- ✅ Cross-platform compatibility

**Validated Platforms:**

- ✅ Windows 10/11 with Git Bash
- ✅ macOS (Intel and Apple Silicon)
- ✅ Ubuntu 20.04+ / Debian-based Linux
- ✅ Various Python versions (3.8-3.11)

### Known Issues & Limitations

**Current Limitations:**

- Requires stable internet connection
- Depends on UCalgary Cards site structure (may break with site updates)
- Chrome/Chromium required (no Firefox support yet)
- Large collections may take significant time to process

**Planned Improvements:**

- Firefox WebDriver support
- Offline processing capabilities
- Faster image processing
- Better error recovery

---

## Contributing

Contributions are welcome! Please feel free to:

- Report bugs or issues
- Suggest new features
- Submit pull requests
- Improve documentation

**To contribute:**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## License

This project is open source and available under the MIT License.

**Terms:**

- Free for personal and educational use
- No warranty or liability
- Use responsibly and ethically

**Compliance:**

- Respect University of Calgary's terms of service
- Follow academic integrity policies
- Use only for legitimate educational purposes

**Disclaimer:**
This tool is for educational purposes only. Users are responsible for complying with their institution's policies regarding automated access to educational platforms. This project is not officially affiliated with or endorsed by the University of Calgary.

---

_Last updated: July 24th, 2025_  
_Repository: [https://github.com/ammargrowme/anki_converter](https://github.com/ammargrowme/anki_converter)_

## 🔐 Security & Privacy

### Credential Management

**Local Storage:**

- Credentials are saved in `~/.uc_anki_config.json` on your local machine
- File is stored in your user home directory (not in the project folder)
- Uses JSON format with basic encoding (not plaintext)

**Security Measures:**

- ✅ **Local-only storage**: No credentials sent to external servers
- ✅ **User-only access**: File permissions restricted to your user account
- ✅ **Session management**: Browser sessions are properly closed after use
- ✅ **No logging**: Passwords are never written to log files

**To reset credentials:**

```bash
# Delete the config file to start fresh
rm ~/.uc_anki_config.json

# On Windows (Git Bash):
rm ~/config.json

# Then run the script again to enter new credentials
```

### Data Privacy

**What data is accessed:**

- Your UCalgary Cards login credentials (stored locally only)
- Card content from decks you have access to
- Images embedded in cards (downloaded temporarily)

**What data is NOT accessed:**

- Other students' private information
- Grades or assessment data beyond card content
- Personal information beyond what's in the cards
- Any data from other UCalgary systems

**Data handling:**

- All processing happens locally on your machine
- No data is sent to external services except UCalgary Cards
- Generated Anki files contain only the card content you select
- Temporary files are cleaned up after processing

### Network Security

**HTTPS Usage:**

- All connections to UCalgary Cards use HTTPS encryption
- Browser sessions follow UCalgary's security protocols
- No man-in-the-middle vulnerabilities

**Firewall Compatibility:**

- Uses standard HTTP/HTTPS ports (80/443)
- Compatible with university network restrictions
- No unusual network requirements

### Responsible Use

**Acceptable Use:**

- ✅ Personal study and learning
- ✅ Creating study materials from your enrolled courses
- ✅ Academic research with proper permissions

**Please DO NOT:**

- ❌ Share generated decks containing copyrighted content
- ❌ Use for courses you're not enrolled in
- ❌ Violate UCalgary's academic integrity policies
- ❌ Share your UCalgary credentials with others

**Compliance:**

- Respects UCalgary's terms of service
- Follows academic integrity guidelines
- Maintains student privacy standards

---

## ⚠️ Important Notes & Disclaimers

### System Requirements Recap

**Minimum Requirements:**

- Python 3.8 or higher
- Git (for Windows users: Git Bash required)
- Google Chrome browser
- Internet connection
- 1GB free disk space for dependencies

**Recommended System:**

- Python 3.9+ for best compatibility
- 8GB RAM for large collections
- SSD storage for faster processing
- Stable broadband internet

### Known Limitations

**Technical Limitations:**

- Requires Chrome/Chromium (Firefox not supported)
- Site structure dependent (may break with Cards updates)
- Processing time scales with deck size
- Large images may slow conversion

**Access Limitations:**

- Only works with decks you have legitimate access to
- Requires active UCalgary student/staff account
- Subject to UCalgary Cards site availability
- May be affected by network restrictions

### Disclaimer

**Educational Use:**
This tool is designed for educational purposes to help UCalgary students create personal study materials from their enrolled courses.

**No Warranty:**
This software is provided "as is" without warranty of any kind. Users are responsible for:

- Ensuring they have proper access to content
- Complying with university policies
- Using the tool responsibly and ethically

**Not Affiliated:**
This project is not officially affiliated with or endorsed by the University of Calgary.

**User Responsibility:**
Users are responsible for:

- Complying with UCalgary's academic integrity policies
- Respecting copyright and intellectual property rights
- Using the tool only for legitimate educational purposes
- Maintaining the security of their own credentials

---
