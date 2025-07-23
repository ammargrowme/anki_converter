#!/usr/bin/env python3

import os
import os.path
import json
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


def add_patient_info_to_cards(cards, patients_list):
    """
    Add patient information to cards that may not have it.
    Distributes cards across patients in round-robin fashion.
    """
    for i, card in enumerate(cards):
        if "patient_info" not in card or not card["patient_info"]:
            # Assign patient in round-robin fashion
            patient_info = (
                patients_list[i % len(patients_list)]
                if patients_list
                else "Unknown Patient"
            )
            card["patient_info"] = patient_info
            card["patient_id"] = None  # Could be enhanced to extract actual patient IDs
    return cards


def extract_patients_from_deck_page(driver, base_host, deck_id, bag_id):
    """
    Extract patient names from a deck/bag page by visiting the deck details page.
    Returns a list of patient names found on the page.
    """
    patients = []
    try:
        # Navigate to the deck page to extract patient information
        deck_page_url = f"{base_host}/details/{deck_id}?bag_id={bag_id}"
        driver.get(deck_page_url)
        time.sleep(2)

        # Try the specific patient selector mentioned by user
        try:
            patient_elements = driver.find_elements(
                By.CSS_SELECTOR, "div.patients > div > h3"
            )
            for elem in patient_elements:
                patient_name = elem.text.strip()
                if patient_name and patient_name not in patients:
                    patients.append(patient_name)
        except Exception:
            pass

        # Fallback selectors for patient information
        if not patients:
            fallback_selectors = [
                "div.patients h3",
                "div.patients h4",
                "div.patients .patient-name",
                ".patient h3",
                ".patient-title",
                "h3[class*='patient']",
                "div[class*='patient'] h3",
            ]

            for selector in fallback_selectors:
                try:
                    patient_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in patient_elements:
                        patient_name = elem.text.strip()
                        if (
                            patient_name
                            and patient_name not in patients
                            and len(patient_name) > 2
                        ):
                            patients.append(patient_name)
                    if patients:  # Stop if we found patients
                        break
                except Exception:
                    continue

        # If still no patients found, look for any links or references to patients
        if not patients:
            try:
                patient_links = driver.find_elements(
                    By.CSS_SELECTOR, "a[href*='/patient/']"
                )
                for link in patient_links:
                    patient_text = link.text.strip()
                    if patient_text and patient_text not in patients:
                        patients.append(patient_text)
            except Exception:
                pass

        print(f"Found {len(patients)} patients for deck {deck_id}: {patients}")

    except Exception as e:
        print(f"Warning: Could not extract patients from deck page: {e}")

    return patients if patients else ["Unknown Patient"]


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
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)
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
                sys.exit(
                    "No submit buttons found on printdeck page; check selectors or page structure."
                )

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

            # Extract patient information from the deck page before processing cards
            patients_list = extract_patients_from_deck_page(
                driver, base_host, deck_id_from_url, bag_id
            )
            print(f"Available patients for deck {deck_id_from_url}: {patients_list}")

            cards = []
            for i, cid in enumerate(tqdm(card_ids, desc="Scraping cards")):
                # Assign patient in round-robin fashion (or use other logic as needed)
                # For now, we'll use round-robin to distribute cards across patients
                patient_info = patients_list[i % len(patients_list)]

                # Build card URL without bag_id parameter to avoid 403 errors on card pages
                card_url = f"{base_host}/card/{cid}"
                driver.get(card_url)
                time.sleep(2)

                # Try to extract more specific patient info from the card page if available
                patient_id = None
                try:
                    # Look for patient links or references on the card page
                    patient_links = driver.find_elements(
                        By.CSS_SELECTOR, "a[href*='/patient/']"
                    )
                    if patient_links:
                        patient_href = patient_links[0].get_attribute("href")
                        patient_id = (
                            patient_href.split("/patient/")[1]
                            if "/patient/" in patient_href
                            else None
                        )
                        patient_text = patient_links[0].text.strip()
                        if patient_text:
                            patient_info = patient_text
                        elif patient_id:
                            patient_info = f"Patient {patient_id}"

                    # Alternative: look for patient information in breadcrumbs or headers
                    if patient_info == "Unknown Patient":
                        breadcrumbs = driver.find_elements(
                            By.CSS_SELECTOR, ".breadcrumb a, .nav a, .patient-info"
                        )
                        for breadcrumb in breadcrumbs:
                            text = breadcrumb.text.strip()
                            if "patient" in text.lower() or text.isdigit():
                                patient_info = text
                                break

                except Exception as e:
                    print(
                        f"Warning: Could not extract patient info for card {cid}: {e}"
                    )

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

            # Add patient information to all cards before returning
            cards = add_patient_info_to_cards(cards, patients_list)
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
                sys.exit(
                    "No submit buttons found on printdeck page; check selectors or page structure."
                )

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

            # Extract patient information from the deck page before processing cards
            patients_list = extract_patients_from_deck_page(
                driver, base_host, deck_id, bag_id
            )
            print(f"Available patients for deck {deck_id}: {patients_list}")

            cards = []
            for i, cid in enumerate(tqdm(card_ids, desc="Scraping cards")):
                # Assign patient in round-robin fashion
                patient_info = patients_list[i % len(patients_list)]
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

            # Add patient information to all cards before returning
            cards = add_patient_info_to_cards(cards, patients_list)
            return cards

    finally:
        driver.quit()


