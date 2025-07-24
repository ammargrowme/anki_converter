#!/usr/bin/env python3

import os
import time
import re
import requests
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urlparse

from utils import get_chrome_options, setup_driver_print_override
from auth import selenium_login
from image_processing import extract_images_from_page
from content_extraction import extract_comprehensive_background, extract_patients_from_deck_page, extract_deck_metadata
from sequential_extraction import extract_cards_sequential_mode


def selenium_scrape_deck(
    deck_id, email, password, base_host, bag_id, details_url=None, card_limit=None
):
    """
    Scrape a single deck using multiple fallback methods:
    1. Printdeck page (primary method)
    2. Sequential mode (for non-print accessible decks)
    3. Patient-based extraction (final fallback)
    """
    opts = get_chrome_options()
    driver = webdriver.Chrome(options=opts)
    setup_driver_print_override(driver)

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

            # Check if printdeck page is accessible
            if "Error 403" in driver.title or "Access denied" in driver.page_source:
                print(
                    f"⚠️  Printdeck page not accessible for deck {deck_id_from_url}, trying sequential method..."
                )
                
                # For decks without print access, use sequential method directly
                # This handles multiple questions per patient properly
                try:
                    print(f"🔄 Using sequential method for deck {deck_id_from_url}...")
                    sequential_cards, expected_questions = extract_cards_sequential_mode(
                        driver, base_host, deck_id_from_url, bag_id, max_cards=50
                    )
                    
                    if sequential_cards:
                        print(f"✅ Sequential method found {len(sequential_cards)} cards")
                        
                        # Convert sequential cards to the format expected by the rest of the function
                        cards = []
                        for i, seq_card in enumerate(sequential_cards):
                            if seq_card.get("error"):
                                continue
                            
                            # Get the card ID and URL
                            card_id = seq_card.get("card_id")
                            if not card_id:
                                continue
                            
                            # Visit the card page to extract full content
                            card_url = f"{base_host}/card/{card_id}"
                            driver.get(card_url)
                            time.sleep(2)
                            
                            # Extract comprehensive background content
                            background = extract_comprehensive_background(driver)
                            
                            # Prepare session with Selenium cookies for image downloading
                            sess = requests.Session()
                            for c in driver.get_cookies():
                                sess.cookies.set(c["name"], c["value"])
                            
                            # Extract images from the current page
                            page_images = extract_images_from_page(driver, sess, base_host)
                            
                            # Add page images to background if found
                            if page_images:
                                background += f"\n\n{page_images}"
                            
                            # For sequential decks, don't organize by patient - put all cards directly under deck
                            cards.append({
                                "id": card_id,
                                "question": seq_card.get("question", ""),
                                "answer": "",  # Sequential cards typically don't have preset answers
                                "explanation": background,  # Put background content in explanation
                                "background": background,  # Keep for compatibility
                                "patient_info": "Sequential Deck",  # Use patient_info key for export compatibility
                                "deck_title": f"Deck {deck_id_from_url}",  # Use deck_title key for export compatibility
                                "is_sequential": True,  # Flag to indicate this came from sequential method
                                "sources": [],
                                "tags": ["Sequential_Extraction"],
                                "multi": False,
                                "freetext": True,  # Treat as freetext since no preset answers
                                "score_text": "",
                                "percent": ""
                            })
                            
                            print(f"    📄 Processed sequential card {i+1}/{len(sequential_cards)}: {card_id}")
                        
                        print(f"✅ Sequential method successfully extracted {len(cards)} cards")
                        return cards
                    else:
                        print(f"❌ Sequential method found no cards")
                        # Fall back to patient-based method as last resort
                        print(f"🔄 Falling back to patient-based method...")
                
                except Exception as e:
                    print(f"❌ Sequential method failed: {e}")
                    print(f"🔄 Falling back to patient-based method...")
                
                # Try patient-based approach as fallback for sequential method failure
                return _extract_cards_patient_based(driver, base_host, deck_id_from_url, bag_id, card_limit)
            else:
                # Printdeck page is accessible, proceed with normal method
                return _extract_cards_printdeck(driver, base_host, deck_id_from_url, bag_id, card_limit)

        else:
            # No details URL provided, use default parameters
            deck_id = deck_id or "unknown"
            return _extract_cards_printdeck(driver, base_host, deck_id, bag_id, card_limit)

    finally:
        driver.quit()


