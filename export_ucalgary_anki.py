#!/usr/bin/env python3
"""
UCalgary Anki Deck Exporter - Clean Version
Extracts medical cases from UCalgary card system and creates Anki decks.
"""

import os
import sys
import time
import re
import base64
import json
import sqlite3
import zipfile
import getpass
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from tqdm import tqdm
import genanki

# Try to import tkinter for file dialogs (fallback to command line if not available)
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

# Config file for storing credentials
CONFIG_PATH = os.path.expanduser("~/.uc_anki_config.json")

# Load environment variables
load_dotenv()

# Configuration
RAW_BASE_URL = os.getenv("UC_BASE_URL", "").strip()
ENV_BAG_ID = os.getenv("UC_BAG_ID", "").strip()

if RAW_BASE_URL:
    parsed = urlparse(RAW_BASE_URL)
    BASE = f"{parsed.scheme}://{parsed.netloc}"
    qs = parse_qs(parsed.query)
    parsed_bag = qs.get("bag_id", [None])[0]
    default_details_url = RAW_BASE_URL if "/details/" in parsed.path else None
else:
    BASE = "https://cards.ucalgary.ca"
    parsed_bag = None
    default_details_url = None

BAG_ID_DEFAULT = ENV_BAG_ID or parsed_bag
DECK_ID_BASE = 1607392319000
MODEL_ID = 1607392319001


def selenium_login(driver, email, password, base_host):
    """Login to UCalgary system."""
    login_url = f"{base_host}/login"
    driver.get(login_url)
    time.sleep(2)

    driver.find_element(By.NAME, "username").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
    time.sleep(3)

    if "Logout" not in driver.page_source:
        raise RuntimeError("Login failed – check credentials")


def is_portrait_image(driver, img_url, sess):
    """Check if an image is a portrait (should be filtered out)."""
    try:
        resp = sess.get(img_url, timeout=10)
        content_type = resp.headers.get("content-type", "").lower()

        if "image" not in content_type:
            return False

        if len(resp.content) < 1000:
            return True

        content_lower = resp.content.lower()

        # Check for face/portrait indicators
        face_indicators = [
            b"face",
            b"portrait",
            b"person",
            b"head",
            b"eyes",
            b"nose",
            b"mouth",
            b"hair",
            b"skin",
            b"facial",
        ]

        face_score = sum(
            1 for indicator in face_indicators if indicator in content_lower
        )

        # Check image dimensions
        try:
            from PIL import Image
            import io

            img = Image.open(io.BytesIO(resp.content))
            width, height = img.size
            aspect_ratio = width / height if height > 0 else 1

            # Portrait-like aspect ratios
            if 0.5 <= aspect_ratio <= 0.9 and face_score > 0:
                return True

            # Very small images are often portraits
            if width < 200 and height < 200 and face_score > 0:
                return True

        except Exception:
            pass

        return face_score >= 2

    except Exception:
        return False


def normalize_html_formatting(html_content):
    """Normalize HTML formatting for Anki."""
    if not html_content:
        return html_content

    # Replace common HTML entities
    html_content = html_content.replace("&nbsp;", " ")
    html_content = html_content.replace("&amp;", "&")
    html_content = html_content.replace("&lt;", "<")
    html_content = html_content.replace("&gt;", ">")
    html_content = html_content.replace("&quot;", '"')

    # Fix broken paragraph tags
    html_content = re.sub(r"<p[^>]*>\s*</p>", "", html_content)
    html_content = re.sub(r"<br\s*/?\s*>\s*<br\s*/?\s*>", "<br/>", html_content)

    # Ensure proper spacing
    html_content = re.sub(r"\s+", " ", html_content)
    html_content = html_content.strip()

    return html_content


