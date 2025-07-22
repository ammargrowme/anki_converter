# anki_converter

Converts UofC Cards into an Anki `.apkg` deck using Selenium + Genanki.

---

## Prerequisites

- **Python 3.8+**
- Chrome browser & [ChromeDriver](https://sites.google.com/chromium.org/driver/) matching your Chrome version
- Git

---

## Quickstart

### macOS / Linux

1. **Clone & enter project:**

   ```bash
   git clone <repo_url> && cd anki_converter
   ```

2. **Make setup script executable & install dependencies:**

   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Activate the virtual environment:**

   ```bash
   source .venv/bin/activate
   ```

4. **Configure credentials:**
   Create a `.env` file in the project root with:

   ```ini
   UC_EMAIL=your_ucalgary_email@example.com
   UC_PW=your_uc_password
   UC_BASE_URL=https://cards.ucalgary.ca/details/<DETAILS_ID>?bag_id=<BAG_ID>
   # (optional) UC_BAG_ID=<bag_id_if_not_in_URL>
   ```

5. **Run the converter (uses UC_BASE_URL from `.env`):**
   ```bash
   python export_ucalgary_anki.py
   ```
   To override the details URL or specify a deck ID:
   ```bash
   python export_ucalgary_anki.py --deck <ID>
   ```

---

### Windows (PowerShell)

```powershell
git clone <repo_url> ; cd anki_converter

# Create & activate venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure credentials (same .env file)
# Run (uses UC_BASE_URL from .env)
python export_ucalgary_anki.py

# To override or specify a deck ID:
python export_ucalgary_anki.py --deck <ID>
```

---

## Command-line Flags

- `--deck <ID>`  
  Optional override: process by deck ID instead of using `UC_BASE_URL` from `.env`.
- `--username <email>`  
  Override `UC_EMAIL` in `.env`.
- `--password <pw>`  
  Override `UC_PW` in `.env`.
- `--base-url <URL>`  
  Override `UC_BASE_URL`.
- `--out-prefix <prefix>`  
  Prefix for output files (`.json`, `.csv`, `.apkg`). Defaults to `output`.

---

## What to Expect

- **Startup logs:**
  ```
  Script started
  Loading screen...
  Logging in...
  Logged in successfully
  ```
- **Progress bar:** Live “Scraping cards” via `tqdm`.
- **Output:**  
  Creates `Deck_<ID>/Deck_<ID>.apkg`.

---

## Troubleshooting

- **Module not found?**
  ```bash
  pip install -r requirements.txt
  ```
- **ChromeDriver mismatch?**  
  Download from https://sites.google.com/chromium.org/driver/
- **Hidden browser issues?**  
  Comment out `opts.add_argument("--headless")` in `export_ucalgary_anki.py`.

---

Enjoy converting your UofC Cards to Anki! Open an issue for questions or feature requests.