def _extract_cards_printdeck(driver, base_host, deck_id, bag_id, card_limit):
    """Extract cards using the printdeck page method"""
    # Find all submit buttons with solution IDs on the printdeck page
    submit_buttons = driver.find_elements(
        By.CSS_SELECTOR, "div.submit button[rel*='/solution/']"
    )

    if not submit_buttons:
        raise Exception("No submit buttons found on printdeck page; check selectors or page structure.")

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
        raise Exception("No card IDs found from submit buttons; check page structure.")

    # Apply card limit for testing if specified
    if card_limit and card_limit < len(card_ids):
        print(f"🔧 Testing mode: Limiting to {card_limit} cards (out of {len(card_ids)} total)")
        card_ids = card_ids[:card_limit]

    # Extract patient information from the deck page
    patients_list = extract_patients_from_deck_page(driver, base_host, deck_id, bag_id)
    print(f"Available patients for deck {deck_id}: {patients_list}")

    return _extract_card_content(driver, base_host, card_ids, patients_list, deck_id)


def _extract_cards_patient_based(driver, base_host, deck_id, bag_id, card_limit):
    """Extract cards using patient-based method (fallback)"""
    try:
        # Navigate back to the deck details page to extract patient information
        deck_details_url = f"{base_host}/details/{deck_id}?bag_id={bag_id}"
        driver.get(deck_details_url)
        time.sleep(2)

        print(f"🔍 Extracting patients from deck {deck_id}...")

        # Extract all patient elements with their rel attributes (patient IDs)
        patient_elements = driver.find_elements(
            By.CSS_SELECTOR, "div.patients > div.patient[rel]"
        )

        if not patient_elements:
            print(f"❌ No patients found on deck details page for deck {deck_id}")
            # Fallback to try alternative selectors
            alternative_selectors = [
                "div.patient[rel]",
                ".patient[rel]",
                "[class*='patient'][rel]",
            ]
            for selector in alternative_selectors:
                patient_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if patient_elements:
                    print(f"  ✅ Found patients using alternative selector: {selector}")
                    break

        if not patient_elements:
            raise Exception(f"No patient elements found with rel attributes for deck {deck_id}")

        # Extract patient IDs and names
        patients_data = []
        for patient_elem in patient_elements:
            try:
                patient_id = patient_elem.get_attribute("rel")
                # Try to get patient name from h3 within the patient div
                patient_name_elem = patient_elem.find_element(By.CSS_SELECTOR, "h3")
                patient_name = (
                    patient_name_elem.text.strip()
                    if patient_name_elem
                    else f"Patient {patient_id}"
                )

                if patient_id:
                    patients_data.append({"id": patient_id, "name": patient_name})
                    print(f"  👤 Found patient: {patient_name} (ID: {patient_id})")
            except Exception as e:
                print(f"  ⚠️  Error extracting patient data: {e}")

        if not patients_data:
            raise Exception(f"No valid patient data extracted for deck {deck_id}")

        print(f"✅ Found {len(patients_data)} patients for deck {deck_id}")

        # Apply card limit for testing if specified
        if card_limit and card_limit < len(patients_data):
            print(f"🔧 Testing mode: Limiting to {card_limit} patients (out of {len(patients_data)} total)")
            patients_data = patients_data[:card_limit]

        # Extract cards for each patient by visiting their patient pages
        card_ids = []
        patients_list = []

        for patient_data in patients_data:
            patient_id = patient_data["id"]
            patient_name = patient_data["name"]
            patients_list.append(patient_name)

            # Visit the patient page to find their card
            patient_url = f"{base_host}/patient/{patient_id}"
            print(f"  🔗 Visiting patient page: {patient_url}")
            driver.get(patient_url)
            time.sleep(2)

            # Look for card links or buttons on the patient page
            card_found = _find_card_for_patient(driver, patient_name)
            if card_found:
                card_ids.append(card_found)

        if not card_ids:
            raise Exception(f"Patient-based fallback method also found no cards for deck {deck_id}")

        print(f"✅ Found {len(card_ids)} unique cards via patient-based fallback method")
        return _extract_card_content(driver, base_host, card_ids, patients_list, deck_id)

    except Exception as e:
        print(f"❌ Error accessing deck via patient-based fallback method: {e}")
        raise Exception(f"All methods failed for deck {deck_id}")


