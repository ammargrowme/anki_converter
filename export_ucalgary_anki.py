#!/usr/bin/env python3

import os
import os.path
import json
import csv
import time
import sys
import getpass
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

import genanki
from tqdm import tqdm
import requests
import re

from urllib.parse import urlparse, parse_qs

# Try to import tkinter for file dialogs (fallback to command line if not available)
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

# Config file for storing credentials
CONFIG_PATH = os.path.expanduser("~/.uc_anki_config.json")


# Load .env for credentials and URLs
load_dotenv()
EMAIL = os.getenv("UC_EMAIL")
PW = os.getenv("UC_PW")

RAW_BASE_URL = os.getenv("UC_BASE_URL", "").strip()
ENV_BAG_ID = os.getenv("UC_BAG_ID", "").strip()  # optional

# Parse whatever the user put in UC_BASE_URL
if RAW_BASE_URL:
    parsed = urlparse(RAW_BASE_URL)
    BASE = f"{parsed.scheme}://{parsed.netloc}"
    # if they embedded a bag_id in the query, pull it out
    qs = parse_qs(parsed.query)
    parsed_bag = qs.get("bag_id", [None])[0]
    # if path is a full details URL, keep it
    default_details_url = RAW_BASE_URL if "/details/" in parsed.path else None
else:
    BASE = "https://cards.ucalgary.ca"
    parsed_bag = None
    default_details_url = None

# Priority for bag_id:
# 1. explicit UC_BAG_ID
# 2. parsed from UC_BASE_URL
# 3. fall back to deck_id at runtime
BAG_ID_DEFAULT = ENV_BAG_ID or parsed_bag


DECK_ID_BASE = 1607392319000
MODEL_ID = 1607392319001


def selenium_login(driver, email, password, base_host):
    login_url = f"{base_host}/login"
    driver.get(login_url)
    time.sleep(2)

    driver.find_element(By.NAME, "username").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
    time.sleep(3)

    if "Logout" not in driver.page_source:
        raise RuntimeError("Login failed – check credentials")