def extract_comprehensive_background(driver):
    """Extract comprehensive background information including medical data and question options."""
    background_content = []

    # Look for content blocks with various selectors
    block_selectors = [
        "div.block.group",
        "div.block",
        "div.background",
        "div.case-info",
        "div.patient-info",
        "div.content",
        "#background",
        ".background",
    ]

    for selector in block_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                text = elem.text.strip()
                if text and len(text) > 10:
                    # Get the HTML content for better formatting
                    html_content = elem.get_attribute("innerHTML")
                    if html_content:
                        # Clean and style the content
                        clean_html = normalize_html_formatting(html_content)

                        # Determine content type and apply styling
                        if any(
                            keyword in text.lower()
                            for keyword in [
                                "vital signs",
                                "blood pressure",
                                "temperature",
                                "heart rate",
                                "medical",
                                "examination",
                                "history",
                            ]
                        ):
                            styled_content = f'<div style="border-left: 3px solid #007acc; padding: 10px; margin: 5px 0; background: #f0f8ff; color: black;">{clean_html}</div>'
                        elif any(
                            keyword in text.lower()
                            for keyword in ["a)", "b)", "c)", "d)", "option", "choice"]
                        ):
                            styled_content = f'<div style="border-left: 3px solid #28a745; padding: 10px; margin: 5px 0; background: #f0fff0; color: black;">{clean_html}</div>'
                        else:
                            styled_content = f'<div style="border-left: 3px solid #6c757d; padding: 10px; margin: 5px 0; background: #f8f9fa; color: black;">{clean_html}</div>'

                        if styled_content not in background_content:
                            background_content.append(styled_content)
        except Exception:
            continue

    return "".join(background_content) if background_content else ""


def extract_images_from_page(driver, sess, base_host):
    """Extract and embed images from the current page."""
    try:
        img_elements = driver.find_elements(By.TAG_NAME, "img")
        embedded_images = []

        for img in img_elements:
            src = img.get_attribute("src")
            if not src:
                continue

            if src.startswith("data:"):
                embedded_images.append(
                    f'<img src="{src}" style="max-width: 100%; height: auto; margin: 10px 0;">'
                )
                continue

            if src.startswith("/"):
                full_url = base_host + src
            elif not src.startswith("http"):
                full_url = base_host + "/" + src
            else:
                full_url = src

            # Skip portrait images
            if is_portrait_image(driver, full_url, sess):
                continue

            try:
                resp = sess.get(full_url, timeout=10)
                if resp.status_code == 200:
                    content_type = resp.headers.get("content-type", "image/jpeg")
                    b64_data = base64.b64encode(resp.content).decode("utf-8")
                    data_uri = f"data:{content_type};base64,{b64_data}"
                    embedded_images.append(
                        f'<img src="{data_uri}" style="max-width: 100%; height: auto; margin: 10px 0;">'
                    )
            except Exception:
                continue

        return "".join(embedded_images)
    except Exception:
        return ""


def extract_images_from_html(html_content, sess, base_host):
    """Extract and process images from HTML content."""
    if not html_content:
        return html_content, []

    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
    img_matches = re.findall(img_pattern, html_content)

    processed_html = html_content
    extracted_images = []

    for img_src in img_matches:
        if img_src.startswith("data:"):
            continue

        if img_src.startswith("/"):
            full_url = base_host + img_src
        elif not img_src.startswith("http"):
            full_url = base_host + "/" + img_src
        else:
            full_url = img_src

        try:
            # Skip portrait images
            if is_portrait_image(None, full_url, sess):
                # Remove portrait images from HTML
                processed_html = re.sub(
                    f"<img[^>]+src=[\"']?{re.escape(img_src)}[\"']?[^>]*>",
                    "",
                    processed_html,
                )
                continue

            resp = sess.get(full_url, timeout=10)
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "image/jpeg")
                b64_data = base64.b64encode(resp.content).decode("utf-8")
                data_uri = f"data:{content_type};base64,{b64_data}"

                # Replace the original src with the data URI
                processed_html = processed_html.replace(img_src, data_uri)
                extracted_images.append(data_uri)
        except Exception:
            continue

    return processed_html, extracted_images


