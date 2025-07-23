# anki_converter

**Repository:** https://github.com/ammargrowme/anki_converter.git

[![GitHub Repo stars](https://img.shields.io/github/stars/ammargrowme/anki_converter)](https://github.com/ammargrowme/anki_converter)

A command-line tool that logs into the University of Calgary Cards site, scrapes question-and-answer cards, and generates a ready-to-import Anki `.apkg` deck using Selenium and Genanki.

---

## Table of Contents

1. [Installation](#installation)
   - [Install Homebrew & Dependencies](#install-homebrew--dependencies)
   - [Clone & Setup Virtualenv](#clone--setup-virtualenv)
   - [Windows (PowerShell)](#windows-powershell)
2. [Configuration](#configuration)
   - [Creating the .env file](#creating-the-env-file)
3. [Usage](#usage)
   - [Run Converter](#run-converter)
4. [Flags](#flags)
5. [Expectations](#expectations)
6. [Troubleshooting](#troubleshooting)
   - [Common Issues](#common-issues)
7. [Tips](#tips)
8. [Full Setup Guides](#full-setup-guides)
   - [macOS Full Setup](#macos-full-setup)
   - [Ubuntu/Debian Linux Full Setup](#ubuntudebian-linux-full-setup)
   - [Windows Full Setup](#windows-full-setup)

---

## Installation

## Requirements by OS

### macOS

- Homebrew
- Git
- Python 3
- Chrome
- ChromeDriver

Refer to installation commands below in [Install Homebrew & Dependencies](#install-homebrew--dependencies) and [Clone & Setup Virtualenv](#clone--setup-virtualenv).

### Ubuntu/Debian Linux

- apt package manager
- Git
- Python 3
- pip
- Chrome
- ChromeDriver

Refer to installation commands below in [Install Homebrew & Dependencies](#install-homebrew--dependencies) and [Clone & Setup Virtualenv](#clone--setup-virtualenv).

### Windows

- Git installer
- Python installer
- Chrome installer
- ChromeDriver installer

Refer to the Windows setup instructions in [Windows (PowerShell)](#windows-powershell).

### macOS / Linux

**Opening Terminal on macOS:**

- Press `⌘` + `Space`, type `Terminal`, and press `Enter`.
- Or open `Finder` > `Applications` > `Utilities` > `Terminal`.

**Basic Terminal Navigation:**

- `pwd` shows your current folder path.
- `ls` lists files and folders.
- `cd <folder>` moves into a folder (e.g. `cd anki_converter`).
- `cd ..` moves up one level.

#### Install Homebrew & Dependencies

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git python3
brew install --cask google-chrome chromedriver
```

#### Clone & Setup Virtualenv

```bash
git clone https://github.com/ammargrowme/anki_converter.git && cd anki_converter
chmod +x setup.sh
./setup.sh
```

#### Windows (PowerShell)

```powershell
# Git
# Python 3 (Add to PATH)
# Chrome & ChromeDriver (add to PATH)
git clone https://github.com/ammargrowme/anki_converter.git ; cd anki_converter
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Configuration

Provide your University of Calgary credentials and the target cards URL so the script can authenticate and fetch your cards.

#### Creating the .env file

1. Open your terminal or command prompt.
2. Change directory to the cloned repo folder:
   ```bash
   cd anki_converter
   ```
3. Create a new file named `.env`:
   - On macOS/Linux:
     ```bash
     touch .env
     ```
   - On Windows:
     ```powershell
     New-Item .env -ItemType File
     ```
4. Open `.env` in your preferred text editor and paste the following, replacing placeholders:

```ini
UC_EMAIL=you@ucalgary.ca
UC_PW=your_password
UC_BASE_URL=https://cards.ucalgary.ca/details/<DETAILS_ID>
```

5. Save and close the file.

##### Opening the .env file

- **On macOS/Linux:**
  ```bash
  # In the project folder:
  nano .env
  # or
  vi .env
  ```
- **On Windows PowerShell:**
  ```powershell
  notepad .env
  ```

---

## Usage

Run the converter script to scrape cards from UofC and generate an Anki deck.

#### Run Converter

```bash
# Default:
python export_ucalgary_anki.py

# Override URL:
python export_ucalgary_anki.py --base-url https://cards.ucalgary.ca/details/12345

# Override Deck ID:
python export_ucalgary_anki.py --deck <ID>
```

---

## Flags

Customize script behavior by overriding default settings via command-line options.

```text
--deck <ID>         Process by deck ID instead of UC_BASE_URL
--username <email>  Override UC_EMAIL
--password <pw>     Override UC_PW
--base-url <URL>    Override UC_BASE_URL
```

---

## Expectations

Observe the following output formats and terminal feedback when running the script.

- **Logs**: “Script started”, “Loading screen…”, “Logging in…”, “Logged in successfully”
- **Progress**: Live bar “Scraping cards”
- **Output**: `Deck_<ID>.apkg`

---

## Troubleshooting

Common issues and their fixes when installing dependencies or running the script.

### Common Issues

- Module not found → `pip install -r requirements.txt`
- ChromeDriver mismatch → download matching version
- Hidden browser → comment out `--headless`
- Verify PATH → `which chromedriver` / `where chromedriver`
- Internet & permissions
- Permission denied errors when running scripts → use `chmod +x`.
- Virtual environment errors → ensure `python3 -m venv .venv` runs and activate correctly.
- `.env` file parse errors → ensure no BOM or extra whitespace.
- Network timeouts → check firewall or proxy settings.

---

## Tips

Additional best practices to ensure smooth operation and maintenance.

- Check `python3 --version` / `pip --version`
- Keep Chrome/ChromeDriver in sync
- No extra spaces in `.env`
- Ensure active internet
- Scripts executable (`chmod +x setup.sh`)

---

## Full Setup Guides

### macOS Full Setup

Follow these steps from a clean system:

1. **Open Terminal:**
   - Press `⌘` + `Space`, type `Terminal`, and press `Enter`.
2. **Install Homebrew:**
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. **Install required tools:**
   ```bash
   brew install git python3
   brew install --cask google-chrome chromedriver
   ```
4. **Clone the repository:**
   ```bash
   git clone https://github.com/ammargrowme/anki_converter.git
   cd anki_converter
   ```
5. **Set up virtual environment & install dependencies:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
6. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate
   ```
7. **Create and configure `.env`:**
   ```bash
   touch .env
   ```
   Open `.env` in a text editor and paste:
   ```ini
   UC_EMAIL=you@ucalgary.ca
   UC_PW=your_password
   UC_BASE_URL=https://cards.ucalgary.ca/details/<DETAILS_ID>
   ```
8. **Run the converter:**
   ```bash
   python export_ucalgary_anki.py
   ```

### Ubuntu/Debian Linux Full Setup

Follow these steps from a clean Ubuntu/Debian system:

1. **Open Terminal** (Ctrl+Alt+T).
2. **Update packages and install prerequisites:**
   ```bash
   sudo apt update
   sudo apt install -y git python3 python3-venv python3-pip wget
   ```
3. **Install Chrome:**
   ```bash
   wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
   sudo apt install -y ./google-chrome-stable_current_amd64.deb
   ```
4. **Install ChromeDriver:**
   ```bash
   sudo apt install -y chromium-chromedriver
   ```
5. **Clone repository & enter folder:**
   ```bash
   git clone https://github.com/ammargrowme/anki_converter.git
   cd anki_converter
   ```
6. **Set up virtual environment & install dependencies:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
7. **Activate virtual environment:**
   ```bash
   source .venv/bin/activate
   ```
8. **Create and configure `.env`:**
   ```bash
   touch .env
   ```
   Edit `.env` and add:
   ```ini
   UC_EMAIL=you@ucalgary.ca
   UC_PW=your_password
   UC_BASE_URL=https://cards.ucalgary.ca/details/<DETAILS_ID>
   ```
9. **Run the converter:**
   ```bash
   python export_ucalgary_anki.py
   ```

### Windows Full Setup

Follow these steps from a clean Windows machine:

1. **Install Git:** Download & run installer from https://git-scm.com/download/win
2. **Install Python 3:** Download & install from https://www.python.org/downloads/windows/ (check “Add Python to PATH”)
3. **Install Google Chrome:** Download & install from https://www.google.com/chrome/
4. **Install ChromeDriver:**
   - Visit https://chromedriver.chromium.org/downloads
   - Download the version matching your Chrome
   - Unzip and place `chromedriver.exe` in a folder on your PATH
5. **Open PowerShell** (Win+X, then “Windows PowerShell”).
6. **Clone repository & enter folder:**
   ```powershell
   git clone https://github.com/ammargrowme/anki_converter.git
   cd anki_converter
   ```
7. **Set up virtual environment & install dependencies:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
8. **Create and configure `.env`:**
   ```powershell
   New-Item .env -ItemType File
   ```
   Open `.env` in Notepad and paste:
   ```ini
   UC_EMAIL=you@ucalgary.ca
   UC_PW=your_password
   UC_BASE_URL=https://cards.ucalgary.ca/details/<DETAILS_ID>
   ```
9. **Run the converter:**
   ```powershell
   python export_ucalgary_anki.py
   ```
