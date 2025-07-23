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

        # If a details URL is provided, extract all card IDs via the patient rel redirect
        if details_url:
            driver.get(details_url)
            time.sleep(2)
            # Find all patient elements with a rel attribute
            patient_elems = driver.find_elements(By.CSS_SELECTOR, ".patient[rel]")
            # Extract rel attributes before navigation to avoid stale element references
            rels = [pe.get_attribute("rel") for pe in patient_elems]
            cards = []
            for rel in tqdm(rels, desc="Scraping cards"):
                patient_url = f"{base_host}/patient/{rel}?bag_id={bag_id}"
                driver.get(patient_url)
                time.sleep(2)
                # Selenium follows the redirect; grab the final card URL
                card_page_url = driver.current_url
                m = re.search(r"/card/(\d+)", card_page_url)
                if not m:
                    continue
                cid = m.group(1)

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
            # Single deck ID provided directly
            deck_ids = [deck_id]

            # 3) COLLECT CARD IDs FROM THE SINGLE DECK
            card_ids = []
            for did in deck_ids:
                sub_deck_url = f"{base_host}/deck/{did}"
                driver.get(sub_deck_url)
                time.sleep(2)
                if "Error 403" in driver.title:
                    driver.save_screenshot(f"deck_{did}_403.png")
                    continue
                link_elements = driver.find_elements(
                    By.CSS_SELECTOR, "a[href*='/card/']"
                )
                for link in link_elements:
                    href = link.get_attribute("href")
                    m = re.search(r"/card/(\d+)", href)
                    if m:
                        cid = m.group(1)
                        if cid not in card_ids:
                            card_ids.append(cid)
            if not card_ids:
                sys.exit("No cards to export; check selectors or page structure.")

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
  <b>Answer:</b> {{CorrectAnswer}}
</div>
{{#Explanation}}
<div id="explanation"><b>Explanation:</b> {{Explanation}}</div>
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

    # reuse ChromeOptions setup
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
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
    os.makedirs(deck_name, exist_ok=True)
    output_path = os.path.join(deck_name, f"{deck_name}.apkg")
    export_apkg(cards, deck_name, output_path)


if __name__ == "__main__":
    main()
