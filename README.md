# anki_converter

**Repository:** [https://github.com/ammargrowme/anki_converter.git](https://github.com/ammargrowme/anki_converter.git)

[![GitHub Repo stars](https://img.shields.io/github/stars/ammargrowme/anki_converter)](https://git## Expectations

**Console Output (what you'll see when it works):**

```
🚀 Setting up UCalgary Anki Converter...
✅ Python 3.9.7 found
✅ pip found
✅ Git found
✅ Google Chrome found
📦 Creating new virtual environment...
✅ Dependencies installed successfully
🎉 Setup completed successfully!

Loading screen...
Logging in...
Logged in successfully
Scraping cards: 100%|████████████| 6/6 [00:15<00:00, 2.5s/it]

📁 Save Location
[GUI file dialog opens for you to choose save location]

[+] APKG → C:\Users\YourName\Desktop\Deck_1261.apkg
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
- Multiple choice options (with interactive selection in Anki)
- Free-text question fields
- Correct answers and explanations
- Score information and feedback
- **All cards from multi-patient decks** (e.g., 6 cards from 3 patients)

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
- Each card takes ~2-3 seconds to processom/ammargrowme/anki_converter)

A command-line tool that logs into the University of Calgary Cards site, scrapes question-and-answer cards, and generates a ready-to-import Anki `.apkg` deck using Selenium and Genanki.

**Features:**

- Scrapes multiple-choice and free-text questions
- Handles multi-patient decks with multiple cards per patient
- Exports interactive Anki cards with clickable options
- Preserves question context, explanations, and scoring
- Automatically handles authentication and session management

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
11. [Editing Files in Terminal Editors](#editing-files-in-terminal-editors)

---

<a id="quick-start-beginner-friendly"></a>

## Quick Start (Beginner-Friendly)

**⚠️ Never coded before? No problem! Follow these exact steps:**

### Option 1: Automatic Setup (Recommended for Beginners)

1. **Download the project:**

   - Go to: https://github.com/ammargrowme/anki_converter
   - Click the green "Code" button → "Download ZIP"
   - Extract the ZIP file to your Desktop

2. **Open Terminal/Command Prompt:**

   - **Windows:** Press `Windows + R`, type `cmd`, press Enter
   - **Mac:** Press `Cmd + Space`, type `Terminal`, press Enter
   - **Linux:** Press `Ctrl + Alt + T`

3. **Navigate to the project folder:**

   ```bash
   cd Desktop/anki_converter-main
   ```

4. **Run the automatic setup (does everything for you):**

   ```bash
   # For Windows in Command Prompt:
   bash setup.sh

   # For Mac/Linux:
   chmod +x setup.sh
   ./setup.sh
   ```

5. **Follow the setup script instructions** - it will:

   - Check if you have everything needed
   - Install missing components automatically
   - Set up the environment
   - Tell you exactly what to do next

6. **Activate the environment (after setup completes):**

   **macOS/Linux:**

   ```bash
   source .venv/bin/activate
   # OR use the helper script:
   source activate.sh
   ```

   **⚠️ Important:** Use `source` or `.` - do NOT run `./activate.sh`

   **Windows:**

   - Double-click `activate.bat` (Command Prompt)
   - Right-click `activate.ps1` → Run with PowerShell

7. **Run the converter:**
   ```bash
   python export_ucalgary_anki.py
   ```

**✅ How to know it worked:**

- You should see `(.venv)` prefix in your terminal prompt after activation
- The setup script will tell you "Virtual environment activated"
- Running `python --version` should work without errors

### Option 2: Manual Setup (If Option 1 doesn't work)

1. **Install prerequisites first:**

   - Install Python 3.8+ from: https://www.python.org/downloads/
   - Install Git from: https://git-scm.com/downloads
   - Install Google Chrome from: https://www.google.com/chrome/

2. **Clone and setup:**

   ```bash
   git clone https://github.com/ammargrowme/anki_converter.git
   cd anki_converter
   pip install -r requirements.txt
   ```

3. **Run the script:**
   ```bash
   python export_ucalgary_anki.py
   ```

### What Happens Next:

1. The script asks for your UCalgary email and password (saved securely)
2. Paste your Cards deck URL when prompted
3. **A "Save As" dialog will open** - choose where to save your Anki deck file (just like saving any file!)
4. Import the `.apkg` file into Anki: **File → Import → Select your file**

**✨ New GUI Features:**

- 💾 **File Save Dialog** - No more typing file paths! Click and save like any app
- 🎉 **Success Popup** - Clear confirmation when your deck is ready
- 🔄 **Automatic Fallback** - Uses command line if GUI isn't available

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

1. Run: `python export_ucalgary_anki.py`
2. Enter **UCalgary email** and **password** (up to 3 attempts)
3. On successful login, credentials are saved automatically
4. Enter **deck URL** (details or printdeck URL - see [URL Examples](#url-examples))
5. Choose save location for the `.apkg` file

**Subsequent runs:**

1. Run: `python export_ucalgary_anki.py`
2. Credentials loaded automatically; only enter **deck URL**
3. Choose save location (defaults to `Deck_<ID>.apkg`)

---

<a id="usage"></a>

## Usage

```bash
python export_ucalgary_anki.py
```

**The script will:**

1. Prompt for credentials (first run only)
2. Ask for a UCalgary Cards deck URL
3. Log into the Cards site automatically
4. Scrape all questions and answers from the deck
5. **Open a "Save As" dialog** for you to choose where to save the `.apkg` file
6. Generate an Anki deck file ready for import
7. **Show a success popup** with import instructions

**Import to Anki:** Open Anki → File → Import → Select your `.apkg` file

---

<a id="url-examples"></a>

## URL Examples

The script accepts both **details** and **printdeck** URLs:

**Details URL (recommended):**

```
https://cards.ucalgary.ca/details/1261?bag_id=151
```

**Printdeck URL:**

```
https://cards.ucalgary.ca/printdeck/1261?bag_id=151
```

**How to find your URL:**

1. Log into cards.ucalgary.ca
2. Navigate to your desired deck
3. Copy the URL from your browser's address bar
4. The script will automatically detect the deck ID and bag_id

---

<a id="expectations"></a>

## Expectations

- **Logs:** “Script started”, “Loading screen…”, “Logging in…”, “Logged in successfully”
- **Progress:** Live “Scraping cards” bar
- **Output:** **`Deck_<ID>.apkg`**

---

<a id="troubleshooting"></a>

## Troubleshooting

**🆘 Need Help? Start Here:**

### First Steps When Something Goes Wrong

1. **Try the automatic setup script first:**

   ```bash
   ./setup.sh
   ```

   It fixes most common issues automatically!

2. **Check the error message** - it usually tells you exactly what's wrong

3. **Make sure you can log into cards.ucalgary.ca manually** in your browser first

### Common Issues for Beginners

**❌ "Command not found" or "python is not recognized"**

```bash
# Solution: Install Python first
# Go to: https://www.python.org/downloads/
# Download and install, then try again
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

### Advanced Troubleshooting

**See what the browser is doing (Debug Mode):**

1. Open `export_ucalgary_anki.py` in a text editor
2. Find the line with `--headless` (around line 73)
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

2. **Copy and paste these commands one at a time:**

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

3. **Get the project and set it up:**

   ```bash
   git clone https://github.com/ammargrowme/anki_converter.git
   cd anki_converter
   ./setup.sh
   ```

4. **The setup script will guide you through the rest!**

5. **When setup is complete, run:**
   ```bash
   python export_ucalgary_anki.py
   ```

---

### Windows Full Setup (Complete Beginner Guide)

**🪟 Never used Command Prompt? Here's step-by-step:**

1. **Install required programs (click each link and install):**

   - [Python 3.8+](https://www.python.org/downloads/windows/) - **IMPORTANT: Check "Add Python to PATH" during installation**
   - [Git for Windows](https://git-scm.com/download/win) - Use default settings
   - [Google Chrome](https://www.google.com/chrome/) - If not already installed

2. **Open Command Prompt:**

   - Press `Windows + R` on your keyboard
   - Type `cmd` and press Enter
   - A black window will open

3. **Navigate to your Desktop:**

   ```cmd
   cd Desktop
   ```

4. **Get the project and set it up:**

   ```cmd
   git clone https://github.com/ammargrowme/anki_converter.git
   cd anki_converter
   setup.sh
   ```

5. **If you get "execution policy" errors, open PowerShell as Administrator:**

   - Right-click Start button → "Windows PowerShell (Admin)"
   - Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
   - Then try step 4 again

6. **When setup is complete, run:**
   ```cmd
   python export_ucalgary_anki.py
   ```

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
   python export_ucalgary_anki.py
   ```

**🔰 First Time Using Terminal Tips:**

- You can copy text and paste with `Ctrl+Shift+V` in most Linux terminals
- If you make a typo, press `Ctrl+C` to cancel and start over
- The `sudo` command asks for your user password (the one you use to log into your computer)

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

## License

This project is open source. Please use responsibly and in accordance with University of Calgary's terms of service.

**Disclaimer:** This tool is for educational purposes. Users are responsible for complying with their institution's policies regarding automated access to educational platforms.

---