def selenium_scrape_collection(collection_id, email, password, base_host):
    """
    Scrape all decks from a collection page and return combined cards with deck organization.
    """
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
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)
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
        print("Loading collection page...")
        print("Logging in...")
        # 1) LOGIN
        selenium_login(driver, email, password, base_host)
        print("Logged in successfully")

        # 2) Navigate to collection page
        collection_url = f"{base_host}/collection/{collection_id}"
        driver.get(collection_url)
        time.sleep(3)

        if "Error 403" in driver.title or "Access denied" in driver.page_source:
            driver.save_screenshot(f"collection_{collection_id}_403.png")
            sys.exit("Access denied to collection page")

        # 3) Get collection name and version
        print("Extracting collection information...")

        # Try to find collection title - look for specific bag-name selector first
        collection_title = "RIME 0.0.1"  # Default fallback
        try:
            # First try the specific bag-name selector
            try:
                bag_name_elem = driver.find_element(By.CSS_SELECTOR, "h3.bag-name")
                potential_title = bag_name_elem.text.strip()
                if potential_title and len(potential_title) > 3:
                    collection_title = potential_title
                    print(f"Found collection title from bag-name: {collection_title}")
                else:
                    raise NoSuchElementException("bag-name element found but empty")
            except NoSuchElementException:
                # Fallback to other selectors
                title_selectors = [
                    "h1",
                    "h2",
                    "h3",
                    ".collection-title",
                    ".title",
                    ".header h1",
                    ".page-title",
                ]

                for selector in title_selectors:
                    try:
                        title_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        potential_title = title_elem.text.strip()
                        if potential_title and len(potential_title) > 3:
                            collection_title = potential_title
                            print(
                                f"Found collection title from {selector}: {collection_title}"
                            )
                            break
                    except NoSuchElementException:
                        continue

        except Exception as e:
            print(f"Warning: Could not extract collection title: {e}")
            print(f"Using fallback title: {collection_title}")

        print(f"Collection: {collection_title}")

        # 4) Find all deck links in the collection
        print("Finding decks in collection...")

        # Look for deck links - these typically have href="/details/DECK_ID?bag_id=COLLECTION_ID"
        deck_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/details/']")

        if not deck_links:
            # Try alternative selectors for deck links
            deck_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/deck/']")

        if not deck_links:
            sys.exit(
                "No deck links found in collection. Check the collection page structure."
            )

        # Extract deck information
        decks_info = []
        
        # Also look for deck name elements to get proper titles
        deck_name_elements = driver.find_elements(By.CSS_SELECTOR, "a.deck-name")
        
        # Create a mapping of deck IDs to deck names
        deck_names_map = {}
        for deck_name_elem in deck_name_elements:
            deck_href = deck_name_elem.get_attribute("href")
            if deck_href and "/deck/" in deck_href:
                try:
                    deck_id = deck_href.split("/deck/")[1].split("?")[0]
                    deck_name = deck_name_elem.text.strip()
                    if deck_name:
                        deck_names_map[deck_id] = deck_name
                except:
                    continue
        
        for link in deck_links:
            href = link.get_attribute("href")
            if not href:
                continue

            # Extract deck ID from href
            if "/details/" in href:
                try:
                    deck_id = href.split("/details/")[1].split("?")[0]
                    # Get bag_id from URL parameters
                    parsed_href = urlparse(href)
                    bag_id = parse_qs(parsed_href.query).get("bag_id", [collection_id])[
                        0
                    ]

                    # Get deck title from the deck names map, or fall back to link text or default
                    deck_title = deck_names_map.get(deck_id) or link.text.strip() or f"Deck {deck_id}"

                    decks_info.append(
                        {
                            "deck_id": deck_id,
                            "bag_id": bag_id,
                            "title": deck_title,
                            "details_url": href,
                        }
                    )
                except Exception as e:
                    print(f"Warning: Could not parse deck link {href}: {e}")
                    continue

        if not decks_info:
            sys.exit("No valid deck information found in collection.")

        print(f"Found {len(decks_info)} decks in collection:")
        for deck in decks_info:
            print(f"  - {deck['title']} (ID: {deck['deck_id']})")

        # 4) Scrape all decks and combine cards
        all_cards = []

        for i, deck_info in enumerate(decks_info, 1):
            print(f"\nScraping deck {i}/{len(decks_info)}: {deck_info['title']}")

            try:
                # Use the existing selenium_scrape_deck function but with details_url
                deck_cards = selenium_scrape_deck(
                    deck_id=None,
                    email=email,
                    password=password,
                    base_host=base_host,
                    bag_id=deck_info["bag_id"],
                    details_url=deck_info["details_url"],
                )

                # Add deck information to each card for organization
                for card in deck_cards:
                    card["deck_title"] = deck_info["title"]
                    card["deck_id_source"] = deck_info["deck_id"]
                    # Add deck name as a tag for organization in Anki
                    if "tags" not in card:
                        card["tags"] = []
                    card["tags"].append(f"Deck_{deck_info['deck_id']}")
                    card["tags"].append(deck_info["title"].replace(" ", "_"))

                all_cards.extend(deck_cards)
                print(f"✅ Scraped {len(deck_cards)} cards from '{deck_info['title']}'")

            except Exception as e:
                print(f"❌ Failed to scrape deck '{deck_info['title']}': {e}")
                continue

        print(f"\n🎉 Total cards scraped from collection: {len(all_cards)}")
        return all_cards, decks_info, collection_title

    finally:
        driver.quit()


