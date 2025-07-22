# anki_converter

Converts UofC Cards into an Anki `.apkg` deck using Selenium + Genanki.

---

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Usage](#usage)
4. [Flags](#flags)
5. [Expectations](#expectations)
6. [Troubleshooting](#troubleshooting)
7. [Tips](#tips)

---

## Installation

Install required system packages and set up the project environment across supported platforms.

### macOS / Linux

Use Homebrew to install Git, Python 3, Google Chrome, and ChromeDriver for headless browsing.

<details>
<summary>Install Homebrew & Dependencies</summary>
Use Homebrew to bootstrap essential tools and browser dependencies.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git python3
brew install --cask google-chrome chromedriver
```

</details>

<details>
<summary>Clone & Setup Virtualenv</summary>
Clone the repository and set up a Python virtual environment with dependencies.

```bash
git clone <repo_url> && cd anki_converter
chmod +x setup.sh
./setup.sh
```

</details>

<details>
<summary>Windows (PowerShell)</summary>
Install required tools and set up the virtual environment using PowerShell commands.

```powershell
# Git
# Python 3 (Add to PATH)
# Chrome & ChromeDriver (add to PATH)
git clone <repo_url> ; cd anki_converter
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

</details>

---

## Configuration

Provide your University of Calgary credentials and the target cards URL so the script can authenticate and fetch your cards.

<details>
<summary>.env File</summary>
Define environment variables for secure authentication without exposing credentials in code.

Create `.env` in project root:

```ini
UC_EMAIL=you@ucalgary.ca
UC_PW=your_password
UC_BASE_URL=https://cards.ucalgary.ca/details/<DETAILS_ID>
```

</details>

---

## Usage

Run the converter script to scrape cards from UofC and generate an Anki deck.

<details>
<summary>Run Converter</summary>
Execute the script with default or custom options to export your cards.

```bash
# Default:
python export_ucalgary_anki.py

# Override URL:
python export_ucalgary_anki.py --base-url https://cards.ucalgary.ca/details/12345

# Override Deck ID:
python export_ucalgary_anki.py --deck <ID>
```

</details>

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

<details>
<summary>Common Issues</summary>

- Module not found → `pip install -r requirements.txt`
- ChromeDriver mismatch → download matching version
- Hidden browser → comment out `--headless`
- Verify PATH → `which chromedriver` / `where chromedriver`
- Internet & permissions
</details>

---

## Tips

Additional best practices to ensure smooth operation and maintenance.

- Check `python3 --version` / `pip --version`
- Keep Chrome/ChromeDriver in sync
- No extra spaces in `.env`
- Ensure active internet
- Scripts executable (`chmod +x setup.sh`)