def _find_card_for_patient(driver, patient_name):
    """Find the card associated with a specific patient"""
    card_selectors = [
        "a[href*='/card/']",
        "button[onclick*='card']",
        "form[action*='/card/']",
        "[data-card-id]",
        "a[href*='/deck/']",  # Sometimes redirects to deck with card
    ]

    # Try direct selectors first
    for selector in card_selectors:
        try:
            card_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for card_elem in card_elements:
                # Extract card ID from href, onclick, or data attributes
                href = card_elem.get_attribute("href") or ""
                onclick = card_elem.get_attribute("onclick") or ""
                card_id_attr = card_elem.get_attribute("data-card-id") or ""
                action = card_elem.get_attribute("action") or ""

                # Look for card ID in various attributes
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

                if card_id:
                    print(f"    ✅ Found card {card_id} for patient {patient_name}")
                    return card_id

        except Exception as e:
            print(f"    ⚠️  Error with selector {selector}: {e}")

    # If no direct card link found, try clicking on elements
    try:
        clickable_elements = driver.find_elements(
            By.CSS_SELECTOR, "a, button, [onclick], [href]"
        )

        for elem in clickable_elements:
            elem_text = elem.text.strip().lower()
            if any(word in elem_text for word in ["start", "view", "case", "question", "card"]):
                try:
                    elem.click()
                    time.sleep(2)

                    # Check if we're now on a card page
                    current_url = driver.current_url
                    card_match = re.search(r"/card/(\d+)", current_url)
                    if card_match:
                        card_id = card_match.group(1)
                        print(f"    ✅ Found card {card_id} for patient {patient_name} via click")
                        return card_id
                except Exception as e:
                    print(f"    ⚠️  Error clicking element: {e}")

    except Exception as e:
        print(f"    ⚠️  Error trying clickable elements: {e}")

    print(f"    ❌ No card found for patient {patient_name}")
    return None


def _extract_card_content(driver, base_host, card_ids, patients_list, deck_id):
    """Extract content for all cards"""
    cards = []
    
    for i, cid in enumerate(tqdm(card_ids, desc="Scraping cards")):
        # Assign patient info based on round-robin distribution
        if len(patients_list) == len(card_ids):
            # Perfect 1:1 mapping from patient-based extraction
            patient_info = patients_list[i]
        else:
            # Round-robin distribution for other methods
            patient_info = patients_list[i % len(patients_list)]

        # Build card URL without bag_id parameter to avoid 403 errors on card pages
        card_url = f"{base_host}/card/{cid}"
        driver.get(card_url)
        time.sleep(2)

        # Try to extract more specific patient info from the card page
        patient_info = _extract_patient_info_from_card(driver, patient_info, cid)

        # Extract comprehensive background content
        background = extract_comprehensive_background(driver)

        # Prepare session with Selenium cookies for image downloading
        sess = requests.Session()
        for c in driver.get_cookies():
            sess.cookies.set(c["name"], c["value"])

        # Extract images from the current page
        page_images = extract_images_from_page(driver, sess, base_host)

        # Fallback text extraction if background is insufficient
        if not background or len(background.strip()) < 50:
            background = _extract_fallback_text(driver, background)

        # Add images to background if found
        if page_images:
            if background:
                background = page_images + "<br/><br/>" + background
            else:
                background = page_images

        # Debug background content
        if background:
            print(f"  📄 Extracted background content ({len(background)} chars)")
            text_preview = re.sub(r"<[^>]+>", "", background)[:200]
            preview = text_preview + "..." if len(text_preview) > 200 else text_preview
            print(f"  Preview: {preview}")
        else:
            print(f"  ⚠️  No background content found for card {cid}")

        # Extract question
        try:
            qel = driver.find_element(
                By.CSS_SELECTOR, "#workspace > div.solution.container > form > h3"
            )
            question = qel.text.strip()
        except NoSuchElementException:
            question = "[No Question]"

        # Determine if multi-select
        try:
            form = driver.find_element(
                By.CSS_SELECTOR, "#workspace > div.solution.container > form"
            )
            multi_flag = form.get_attribute("rel") == "pickmany"
        except Exception:
            multi_flag = False

        # Detect free-text questions
        freetext_question = False
        freetext_answer = ""
        try:
            freetext_elem = driver.find_element(By.CSS_SELECTOR, "div.freetext-answer")
            freetext_html = freetext_elem.get_attribute("outerHTML")
            if freetext_html:
                freetext_question = True
                freetext_answer = freetext_html
        except NoSuchElementException:
            pass

        if freetext_question:
            # For free-text questions, use a simpler structure
            cards.append({
                "id": cid,
                "question": question,
                "answer": "[Open-ended question - no preset answer]",
                "explanation": background,
                "background": background,
                "patient_info": patient_info,
                "deck_title": f"Deck {deck_id}",
                "sources": [],
                "tags": ["Freetext"],
                "multi": False,
                "freetext": True,
                "score_text": "",
                "percent": ""
            })
        else:
            # Extract multiple choice options and answers
            card_data = _extract_mcq_content(driver, cid, question, background, patient_info, deck_id, multi_flag)
            if card_data:
                cards.append(card_data)

    return cards


