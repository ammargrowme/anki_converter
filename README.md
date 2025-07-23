# anki_converter

**Repository:** https://github.com/ammargrowme/anki_converter.git

[![GitHub Repo stars](https://img.shields.io/github/stars/ammargrowme/anki_converter)](https://github.com/ammargrowme/anki_converter)

A command-line tool that logs into the University of Calgary Cards site, scrapes question-and-answer cards, and generates a ready-to-import Anki `.apkg` deck using Selenium and Genanki.

---

## Table of Contents

1. [Installation](#installation)
2. [Setup and Configuration](#setup-and-configuration)
3. [Usage](#usage)
4. [Expectations](#expectations)
5. [Troubleshooting](#troubleshooting)
   - [Common Issues](#common-issues)
6. [Tips](#tips)
7. [Full Setup Guides](#full-setup-guides)
   - [macOS Full Setup](#macos-full-setup)
   - [Ubuntu/Debian Linux Full Setup](#ubuntudebian-linux-full-setup)
   - [Windows Full Setup](#windows-full-setup)
8. [Requirements by OS](#requirements-by-os)
9. [Editing Files in Terminal Editors](#editing-files-in-terminal-editors)

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
git --version
python3 --version
```

**Copy & Paste:**

```bash
brew install --cask google-chrome chromedriver
```

**Verify installation:**

```bash
which chromedriver
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
git clone https://github.com/ammargrowme/anki_converter.git ; cd anki_converter
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

**Verify installation:**

```powershell
git --version
python --version
```

---

## Installation

Install system dependencies as needed (see Requirements by OS).

---

## Setup and Configuration

On first run, the script will interactively prompt you for your University of Calgary email, password, and the target cards URL. Credentials will be validated (up to 3 attempts) and then securely saved in a local `config.json`. Subsequent runs will only ask for the URL.

- **First run**:

  1. Execute `python export_ucalgary_anki.py`.
  2. When prompted, enter your **email** and **password**.
  3. The script attempts to log in; if login fails, you get up to 3 attempts.
  4. On successful login, credentials are saved to `config.json`.
  5. You are then prompted for the **cards URL**, after which the deck is generated.

- **Subsequent runs**:

  1. Execute `python export_ucalgary_anki.py`.
  2. The script loads credentials from `config.json`.
  3. You are prompted for the **cards URL**.
  4. If login fails (credentials changed), you will be re-prompted (up to 3 attempts) and `config.json` updated.

- **Credentials & URL Prompt**: When you run `python export_ucalgary_anki.py`, you will be prompted first for your University of Calgary email (username) and password on the very first run. After successful login (up to 3 attempts), you will then be prompted to enter the cards URL you wish to convert. Your credentials are securely saved in `config.json` for all future runs, so subsequent executions only require the URL.

(No CLI flags or `.env` file edits are required.)

---

## Usage

Simply run:

```bash
python export_ucalgary_anki.py
```

and follow the on‑screen prompts. No flags or environment files are needed.

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

#### Untrusted Package Warning

If you see a warning about unverified or untrusted packages when running scripts:

- **macOS**  
  Run:

  ```bash
  xattr -d com.apple.quarantine path/to/file
  ```

  to remove the quarantine flag from the downloaded script.

- **Windows (PowerShell)**  
  Run:

  ```powershell
  Unblock-File -Path .\setup.sh
  ```

  to unblock the script before execution.

- **Linux**  
  Ensure the script is executable and trusted:

  ```bash
  chmod +x setup.sh
  ```

  and verify its source before running.

- **General Guidelines**  
  Always verify scripts from trusted repositories, review any third‑party code before execution, and consider checking checksums or GPG signatures if available.

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
git --version
python3 --version
```

**Copy & Paste:**

```bash
brew install --cask google-chrome chromedriver
```

**Verify installation:**

```bash
which chromedriver
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

**7. Run the converter and follow interactive prompts:**

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
git --version
python3 --version
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
which chromedriver
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

**8. Run the converter and follow interactive prompts:**

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
git --version
python --version
```

**9. Run the converter and follow interactive prompts:**

```powershell
python export_ucalgary_anki.py
```

---
