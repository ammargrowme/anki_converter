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

### macOS / Linux

<details>
<summary>Install Homebrew & Dependencies</summary>

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git python3
brew install --cask google-chrome chromedriver
```

</details>

<details>
<summary>Clone & Setup Virtualenv</summary>

```bash
git clone <repo_url> && cd anki_converter
chmod +x setup.sh
./setup.sh
```

</details>

<details>
<summary>Windows (PowerShell)</summary>

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

<details>
<summary>.env File</summary>

Create `.env` in project root:

```ini
UC_EMAIL=you@ucalgary.ca
UC_PW=your_password
UC_BASE_URL=https://cards.ucalgary.ca/details/<DETAILS_ID>
```

</details>

---

## Usage

<details>
<summary>Run Converter</summary>

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

```text
--deck <ID>         Process by deck ID instead of UC_BASE_URL
--username <email>  Override UC_EMAIL
--password <pw>     Override UC_PW
--base-url <URL>    Override UC_BASE_URL
```

---

## Expectations

- **Logs**: “Script started”, “Loading screen…”, “Logging in…”, “Logged in successfully”
- **Progress**: Live bar “Scraping cards”
- **Output**: `Deck_<ID>.apkg`

---

## Troubleshooting

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

- Check `python3 --version` / `pip --version`
- Keep Chrome/ChromeDriver in sync
- No extra spaces in `.env`
- Ensure active internet
- Scripts executable (`chmod +x setup.sh`)