def _extract_patient_info_from_card(driver, default_patient_info, card_id):
    """Extract patient information from the card page"""
    patient_info = default_patient_info
    
    try:
        # Look for patient links or references on the card page
        patient_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/patient/']")
        if patient_links:
            patient_href = patient_links[0].get_attribute("href")
            patient_text = patient_links[0].text.strip()
            if patient_text:
                patient_info = patient_text
            elif "/patient/" in patient_href:
                patient_id = patient_href.split("/patient/")[1]
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
        print(f"Warning: Could not extract patient info for card {card_id}: {e}")

    return patient_info


def _extract_fallback_text(driver, existing_background):
    """Extract fallback text content if main background extraction failed"""
    try:
        print(f"  🔍 Background content insufficient ({len(existing_background) if existing_background else 0} chars), trying fallback extraction...")
        
        # Look for any text content in the card container
        card_containers = driver.find_elements(By.CSS_SELECTOR, "body > div > div.container.card")
        if not card_containers:
            card_containers = driver.find_elements(By.CSS_SELECTOR, "div.container.card")

        text_parts = []
        seen_text = set()  # Prevent duplicates

        for container in card_containers:
            # Extract paragraphs
            paragraphs = container.find_elements(By.TAG_NAME, "p")
            for p in paragraphs:
                p_text = p.text.strip()
                if len(p_text) > 20 and p_text not in seen_text:
                    text_parts.append(f"<p>{p_text}</p>")
                    seen_text.add(p_text)

            # Extract divs with substantial text
            text_divs = container.find_elements(By.CSS_SELECTOR, "div")
            for div in text_divs:
                # Skip if it contains other elements we've already processed
                if div.find_elements(By.CSS_SELECTOR, "p, table, img, canvas"):
                    continue
                div_text = div.text.strip()
                if len(div_text) > 30 and div_text not in seen_text:
                    text_parts.append(f"<div>{div_text}</div>")
                    seen_text.add(div_text)

        if text_parts:
            background = "<br/>".join(text_parts[:3])  # Limit to 3 parts
            print(f"  📝 Extracted fallback text content: {len(background)} chars")
            return background
        
    except Exception as e:
        print(f"  ⚠️ Error extracting text content: {e}")
    
    return existing_background


