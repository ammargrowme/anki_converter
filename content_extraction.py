#!/usr/bin/env python3

import re
import time
from selenium.webdriver.common.by import By
from image_processing import normalize_html_formatting


def extract_comprehensive_background(driver):
    """
    Extract comprehensive background content from cards including tables, images, lists, etc.
    Focuses on vital signs monitor and medical content while avoiding duplicates.
    Returns HTML-formatted content suitable for Anki cards.
    """
    background_parts = []

    # Method 1: Extract vital signs monitor data with better formatting
    try:
        # Look for the vital signs monitor container
        monitor_containers = driver.find_elements(
            By.CSS_SELECTOR, "body > div > div.container.card > div.group.box.monitor"
        )

        if monitor_containers:
            for i, monitor in enumerate(monitor_containers):
                # Extract vital signs data and format it nicely
                try:
                    hr_elem = monitor.find_element(By.CSS_SELECTOR, ".hr span")
                    hr_value = hr_elem.text.strip()
                except:
                    hr_value = "N/A"

                try:
                    spo2_elem = monitor.find_element(By.CSS_SELECTOR, ".o2 span")
                    spo2_value = spo2_elem.text.strip()
                except:
                    spo2_value = "N/A"

                try:
                    rr_elem = monitor.find_element(By.CSS_SELECTOR, ".rr span")
                    rr_value = rr_elem.text.strip()
                except:
                    rr_value = "N/A"

                try:
                    temp_elem = monitor.find_element(By.CSS_SELECTOR, ".temp span")
                    temp_value = temp_elem.text.strip()
                except:
                    temp_value = "N/A"

                try:
                    bp_elem = monitor.find_element(By.CSS_SELECTOR, ".bp span")
                    bp_value = bp_elem.text.strip()
                except:
                    bp_value = "N/A"

                # Create a nicely formatted vital signs table with proper contrast
                vitals_html = f"""
                <div class="vital-signs-monitor" style="border: 2px solid #333; background: #1a1a1a; color: #00ff00; padding: 15px; margin: 10px 0; border-radius: 8px; font-family: 'Courier New', monospace; clear: both; display: block;">
                    <h3 style="color: #00ff00; text-align: center; margin: 0 0 15px 0; font-size: 16px;">📊 VITAL SIGNS MONITOR</h3>
                    <table style="width: 100%; border-collapse: collapse; color: #00ff00;">
                        <tr style="border-bottom: 1px solid #00ff00;">
                            <td style="padding: 8px; font-weight: bold; color: #00ff00;">❤️ Heart Rate:</td>
                            <td style="padding: 8px; color: #ffff00; font-size: 18px; font-weight: bold;">{hr_value} bpm</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #00ff00;">
                            <td style="padding: 8px; font-weight: bold; color: #00ff00;">🫁 SpO2:</td>
                            <td style="padding: 8px; color: #ffff00; font-size: 18px; font-weight: bold;">{spo2_value}%</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #00ff00;">
                            <td style="padding: 8px; font-weight: bold; color: #00ff00;">🌬️ Respiratory Rate:</td>
                            <td style="padding: 8px; color: #ffff00; font-size: 18px; font-weight: bold;">{rr_value} BrPM</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #00ff00;">
                            <td style="padding: 8px; font-weight: bold; color: #00ff00;">🌡️ Temperature:</td>
                            <td style="padding: 8px; color: #ffff00; font-size: 18px; font-weight: bold;">{temp_value}°C</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; font-weight: bold; color: #00ff00;">💉 Blood Pressure:</td>
                            <td style="padding: 8px; color: #ffff00; font-size: 18px; font-weight: bold;">{bp_value}</td>
                        </tr>
                    </table>
                </div>
                """
                background_parts.append(vitals_html)

    except Exception as e:
        print(f"Warning: Could not extract vital signs monitor: {e}")

    # Method 2: Extract additional medical content (tables, charts) from card container
    try:
        # Look for the main card container
        card_containers = driver.find_elements(
            By.CSS_SELECTOR, "body > div > div.container.card"
        )
        if not card_containers:
            card_containers = driver.find_elements(
                By.CSS_SELECTOR, "div.container.card"
            )

        for container in card_containers:
            # Extract tables specifically
            try:
                tables = container.find_elements(By.TAG_NAME, "table")
                for i, table in enumerate(tables):
                    table_html = table.get_attribute("outerHTML")
                    # Clean up table HTML for Anki compatibility
                    styled_table = table_html.replace(
                        'class="',
                        'style="border-collapse: collapse; margin: 10px 0; border: 1px solid #ccc; width: 100%;" class="',
                    )
                    # Add cell styling
                    styled_table = re.sub(
                        r"<td([^>]*)>",
                        r'<td\1 style="border: 1px solid #ccc; padding: 8px;">',
                        styled_table,
                    )
                    styled_table = re.sub(
                        r"<th([^>]*)>",
                        r'<th\1 style="border: 1px solid #ccc; padding: 8px; background: #f5f5f5; font-weight: bold;">',
                        styled_table,
                    )
                    background_parts.append(
                        f"<div><h4>📊 Medical Data Table {i+1}:</h4>{styled_table}</div>"
                    )

            except Exception as e:
                print(f"Warning: Error extracting tables: {e}")

            # Extract charts/graphs (canvas elements)
            try:
                canvases = container.find_elements(By.TAG_NAME, "canvas")
                for i, canvas in enumerate(canvases):
                    canvas_id = canvas.get_attribute("id") or f"Chart_{i+1}"
                    canvas_html = f'<div style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;"><h4>📈 Medical Chart: {canvas_id}</h4><p>Interactive chart/graph content</p></div>'
                    background_parts.append(canvas_html)

            except Exception as e:
                print(f"Warning: Error extracting charts: {e}")

            # Extract any text content that might be medically relevant
            try:
                # Look for specific content blocks - capture ALL div.block.group elements
                content_blocks = container.find_elements(
                    By.CSS_SELECTOR, "div.block.group"
                )
                for i, div in enumerate(content_blocks):
                    div_text = div.text.strip()
                    # Include ALL substantial content blocks, not just medical ones
                    if len(div_text) > 20 and not div.find_elements(
                        By.CSS_SELECTOR, "table, canvas, .monitor"
                    ):
                        # Detect if this is medical information or question options
                        is_question_options = any(
                            indicator in div_text
                            for indicator in ["A.", "B.", "C.", "D.", "E.", "F."]
                        )

                        is_medical_info = not is_question_options and any(
                            word in div_text.lower()
                            for word in [
                                "sensory",
                                "motor",
                                "reflexes",
                                "symptoms",
                                "findings",
                                "patient",
                                "medical",
                                "diagnosis",
                                "treatment",
                                "condition",
                                "exam",
                                "language",
                                "gait",
                                "cerebellar",
                            ]
                        )

                        if is_medical_info:
                            background_parts.append(
                                f"<div><h4>🏥 Medical Information:</h4><p>{div_text}</p></div>"
                            )
                        elif is_question_options:
                            background_parts.append(
                                f"<div><h4>📝 Question Options:</h4><p>{div_text}</p></div>"
                            )

                # If no block.group elements found, look for any substantial text content (fallback)
                if not background_parts:
                    # Look for any divs with substantial text content
                    all_divs = container.find_elements(By.CSS_SELECTOR, "div")
                    seen_text = set()  # Prevent duplicates

                    for div in all_divs:
                        # Skip divs that contain other complex elements
                        if div.find_elements(
                            By.CSS_SELECTOR, "div, table, canvas, img, form"
                        ):
                            continue

                        div_text = div.text.strip()
                        if len(div_text) > 30 and div_text not in seen_text:
                            background_parts.append(f"<div><p>{div_text}</p></div>")
                            seen_text.add(div_text)

                    # Also look for paragraphs directly (but ONLY if no div content was found)
                    if not background_parts:
                        paragraphs = container.find_elements(By.TAG_NAME, "p")
                        seen_paragraphs = set()

                        for p in paragraphs:
                            p_text = p.text.strip()
                            if len(p_text) > 20 and p_text not in seen_paragraphs:
                                background_parts.append(f"<p>{p_text}</p>")
                                seen_paragraphs.add(p_text)

            except Exception as e:
                print(f"Warning: Error extracting medical text: {e}")

    except Exception as e:
        print(f"Warning: Could not find card containers: {e}")

    # Clean up and remove duplicates
    unique_parts = []
    seen = set()
    for part in background_parts:
        # Remove extra whitespace and normalize
        cleaned_part = re.sub(r"\s+", " ", part.strip())
        if cleaned_part and cleaned_part not in seen and len(cleaned_part) > 20:
            seen.add(cleaned_part)
            unique_parts.append(part.strip())

    # Join with proper HTML spacing
    if unique_parts:
        final_content = "<br/><br/>".join(unique_parts)
        return final_content
    else:
        return ""


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


