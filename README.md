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

1. Clone & enter project:

   ```bash
   git clone <repo_url> && cd anki_converter

   2.	Make the setup script executable and run it:
   ```

chmod +x setup.sh
./setup.sh

    3.	Activate the virtual environment:

source .venv/bin/activate

    4.	Configure your credentials:

Create a file named .env in the project root with these entries:

UC_EMAIL=your_ucalgary_email@example.com
UC_PW=your_uc_password
UC_BASE_URL=https://cards.ucalgary.ca/details/<DETAILS_ID>?bag_id=<BAG_ID>

# (optional) UC_BAG_ID=<bag_id_if_not_in_URL>

    5.	Run the converter:
    •	Using the details URL from your .env:

python export_ucalgary_anki.py

    •	Or specifying a deck ID directly:

python export_ucalgary_anki.py --deck 335

⸻

Windows (PowerShell)

git clone <repo_url> ; cd anki_converter

# Create & activate venv

python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies

pip install --upgrade pip
pip install -r requirements.txt

# Configure credentials (same .env file in project root)

# Run

python export_ucalgary_anki.py --deck 335

⸻

Command-line flags
• --deck <ID>
Deck ID to process (overrides .env details URL).
• --username <email>
Override UC_EMAIL in .env.
• --password <pw>
Override UC_PW in .env.
• --base-url <URL>
Override UC_BASE_URL (can be just the host or the full details URL).
• --out-prefix <prefix>
Prefix for output files (.json, .csv, .apkg). Defaults to output.

⸻

What to Expect
• Startup logs:

Script started
Loading screen...
Logging in...
Logged in successfully

    •	Progress bar: Live “Scraping cards” counter via tqdm
    •	Result:

Creates a folder Deck*<ID>, containing Deck*<ID>.apkg.

⸻

Troubleshooting
• Module not found?

pip install -r requirements.txt

    •	ChromeDriver mismatch?

Download the matching version from https://sites.google.com/chromium.org/driver/
• Hidden browser issues?
Edit export_ucalgary_anki.py and comment out:

opts.add_argument("--headless")

to watch the browser run.

⸻

Enjoy converting your UofC Cards to Anki! Feel free to open an issue for questions or feature requests.