def selenium_scrape_deck(deck_id, email, password, base_host, bag_id, details_url=None):
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--kiosk-printing")
    # Suppress Chrome error messages and warnings
    opts.add_argument("--disable-logging")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-web-security")
    opts.add_argument("--disable-features=VizDisplayCompositor")
    opts.add_argument("--log-level=3")  # Only show fatal errors
    opts.add_experimental_option('excludeSwitches', ['enable-logging'])
    opts.add_experimental_option('useAutomationExtension', False)
    opts.add_experimental_option(
        "prefs",
        {
            "printing.print_preview_sticky_settings.appState": '{"recentDestinations":[],"selectedDestinationId":"Save as PDF","version":2}'
        },
    )
    driver = webdriver.Chrome(options=opts)
    # Prevent the print dialog by overriding window.print before any page loads
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument", {"source": "window.print = () => {};"}
    )

    try:
        print("Loading screen...")
        print("Logging in...")
        # 1) LOGIN
        selenium_login(driver, email, password, base_host)
        print("Logged in successfully")

        # If a details URL is provided, convert it to printdeck URL to get all cards
        if details_url:
            # Extract deck_id from details URL and use printdeck approach
            parsed_details = urlparse(details_url)
            try:
                deck_id_from_url = parsed_details.path.split("/details/")[1]
            except (IndexError, AttributeError):
                deck_id_from_url = "unknown"
            
            # Use printdeck page to collect all cards for the deck (including multiple per question)
            printdeck_url = f"{base_host}/printdeck/{deck_id_from_url}?bag_id={bag_id}"
            driver.get(printdeck_url)
            time.sleep(2)
            
            if "Error 403" in driver.title:
                driver.save_screenshot(f"deck_{deck_id_from_url}_403.png")
                sys.exit("Access denied to printdeck page")
            
            # Find all submit buttons with solution IDs on the printdeck page
            submit_buttons = driver.find_elements(
                By.CSS_SELECTOR, "div.submit button[rel*='/solution/']"
            )
            
            if not submit_buttons:
                sys.exit("No submit buttons found on printdeck page; check selectors or page structure.")
            
            # Extract card IDs from solution button rel attributes
            card_ids = []
            for button in submit_buttons:
                rel = button.get_attribute("rel")
                # Extract card ID from rel like "/solution/17623644/"
                m = re.search(r"/solution/(\d+)/", rel)
                if m:
                    cid = m.group(1)
                    if cid not in card_ids:
                        card_ids.append(cid)
            
            if not card_ids:
                sys.exit("No card IDs found from submit buttons; check page structure.")
            
            cards = []
            for cid in tqdm(card_ids, desc="Scraping cards"):
                # Build card URL without bag_id parameter to avoid 403 errors on card pages
                card_url = f"{base_host}/card/{cid}"
                driver.get(card_url)
                time.sleep(2)

                # Now scrape the card page just like before
                # background parts (paragraphs in card)
                background_parts = []
                bg_elems = driver.find_elements(
                    By.CSS_SELECTOR, "div.container.card div.block.group p"
                )
                for el in bg_elems:
                    txt = el.text.strip()
                    if txt:
                        background_parts.append(txt)
                background = "\n\n".join(background_parts).strip()

                # question
                try:
                    qel = driver.find_element(
                        By.CSS_SELECTOR,
                        "#workspace > div.solution.container > form > h3",
                    )
                    question = qel.text.strip()
                except NoSuchElementException:
                    question = "[No Question]"

                # Determine if multi-select (pickmany) by form attribute
                try:
                    form = driver.find_element(
                        By.CSS_SELECTOR, "#workspace > div.solution.container > form"
                    )
                    multi_flag = form.get_attribute("rel") == "pickmany"
                except Exception:
                    multi_flag = False

                # Detect free-text questions
                try:
                    freetext_elem = driver.find_element(
                        By.CSS_SELECTOR, "div.freetext-answer"
                    )
                    freetext_html = freetext_elem.get_attribute("outerHTML")
                    # Fetch provided answer via solution endpoint
                    sess = requests.Session()
                    for c in driver.get_cookies():
                        sess.cookies.set(c["name"], c["value"])
                    sol_resp = sess.post(
                        f"{base_host}/solution/{cid}/",
                        data=[("guess", ""), ("timer", "1")],
                    )
                    json_sol = {}
                    try:
                        json_sol = sol_resp.json()
                    except Exception:
                        pass
                    answer = json_sol.get("feedback", "").strip()
                    # Build front HTML including the textarea element
                    if background:
                        full_q = (
                            f'<div class="background">{background}</div>'
                            f'<div class="question"><b>{question}</b></div>'
                            f"{freetext_html}"
                        )
                    else:
                        full_q = (
                            f'<div class="question"><b>{question}</b></div>'
                            f"{freetext_html}"
                        )
                    # Append free-text card and skip MCQ logic
                    cards.append(
                        {
                            "id": cid,
                            "question": full_q,
                            "answer": answer,
                            "explanation": "",
                            "score_text": "",
                            "sources": [],
                            "tags": [],
                            "images": [],
                            "multi": False,
                            "percent": "",
                            "freetext": True,
                        }
                    )
                    continue
                except NoSuchElementException:
                    pass

                # Scrape options and fetch correct answers via API
                option_divs = driver.find_elements(
                    By.CSS_SELECTOR,
                    "#workspace > div.solution.container > form > div.options > div.option",
                )
                # Extract IDs and texts
                option_info = []
                for div in option_divs:
                    inp = div.find_element(By.TAG_NAME, "input")
                    opt_id = inp.get_attribute("value")
                    label = div.find_element(By.TAG_NAME, "label")
                    opt_text = label.text.strip()
                    option_info.append((opt_id, opt_text))
                # Prepare session with Selenium cookies
                sess = requests.Session()
                for c in driver.get_cookies():
                    sess.cookies.set(c["name"], c["value"])
                # Call solution endpoint to get correct answer IDs
                sol_url = f"{base_host}/solution/{cid}/"
                payload = [("guess[]", oid) for oid, _ in option_info] + [
                    ("timer", "2")
                ]
                resp = sess.post(sol_url, data=payload)
                json_resp = {}
                try:
                    json_resp = resp.json()
                except Exception:
                    pass
                correct_ids = json_resp.get("answers", [])
                feedback = json_resp.get("feedback", "").strip()
                score_text = json_resp.get("scoreText", "").strip()
                sources = []
                # Compute percentage score
                percent = f"{json_resp.get('score', 0)}%"
                # Build options and correct_answers lists by matching IDs
                options = [text for oid, text in option_info]
                correct_answers = [
                    text for oid, text in option_info if oid in correct_ids
                ]
                if not correct_answers and options:
                    correct_answers = [options[0]]
                # Format choices for front
                # Build clickable options HTML
                input_type = "checkbox" if multi_flag else "radio"
                options_html = "".join(
                    f'<div class="option">'
                    f'<input type="{input_type}" name="choice" id="choice_{cid}_{i}" value="{opt}">'
                    f'<label for="choice_{cid}_{i}">{opt}</label>'
                    f"</div>"
                    for i, opt in enumerate(options)
                )
                if background:
                    full_q = (
                        f'<div class="background">{background}</div>'
                        f'<div class="question"><b>{question}</b></div>'
                        f'<div class="options">{options_html}</div>'
                    )
                else:
                    full_q = (
                        f'<div class="question"><b>{question}</b></div>'
                        f'<div class="options">{options_html}</div>'
                    )
                answer = (
                    ", ".join(correct_answers)
                    if correct_answers
                    else "[No Answer Found]"
                )
                cards.append(
                    {
                        "id": cid,
                        "question": full_q,
                        "answer": answer,
                        "explanation": feedback,
                        "score_text": score_text,
                        "sources": sources,
                        "tags": [],
                        "images": [],
                        "multi": multi_flag,
                        "percent": percent,
                    }
                )
            return cards
        else:
            # Single deck ID provided directly - use printdeck page to scrape all questions directly
            printdeck_url = f"{base_host}/printdeck/{deck_id}?bag_id={bag_id}"
            driver.get(printdeck_url)
            time.sleep(2)
            
            if "Error 403" in driver.title:
                driver.save_screenshot(f"deck_{deck_id}_403.png")
                sys.exit("Access denied to printdeck page")
            
            # Find all submit buttons with solution IDs on the printdeck page
            submit_buttons = driver.find_elements(
                By.CSS_SELECTOR, "div.submit button[rel*='/solution/']"
            )
            
            if not submit_buttons:
                sys.exit("No submit buttons found on printdeck page; check selectors or page structure.")
            
            # Extract card IDs from solution button rel attributes
            card_ids = []
            for button in submit_buttons:
                rel = button.get_attribute("rel")
                # Extract card ID from rel like "/solution/17623644/"
                m = re.search(r"/solution/(\d+)/", rel)
                if m:
                    cid = m.group(1)
                    if cid not in card_ids:
                        card_ids.append(cid)
            
            if not card_ids:
                sys.exit("No card IDs found from submit buttons; check page structure.")

            cards = []
            for cid in tqdm(card_ids, desc="Scraping cards"):
                # Build card URL without bag_id parameter to avoid 403 errors on card pages
                card_url = f"{base_host}/card/{cid}"
                driver.get(card_url)
                time.sleep(2)

                # background parts (paragraphs in card)
                background_parts = []
                bg_elems = driver.find_elements(
                    By.CSS_SELECTOR, "div.container.card div.block.group p"
                )
                for el in bg_elems:
                    txt = el.text.strip()
                    if txt:
                        background_parts.append(txt)
                background = "\n\n".join(background_parts).strip()

                # question
                try:
                    qel = driver.find_element(
                        By.CSS_SELECTOR,
                        "#workspace > div.solution.container > form > h3",
                    )
                    question = qel.text.strip()
                except NoSuchElementException:
                    question = "[No Question]"

                # Determine if multi-select (pickmany) by form attribute
                try:
                    form = driver.find_element(
                        By.CSS_SELECTOR, "#workspace > div.solution.container > form"
                    )
                    multi_flag = form.get_attribute("rel") == "pickmany"
                except Exception:
                    multi_flag = False

                # Detect free-text questions
                try:
                    freetext_elem = driver.find_element(
                        By.CSS_SELECTOR, "div.freetext-answer"
                    )
                    freetext_html = freetext_elem.get_attribute("outerHTML")
                    # Fetch provided answer via solution endpoint
                    sess = requests.Session()
                    for c in driver.get_cookies():
                        sess.cookies.set(c["name"], c["value"])
                    sol_resp = sess.post(
                        f"{base_host}/solution/{cid}/",
                        data=[("guess", ""), ("timer", "1")],
                    )
                    json_sol = {}
                    try:
                        json_sol = sol_resp.json()
                    except Exception:
                        pass
                    answer = json_sol.get("feedback", "").strip()
                    # Build front HTML including the textarea element
                    if background:
                        full_q = (
                            f'<div class="background">{background}</div>'
                            f'<div class="question"><b>{question}</b></div>'
                            f"{freetext_html}"
                        )
                    else:
                        full_q = (
                            f'<div class="question"><b>{question}</b></div>'
                            f"{freetext_html}"
                        )
                    # Append free-text card and skip MCQ logic
                    cards.append(
                        {
                            "id": cid,
                            "question": full_q,
                            "answer": answer,
                            "explanation": "",
                            "score_text": "",
                            "sources": [],
                            "tags": [],
                            "images": [],
                            "multi": False,
                            "percent": "",
                            "freetext": True,
                        }
                    )
                    continue
                except NoSuchElementException:
                    pass

                # Scrape options and fetch correct answers via API
                option_divs = driver.find_elements(
                    By.CSS_SELECTOR,
                    "#workspace > div.solution.container > form > div.options > div.option",
                )
                # Extract IDs and texts
                option_info = []
                for div in option_divs:
                    inp = div.find_element(By.TAG_NAME, "input")
                    opt_id = inp.get_attribute("value")
                    label = div.find_element(By.TAG_NAME, "label")
                    opt_text = label.text.strip()
                    option_info.append((opt_id, opt_text))
                # Prepare session with Selenium cookies
                sess = requests.Session()
                for c in driver.get_cookies():
                    sess.cookies.set(c["name"], c["value"])
                # Call solution endpoint to get correct answer IDs
                sol_url = f"{base_host}/solution/{cid}/"
                payload = [("guess[]", oid) for oid, _ in option_info] + [
                    ("timer", "2")
                ]
                resp = sess.post(sol_url, data=payload)
                json_resp = {}
                try:
                    json_resp = resp.json()
                except Exception:
                    pass
                correct_ids = json_resp.get("answers", [])
                feedback = json_resp.get("feedback", "").strip()
                score_text = json_resp.get("scoreText", "").strip()
                sources = []
                # Compute percentage score
                percent = f"{json_resp.get('score', 0)}%"
                # Build options and correct_answers lists by matching IDs
                options = [text for oid, text in option_info]
                correct_answers = [
                    text for oid, text in option_info if oid in correct_ids
                ]
                if not correct_answers and options:
                    correct_answers = [options[0]]
                # Format choices for front
                # Build clickable options HTML
                input_type = "checkbox" if multi_flag else "radio"
                options_html = "".join(
                    f'<div class="option">'
                    f'<input type="{input_type}" name="choice" id="choice_{cid}_{i}" value="{opt}">'
                    f'<label for="choice_{cid}_{i}">{opt}</label>'
                    f"</div>"
                    for i, opt in enumerate(options)
                )
                if background:
                    full_q = (
                        f'<div class="background">{background}</div>'
                        f'<div class="question"><b>{question}</b></div>'
                        f'<div class="options">{options_html}</div>'
                    )
                else:
                    full_q = (
                        f'<div class="question"><b>{question}</b></div>'
                        f'<div class="options">{options_html}</div>'
                    )
                answer = (
                    ", ".join(correct_answers)
                    if correct_answers
                    else "[No Answer Found]"
                )
                cards.append(
                    {
                        "id": cid,
                        "question": full_q,
                        "answer": answer,
                        "explanation": feedback,
                        "score_text": score_text,
                        "sources": sources,
                        "tags": [],
                        "images": [],
                        "multi": multi_flag,
                        "percent": percent,
                    }
                )
            return cards

    finally:
        driver.quit()