def detect_curriculum_pattern(collection_name, decks_info):
    """
    Detect if this is a curriculum-style collection (e.g., RIME 1.1.3, ASWD 2.1.5)
    Returns (is_curriculum, base_name) where base_name is like "RIME" or "ASWD"
    """
    # Pattern to match curriculum format: NAME X.Y.Z where X, Y, Z are numbers
    pattern = r'^([A-Z]+(?:\s+[A-Z]+)*)\s+(\d+)\.(\d+)\.(\d+)$'
    match = re.match(pattern, collection_name.strip())
    
    if match:
        base_name = match.group(1)  # e.g., "RIME" or "ASWD"
        block_num = int(match.group(2))
        unit_num = int(match.group(3))
        week_num = int(match.group(4))
        
        print(f"🎓 Detected curriculum pattern: {base_name} Block {block_num}, Unit {unit_num}, Week {week_num}")
        return True, base_name, block_num, unit_num, week_num
    
    return False, None, None, None, None


def export_hierarchical_apkg(data, collection_name, decks_info, path):
    """
    Export cards with hierarchical deck structure:
    
    For curriculum collections (e.g., RIME 1.1.3):
    Base Name (e.g., RIME)
    └── Block X
        └── Unit Y
            └── Week Z
                ├── Patient 1
                ├── Patient 2
                └── Patient 3
    
    For regular collections:
    Collection Name
    ├── Deck 1
    │   ├── Patient 1
    │   ├── Patient 2
    │   └── Patient 3
    └── Deck 2
        ├── Patient 1
        └── Patient 2
    """
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

    # Check if this is a curriculum-style collection
    is_curriculum, base_name, block_num, unit_num, week_num = detect_curriculum_pattern(collection_name, decks_info)
    
    # Group cards by deck and patient
    deck_structure = {}

    for card in data:
        deck_title = card.get("deck_title", "Unknown Deck")
        patient_info = card.get("patient_info", "Unknown Patient")

        if deck_title not in deck_structure:
            deck_structure[deck_title] = {}

        if patient_info not in deck_structure[deck_title]:
            deck_structure[deck_title][patient_info] = []

        deck_structure[deck_title][patient_info].append(card)

    # Create hierarchical decks
    decks = []
    deck_id_counter = DECK_ID_BASE

    if is_curriculum:
        # For curriculum collections, create Base::Block::Unit::Week::Deck::Patient hierarchy
        for deck_title, patients in deck_structure.items():
            for patient_info, cards in patients.items():
                # Create curriculum hierarchy: "BaseName::Block X::Unit Y::Week Z::DeckName::Patient"
                hierarchical_name = f"{base_name}::Block {block_num}::Unit {unit_num}::Week {week_num}::{deck_title}::{patient_info}"

                deck = genanki.Deck(deck_id_counter, hierarchical_name)
                deck_id_counter += 1

                for card in cards:
                    multi_flag = card.get("multi", False)
                    multi = "1" if multi_flag else ""
                    sources_html = "".join(
                        f"<li>{src}</li>" for src in card.get("sources", [])
                    )
                    model = text_model if card.get("freetext") else mcq_model

                    if card.get("freetext"):
                        fields = [
                            card["question"],
                            card["answer"],
                            card.get("explanation", ""),
                        ]
                    else:
                        fields = [
                            card["question"],
                            card["answer"],
                            card.get("explanation", ""),
                            card.get("score_text", ""),
                            card.get("percent", ""),
                            sources_html,
                            multi,
                            card["id"],
                        ]

                    # Add comprehensive tags for curriculum
                    tags = card.get("tags", []) + [
                        f"Curriculum_{base_name.replace(' ', '_')}",
                        f"Block_{block_num}",
                        f"Unit_{unit_num}",
                        f"Week_{week_num}",
                        f"Deck_{deck_title.replace(' ', '_')}",
                        f"Patient_{patient_info.replace(' ', '_')}",
                    ]

                    deck.add_note(
                        genanki.Note(
                            model=model,
                            fields=fields,
                            tags=tags,
                        )
                    )

                decks.append(deck)
    else:
        # For regular collections, use the existing Collection::Deck::Patient hierarchy
        for deck_title, patients in deck_structure.items():
            for patient_info, cards in patients.items():
                # Create deck name with hierarchy: "Collection::Deck::Patient"
                hierarchical_name = f"{collection_name}::{deck_title}::{patient_info}"

                deck = genanki.Deck(deck_id_counter, hierarchical_name)
                deck_id_counter += 1

                for card in cards:
                    multi_flag = card.get("multi", False)
                    multi = "1" if multi_flag else ""
                    sources_html = "".join(
                        f"<li>{src}</li>" for src in card.get("sources", [])
                    )
                    model = text_model if card.get("freetext") else mcq_model

                    if card.get("freetext"):
                        fields = [
                            card["question"],
                            card["answer"],
                            card.get("explanation", ""),
                        ]
                    else:
                        fields = [
                            card["question"],
                            card["answer"],
                            card.get("explanation", ""),
                            card.get("score_text", ""),
                            card.get("percent", ""),
                            sources_html,
                            multi,
                            card["id"],
                        ]

                    # Add comprehensive tags
                    tags = card.get("tags", []) + [
                        f"Collection_{collection_name.replace(' ', '_')}",
                        f"Deck_{deck_title.replace(' ', '_')}",
                        f"Patient_{patient_info.replace(' ', '_')}",
                    ]

                    deck.add_note(
                        genanki.Note(
                            model=model,
                            fields=fields,
                            tags=tags,
                        )
                    )

                decks.append(deck)

    # Create package with all decks
    package = genanki.Package(decks)
    package.write_to_file(path)

    print(f"[+] HIERARCHICAL APKG → {path}")
    print(f"📊 Created {len(decks)} sub-decks with hierarchical structure")

    # Print structure summary
    if is_curriculum:
        print("📋 Curriculum Deck Structure:")
        print(f"  🎓 {base_name}")
        print(f"    📚 Block {block_num}")
        print(f"      📖 Unit {unit_num}")
        print(f"        📅 Week {week_num}")
        for deck_title, patients in deck_structure.items():
            print(f"          � {deck_title}")
            for patient_info, cards in patients.items():
                print(f"            👤 {patient_info} ({len(cards)} cards)")
    else:
        print("📋 Deck Structure:")
        for deck_title, patients in deck_structure.items():
            print(f"  �📚 {deck_title}")
            for patient_info, cards in patients.items():
                print(f"    👤 {patient_info} ({len(cards)} cards)")


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
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)
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
            root.lift()  # Bring to front
            root.attributes("-topmost", True)  # Keep on top

            # Configure file dialog
            file_types = [("Anki Deck Files", "*.apkg"), ("All Files", "*.*")]

            # Show save dialog
            file_path = filedialog.asksaveasfilename(
                title="Save Anki Deck As...",
                defaultextension=".apkg",
                filetypes=file_types,
                initialfile=default_filename,
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
    user_input = input(
        f"Enter path to save Anki deck (or press Enter for default): "
    ).strip()
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
    base_url_override = input("Enter UCalgary collection or deck URL: ").strip()

    # Detect if this is a collection or individual deck URL
    is_collection = False
    collection_id = None
    details_url = None
    bag_id = None

    if base_url_override:
        po = urlparse(base_url_override)
        host = f"{po.scheme}://{po.netloc}" if po.scheme else base_url_override

        if "/collection/" in po.path:
            # This is a collection URL
            is_collection = True
            try:
                collection_id = po.path.split("/collection/")[1].split("/")[0]
                print(f"🔍 Detected collection URL (ID: {collection_id})")
            except (IndexError, AttributeError):
                sys.exit("❌ Could not extract collection ID from URL")

        elif "/details/" in po.path:
            # This is an individual deck URL
            details_url = base_url_override
            bag_id = parse_qs(po.query).get("bag_id", [None])[0] or BAG_ID_DEFAULT
            print(f"🔍 Detected individual deck URL")
        else:
            # Neither collection nor details URL
            details_url = None
            bag_id = BAG_ID_DEFAULT
            print(f"🔍 Using default settings")
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

    # Scrape cards based on URL type
    try:
        if is_collection:
            # Scrape entire collection
            cards, decks_info, collection_title = selenium_scrape_collection(
                collection_id=collection_id,
                email=email,
                password=password,
                base_host=host,
            )
            # Use collection title for naming
            deck_name = collection_title
            deck_id = collection_id

        else:
            # Scrape individual deck
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

    except RuntimeError as e:
        print(f"Login error during scrape: {e}")
        email, password = prompt_credentials(host)
        with open(CONFIG_PATH, "w") as cf:
            json.dump({"username": email, "password": password}, cf)

        # Retry scraping with new credentials
        if is_collection:
            cards, decks_info, collection_title = selenium_scrape_collection(
                collection_id=collection_id,
                email=email,
                password=password,
                base_host=host,
            )
            deck_name = collection_title
            deck_id = collection_id
        else:
            cards = selenium_scrape_deck(
                deck_id=None,
                email=email,
                password=password,
                base_host=host,
                bag_id=bag_id,
                details_url=details_url,
            )
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

    # Export the deck - use hierarchical export for collections
    if is_collection:
        export_hierarchical_apkg(cards, collection_title, decks_info, output_path)
    else:
        export_apkg(cards, deck_name, output_path)

    # Show completion message with additional info for collections
    if is_collection:
        deck_count = len(set(card.get("deck_id_source", "unknown") for card in cards))
        message_extra = f"\n\nThis collection contains {deck_count} decks with a total of {len(cards)} cards."
        print(f"📊 Collection Summary: {deck_count} decks, {len(cards)} total cards")
    else:
        message_extra = ""

    show_completion_message(output_path, len(cards))
    if is_collection:
        print(
            f"📋 Decks included: {', '.join(set(card.get('deck_title', 'Unknown') for card in cards))}"
        )


if __name__ == "__main__":
    main()
