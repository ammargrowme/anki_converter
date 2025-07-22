#!/usr/bin/env python3

import os
import json
import csv
import argparse
import time
from dotenv import load_dotenv
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

import genanki
import logging
import re

from urllib.parse import urlparse, parse_qs

# configure root logger
logging.basicConfig(
    level=logging.DEBUG,  # switch to INFO once happy
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

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

logger.debug(
    f"CONFIG → BASE={BASE!r}, default_details_url={default_details_url!r}, "
    f"bag_id_default={BAG_ID_DEFAULT!r}, UC_EMAIL={'***' if EMAIL else None}"
)

DECK_ID_BASE = 1607392319000
MODEL_ID = 1607392319001


def selenium_login(driver, email, password, base_host):
    login_url = f"{base_host}/login"
    driver.get(login_url)
    logger.debug(f"[login] GET {login_url}")
    time.sleep(2)

    driver.find_element(By.NAME, "username").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
    time.sleep(3)
    logger.debug("Post-login page title=%r", driver.title)
    logger.debug("Cookies after login: %s", driver.get_cookies())

    if "Logout" not in driver.page_source:
        raise RuntimeError("Login failed – check credentials")
    logger.debug("✅ Logged in")


def selenium_scrape_deck(deck_id, email, password, base_host, bag_id, details_url=None):
    opts = webdriver.ChromeOptions()
    # opts.add_argument("--headless")
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
        # 1) LOGIN
        selenium_login(driver, email, password, base_host)

        # If a details URL is provided, extract all card IDs via the patient rel redirect
        if details_url:
            logger.debug(f"[details] GET {details_url}")
            driver.get(details_url)
            time.sleep(2)
            # Find all patient elements with a rel attribute
            patient_elems = driver.find_elements(By.CSS_SELECTOR, ".patient[rel]")
            # Extract rel attributes before navigation to avoid stale element references
            rels = [pe.get_attribute("rel") for pe in patient_elems]
            logger.debug("Found %d patient elements on details page", len(rels))
            cards = []
            for rel in rels:
                patient_url = f"{base_host}/patient/{rel}?bag_id={bag_id}"
                logger.debug(f"[patient] GET {patient_url}")
                driver.get(patient_url)
                time.sleep(2)
                # Selenium follows the redirect; grab the final card URL
                card_page_url = driver.current_url
                logger.debug("Redirected to card URL=%r", card_page_url)
                m = re.search(r"/card/(\d+)", card_page_url)
                if not m:
                    logger.error("Could not parse card ID from URL %s", card_page_url)
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

                # Scrape options and detect the correct answer
                opts_elems = driver.find_elements(
                    By.CSS_SELECTOR,
                    "#workspace > div.solution.container > form > div.options > div.option > label",
                )
                options = []
                correct_answer = None
                for idx, label in enumerate(opts_elems):
                    text = label.text.strip()
                    if not text:
                        continue
                    options.append(text)
                    try:
                        inp = label.find_element(
                            By.XPATH, "preceding-sibling::input[@type='radio']"
                        )
                        if (
                            inp.get_attribute("checked") in ("true", "checked")
                            or inp.get_attribute("aria-checked") == "true"
                        ):
                            correct_answer = text
                    except NoSuchElementException:
                        pass

                if correct_answer is None and options:
                    correct_answer = options[0]

                formatted_opts = "\n".join(
                    f"{i+1}. {opt}" for i, opt in enumerate(options)
                )
                if background:
                    full_q = f"{background}\n\n<b>{question}</b>\n\n{formatted_opts}"
                else:
                    full_q = f"{question}\n\n{formatted_opts}"

                answer = correct_answer or "[No Answer Found]"
                cards.append(
                    {
                        "id": cid,
                        "question": full_q,
                        "answer": answer,
                        "tags": [],
                        "images": [],
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
                logger.debug(f"[sub-deck] GET {sub_deck_url}")
                driver.get(sub_deck_url)
                time.sleep(2)
                logger.debug(f"[sub-deck] title={driver.title!r}")
                if "Error 403" in driver.title:
                    logger.error("Sub-deck page 403 Forbidden: %s", driver.current_url)
                    driver.save_screenshot(f"deck_{did}_403.png")
                    continue
                link_elements = driver.find_elements(
                    By.CSS_SELECTOR, "a[href*='/card/']"
                )
                logger.debug(
                    "Found %d card link elements on deck %s: %r",
                    len(link_elements),
                    did,
                    link_elements,
                )
                for link in link_elements:
                    href = link.get_attribute("href")
                    m = re.search(r"/card/(\d+)", href)
                    if m:
                        cid = m.group(1)
                        if cid not in card_ids:
                            card_ids.append(cid)
            logger.debug("→ Total unique card IDs: %r", card_ids)
            if not card_ids:
                logger.error("No card links found in any sub-deck.")
                sys.exit("No cards to export; check selectors or page structure.")

            cards = []
            for cid in card_ids:
                # Build card URL without bag_id parameter to avoid 403 errors on card pages
                card_url = f"{base_host}/card/{cid}"
                logger.debug(f"[card] GET {card_url}")
                driver.get(card_url)
                time.sleep(2)
                logger.debug(f"[card] title={driver.title!r}")

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
                logger.debug(f"  background → {background!r}")

                # question
                try:
                    qel = driver.find_element(
                        By.CSS_SELECTOR,
                        "#workspace > div.solution.container > form > h3",
                    )
                    question = qel.text.strip()
                except NoSuchElementException:
                    question = "[No Question]"
                logger.debug(f"  question → {question!r}")

                # Scrape options and detect the correct answer
                opts_elems = driver.find_elements(
                    By.CSS_SELECTOR,
                    "#workspace > div.solution.container > form > div.options > div.option > label",
                )
                options = []
                correct_answer = None
                for idx, label in enumerate(opts_elems):
                    text = label.text.strip()
                    if not text:
                        continue
                    options.append(text)
                    try:
                        inp = label.find_element(
                            By.XPATH, "preceding-sibling::input[@type='radio']"
                        )
                        if (
                            inp.get_attribute("checked") in ("true", "checked")
                            or inp.get_attribute("aria-checked") == "true"
                        ):
                            correct_answer = text
                    except NoSuchElementException:
                        pass

                if correct_answer is None and options:
                    correct_answer = options[0]

                formatted_opts = "\n".join(
                    f"{i+1}. {opt}" for i, opt in enumerate(options)
                )
                if background:
                    full_q = f"{background}\n\n<b>{question}</b>\n\n{formatted_opts}"
                else:
                    full_q = f"{question}\n\n{formatted_opts}"

                answer = correct_answer or "[No Answer Found]"
                cards.append(
                    {
                        "id": cid,
                        "question": full_q,
                        "answer": answer,
                        "tags": [],
                        "images": [],
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
    # Extended MCQ model: fields for background, question, choices, correct index
    mcq_model = genanki.Model(
        MODEL_ID,
        "MCQ Q&A",
        fields=[
            {"name": "Background"},
            {"name": "Question"},
            {"name": "Choice1"},
            {"name": "Choice2"},
            {"name": "Choice3"},
            {"name": "Choice4"},
            {"name": "CorrectAnswer"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": """
{{Background}}<br><br>
<b>{{Question}}</b>
<ul>
  {{#Choice1}}<li><label><input type="radio" name="choice">{{Choice1}}</label></li>{{/Choice1}}
  {{#Choice2}}<li><label><input type="radio" name="choice">{{Choice2}}</label></li>{{/Choice2}}
  {{#Choice3}}<li><label><input type="radio" name="choice">{{Choice3}}</label></li>{{/Choice3}}
  {{#Choice4}}<li><label><input type="radio" name="choice">{{Choice4}}</label></li>{{/Choice4}}
</ul>
""",
                "afmt": """
{{FrontSide}}<hr id=answer>
<b>Answer:</b> {{CorrectAnswer}}
""",
            }
        ],
    )
    deck = genanki.Deck(DECK_ID_BASE, deck_name)
    for c in data:
        # You now need to split out background, question, choices, and correct answer index
        background = ""
        question = c["question"]
        choices = []
        correct_idx = 1
        # Split the full question into background, question, choices
        if "\n\n" in question:
            # Assume format: background\n\n<b>question</b>\n\n1. choice...
            parts = question.split("\n\n")
            if len(parts) == 3:
                background = parts[0]
                question_text = parts[1]
                choices_text = parts[2]
            else:
                background = ""
                question_text = parts[0]
                choices_text = parts[1]
        else:
            background = ""
            question_text = question
            choices_text = ""
        # Remove <b> tags
        question_text = question_text.replace("<b>", "").replace("</b>", "")
        # Parse choices
        for line in choices_text.split("\n"):
            if line.strip() and "." in line:
                # Remove the number
                opt = line.split(".", 1)[1].strip()
                choices.append(opt)
        # Map correct answer to index
        correct_idx = 0
        for i, opt in enumerate(choices):
            if opt == c["answer"]:
                correct_idx = i + 1  # Anki models often start from 1
                break
        # Pad choices up to 4 (or leave blank)
        while len(choices) < 4:
            choices.append("")
        deck.add_note(
            genanki.Note(
                model=mcq_model,
                fields=[
                    background,
                    question_text,
                    choices[0],
                    choices[1],
                    choices[2],
                    choices[3],
                    c["answer"],
                ],
                tags=c.get("tags", []),
            )
        )
    genanki.Package(deck).write_to_file(path)
    print(f"[+] APKG → {path}")


def main():
    p = argparse.ArgumentParser(
        description="Export UCalgary Cards → Anki (via Selenium)"
    )
    p.add_argument(
        "--deck",
        dest="deck",
        required=False,
        help="Deck ID to process (optional if base URL contains a details URL)",
    )
    p.add_argument("--username", help="UCalgary email (overrides .env)")
    p.add_argument("--password", help="UCalgary password (overrides .env)")
    p.add_argument(
        "--base-url",
        dest="base_url_override",
        help=(
            "Host (e.g. https://cards.ucalgary.ca) or full "
            "details URL (…/details/ID?bag_id=XYZ) to override .env"
        ),
    )
    p.add_argument(
        "--out-prefix",
        default="output",
        help="Output prefix (e.g. pediatrics_decks)",
    )
    args = p.parse_args()

    email = args.username or EMAIL
    pw = args.password or PW
    if not email or not pw:
        p.error(
            "🔒 Missing credentials – set UC_EMAIL/UC_PW in .env or pass --username/--password"
        )
    deck_id_arg = args.deck

    # figure out host, details_url and bag_id
    if args.base_url_override:
        po = urlparse(args.base_url_override)
        host = f"{po.scheme}://{po.netloc}" if po.scheme else args.base_url_override
        if "/details/" in po.path:
            details_url = args.base_url_override
            bag_id = parse_qs(po.query).get("bag_id", [None])[0] or BAG_ID_DEFAULT
        else:
            details_url = None
            bag_id = BAG_ID_DEFAULT or deck_id_arg
    else:
        host = BASE
        details_url = default_details_url
        bag_id = BAG_ID_DEFAULT or deck_id_arg

    # Determine deck_id: prefer CLI, otherwise parse from details_url
    if deck_id_arg:
        deck_id = deck_id_arg
    elif details_url:
        # extract deck ID from the details URL path
        parsed_details = urlparse(details_url)
        try:
            deck_id = parsed_details.path.split("/details/")[1]
        except (IndexError, AttributeError):
            p.error("🔧 Could not parse deck ID from base URL")
    else:
        p.error(
            "🔒 Missing deck ID – set UC_BASE_URL to a details URL in .env or pass --deck"
        )

    logger.debug(f"RUN → host={host}, details_url={details_url!r}, bag_id={bag_id!r}")

    cards = selenium_scrape_deck(deck_id, email, pw, host, bag_id, details_url)
    deck_name = f"Deck_{deck_id}"

    # export_json(cards, f"{args.out_prefix}.json")
    # export_csv(cards, f"{args.out_prefix}.csv")
    export_apkg(cards, deck_name, f"{args.out_prefix}.apkg")


if __name__ == "__main__":
    main()