def export_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[+] JSON → {path}")


def export_csv(data, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        w.writerow(["Question", "Answer", "Tags"])
        for c in data:
            w.writerow([c["question"], c["answer"], " ".join(c.get("tags", []))])
    print(f"[+] CSV → {path}")


def export_apkg(data, deck_name, path):
    mcq_model = genanki.Model(
        MODEL_ID,
        "MCQ Q&A",
        fields=[
            {"name": "Front"},
            {"name": "CorrectAnswer"},
            {"name": "Explanation"},
            {"name": "ScoreText"},
            {"name": "Percent"},
            {"name": "Sources"},
            {"name": "Multi"},
            {"name": "CardId"},
        ],
        css="""
.background { margin-bottom: 16px; }
.question    { font-size: 1.1em; margin-bottom: 8px; font-weight: bold; }
.options     { border: 1px solid #666; padding: 10px; display: inline-block; }
.option      { margin: 6px 0; }
.option input{ margin-right: 6px; }
#answer-section { margin-top: 12px; }
.correct { color: green !important; font-weight: bold; }
.incorrect { color: red !important; }
hr#answer-divider { border: none; border-top: 1px solid #888; margin: 16px 0; }
#answer-section { color: white; }
#explanation { color: white; }
""",
        templates=[
            {
                "name": "Card 1",
                "qfmt": """
{{Front}}
<script>
(function(){
  var cid = "{{CardId}}", key = "sel_"+cid;
  // Reset stored selections each time the card front loads
  localStorage.removeItem(key);
  var saved = JSON.parse(localStorage.getItem(key) || '[]');
  saved.forEach(function(id){
    var inp = document.getElementById(id);
    if(inp) inp.checked = true;
  });
  document.querySelectorAll('.option input').forEach(function(inp){
    inp.addEventListener('change', function(){
      var sel = Array.from(
        document.querySelectorAll('.option input:checked')
      ).map(function(e){ return e.id; });
      localStorage.setItem(key, JSON.stringify(sel));
    });
  });
})();
</script>
""",
                "afmt": """
{{Front}}
<script>
(function(){
  var cid = "{{CardId}}", key = "sel_"+cid,
      saved = JSON.parse(localStorage.getItem(key) || '[]');
  saved.forEach(function(id){
    var inp = document.getElementById(id);
    if(inp) inp.checked = true;
  });
})();
</script>
<hr id="answer-divider">
<script>
(function(){
  var answers = "{{CorrectAnswer}}".split(",").map(function(s){ return s.trim(); });
  document.querySelectorAll('.option label').forEach(function(lbl){
    var text = lbl.innerText.trim(),
        inp  = document.getElementById(lbl.getAttribute('for'));
    if(answers.includes(text)){
      lbl.classList.add('correct');
    } else if(inp && inp.checked){
      lbl.classList.add('incorrect');
    }
  });
})();
</script>
<div id="answer-section">
  <b>Correct answer(s):</b> {{CorrectAnswer}}<br>
  <b>Score:</b> <span id="score-text">{{ScoreText}}</span><br>
  <b>Percent:</b> <span id="percent-text">{{Percent}}</span>
</div>
<script>
(function(){
  var answers = "{{CorrectAnswer}}".split(",").map(function(s){ return s.trim(); });
  var selected = Array.from(document.querySelectorAll('.option input:checked')).map(function(inp){ return inp.value; });
  var correctLen = answers.length;
  var selectedCorrect = 0;
  selected.forEach(function(val){
    if(answers.includes(val)) selectedCorrect++;
  });
  var scoreEl = document.getElementById('score-text');
  var pctEl = document.getElementById('percent-text');
  if(scoreEl){
    scoreEl.innerText = selectedCorrect + " / " + correctLen;
  }
  if(pctEl){
    var pct = correctLen > 0 ? Math.round((selectedCorrect / correctLen) * 100) : 0;
    pctEl.innerText = pct + "%";
  }
})();
</script>
{{#Sources}}
<hr>
<div id="sources">
  <b>Sources:</b><br>
  {{{Sources}}}
</div>
{{/Sources}}
<hr>
{{#Explanation}}
<div id="explanation"><b>Explanation:</b> {{Explanation}}</div>
{{/Explanation}}
""",
            }
        ],
    )
    text_model = genanki.Model(
        MODEL_ID + 1,
        "FreeText Q&A",
        fields=[{"name": "Front"}, {"name": "CorrectAnswer"}, {"name": "Explanation"}],
        css=mcq_model.css,
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": """
{{Front}}
<hr id="answer-divider">
<div id="answer-section">
  <b>Answer:</b> <span style="color:white;">{{CorrectAnswer}}</span>
</div>
{{#Explanation}}
<div id="explanation"><b>Explanation:</b> <span style="color:white;">{{Explanation}}</span></div>
{{/Explanation}}
""",
            }
        ],
    )
    deck = genanki.Deck(DECK_ID_BASE, deck_name)
    for c in data:
        multi_flag = c.get("multi", False)
        multi = "1" if multi_flag else ""
        sources_html = "".join(f"<li>{src}</li>" for src in c.get("sources", []))
        model = text_model if c.get("freetext") else mcq_model
        fields = (
            [c["question"], c["answer"], c.get("explanation", "")]
            if c.get("freetext")
            else [
                c["question"],
                c["answer"],
                c.get("explanation", ""),
                c.get("score_text", ""),
                c.get("percent", ""),
                sources_html,
                multi,
                c["id"],
            ]
        )
        deck.add_note(
            genanki.Note(
                model=model,
                fields=fields,
                tags=c.get("tags", []),
            )
        )
    genanki.Package(deck).write_to_file(path)
    print(f"[+] APKG → {path}")


def prompt_credentials(base_host):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import TimeoutException

    # reuse ChromeOptions setup with error suppression
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    # Suppress Chrome error messages
    opts.add_argument("--disable-logging")
    opts.add_argument("--log-level=3")
    opts.add_experimental_option('excludeSwitches', ['enable-logging'])
    opts.add_experimental_option('useAutomationExtension', False)
    for attempt in range(3):
        email = input("Enter your UCalgary email: ").strip()
        password = getpass.getpass("Enter your UCalgary password: ")
        driver = webdriver.Chrome(options=opts)
        # override print
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "window.print = () => {};"},
        )
        try:
            selenium_login(driver, email, password, base_host)
            print("Login successful")
            driver.quit()
            return email, password
        except Exception as e:
            print(f"Login failed: {e}")
            driver.quit()
    sys.exit("Failed to login after 3 attempts")


def prompt_save_location(default_filename):
    """
    Prompt user for save location using GUI file dialog if available,
    otherwise fall back to command line input.
    """
    if HAS_GUI:
        try:
            # Create a root window but hide it
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            root.lift()      # Bring to front
            root.attributes('-topmost', True)  # Keep on top
            
            # Configure file dialog
            file_types = [
                ('Anki Deck Files', '*.apkg'),
                ('All Files', '*.*')
            ]
            
            # Show save dialog
            file_path = filedialog.asksaveasfilename(
                title="Save Anki Deck As...",
                defaultextension=".apkg",
                filetypes=file_types,
                initialfile=default_filename
            )
            
            # Clean up
            root.destroy()
            
            if file_path:  # User selected a file
                return file_path
            else:  # User cancelled
                print("Save cancelled by user.")
                sys.exit(0)
                
        except Exception as e:
            print(f"GUI dialog failed ({e}), falling back to command line input...")
            # Fall through to command line prompt
    
    # Command line fallback
    print(f"\n📁 Save Location")
    print(f"Default: {default_filename}")
    user_input = input(f"Enter path to save Anki deck (or press Enter for default): ").strip()
    return user_input if user_input else default_filename


def show_completion_message(output_path, card_count):
    """
    Show completion message with GUI if available, otherwise console only.
    """
    message = f"✅ Success! Created Anki deck with {card_count} cards.\n\nSaved to: {output_path}\n\nImport this file into Anki:\nFile → Import → Select your .apkg file"
    
    if HAS_GUI:
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("Anki Deck Created Successfully!", message)
            root.destroy()
        except Exception:
            # Fall back to console if GUI fails
            pass
    
    print(f"\n🎉 {message}")


def main():
    # Interactive credential setup
    # Determine host and default BASE from .env parsing above
    host = BASE
    # Prompt URL every run
    base_url_override = input("Enter UCalgary base URL or details URL: ").strip()
    # Derive details_url and bag_id same as before but using base_url_override
    if base_url_override:
        po = urlparse(base_url_override)
        host = f"{po.scheme}://{po.netloc}" if po.scheme else base_url_override
        if "/details/" in po.path:
            details_url = base_url_override
            bag_id = parse_qs(po.query).get("bag_id", [None])[0] or BAG_ID_DEFAULT
        else:
            details_url = None
            bag_id = BAG_ID_DEFAULT
    else:
        details_url = default_details_url
        bag_id = BAG_ID_DEFAULT
    # Load or prompt credentials
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as cf:
            cfg = json.load(cf)
        email = cfg.get("username")
        password = cfg.get("password")
    else:
        email, password = prompt_credentials(host)
        with open(CONFIG_PATH, "w") as cf:
            json.dump({"username": email, "password": password}, cf)
    # If login fails during scraping, prompt to update credentials
    try:
        cards = selenium_scrape_deck(
            deck_id=None,
            email=email,
            password=password,
            base_host=host,
            bag_id=bag_id,
            details_url=details_url,
        )
    except RuntimeError as e:
        print(f"Login error during scrape: {e}")
        email, password = prompt_credentials(host)
        with open(CONFIG_PATH, "w") as cf:
            json.dump({"username": email, "password": password}, cf)
        cards = selenium_scrape_deck(
            deck_id=None,
            email=email,
            password=password,
            base_host=host,
            bag_id=bag_id,
            details_url=details_url,
        )
    # Determine deck_id for output naming
    if details_url:
        parsed_details = urlparse(details_url)
        try:
            deck_id = parsed_details.path.split("/details/")[1]
        except (IndexError, AttributeError):
            deck_id = "unknown"
    else:
        deck_id = bag_id or "unknown"
    deck_name = f"Deck_{deck_id}"
    
    # Use GUI file dialog or command line prompt for save location
    default_filename = f"{deck_name}.apkg"
    output_path = prompt_save_location(default_filename)
    
    # Export the deck
    export_apkg(cards, deck_name, output_path)
    
    # Show completion message
    show_completion_message(output_path, len(cards))


if __name__ == "__main__":
    main()
