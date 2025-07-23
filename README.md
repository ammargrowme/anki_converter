# anki_converter

**Repository:** https://github.com/ammargrowme/anki_converter.git

[![GitHub Repo stars](https://img.shields.io/github/stars/ammargrowme/anki_converter)](https://github.com/ammargrowme/anki_converter)

Converts UofC Cards into an Anki `.apkg` deck using Selenium + Genanki.

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

---

## Installation

Install required system packages and set up the project environment across supported platforms.

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

---

## Tips

Additional best practices to ensure smooth operation and maintenance.

- Check `python3 --version` / `pip --version`
- Keep Chrome/ChromeDriver in sync
- No extra spaces in `.env`
- Ensure active internet
- Scripts executable (`chmod +x setup.sh`)
