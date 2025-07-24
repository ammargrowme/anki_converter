#!/usr/bin/env python3

import time
import re
from selenium.webdriver.common.by import By
from content_extraction import extract_deck_metadata


def extract_card_details_sequential(driver, card_number):
    """Extract detailed information from the current card in sequential mode"""
    try:
        # Get current URL to extract card ID
        current_url = driver.current_url
        card_id = None
        if "/card/" in current_url:
            try:
                card_id = current_url.split("/card/")[1].split("/")[0].split("?")[0]
            except:
                pass
        
        # Extract question content using multiple selectors
        question_selectors = [
            ".question", ".card-question", "[class*='question']",
            ".prompt", ".card-prompt", "[class*='prompt']",
            "h1", "h2", "h3", ".title", ".card-title",
            "#workspace .container h1", "#workspace .container h2"
        ]
        
        question_text = ""
        for selector in question_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = elem.text.strip()
                    if text and len(text) > 10:
                        question_text = text
                        break
                if question_text:
                    break
            except:
                pass
        
        # Extract answer options for analysis
        answer_selectors = [
            ".answer", ".option", ".choice", "input[type='radio']", 
            "button[type='submit']", ".answer-option", "[class*='answer']",
            "[class*='option']", "[class*='choice']"
        ]
        
        answer_options = []
        for selector in answer_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = elem.text.strip()
                    value = elem.get_attribute("value") or ""
                    if text or value:
                        answer_options.append({"text": text, "value": value})
            except:
                pass
        
        return {
            "card_number": card_number,
            "card_id": card_id,
            "url": current_url,
            "question": question_text,
            "answer_options": answer_options,
            "page_title": driver.title,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "card_number": card_number,
            "error": str(e),
            "url": driver.current_url,
            "timestamp": time.time()
        }


def navigate_to_next_card_sequential(driver):
    """Navigate to the next card in sequential mode using two-step process"""
    try:
        # Step 1: First submit an answer (required before next card appears)
        submitted = False
        
        # Try to find and submit an answer first
        submit_selectors = [
            "button[type='submit']", "input[type='submit']",
            "button[onclick*='submit']", "form button"
        ]
        
        for selector in submit_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    try:
                        if elem.is_displayed() and elem.is_enabled():
                            elem.click()
                            time.sleep(3)
                            submitted = True
                            break
                    except:
                        pass
                if submitted:
                    break
            except:
                pass
        
        # If no submit button found, try selecting a radio button first
        if not submitted:
            try:
                radio_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                if radio_buttons:
                    radio_buttons[0].click()
                    time.sleep(2)
                    
                    # Now try submit again
                    submit_elements = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                    if submit_elements:
                        submit_elements[0].click()
                        time.sleep(3)
                        submitted = True
            except:
                pass
        
        # Step 2: Now look for "Next Card" button
        next_card_selectors = [
            # Specific "Next Card" text
            "//*[contains(text(), 'Next Card')]",
            "//*[contains(text(), 'Next')]",
            "//*[contains(text(), 'Continue')]",
            
            # Button attributes that might indicate next
            "button[onclick*='next']", "button[onclick*='continue']",
            "a[href*='next']", "a[onclick*='next']",
            
            # Class-based selectors
            ".next", ".continue", "[class*='next']", "[class*='continue']",
            ".next-card", ".btn-next", "[class*='next-card']"
        ]
        
        for selector in next_card_selectors:
            try:
                if selector.startswith("//"):
                    # XPath selector
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    # CSS selector
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for elem in elements:
                    try:
                        if elem.is_displayed() and elem.is_enabled():
                            elem.click()
                            time.sleep(4)  # Wait for navigation
                            return True
                    except Exception as e:
                        continue
            except:
                continue
        
        return False
        
    except Exception as e:
        print(f"    ❌ Error navigating to next card: {e}")
        return False