def extract_patients_from_deck(driver, base_host, deck_id, bag_id):
    """Extract patient information from deck details page."""
    try:
        deck_details_url = f"{base_host}/details/{deck_id}?bag_id={bag_id}"
        driver.get(deck_details_url)
        time.sleep(2)

        patient_elements = driver.find_elements(
            By.CSS_SELECTOR, "div.patients > div.patient[rel]"
        )

        if not patient_elements:
            # Try alternative selectors
            alternative_selectors = [
                "div.patient[rel]",
                ".patient[rel]",
                "[class*='patient'][rel]",
            ]
            for selector in alternative_selectors:
                patient_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if patient_elements:
                    break

        patients_data = []
        for patient_elem in patient_elements:
            try:
                patient_id = patient_elem.get_attribute("rel")
                patient_name_elem = patient_elem.find_element(By.CSS_SELECTOR, "h3")
                patient_name = (
                    patient_name_elem.text.strip()
                    if patient_name_elem
                    else f"Patient {patient_id}"
                )

                if patient_id:
                    patients_data.append({"id": patient_id, "name": patient_name})
            except Exception:
                continue

        return patients_data
    except Exception:
        return []


def extract_cards_from_patients(driver, base_host, patients_data):
    """Extract card IDs by visiting each patient page."""
    card_ids = []
    patients_list = []

    for patient_data in patients_data:
        try:
            patient_id = patient_data["id"]
            patient_name = patient_data["name"]
            patients_list.append(patient_name)

            patient_url = f"{base_host}/patient/{patient_id}"
            driver.get(patient_url)
            time.sleep(2)

            # Look for card links
            card_selectors = [
                "a[href*='/card/']",
                "button[onclick*='card']",
                "form[action*='/card/']",
                "[data-card-id]",
                "a[href*='/deck/']",
            ]

            card_found = False
            for selector in card_selectors:
                try:
                    card_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for card_elem in card_elements:
                        href = card_elem.get_attribute("href") or ""
                        onclick = card_elem.get_attribute("onclick") or ""
                        card_id_attr = card_elem.get_attribute("data-card-id") or ""
                        action = card_elem.get_attribute("action") or ""

                        card_id_match = None
                        for attr in [href, onclick, action]:
                            if attr:
                                card_id_match = re.search(r"/card/(\d+)", attr)
                                if card_id_match:
                                    break

                        if card_id_match:
                            card_id = card_id_match.group(1)
                        elif card_id_attr:
                            card_id = card_id_attr
                        else:
                            continue

                        if card_id and card_id not in card_ids:
                            card_ids.append(card_id)
                            card_found = True
                            break

                    if card_found:
                        break
                except Exception:
                    continue

            # Try clicking elements if no direct card link found
            if not card_found:
                try:
                    clickable_elements = driver.find_elements(
                        By.CSS_SELECTOR, "a, button, [onclick], [href]"
                    )
                    for elem in clickable_elements:
                        elem_text = elem.text.strip().lower()
                        if any(
                            word in elem_text
                            for word in ["start", "view", "case", "question", "card"]
                        ):
                            try:
                                elem.click()
                                time.sleep(2)
                                current_url = driver.current_url
                                card_match = re.search(r"/card/(\d+)", current_url)
                                if card_match:
                                    card_id = card_match.group(1)
                                    if card_id not in card_ids:
                                        card_ids.append(card_id)
                                        card_found = True
                                        break
                            except Exception:
                                continue
                except Exception:
                    pass
        except Exception:
            continue

    return card_ids, patients_list