def extract_deck_metadata(driver, base_host, deck_id, bag_id):
    """
    Extract deck metadata including patient names and total card count from the deck details page.
    Returns a tuple of (patients_list, total_cards_count).
    """
    patients = []
    total_cards = None

    try:
        # Navigate to the deck page to extract metadata
        deck_page_url = f"{base_host}/details/{deck_id}?bag_id={bag_id}"
        driver.get(deck_page_url)
        time.sleep(2)

        # Extract total card count from the deck page
        try:
            # First try the specific "Correct: X of Y" selector
            try:
                correct_span = driver.find_element(
                    By.CSS_SELECTOR,
                    "body > div.wrap > div.container > div.details > div:nth-child(1) > div:nth-child(5) > span",
                )
                correct_text = correct_span.text.strip()

                # Look for pattern like "Correct: 22 of 22" or "X of Y"
                correct_match = re.search(r"(\d+)\s+of\s+(\d+)", correct_text)
                if correct_match:
                    total_cards = int(correct_match.group(2))
            except Exception:
                pass

            # If we didn't find it with the specific selector, try other methods
            if total_cards is None:
                # Try to find card count in page text
                page_text = driver.page_source.lower()

                # Look for patterns like "X cards", "X questions", "Total: X", "X of Y", etc.
                card_count_patterns = [
                    r"(\d+)\s+of\s+(\d+)",  # "X of Y" pattern (prioritize the Y)
                    r"(\d+)\s+cards?",
                    r"(\d+)\s+questions?",
                    r"total[:\s]+(\d+)",
                    r"(\d+)\s+total",
                    r"count[:\s]+(\d+)",
                ]

                for pattern in card_count_patterns:
                    matches = re.findall(pattern, page_text)
                    if matches:
                        if "of" in pattern:
                            # For "X of Y" pattern, take the Y (total)
                            potential_totals = [
                                int(match[1]) for match in matches if int(match[1]) > 0
                            ]
                        else:
                            potential_totals = [
                                int(match) if isinstance(match, str) else int(match[0])
                                for match in matches
                                if (
                                    int(match)
                                    if isinstance(match, str)
                                    else int(match[0])
                                )
                                > 0
                            ]

                        if potential_totals:
                            total_cards = max(
                                potential_totals
                            )  # Take the largest reasonable number
                            break

        except Exception as e:
            print(f"Warning: Could not extract total card count: {e}")
            total_cards = None

        # Try the specific patient selector
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

    except Exception as e:
        print(f"Warning: Could not extract deck metadata: {e}")

    return (patients if patients else ["Unknown Patient"], total_cards)