def get_total_questions_from_deck_details_page(driver, base_host, deck_id, bag_id):
    """Get total number of questions from the deck details page (where 'Correct: X of Y' is shown)"""
    try:
        # Visit the deck details page to get the question counter
        details_url = f"{base_host}/details/{deck_id}?bag_id={bag_id}"
        driver.get(details_url)
        time.sleep(3)
        
        # Look for "Correct: X of Y" pattern on the deck details page
        page_text = driver.page_source
        
        # Common patterns for question counters on deck details page
        patterns = [
            r'Correct:\s*(\d+)\s+of\s+(\d+)',  # "Correct: 1 of 9" or "Correct:1 of 9"
            r'Correct\s*(\d+)\s+of\s+(\d+)',   # "Correct 1 of 9"
            r'(\d+)\s+of\s+(\d+)',             # "1 of 9" (fallback)
        ]
        
        # Try each pattern
        for pattern in patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                # Filter out 0 of 0 matches and get the last valid one
                valid_matches = [(c, t) for c, t in matches if int(t) > 0]
                if valid_matches:
                    current, total = valid_matches[-1]
                    total_questions = int(total)
                    print(f"📊 Found question counter: {current} of {total} (pattern: {pattern})")
                    return total_questions
        
        # If no pattern found, return default but warn
        print(f"⚠️ Could not find question counter on deck details page, using default of 5")
        return 5
        
    except Exception as e:
        print(f"⚠️ Error getting total questions from deck details: {e}")
        return 5


def extract_cards_sequential_mode(driver, base_host, deck_id, bag_id, max_cards=20):
    """Extract all cards using sequential mode without patient organization"""
    print(f"\n🔄 EXTRACTING CARDS VIA SEQUENTIAL MODE")
    print("=" * 60)
    
    # Get expected total questions from the deck details page
    expected_questions = get_total_questions_from_deck_details_page(driver, base_host, deck_id, bag_id)
    
    # Now start sequential mode
    sequential_url = f"{base_host}/deck/{deck_id}?timer-enabled=1&mode=sequential"
    print(f"🎯 Starting sequential mode: {sequential_url}")
    
    driver.get(sequential_url)
    time.sleep(5)  # Wait for page to load
    
    print(f"📊 Target: {expected_questions} questions (no patient organization)")
    
    all_cards = []
    seen_card_ids = set()
    card_number = 1
    
    # Adjust max_cards based on expected questions
    max_cards_to_try = max(expected_questions + 3, max_cards)  # Add buffer for safety
    
    while card_number <= max_cards_to_try:
        print(f"\n📄 Processing Card {card_number}")
        print("-" * 40)
        
        # Extract current card details
        card_data = extract_card_details_sequential(driver, card_number)
        
        if card_data.get("error"):
            print(f"    ❌ Error: {card_data['error']}")
            break
        
        # Check for cycle detection
        card_id = card_data.get("card_id")
        
        print(f"    🆔 Card ID: {card_id}")
        print(f"    📝 Question: {card_data.get('question', '')[:100]}..." if card_data.get('question') else "    📝 Question: [Not found]")
        
        # Primary cycle detection: Card ID repetition (most reliable)
        if card_id and card_id in seen_card_ids:
            print(f"    🔄 CYCLE DETECTED: Card ID {card_id} already seen")
            print(f"    🏁 Stopping extraction - found {len(all_cards)} unique cards")
            break
        
        # Stop exactly when we reach the expected number of questions
        if len(all_cards) >= expected_questions:
            print(f"    🎯 REACHED TARGET: Found {len(all_cards)} cards (expected {expected_questions})")
            print(f"    🏁 Stopping extraction - target achieved!")
            break
        
        # Record this card
        all_cards.append(card_data)
        if card_id:
            seen_card_ids.add(card_id)
        
        print(f"    ✅ Card {card_number} recorded (total: {len(all_cards)}/{expected_questions})")
        
        # Navigate to next card
        print(f"    ➡️ Navigating to next card...")
        if not navigate_to_next_card_sequential(driver):
            print(f"    ❌ Could not navigate to next card, stopping extraction")
            break
        
        card_number += 1
        
        # Brief pause between cards
        time.sleep(2)
    
    return all_cards, expected_questions