def _extract_mcq_content(driver, card_id, question, background, patient_info, deck_id, multi_flag):
    """Extract multiple choice question content"""
    try:
        # Extract answer choices
        labels = driver.find_elements(By.CSS_SELECTOR, "div.options label")
        if not labels:
            print(f"  ⚠️  No answer choices found for card {card_id}")
            return None

        choices = []
        for lbl in labels:
            choice_text = lbl.text.strip()
            if choice_text:
                choices.append(choice_text)

        if not choices:
            print(f"  ⚠️  No valid choices extracted for card {card_id}")
            return None

        # Create formatted question with options
        formatted_question = f"{question}\n\n"
        for i, choice in enumerate(choices):
            choice_id = f"choice_{card_id}_{i}"
            input_type = "checkbox" if multi_flag else "radio"
            formatted_question += f'<div class="option"><input type="{input_type}" id="{choice_id}" value="{choice}"><label for="{choice_id}">{choice}</label></div>\n'

        return {
            "id": card_id,
            "question": formatted_question,
            "answer": " ||| ".join(choices),  # Default - will be updated with correct answers
            "explanation": background,
            "background": background,
            "patient_info": patient_info,
            "deck_title": f"Deck {deck_id}",
            "sources": [],
            "tags": ["MCQ", "Multi-select" if multi_flag else "Single-select"],
            "multi": multi_flag,
            "freetext": False,
            "score_text": f"0 / {len(choices)}",
            "percent": "0%"
        }

    except Exception as e:
        print(f"  ❌ Error extracting MCQ content for card {card_id}: {e}")
        return None


def selenium_scrape_collection(collection_id, email, password, base_host, card_limit=None):
    """
    Scrape an entire collection by discovering all decks within it
    and then scraping each deck individually.
    
    Returns:
        cards: List of all cards from all decks
        decks_info: Dictionary with deck metadata
        collection_title: Name of the collection
    """
    opts = get_chrome_options()
    driver = webdriver.Chrome(options=opts)
    setup_driver_print_override(driver)

    try:
        print("Loading collection screen...")
        print("Logging in...")
        
        # Login first
        selenium_login(driver, email, password, base_host)
        print("Logged in successfully")

        # Navigate to the collection page
        collection_url = f"{base_host}/collection/{collection_id}"
        print(f"🔍 Accessing collection: {collection_url}")
        driver.get(collection_url)
        time.sleep(3)

        # Extract collection title
        try:
            title_elem = driver.find_element(By.CSS_SELECTOR, "h1, .collection-title, .page-title")
            collection_title = title_elem.text.strip()
        except NoSuchElementException:
            collection_title = f"Collection {collection_id}"

        print(f"📚 Collection: {collection_title}")

        # Find all deck links in the collection
        deck_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/details/']")
        
        if not deck_links:
            # Try alternative selectors
            deck_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/deck/']")
        
        if not deck_links:
            raise Exception(f"No deck links found in collection {collection_id}")

        # Extract deck information
        decks_info = {}
        deck_urls = []

        for link in deck_links:
            href = link.get_attribute("href")
            if "/details/" in href:
                # Extract deck metadata
                deck_info = extract_deck_metadata(driver, link, base_host)
                if deck_info:
                    decks_info[deck_info["id"]] = deck_info
                    deck_urls.append(href)

        print(f"📦 Found {len(deck_urls)} decks in collection")

        # Apply deck limit for testing if specified
        if card_limit:
            # For collections, interpret card_limit as deck limit
            deck_limit = min(card_limit, len(deck_urls))
            deck_urls = deck_urls[:deck_limit]
            print(f"🔧 Testing mode: Limiting to {deck_limit} decks")

        # Scrape each deck in the collection
        all_cards = []
        
        for i, deck_url in enumerate(deck_urls):
            try:
                print(f"\n📖 Scraping deck {i+1}/{len(deck_urls)}: {deck_url}")
                
                # Use selenium_scrape_deck for each individual deck
                deck_cards = selenium_scrape_deck(
                    deck_id=None,
                    email=email,
                    password=password,
                    base_host=base_host,
                    bag_id=None,  # Will be extracted from URL
                    details_url=deck_url,
                    card_limit=None  # Don't limit individual deck cards
                )
                
                if deck_cards:
                    # Add collection information to each card
                    for card in deck_cards:
                        card["collection_id"] = collection_id
                        card["collection_title"] = collection_title
                    
                    all_cards.extend(deck_cards)
                    print(f"  ✅ Added {len(deck_cards)} cards from deck")
                else:
                    print(f"  ⚠️  No cards found in deck")

            except Exception as e:
                print(f"  ❌ Error scraping deck {deck_url}: {e}")
                continue

        print(f"\n✅ Collection scraping complete: {len(all_cards)} total cards from {len(deck_urls)} decks")
        
        return all_cards, decks_info, collection_title

    finally:
        driver.quit()