def extract_patients_from_deck_page(driver, base_host, deck_id, bag_id):
    """
    Extract patient names from a deck/bag page by visiting the deck details page.
    Returns a list of patient names found on the page.
    (Legacy function - kept for compatibility)
    """
    patients_list, _ = extract_deck_metadata(driver, base_host, deck_id, bag_id)
    return patients_list


def extract_card_content_from_page(driver):
    """
    Extract card content from the current page (for fast scraper browser fallback).

    Args:
        driver: Selenium WebDriver positioned on a card page

    Returns:
        dict: Card data with question, background, patient_info, is_multi, etc.
    """
    import requests
    from image_processing import extract_images_from_page

    # Extract comprehensive background content
    background = extract_comprehensive_background(driver)

    # Extract patient info from current page
    patient_info = "Unknown Patient"
    try:
        # Look for patient info in various locations
        patient_selectors = [".patient-info", ".card-patient", "h4", ".info-section h4"]

        for selector in patient_selectors:
            try:
                patient_elem = driver.find_element(By.CSS_SELECTOR, selector)
                text = patient_elem.text.strip()
                if text and len(text) < 100:  # Reasonable patient info length
                    patient_info = text
                    break
            except Exception:
                continue

    except Exception:
        pass

    # Prepare session with Selenium cookies for image downloading
    sess = requests.Session()
    for c in driver.get_cookies():
        sess.cookies.set(c["name"], c["value"])

    # Extract images from the current page
    try:
        page_images = extract_images_from_page(driver, sess, driver.current_url)

        # Add images to background if found
        if page_images:
            if background:
                background = page_images + "<br/><br/>" + background
            else:
                background = page_images
    except Exception:
        pass  # Continue without images if extraction fails

    # Extract question
    question = "[No Question]"
    try:
        qel = driver.find_element(
            By.CSS_SELECTOR, "#workspace > div.solution.container > form > h3"
        )
        question = qel.text.strip()
    except Exception:
        pass

    # Determine if multi-select
    is_multi = False
    try:
        form = driver.find_element(
            By.CSS_SELECTOR, "#workspace > div.solution.container > form"
        )
        is_multi = form.get_attribute("rel") == "pickmany"
    except Exception:
        pass

    # Extract options (for MCQ cards)
    options = []
    try:
        option_elements = driver.find_elements(
            By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox']"
        )
        for i, option_elem in enumerate(option_elements):
            try:
                label = driver.find_element(
                    By.CSS_SELECTOR, f"label[for='{option_elem.get_attribute('id')}']"
                )
                option_text = label.text.strip()
                if option_text:
                    options.append((str(i), option_text))
            except:
                continue
    except Exception:
        pass

    return {
        "question": question,
        "background": background,
        "patient_info": patient_info,
        "is_multi": is_multi,
        "options": options,
    }
