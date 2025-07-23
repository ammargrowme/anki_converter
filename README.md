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
9. [Requirements by OS](#requirements-by-os)
10. [Editing Files in Terminal Editors](#editing-files-in-terminal-editors)

---

<a id="requirements-by-os"></a>

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

- Press **⌘ + Space**, **type `Terminal`**, and press **Enter**.
- Or open **Finder > Applications > Utilities > Terminal**.

**Basic Terminal Navigation:**

- **`pwd`** shows your current folder path.
- **`ls`** lists files and folders.
- **`cd <folder>`** moves into a folder (e.g. **`cd anki_converter`**).
- **`cd ..`** moves up one level.

#### Install Homebrew & Dependencies

**Copy & Paste:**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Copy & Paste:**

```bash
brew install git python3
```

**Verify installation:**

```bash
git --version   # should print 'git version ...'
python3 --version  # should print 'Python 3.x.x'
```

**Copy & Paste:**

```bash
brew install --cask google-chrome chromedriver
```

**Verify installation:**

```bash
which chromedriver  # should output path
```

#### Clone & Setup Virtualenv

**Copy & Paste:**

```bash
git clone https://github.com/ammargrowme/anki_converter.git && cd anki_converter
chmod +x setup.sh
./setup.sh
```

#### Windows (PowerShell)

**Copy & Paste:**

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

**Verify installation:**

```powershell
git --version   # should print 'git version ...'
python --version  # should print 'Python 3.x.x'
```

---

## Installation

Install system dependencies as needed (see Requirements by OS).

---

## Configuration

Provide your University of Calgary credentials and the target cards URL so the script can authenticate and fetch your cards.

#### Locating and Opening the Project Folder

You need to run commands from the `anki_converter` project folder. If you don't know where it is:

- **On macOS/Linux via Terminal:**
  1. Open Terminal.
  2. Use `pwd` to print your current directory.
  3. If the folder is in your home directory, run:
     ```bash
     cd ~/anki_converter
     ```
  4. If it's elsewhere, run:
     ```bash
     cd /path/to/anki_converter
     ```
- **On Windows via PowerShell:**
  1. Open PowerShell.
  2. Use `Get-Location` to show current path.
  3. If cloned to your user folder:
     ```powershell
     cd $HOME\anki_converter
     ```
  4. Or adjust to the correct path:
     ```powershell
     cd C:\path\to\anki_converter
     ```
- **Via File Explorer/Finder:**
  - macOS: In Finder, navigate to the folder, then press **⌘ + ↑** to go up or **⌘ + ↓** to open.
  - Windows: In File Explorer, locate the folder and double-click to open.

#### Creating the .env file

1. Open your terminal or command prompt.

2. Change directory to the cloned repo folder:
   **Copy & Paste:**

   ```bash
   cd anki_converter
   ```

3. Create a new file named `.env`:

   - On macOS/Linux:
     **Copy & Paste:**

     ```bash
     touch .env
     ```

   - On Windows:
     **Copy & Paste:**

     ```powershell
     New-Item .env -ItemType File
     ```

4. Open `.env` in your preferred text editor and paste the following, replacing placeholders:

**Copy & Paste into your `.env` file:**

```ini
UC_EMAIL=you@ucalgary.ca
UC_PW=your_password
UC_BASE_URL=https://cards.ucalgary.ca/details/<DETAILS_ID>
```

5. Save and close the file.

##### Opening the .env file

- **On macOS/Linux:**
  **Copy & Paste:**

  ```bash
  # In the project folder:
  nano .env
  # or
  vi .env
  ```

- **On Windows PowerShell:**
  **Copy & Paste:**

  ```powershell
  notepad .env
  ```

---

## Usage

Run the converter script to scrape cards from UofC and generate an Anki deck.

#### Run Converter

**Copy & Paste:**

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

- Module not found → **`pip install -r requirements.txt`**
- ChromeDriver mismatch → download matching version
- Hidden browser → comment out `--headless`
- Verify PATH → **`which chromedriver`** / **`where chromedriver`**
- Internet & permissions
- Permission denied errors when running scripts → use **`chmod +x`**.
- Virtual environment errors → ensure **`python3 -m venv .venv`** runs and activate correctly.
- `.env` file parse errors → ensure no BOM or extra whitespace.
- Network timeouts → check firewall or proxy settings.

---

## Tips

Additional best practices to ensure smooth operation and maintenance.

- Check **`python3 --version`** / **`pip --version`**
- Keep Chrome/ChromeDriver in sync
- No extra spaces in `.env`
- Ensure active internet
- Scripts executable (**`chmod +x setup.sh`**)

---

<a id="editing-files-in-terminal-editors"></a>

## Editing Files in Terminal Editors

When using command-line editors to modify files (e.g., `.env`), note:

### Nano (macOS/Linux)

- Navigation: Use the arrow keys; mouse does not work.
- To delete text:
  - **Ctrl+K** cuts (deletes) the current line.
  - **Ctrl+^** then arrow keys selects text; **Ctrl+K** cuts selection.
- To paste: **Ctrl+U**.
- To save (write out): **Ctrl+O**, then **Enter** to confirm.
- To exit: **Ctrl+X**.
- To cancel an action: **Ctrl+C**.

### Vi/Vim (macOS/Linux)

- Modes:
  - **Normal mode** (navigate, delete)
  - **Insert mode** (type text)
- Enter Insert mode: press **i**.
- Exit Insert mode: press **Esc**.
- Navigation: arrow keys or **h** (left), **j** (down), **k** (up), **l** (right).
- To delete:
  - **dd** deletes the current line.
  - **x** deletes the character under the cursor.
- To save and exit: **:wq** then **Enter**.
- To exit without saving: **:q!** then **Enter**.

### Notepad (Windows)

- Standard GUI editor; use mouse or arrow keys to navigate.
- Save: **Ctrl+S**
- Close: click "X" or press **Alt+F4**.

---

## Full Setup Guides

---

### macOS Full Setup

Follow these steps from a clean system:

**Open the project folder in Terminal:** `cd ~/anki_converter`

**1. Open Terminal:**

- Press **⌘ + Space**, **type `Terminal`**, and press **Enter**.

**2. Install Homebrew:**

**Copy & Paste:**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**3. Install required tools:**

**Copy & Paste:**

```bash
brew install git python3
```

**Verify installation:**

```bash
git --version   # should print 'git version ...'
python3 --version  # should print 'Python 3.x.x'
```

**Copy & Paste:**

```bash
brew install --cask google-chrome chromedriver
```

**Verify installation:**

```bash
which chromedriver  # should output path
```

**4. Clone the repository:**

**Copy & Paste:**

```bash
git clone https://github.com/ammargrowme/anki_converter.git
cd anki_converter
```

**5. Set up virtual environment & install dependencies:**

**Copy & Paste:**

```bash
chmod +x setup.sh
./setup.sh
```

**6. Activate the virtual environment:**

**Copy & Paste:**

```bash
source .venv/bin/activate
```

**7. Create and configure `.env`:**

**Copy & Paste:**

```bash
touch .env
```

Open `.env` in a text editor and paste:

**Copy & Paste into your `.env` file:**

```ini
UC_EMAIL=you@ucalgary.ca
UC_PW=your_password
UC_BASE_URL=https://cards.ucalgary.ca/details/<DETAILS_ID>
```

**7a. Open and edit `.env`:**

**Copy & Paste:**

```bash
nano .env   # or vi .env
```

Make sure to save changes before exiting (Ctrl+O, Enter, Ctrl+X in nano).

**8. Run the converter:**

**Copy & Paste:**

```bash
python export_ucalgary_anki.py
```

---

### Ubuntu/Debian Linux Full Setup

Follow these steps from a clean Ubuntu/Debian system:

**Open the project folder in Terminal:** `cd ~/anki_converter`

**1. Open Terminal** (Ctrl+Alt+T).

**2. Update packages and install prerequisites:**

**Copy & Paste:**

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip wget
```

**Verify installation:**

```bash
git --version   # should print 'git version ...'
python3 --version  # should print 'Python 3.x.x'
```

**3. Install Chrome:**

**Copy & Paste:**

```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

**4. Install ChromeDriver:**

**Copy & Paste:**

```bash
sudo apt install -y chromium-chromedriver
```

**Verify installation:**

```bash
which chromedriver  # should output path
```

**5. Clone repository & enter folder:**

**Copy & Paste:**

```bash
git clone https://github.com/ammargrowme/anki_converter.git
cd anki_converter
```

**6. Set up virtual environment & install dependencies:**

**Copy & Paste:**

```bash
chmod +x setup.sh
./setup.sh
```

**7. Activate virtual environment:**

**Copy & Paste:**

```bash
source .venv/bin/activate
```

**8. Create and configure `.env`:**

**Copy & Paste:**

```bash
touch .env
```

Edit `.env` and add:

**Copy & Paste into your `.env` file:**

```ini
UC_EMAIL=you@ucalgary.ca
UC_PW=your_password
UC_BASE_URL=https://cards.ucalgary.ca/details/<DETAILS_ID>
```

**8a. Open and edit `.env`:**

**Copy & Paste:**

```bash
nano .env   # or vi .env
```

Make sure to save changes before exiting (Ctrl+O, Enter, Ctrl+X in nano).

**9. Run the converter:**

**Copy & Paste:**

```bash
python export_ucalgary_anki.py
```

---

### Windows Full Setup

Follow these steps from a clean Windows machine:

**Open the project folder in PowerShell:** `cd C:\path\to\anki_converter`

**1. Install Git:** [Download Git for Windows](https://git-scm.com/download/win) and run the installer.

**2. Install Python 3:** [Download Python 3](https://www.python.org/downloads/windows/) and install (check “Add Python to PATH”).

**3. Install Google Chrome:** Download & install from [Google Chrome](https://www.google.com/chrome/).

**4. Install ChromeDriver:**

- Visit [ChromeDriver Downloads](https://chromedriver.chromium.org/downloads)
- Download the version matching your Chrome
- Unzip and place `chromedriver.exe` in a folder on your PATH

**5. Add ChromeDriver to PATH:**

**Copy & Paste:**

```powershell
# Add to PATH (example):
$env:PATH += ";C:\path\to\chromedriver"
```

**6. Open PowerShell** (Win+X, then “Windows PowerShell”).

**7. Clone repository & enter folder:**

**Copy & Paste:**

```powershell
git clone https://github.com/ammargrowme/anki_converter.git
cd anki_converter
```

**8. Set up virtual environment & install dependencies:**

**Copy & Paste:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

**Verify installation:**

```powershell
git --version   # should print 'git version ...'
python --version  # should print 'Python 3.x.x'
```

**8. Create and configure `.env`:**

**Copy & Paste:**

```powershell
New-Item .env -ItemType File
```

Open `.env` in Notepad and paste:

**Copy & Paste into your `.env` file:**

```ini
UC_EMAIL=you@ucalgary.ca
UC_PW=your_password
UC_BASE_URL=https://cards.ucalgary.ca/details/<DETAILS_ID>
```

**8a. Open `.env` for editing:**

**Copy & Paste:**

```powershell
notepad .env
```

**9. Run the converter:**

**Copy & Paste:**

```powershell
python export_ucalgary_anki.py
```

---
