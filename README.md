# anki\_converter

**Repository:** [https://github.com/ammargrowme/anki\_converter.git](https://github.com/ammargrowme/anki_converter.git)

[![GitHub Repo stars](https://img.shields.io/github/stars/ammargrowme/anki_converter)](https://github.com/ammargrowme/anki_converter)

A command-line tool that logs into the University of Calgary Cards site, scrapes question-and-answer cards, and generates a ready-to-import Anki `.apkg` deck using Selenium and Genanki.

---

## Table of Contents

1. [Installation](#installation)
2. [Setup and Configuration](#setup-and-configuration)
3. [Usage](#usage)
4. [Expectations](#expectations)
5. [Troubleshooting](#troubleshooting)

   * [Common Issues](#common-issues)
6. [Tips](#tips)
7. [Full Setup Guides](#full-setup-guides)

   * [macOS Full Setup](#macos-full-setup)
   * [Ubuntu/Debian Linux Full Setup](#ubuntudebian-linux-full-setup)
   * [Windows Full Setup](#windows-full-setup)
8. [Requirements by OS](#requirements-by-os)
9. [Editing Files in Terminal Editors](#editing-files-in-terminal-editors)

---

<a id="requirements-by-os"></a>

## Requirements by OS

### macOS

* Homebrew
* Git
* Python 3
* Chrome
* ChromeDriver

Refer to [Install Homebrew & Dependencies](#install-homebrew--dependencies) and [Clone & Setup Virtualenv](#clone--setup-virtualenv).

### Ubuntu/Debian Linux

* apt package manager
* Git
* Python 3
* pip
* Chrome
* ChromeDriver

Refer to [Install Homebrew & Dependencies](#install-homebrew--dependencies) and [Clone & Setup Virtualenv](#clone--setup-virtualenv).

### Windows

* Git installer
* Python installer
* Chrome installer
* ChromeDriver installer

Refer to [Windows (PowerShell)](#windows-powershell).

---

<a id="installation"></a>

## Installation

Install system dependencies as needed (see [Requirements by OS](#requirements-by-os)).

---

<a id="setup-and-configuration"></a>

## Setup and Configuration

On first run, the script prompts for your UofC email, password, and target cards URL, saving credentials in `config.json`. Subsequent runs only ask for URL.

**First run**:

1. **Copy & Paste:** `python export_ucalgary_anki.py`
2. Enter **email** and **password** (3 attempts max).
3. On success, credentials saved.
4. Enter **cards URL** to generate deck.

**Subsequent runs**:

1. **Copy & Paste:** `python export_ucalgary_anki.py`
2. Loads credentials; prompts for **URL**.

**Save Location:** Confirm or change output path (`Deck_<ID>.apkg`).

---

<a id="usage"></a>

## Usage

```bash
python export_ucalgary_anki.py
```

> Follow prompts: (1) credentials if first run, (2) cards URL, (3) save location.

---

<a id="expectations"></a>

## Expectations

* **Logs:** “Script started”, “Loading screen…”, “Logging in…”, “Logged in successfully”
* **Progress:** Live “Scraping cards” bar
* **Output:** **`Deck_<ID>.apkg`**

---

<a id="troubleshooting"></a>

## Troubleshooting

### Common Issues

* **Module not found:** `pip install -r requirements.txt`
* **ChromeDriver mismatch:** download matching version
* **Hidden browser:** comment out `--headless`
* **Verify PATH:** `which chromedriver` / `where chromedriver`
* **Permissions:** `chmod +x setup.sh`
* **venv errors:** `python3 -m venv .venv` & activate
* **Network/timeouts:** check firewall/proxy
* **Save location:** ensure valid path & write access

#### Untrusted Package Warning

* **macOS:** `xattr -d com.apple.quarantine path/to/file`
* **Windows:** `Unblock-File -Path .\setup.sh`
* **Linux:** `chmod +x setup.sh`

---

<a id="tips"></a>

## Tips

* Check **`python3 --version`** / **`pip --version`**
* Keep Chrome/ChromeDriver in sync
* Ensure active internet
* Scripts executable (**`chmod +x setup.sh`**)

---

<a id="editing-files-in-terminal-editors"></a>

## Editing Files in Terminal Editors

### Nano (macOS/Linux)

* Nav: arrow keys (no mouse)
* Delete line: **Ctrl+K**
* Select: **Ctrl+^** + arrows + **Ctrl+K**
* Paste: **Ctrl+U**
* Save: **Ctrl+O**, Enter
* Exit: **Ctrl+X**
* Cancel: **Ctrl+C**

### Vi/Vim (macOS/Linux)

* Modes: Normal, Insert
* Insert: **i**; Exit: **Esc**
* Nav: arrows or **h/j/k/l**
* Delete line: **dd**; delete char: **x**
* Save & exit: `:wq`; exit no save: `:q!`

### Notepad (Windows)

* Nav: mouse or arrows
* Save: **Ctrl+S**
* Close: **Alt+F4**

---

<a id="full-setup-guides"></a>

## Full Setup Guides

---

### macOS Full Setup

1. **Open folder:** `cd ~/anki_converter`
2. **Open Terminal:** **⌘+Space**, type `Terminal`, Enter
3. **Copy & Paste:** `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
4. **Copy & Paste:** `brew install git python3`

   * **Verify:** `git --version`; `python3 --version`
5. **Copy & Paste:** `brew install --cask google-chrome chromedriver`

   * **Verify:** `which chromedriver`
6. **Copy & Paste:** `git clone https://github.com/ammargrowme/anki_converter.git && cd anki_converter`
7. **Copy & Paste:** `chmod +x setup.sh && ./setup.sh`
8. **Copy & Paste:** `source .venv/bin/activate`
9. **Copy & Paste:** `python export_ucalgary_anki.py`

---

### Ubuntu/Debian Linux Full Setup

1. **Open folder:** `cd ~/anki_converter`
2. **Open Terminal:** Ctrl+Alt+T
3. **Copy & Paste:** `sudo apt update && sudo apt install -y git python3 python3-venv python3-pip wget`

   * **Verify:** `git --version`; `python3 --version`
4. **Copy & Paste:** `wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && sudo apt install -y ./google-chrome-stable_current_amd64.deb`
5. **Copy & Paste:** `sudo apt install -y chromium-chromedriver`

   * **Verify:** `which chromedriver`
6. **Copy & Paste:** `git clone https://github.com/ammargrowme/anki_converter.git && cd anki_converter`
7. **Copy & Paste:** `chmod +x setup.sh && ./setup.sh`
8. **Copy & Paste:** `source .venv/bin/activate`
9. **Copy & Paste:** `python export_ucalgary_anki.py`

---

### Windows Full Setup

1. **Open folder in PowerShell:** `cd C:\path\to\anki_converter`
2. **Run as Admin** and **Set policy:**
   **Copy & Paste:** `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
3. **Copy & Paste:** `git clone https://github.com/ammargrowme/anki_converter.git && cd anki_converter`
4. **Copy & Paste:** `python -m venv .venv && .\.venv\Scripts\Activate.ps1`
5. **Copy & Paste:** `pip install --upgrade pip && pip install -r requirements.txt`

   * **Verify:** `git --version`; `python --version`
6. **Copy & Paste:** `python export_ucalgary_anki.py`

---