def scrape_single_card(driver, base_host, card_id, patient_info):
    """Scrape a single card and return card data."""
    card_url = f"{base_host}/card/{card_id}"
    driver.get(card_url)
    time.sleep(2)

    # Extract background content and images
    background = extract_comprehensive_background(driver)

    sess = requests.Session()
    for c in driver.get_cookies():
        sess.cookies.set(c["name"], c["value"])

    page_images = extract_images_from_page(driver, sess, base_host)

    if page_images:
        if background:
            background = page_images + "<br/><br/>" + background
        else:
            background = page_images

    # Extract question
    try:
        qel = driver.find_element(
            By.CSS_SELECTOR, "#workspace > div.solution.container > form > h3"
        )
        question = qel.text.strip()
    except NoSuchElementException:
        question = "[No Question]"

    # Check if multi-select
    try:
        form = driver.find_element(
            By.CSS_SELECTOR, "#workspace > div.solution.container > form"
        )
        multi_flag = form.get_attribute("rel") == "pickmany"
    except Exception:
        multi_flag = False

    # Check for free-text questions
    try:
        freetext_elem = driver.find_element(By.CSS_SELECTOR, "div.freetext-answer")
        freetext_html = freetext_elem.get_attribute("outerHTML")

        sess = requests.Session()
        for c in driver.get_cookies():
            sess.cookies.set(c["name"], c["value"])

        sol_resp = sess.post(
            f"{base_host}/solution/{card_id}/", data=[("guess", ""), ("timer", "1")]
        )
        json_sol = {}
        try:
            json_sol = sol_resp.json()
        except Exception:
            pass

        answer = json_sol.get("feedback", "").strip()

        if background:
            full_q = (
                f'<div class="background" style="background: white; color: black; padding: 10px; margin: 10px 0; border-radius: 5px;">{background}</div>'
                f'<div class="question" style="background: white; color: black; padding: 10px; margin: 10px 0;"><b>{question}</b></div>'
                f"{freetext_html}"
            )
        else:
            full_q = (
                f'<div class="question" style="background: white; color: black; padding: 10px; margin: 10px 0;"><b>{question}</b></div>'
                f"{freetext_html}"
            )

        return {
            "id": card_id,
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
            "patient_info": patient_info,
        }
    except NoSuchElementException:
        pass

    # Extract MCQ options
    option_divs = driver.find_elements(
        By.CSS_SELECTOR,
        "#workspace > div.solution.container > form > div.options > div.option",
    )
    option_info = []
    for div in option_divs:
        inp = div.find_element(By.TAG_NAME, "input")
        opt_id = inp.get_attribute("value")
        label = div.find_element(By.TAG_NAME, "label")
        opt_text = label.text.strip()
        option_info.append((opt_id, opt_text))

    # Get correct answers
    sess = requests.Session()
    for c in driver.get_cookies():
        sess.cookies.set(c["name"], c["value"])

    sol_url = f"{base_host}/solution/{card_id}/"
    empty_payload = [("timer", "1")]
    resp = sess.post(sol_url, data=empty_payload)
    json_resp = {}
    try:
        json_resp = resp.json()
    except Exception:
        payload = [("guess[]", oid) for oid, _ in option_info] + [("timer", "2")]
        resp = sess.post(sol_url, data=payload)
        try:
            json_resp = resp.json()
        except Exception:
            json_resp = {}

    correct_ids = json_resp.get("answers", [])
    feedback = json_resp.get("feedback", "").strip()
    feedback = normalize_html_formatting(feedback)
    score_text = json_resp.get("scoreText", "").strip()

    # Calculate percentage
    raw_score = json_resp.get("score", 0)
    if isinstance(raw_score, (int, float)):
        percent = f"{raw_score}%"
    else:
        score_match = re.search(r"(\d+)%", score_text)
        if score_match:
            percent = f"{score_match.group(1)}%"
        else:
            percent = "0%"

    # Build options and answers
    options = [text for oid, text in option_info]
    correct_answers = [text for oid, text in option_info if oid in correct_ids]
    if not correct_answers and options:
        correct_answers = [options[0]]

    # Build HTML
    input_type = "checkbox" if multi_flag else "radio"
    options_html = "".join(
        f'<div class="option" style="margin: 5px 0; padding: 8px; border: 1px solid #ccc; border-radius: 4px; background: white; color: black;">'
        f'<input type="{input_type}" name="choice" id="choice_{card_id}_{i}" value="{opt}" style="margin-right: 8px;">'
        f'<label for="choice_{card_id}_{i}" style="color: black; cursor: pointer;">{opt}</label>'
        f"</div>"
        for i, opt in enumerate(options)
    )

    if background:
        full_q = (
            f'<div class="background" style="background: white; color: black; padding: 10px; margin: 10px 0; border-radius: 5px;">{background}</div>'
            f'<div class="question" style="background: white; color: black; padding: 10px; margin: 10px 0; font-weight: bold;"><b>{question}</b></div>'
            f'<div class="options" style="background: white; color: black; padding: 10px; margin: 10px 0;">{options_html}</div>'
        )
    else:
        full_q = (
            f'<div class="question" style="background: white; color: black; padding: 10px; margin: 10px 0; font-weight: bold;"><b>{question}</b></div>'
            f'<div class="options" style="background: white; color: black; padding: 10px; margin: 10px 0;">{options_html}</div>'
        )

    answer = " ||| ".join(correct_answers) if correct_answers else "[No Answer Found]"

    return {
        "id": card_id,
        "question": full_q,
        "answer": answer,
        "explanation": feedback,
        "score_text": score_text,
        "sources": [],
        "tags": [],
        "images": [],
        "multi": multi_flag,
        "percent": percent,
        "patient_info": patient_info,
    }


