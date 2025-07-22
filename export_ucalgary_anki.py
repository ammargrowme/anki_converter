#!/usr/bin/env python3

import os
import json
import csv
import argparse
import time
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

import genanki
import logging

from urllib.parse import urlparse

# configure root logger
logging.basicConfig(
    level=logging.DEBUG,  # switch to INFO or WARNING once you’re happy
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Load .env for credentials
load_dotenv()
EMAIL = os.getenv("UC_EMAIL")
PW = os.getenv("UC_PW")
RAW_BASE_URL = os.getenv("UC_BASE_URL", "")
# Derive root host from any provided URL
if RAW_BASE_URL:
    parsed = urlparse(RAW_BASE_URL)
    BASE = f"{parsed.scheme}://{parsed.netloc}"
else:
    BASE = "https://cards.ucalgary.ca"

logger.debug(
    f"Parsed UC_BASE_URL={RAW_BASE_URL} to BASE={BASE}, UC_EMAIL={EMAIL}, UC_PW={'***' if PW else None}"
)

# Unique IDs for genanki (change if needed)
DECK_ID_BASE = 1607392319000
MODEL_ID = 1607392319001


def selenium_login(driver, email, password, base_url):
    driver.get(f"{base_url}/login")
    logger.debug(f"Navigated to login page: {driver.current_url}")
    time.sleep(2)
    driver.find_element(By.NAME, "username").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
    time.sleep(3)
    logger.debug("Submitted login form, waiting to verify login")
    if "Logout" not in driver.page_source:
        raise RuntimeError("Login failed – check credentials.")
    logger.debug("Login successful")


def selenium_scrape_deck(deck_id, email, password, base_url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    try:
        logger.debug(f"Starting scrape for deck {deck_id}")
        selenium_login(driver, email, password, base_url)
        deck_url = f"{base_url}/details/{deck_id}?bag_id={deck_id}"
        logger.debug(f"Navigating to deck URL: {deck_url}")
        driver.get(deck_url)
        time.sleep(2)
        logger.debug(f"Page title after deck load: {driver.title}")

        # Get card IDs
        card_elements = driver.find_elements(By.CSS_SELECTOR, "div.patient[rel]")
        card_ids = [el.get_attribute("rel") for el in card_elements]
        logger.debug(f"Found {len(card_ids)} card IDs: {card_ids}")

        cards = []
        for cid in card_ids:
            card_url = f"{base_url}/card/{cid}"
            logger.debug(f"Scraping card ID: {cid}")
            logger.debug(f"Card page URL: {card_url}")
            driver.get(card_url)
            time.sleep(2)
            logger.debug(f"Page title after card load: {driver.title}")

            # Extract background paragraphs
            background_parts = []
            bg_selectors = [
                "body > div > div.container.card > div:nth-child(2) > table > tbody > tr > td",
                "body > div > div.container.card > div:nth-child(3) > div > div > div > table > tbody > tr > td",
            ]
            for sel in bg_selectors:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                logger.debug(
                    f"Found {len(elems)} elements for background selector: {sel}"
                )
                for el in elems:
                    text = el.text.strip()
                    if text:
                        background_parts.append(text)
            background = "\n\n".join(background_parts) if background_parts else ""
            logger.debug(f"Extracted background: {background!r}")

            # Extract question
            try:
                question_el = driver.find_element(
                    By.CSS_SELECTOR, "#workspace > div.solution.container > form > h3"
                )
                question = question_el.text.strip()
            except NoSuchElementException:
                question = "[No Question]"
            logger.debug(f"Extracted question: {question!r}")

            # Extract options
            option_elems = driver.find_elements(
                By.CSS_SELECTOR,
                "#workspace > div.solution.container > form > div.options > div.option > label",
            )
            options = [el.text.strip() for el in option_elems if el.text.strip()]
            logger.debug(f"Extracted {len(options)} options: {options}")

            # Combine for Anki
            full_question = (
                f"{background}\n\n<b>{question}</b>" if background else question
            )
            answer = "\n".join(f"- {opt}" for opt in options)

            cards.append(
                {
                    "id": cid,
                    "question": full_question,
                    "answer": answer,
                    "tags": [],
                    "images": [],
                }
            )
        return cards
    finally:
        driver.quit()


# Export functions unchanged


def export_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[+] JSON written to {path}")


def export_csv(data, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Question", "Answer", "Tags"])
        for c in data:
            writer.writerow([c["question"], c["answer"], " ".join(c.get("tags", []))])
    print(f"[+] CSV written to {path}")


def export_apkg(data, deck_name, path):
    model = genanki.Model(
        MODEL_ID,
        "Basic Q&A",
        fields=[{"name": "Question"}, {"name": "Answer"}],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Question}}",
                "afmt": "{{FrontSide}}<hr id=answer>{{Answer}}",
            }
        ],
    )
    deck = genanki.Deck(DECK_ID_BASE, deck_name)
    for c in data:
        note = genanki.Note(
            model=model, fields=[c["question"], c["answer"]], tags=c.get("tags", [])
        )
        deck.add_note(note)
    gen = genanki.Package(deck)
    gen.write_to_file(path)
    print(f"[+] APKG written to {path}")


def main():
    p = argparse.ArgumentParser(
        description="Export UCalgary Cards → Anki (via Selenium)"
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--deck", metavar="ID", help="Process one deck ID → cards only")

    p.add_argument("--username", help="UCalgary email (overrides .env UC_EMAIL)")
    p.add_argument("--password", help="UCalgary password (overrides .env UC_PW)")
    p.add_argument(
        "--base-url",
        dest="base_url",
        help="UCalgary base URL (overrides .env UC_BASE_URL)",
    )
    p.add_argument(
        "--out-prefix",
        dest="out_prefix",
        default="output",
        help="Prefix for output files (default: 'output')",
    )

    args = p.parse_args()

    email = args.username or EMAIL
    pw = args.password or PW
    base_url = args.base_url or BASE

    if not email or not pw:
        p.error(
            "Missing credentials: set UC_EMAIL and UC_PW in a .env file "
            "or pass --username/--password arguments."
        )
    if not args.deck:
        p.error("You must provide --deck")

    cards = selenium_scrape_deck(args.deck, email, pw, base_url)
    deck_name = f"Deck_{args.deck}"

    export_json(cards, f"{args.out_prefix}.json")
    export_csv(cards, f"{args.out_prefix}.csv")
    export_apkg(cards, deck_name, f"{args.out_prefix}.apkg")


if __name__ == "__main__":
    main()