def build_anki_package(cards, deck_name="UCalgary_Medical_Cases"):
    """Build an Anki package from the extracted cards."""
    # Create a deck with a unique ID
    deck_id = DECK_ID_BASE + abs(hash(deck_name)) % 1000000
    deck = genanki.Deck(deck_id, deck_name)

    # Define a model for the cards
    model = genanki.Model(
        MODEL_ID,
        "UCalgary Medical Case Model",
        fields=[
            {"name": "Question"},
            {"name": "Answer"},
            {"name": "Explanation"},
            {"name": "Patient"},
            {"name": "Score"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": """
                <style>
                .card {
                    font-family: Arial, sans-serif;
                    font-size: 16px;
                    text-align: left;
                    color: black;
                    background-color: white;
                }
                .patient-info {
                    background: #e3f2fd;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 5px;
                    border-left: 4px solid #2196f3;
                }
                .question {
                    margin: 15px 0;
                }
                .options {
                    margin: 10px 0;
                }
                .option {
                    margin: 5px 0;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background: #f9f9f9;
                }
                </style>
                <div class="patient-info">
                    <strong>Patient:</strong> {{Patient}}
                </div>
                <div class="question">
                    {{Question}}
                </div>
                """,
                "afmt": """
                <style>
                .card {
                    font-family: Arial, sans-serif;
                    font-size: 16px;
                    text-align: left;
                    color: black;
                    background-color: white;
                }
                .patient-info {
                    background: #e3f2fd;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 5px;
                    border-left: 4px solid #2196f3;
                }
                .question {
                    margin: 15px 0;
                }
                .answer {
                    background: #e8f5e8;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 5px;
                    border-left: 4px solid #4caf50;
                }
                .explanation {
                    background: #fff3e0;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 5px;
                    border-left: 4px solid #ff9800;
                }
                .score {
                    background: #f3e5f5;
                    padding: 5px 10px;
                    margin: 5px 0;
                    border-radius: 3px;
                    font-size: 14px;
                    text-align: center;
                }
                </style>
                <div class="patient-info">
                    <strong>Patient:</strong> {{Patient}}
                </div>
                <div class="question">
                    {{Question}}
                </div>
                <div class="answer">
                    <strong>Correct Answer:</strong><br/>
                    {{Answer}}
                </div>
                {{#Explanation}}
                <div class="explanation">
                    <strong>Explanation:</strong><br/>
                    {{Explanation}}
                </div>
                {{/Explanation}}
                {{#Score}}
                <div class="score">
                    Score: {{Score}}
                </div>
                {{/Score}}
                """,
            },
        ],
    )

    # Create notes for each card
    for card in cards:
        note = genanki.Note(
            model=model,
            fields=[
                card.get("question", ""),
                card.get("answer", ""),
                card.get("explanation", ""),
                card.get("patient_info", "Unknown Patient"),
                card.get("percent", ""),
            ],
            tags=[
                f"UCalgary",
                f"Patient_{card.get('patient_info', 'Unknown').replace(' ', '_')}",
            ],
        )
        deck.add_note(note)

    # Create the package
    package = genanki.Package(deck)

    # Return the package bytes
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".apkg", delete=False) as temp_file:
        package.write_to_file(temp_file.name)
        with open(temp_file.name, "rb") as f:
            apkg_bytes = f.read()
        os.unlink(temp_file.name)

    return apkg_bytes


def selenium_scrape_deck(deck_id, email, password, base_host, bag_id, details_url=None):
    """Main scraping function with progress logging."""
    print("🌐 Initializing browser...")
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-logging")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-web-security")
    opts.add_argument("--disable-features=VizDisplayCompositor")
    opts.add_argument("--log-level=3")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=opts)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument", {"source": "window.print = () => {};"}
    )

    try:
        print("🔐 Logging into UCalgary system...")
        selenium_login(driver, email, password, base_host)
        print("✅ Login successful!")

        if details_url:
            parsed_details = urlparse(details_url)
            try:
                deck_id_from_url = parsed_details.path.split("/details/")[1]
            except (IndexError, AttributeError):
                deck_id_from_url = "unknown"

            print(f"📚 Accessing deck: {deck_id_from_url}")

            # Try printdeck first
            printdeck_url = f"{base_host}/printdeck/{deck_id_from_url}?bag_id={bag_id}"
            driver.get(printdeck_url)
            time.sleep(2)

            if "Error 403" in driver.title or "Access denied" in driver.page_source:
                # Use patient-based method
                print("� Deck requires patient-based extraction...")
                print("📋 Discovering patients in collection...")
                patients_data = extract_patients_from_deck(
                    driver, base_host, deck_id_from_url, bag_id
                )

                if not patients_data:
                    print("❌ No patients found in this collection")
                    return []

                print(f"👥 Found {len(patients_data)} patients")

                print("🔍 Extracting cards from patient cases...")
                card_ids, patients_list = extract_cards_from_patients(
                    driver, base_host, patients_data
                )

                if not card_ids:
                    print("❌ No cards found in patient cases")
                    return []

                print(f"📝 Discovered {len(card_ids)} unique cards")
            else:
                # Use printdeck method
                print("📄 Using direct deck access method...")
                submit_buttons = driver.find_elements(
                    By.CSS_SELECTOR, "div.submit button[rel*='/solution/']"
                )

                if not submit_buttons:
                    print("❌ No cards found in deck")
                    return []

                card_ids = []
                for button in submit_buttons:
                    rel = button.get_attribute("rel")
                    m = re.search(r"/solution/(\d+)/", rel)
                    if m:
                        cid = m.group(1)
                        if cid not in card_ids:
                            card_ids.append(cid)

                # Extract patients for organization
                patients_data = extract_patients_from_deck(
                    driver, base_host, deck_id_from_url, bag_id
                )
                patients_list = (
                    [p["name"] for p in patients_data]
                    if patients_data
                    else ["Unknown Patient"]
                )

                print(f"📝 Found {len(card_ids)} cards in deck")

            # Scrape cards
            print(f"⚙️  Processing {len(card_ids)} cards...")
            cards = []
            for i, cid in enumerate(tqdm(card_ids, desc="Extracting card content", unit="card")):
                if len(patients_list) == len(card_ids):
                    patient_info = patients_list[i]
                else:
                    patient_info = patients_list[i % len(patients_list)]

                try:
                    card = scrape_single_card(driver, base_host, cid, patient_info)
                    cards.append(card)
                except Exception as e:
                    print(f"⚠️  Skipped card {cid}: {str(e)[:50]}...")
                    continue

            # Process images in explanations
            print("🖼️  Processing embedded images...")
            sess = requests.Session()
            for c in driver.get_cookies():
                sess.cookies.set(c["name"], c["value"])

            image_processed = 0
            for card in cards:
                if card.get("explanation") and (
                    "<img" in card["explanation"] or "src=" in card["explanation"]
                ):
                    try:
                        processed_explanation, extracted_images = (
                            extract_images_from_html(
                                card["explanation"], sess, base_host
                            )
                        )
                        card["explanation"] = processed_explanation
                        card["images"] = extracted_images
                        image_processed += 1
                    except Exception:
                        pass
            
            if image_processed > 0:
                print(f"✅ Processed images in {image_processed} explanations")

            return cards

        else:
            # Handle single deck ID (legacy support)
            print(f"📚 Processing legacy deck format: {deck_id}")

            printdeck_url = f"{base_host}/printdeck/{deck_id}?bag_id={bag_id}"
            driver.get(printdeck_url)
            time.sleep(2)

            if "Error 403" in driver.title or "Access denied" in driver.page_source:
                print("❌ Access denied to deck")
                return []

            submit_buttons = driver.find_elements(
                By.CSS_SELECTOR, "div.submit button[rel*='/solution/']"
            )

            if not submit_buttons:
                print("❌ No cards found in deck")
                return []

            card_ids = []
            for button in submit_buttons:
                rel = button.get_attribute("rel")
                m = re.search(r"/solution/(\d+)/", rel)
                if m:
                    cid = m.group(1)
                    if cid not in card_ids:
                        card_ids.append(cid)

            patients_data = extract_patients_from_deck(
                driver, base_host, deck_id, bag_id
            )
            patients_list = (
                [p["name"] for p in patients_data]
                if patients_data
                else ["Unknown Patient"]
            )

            print(f"📝 Found {len(card_ids)} cards")

            # Scrape cards
            print(f"⚙️  Processing {len(card_ids)} cards...")
            cards = []
            for i, cid in enumerate(tqdm(card_ids, desc="Extracting card content", unit="card")):
                patient_info = patients_list[i % len(patients_list)]
                try:
                    card = scrape_single_card(driver, base_host, cid, patient_info)
                    cards.append(card)
                except Exception as e:
                    print(f"⚠️  Skipped card {cid}: {str(e)[:50]}...")
                    continue

            return cards

    finally:
        print("🔒 Closing browser session...")
        driver.quit()


def get_credentials_interactive():
    """Get credentials from user input or environment variables."""
    # Try environment variables first
    email = os.getenv("UC_EMAIL")
    password = os.getenv("UC_PASSWORD")
    
    if email and password:
        return email, password
    
    # If not in environment, prompt user
    print("� Please provide your UCalgary credentials:")
    if not email:
        email = input("Email: ").strip()
    if not password:
        import getpass
        password = getpass.getpass("Password: ").strip()
    
    if not email or not password:
        print("❌ Email and password are required")
        sys.exit(1)
    
    return email, password

def get_deck_url_interactive():
    """Get deck URL from command line or user input."""
    if len(sys.argv) >= 2:
        return sys.argv[1]
    
    print("📚 Please provide the deck URL:")
    print("Example: https://cards.ucalgary.ca/details/1281?bag_id=125")
    url = input("Deck URL: ").strip()
    
    if not url:
        print("❌ Deck URL is required")
        sys.exit(1)
    
    return url

def main():
    """Main entry point with interactive prompts."""
    print("🚀 UCalgary Anki Deck Exporter")
    print("=" * 50)
    
    # Get deck URL
    details_url = get_deck_url_interactive()
    
    # Get credentials
    email, password = get_credentials_interactive()
    
    bag_id = BAG_ID_DEFAULT or "125"
    
    print(f"\n� Target Deck: {details_url}")
    print(f"� User: {email}")
    print(f"🆔 Bag ID: {bag_id}")
    print("=" * 50)

    print("=" * 50)
    
    try:
        print("\n🔄 Starting extraction process...")
        cards = selenium_scrape_deck(None, email, password, BASE, bag_id, details_url)

        if not cards:
            print("❌ No cards were extracted")
            sys.exit(1)

        print(f"\n✅ Successfully extracted {len(cards)} cards")
        
        # Create APKG
        print("📦 Building Anki deck package...")
        
        # Extract deck ID from URL for filename
        parsed_url = urlparse(details_url)
        deck_id = (
            parsed_url.path.split("/details/")[1]
            if "/details/" in parsed_url.path
            else "deck"
        )

        output_path = f"/Users/{os.getenv('USER', 'user')}/Desktop/Deck_{deck_id}.apkg"
        
        # Build and save deck
        apkg_bytes = build_anki_package(cards, f"UCalgary_Deck_{deck_id}")
        
        print(f"💾 Saving deck to: {output_path}")
        with open(output_path, "wb") as f:
            f.write(apkg_bytes)
        
        print("=" * 50)
        print(f"🎉 SUCCESS! Anki deck created successfully!")
        print(f"📁 Location: {output_path}")
        print(f"📊 Total cards: {len(cards)}")
        print("=" * 50)
        print("\n📥 To import into Anki:")
        print("   1. Open Anki")
        print("   2. File → Import")
        print("   3. Select your .apkg file")
        print("   4. Click Import")

    except Exception as e:
        print("=" * 50)
        print(f"❌ ERROR: {e}")
        print("=" * 50)
        sys.exit(1)


if __name__ == "__main__":
    main()
