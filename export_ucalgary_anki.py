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


def clean_html_portraits(html_content):
    """
    Remove portrait images from HTML content while preserving medical images.
    This includes both <img> tags and portrait SVG elements.
    """
    if not html_content:
        return html_content

    import re

    print(f"🧹 Cleaning portraits from HTML content ({len(html_content)} chars)")

    # First, remove portrait DIV containers entirely
    # Look for <div class="portrait"> containers and remove them
    portrait_div_pattern = (
        r'<div[^>]*class=["\'][^"\']*portrait[^"\']*["\'][^>]*>.*?</div>'
    )
    portrait_divs_found = len(re.findall(portrait_div_pattern, html_content, re.DOTALL))
    if portrait_divs_found > 0:
        print(f"  🎭 Removing {portrait_divs_found} portrait div containers")
        html_content = re.sub(portrait_div_pattern, "", html_content, flags=re.DOTALL)

    # More aggressive SVG removal - remove ALL SVGs that contain common portrait indicators
    def should_remove_svg(match):
        svg_content = match.group(0)

        # Check if SVG contains portrait/doctor indicators
        portrait_indicators = [
            "doctor_room",
            "doctor",
            "portrait",
            "physician",
            "staff",
            "headshot",
            "face",
            "person",
            "human",
            "head",
            "hair",
            "eyes",
            "nose",
            "mouth",
            "skin",
            "body",
            "arm",
            "hand",
            "leg",
            "shirt",
            "clothing",
            "uniform",
        ]
        medical_indicators = [
            "ecg",
            "ekg",
            "electrocardiogram",
            "waveform",
            "heartbeat",
            "chart",
            "graph",
            "plot",
            "data",
            "line",
            "axis",
            "grid",
        ]

        # Count indicators - be much more aggressive about portraits
        portrait_count = sum(
            1
            for indicator in portrait_indicators
            if indicator.lower() in svg_content.lower()
        )
        medical_count = sum(
            1
            for indicator in medical_indicators
            if indicator.lower() in svg_content.lower()
        )

        # Remove if ANY portrait indicators found, unless there are significantly more medical indicators
        if portrait_count > 0 and medical_count < (portrait_count * 2):
            print(
                f"  🚫 Removing SVG with portrait indicators (portrait: {portrait_count}, medical: {medical_count})"
            )
            return ""

        return svg_content

    # Remove portrait SVG elements
    svg_pattern = r"<svg[^>]*>.*?</svg>"
    svg_count = len(re.findall(svg_pattern, html_content, re.DOTALL))
    if svg_count > 0:
        print(f"  🔍 Processing {svg_count} SVG elements")
        html_content = re.sub(
            svg_pattern, should_remove_svg, html_content, flags=re.DOTALL
        )

    # Also handle img tags (existing functionality)
    def should_remove_img(match):
        img_tag = match.group(0)

        # Extract attributes
        src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag)
        alt_match = re.search(r'alt=["\']([^"\']*)["\']', img_tag)
        title_match = re.search(r'title=["\']([^"\']*)["\']', img_tag)
        class_match = re.search(r'class=["\']([^"\']*)["\']', img_tag)

        img_src = src_match.group(1) if src_match else ""
        img_alt = alt_match.group(1) if alt_match else ""
        img_title = title_match.group(1) if title_match else ""
        img_class = class_match.group(1) if class_match else ""

        # If it's a portrait, return empty string (remove it)
        if is_portrait_image(img_src, img_alt, img_title, img_class):
            print(f"  🚫 Removing portrait img: {img_alt}")
            return ""

        # Otherwise, keep the image
        return img_tag

    # Replace img tags, removing portraits
    img_count = len(re.findall(r"<img[^>]*>", html_content))
    if img_count > 0:
        print(f"  🔍 Processing {img_count} img elements")
        html_content = re.sub(r"<img[^>]*>", should_remove_img, html_content)

    print(f"✅ Portrait cleaning complete (final size: {len(html_content)} chars)")
    return html_content


def extract_images_from_html(html_content, session, base_host):
    """
    Extract images from HTML content and return processed HTML with embedded images.
    """
    if not html_content:
        return html_content, []

    import re
    import base64
    import os

    print(f"🖼️ Extracting images from HTML content...")

    # Find all img tags
    img_pattern = r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>'
    images = re.findall(img_pattern, html_content)
    extracted_images = []

    for img_src in images:
        try:
            # Handle relative URLs
            if img_src.startswith("/"):
                img_url = base_host + img_src
            elif img_src.startswith("http"):
                img_url = img_src
            else:
                img_url = base_host + "/" + img_src

            print(f"  📥 Downloading image: {img_url}")

            # Download the image
            response = session.get(img_url, timeout=10)
            if response.status_code == 200:
                # Get file extension
                content_type = response.headers.get("content-type", "")
                if "image/png" in content_type:
                    ext = "png"
                elif "image/jpeg" in content_type or "image/jpg" in content_type:
                    ext = "jpg"
                elif "image/gif" in content_type:
                    ext = "gif"
                elif "image/svg" in content_type:
                    ext = "svg"
                else:
                    ext = "png"  # default

                # Create base64 data URL
                img_data = base64.b64encode(response.content).decode("utf-8")
                data_url = f"data:image/{ext};base64,{img_data}"

                # Replace the original src with the data URL
                html_content = html_content.replace(
                    f'src="{img_src}"', f'src="{data_url}"'
                )
                html_content = html_content.replace(
                    f"src='{img_src}'", f"src='{data_url}'"
                )

                extracted_images.append({"url": img_url, "data": img_data, "type": ext})

                print(
                    f"  ✅ Successfully embedded image ({len(response.content)} bytes)"
                )
            else:
                print(f"  ❌ Failed to download image: HTTP {response.status_code}")

        except Exception as e:
            print(f"  ❌ Error processing image {img_src}: {e}")

    print(f"🖼️ Image extraction complete: {len(extracted_images)} images processed")
    return html_content, extracted_images


def extract_images_from_page(driver, session, base_host):
    """
    Extract images directly from the current page using multiple selectors.
    Returns HTML content with embedded images for inclusion in question/background.
    """
    print(f"🖼️ Extracting images from current page...")

    # Multiple selectors to find images in different sections
    image_selectors = [
        "#workspace > div.solution.container > div > img",  # Question section images
        "#workspace > div.solution.container > div.options > img",  # In options
        "#workspace > div.solution.container img",  # Any image in solution container
        ".question img",  # Question area images
        ".background img",  # Background area images
        ".container.card img",  # Card container images
        "div.solution img",  # Solution area images
        "img[src]",  # Fallback - any image with src
    ]

    all_images_html = []
    processed_urls = set()  # Prevent duplicates

    for selector in image_selectors:
        try:
            images = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"  🔍 Found {len(images)} images with selector: {selector}")

            for img in images:
                try:
                    img_src = img.get_attribute("src")
                    if not img_src or img_src in processed_urls:
                        continue

                    processed_urls.add(img_src)

                    # Get additional attributes for better HTML reconstruction
                    img_alt = img.get_attribute("alt") or ""
                    img_title = img.get_attribute("title") or ""
                    img_class = img.get_attribute("class") or ""
                    img_style = img.get_attribute("style") or ""
                    img_width = img.get_attribute("width") or ""
                    img_height = img.get_attribute("height") or ""

                    # Check if this is a portrait image we should filter
                    if is_portrait_image(img_src, img_alt, img_title, img_class):
                        print(f"  🚫 Skipping portrait image: {img_src}")
                        continue

                    # Handle relative URLs
                    if img_src.startswith("/"):
                        img_url = base_host + img_src
                    elif img_src.startswith("http"):
                        img_url = img_src
                    else:
                        img_url = base_host + "/" + img_src

                    print(f"  📥 Downloading image: {img_url}")

                    # Download the image
                    response = session.get(img_url, timeout=10)
                    if response.status_code == 200:
                        # Get file extension
                        content_type = response.headers.get("content-type", "")
                        if "image/png" in content_type:
                            ext = "png"
                        elif (
                            "image/jpeg" in content_type or "image/jpg" in content_type
                        ):
                            ext = "jpg"
                        elif "image/gif" in content_type:
                            ext = "gif"
                        elif "image/svg" in content_type:
                            ext = "svg"
                        else:
                            ext = "png"  # default

                        # Create base64 data URL
                        import base64

                        img_data = base64.b64encode(response.content).decode("utf-8")
                        data_url = f"data:image/{ext};base64,{img_data}"

                        # Reconstruct the HTML img tag with all attributes
                        img_attrs = []
                        img_attrs.append(f'src="{data_url}"')
                        if img_alt:
                            img_attrs.append(f'alt="{img_alt}"')
                        if img_title:
                            img_attrs.append(f'title="{img_title}"')
                        if img_class:
                            img_attrs.append(f'class="{img_class}"')
                        if img_style:
                            img_attrs.append(f'style="{img_style}"')
                        if img_width:
                            img_attrs.append(f'width="{img_width}"')
                        if img_height:
                            img_attrs.append(f'height="{img_height}"')

                        img_html = f'<img {" ".join(img_attrs)}>'
                        all_images_html.append(img_html)

                        print(
                            f"  ✅ Successfully embedded image ({len(response.content)} bytes)"
                        )
                    else:
                        print(
                            f"  ❌ Failed to download image: HTTP {response.status_code}"
                        )

                except Exception as e:
                    print(f"  ❌ Error processing image: {e}")

        except Exception as e:
            print(f"  ⚠️ Error with selector {selector}: {e}")

    if all_images_html:
        # Wrap images in a container for better styling
        images_section = (
            '<div class="extracted-images">' + "".join(all_images_html) + "</div>"
        )
        print(f"  ✅ Extracted {len(all_images_html)} images from page")
        return images_section
    else:
        print(f"  ⚠️ No images found on page")
        return ""


def is_portrait_image(img_src, img_alt, img_title="", img_class=""):
    """
    Determine if an image is likely a portrait/headshot that should be filtered out.
    Returns True if it's likely a portrait, False if it's medically relevant content.
    """
    # Convert all text to lowercase for easier matching
    src_lower = (img_src or "").lower()
    alt_lower = (img_alt or "").lower()
    title_lower = (img_title or "").lower()
    class_lower = (img_class or "").lower()

    # Debug: Print what we're analyzing
    all_text = f"{src_lower} {alt_lower} {title_lower} {class_lower}"
    print(
        f"    🔍 Analyzing image: src='{img_src}', alt='{img_alt}', title='{img_title}', class='{img_class}'"
    )

    # Portrait indicators in file names/paths
    portrait_indicators = [
        "portrait",
        "headshot",
        "profile",
        "photo",
        "mugshot",
        "avatar",
        "face",
        "person",
        "doctor",
        "patient_photo",
        "staff",
        "physician",
        "nurse",
        "resident",
        "attending",
        "faculty",
        "bio",
        "biography",
        "people",
    ]

    # UI/Logo/Avatar indicators - these should always be filtered (be more specific)
    ui_indicators = [
        "anon.png",
        "anonymous",
        "uc-cumming",
        "UC-cumming-black.png",
        "logo.png",
        "logo.jpg",
        "logo.svg",
        "badge",
        "icon",
        "nav",
        "navigation",
        "header",
        "footer",
        "sidebar",
        "menu",
        "button",
    ]

    # Medical content indicators that should be kept - comprehensive list
    medical_indicators = [
        "ecg",
        "ekg",
        "electrocardiogram",
        "monitor",
        "vital_signs",
        "vitalsigns",
        "cardiac_monitor",
        "heart_monitor",
        "rhythm_strip",
        "waveform",
        "mri",
        "ct_scan",
        "ultrasound",
        "x-ray",
        "xray",
        "scan",
        "blood_pressure",
        "bp_monitor",
        "oxygen",
        "saturation",
        "pulse_ox",
        "cardiac",
        "pulmonary",
        "respiratory",
        "chest_xray",
        "diagnostic",
        "test_result",
        "lab_result",
        "pathology",
        "radiology",
        "equipment",
        "device",
        "machine",
        "display",
        "screen",
        "readout",
        "medical_chart",
        "ecg_trace",
        "rhythm",
        "heart_rate",
        "anatomy",
        "antcirc",
        "circulation",
        "structure",
        "identify",
        "diagram",
        "uploads/card",
        "medical",
        "clinical",
        "patient",
        "case",
        "study",
        "education",
        "learning",
    ]

    # Check for medical indicators FIRST - highest priority for keeping
    medical_matches = []
    for indicator in medical_indicators:
        if indicator in all_text:
            medical_matches.append(indicator)

    if medical_matches:
        print(
            f"    ✅ MEDICAL content detected (indicators: {medical_matches}) - KEEPING"
        )
        return False  # Medical content, keep it

    # Check for specific UI/Logo indicators
    for indicator in ui_indicators:
        if indicator in all_text:
            print(f"    🚫 UI/LOGO detected (indicator: '{indicator}')")
            return True

    # Check for strong portrait indicators
    for indicator in portrait_indicators:
        if indicator in all_text:
            print(f"    🚫 PORTRAIT detected (indicator: '{indicator}')")
            return True  # Likely a portrait, filter it out

    # Additional heuristics based on file names
    if "jpg" in src_lower or "jpeg" in src_lower or "png" in src_lower:
        # If it's in a people/photos/portraits directory
        if any(
            word in src_lower
            for word in [
                "people",
                "photos",
                "portraits",
                "staff",
                "faculty",
                "bio",
                "headshots",
            ]
        ):
            print(f"    🚫 PORTRAIT detected (directory-based)")
            return True

        # If filename suggests it's a person's photo
        if any(
            word in src_lower
            for word in ["headshot", "bio", "profile", "_person", "staff_", "faculty_"]
        ):
            print(f"    🚫 PORTRAIT detected (filename-based)")
            return True

    # If no clear indicators, examine the source path more carefully
    # Many portrait images come from specific paths
    portrait_paths = [
        "/images/people/",
        "/staff/",
        "/faculty/",
        "/photos/",
        "/portraits/",
        "/bio/",
    ]
    for path in portrait_paths:
        if path in src_lower:
            print(f"    🚫 PORTRAIT detected (path-based: '{path}')")
            return True

    # Default to filtering if uncertain and looks like a person-related image
    if any(
        word in all_text
        for word in ["dr.", "dr ", "md", "phd", "professor", "physician"]
    ):
        print(f"    🚫 PORTRAIT detected (title-based)")
        return True

    # If we can't identify it clearly, but it's in a medical/educational context, keep it
    # Look for educational context clues
    educational_context = any(
        word in all_text
        for word in [
            "uploads/card",
            "question",
            "case",
            "study",
            "patient",
            "medical",
            "clinical",
            "anatomy",
            "identify",
            "structure",
            "diagram",
        ]
    )

    if educational_context:
        print(f"    ✅ EDUCATIONAL context detected - keeping image")
        return False

    # Only filter if we're confident it's not medical/educational content
    print(f"    🚫 UNIDENTIFIED - filtering out (safety)")
    return True


def extract_comprehensive_background(driver):
    """
    Extract comprehensive background content from cards including tables, images, lists, etc.
    Focuses on vital signs monitor and medical content while avoiding duplicates.
    Filters out portrait images while keeping medically relevant visual content.
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
            print(f"  💓 Found {len(monitor_containers)} vital signs monitors")
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
                print(
                    f"  � Formatted vital signs monitor {i+1}: HR={hr_value}, SpO2={spo2_value}, RR={rr_value}, Temp={temp_value}, BP={bp_value}"
                )

        else:
            print(f"  ⚠️  No vital signs monitors found")

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
                    print(f"  📊 Extracted medical table {i+1}")

            except Exception as e:
                print(f"Warning: Error extracting tables: {e}")

            # Extract charts/graphs (canvas elements)
            try:
                canvases = container.find_elements(By.TAG_NAME, "canvas")
                for i, canvas in enumerate(canvases):
                    canvas_id = canvas.get_attribute("id") or f"Chart_{i+1}"
                    canvas_html = f'<div style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;"><h4>📈 Medical Chart: {canvas_id}</h4><p>Interactive chart/graph content</p></div>'
                    background_parts.append(canvas_html)
                    print(f"  📈 Found medical chart: {canvas_id}")

            except Exception as e:
                print(f"Warning: Error extracting charts: {e}")

            # Extract any text content that might be medically relevant
            try:
                # Look for specific medical content divs (but avoid portrait areas)
                medical_content_divs = container.find_elements(
                    By.CSS_SELECTOR, "div.block.group"
                )
                for div in medical_content_divs:
                    div_text = div.text.strip()
                    # Only include if it has substantial medical content and isn't just structure
                    if (
                        len(div_text) > 50
                        and not div.find_elements(
                            By.CSS_SELECTOR, "table, canvas, .monitor"
                        )  # Not already captured
                        and any(
                            word in div_text.lower()
                            for word in [
                                "patient",
                                "medical",
                                "diagnosis",
                                "treatment",
                                "symptom",
                                "condition",
                            ]
                        )
                    ):

                        medical_text_html = f'<div style="border-left: 4px solid #007cba; padding: 10px; margin: 10px 0; background: #f9f9f9;"><h4>🏥 Medical Information:</h4><p>{div_text}</p></div>'
                        background_parts.append(medical_text_html)
                        print(
                            f"  🏥 Extracted medical text content ({len(div_text)} chars)"
                        )

                # If no specific medical content found, look for any substantial text content
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
                        if (
                            len(div_text) > 30 and div_text not in seen_text
                        ):  # Any substantial text content, no duplicates
                            text_html = f'<div style="padding: 10px; margin: 10px 0; background: #f9f9f9;"><p>{div_text}</p></div>'
                            background_parts.append(text_html)
                            seen_text.add(div_text)
                            print(
                                f"  📝 Extracted text content ({len(div_text)} chars)"
                            )

                    # Also look for paragraphs directly (but ONLY if no div content was found)
                    if not background_parts:
                        paragraphs = container.find_elements(By.TAG_NAME, "p")
                        seen_paragraphs = set()

                        for p in paragraphs:
                            p_text = p.text.strip()
                            if (
                                len(p_text) > 20 and p_text not in seen_paragraphs
                            ):  # Substantial paragraph content, no duplicates
                                p_html = f'<p style="padding: 5px; margin: 5px 0;">{p_text}</p>'
                                background_parts.append(p_html)
                                seen_paragraphs.add(p_text)
                                print(f"  📄 Extracted paragraph ({len(p_text)} chars)")
                else:
                    print(
                        f"  ✅ Using medical content divs, skipping general text extraction"
                    )

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
        print(
            f"  ✅ Final background content: {len(final_content)} chars ({len(unique_parts)} sections)"
        )
        return final_content
    else:
        print(f"  ⚠️  No background content extracted")
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


def selenium_scrape_deck(
    deck_id, email, password, base_host, bag_id, details_url=None, card_limit=None
):
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

            # Apply card limit for testing if specified
            if card_limit and card_limit < len(card_ids):
                print(
                    f"🔧 Testing mode: Limiting to {card_limit} cards (out of {len(card_ids)} total)"
                )
                card_ids = card_ids[:card_limit]

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
                # Extract comprehensive background content (paragraphs, tables, images, etc.)
                background = extract_comprehensive_background(driver)

                # Prepare session with Selenium cookies for image downloading
                sess = requests.Session()
                for c in driver.get_cookies():
                    sess.cookies.set(c["name"], c["value"])

                # Extract images from the current page (question section, etc.)
                page_images = extract_images_from_page(driver, sess, base_host)

                # Only use fallback text extraction if extract_comprehensive_background found NOTHING
                if (
                    not background or len(background.strip()) < 50
                ):  # Only if truly empty or very minimal
                    try:
                        print(
                            f"  🔍 Background content insufficient ({len(background) if background else 0} chars), trying fallback extraction..."
                        )
                        # Look for any text content in the card container
                        card_containers = driver.find_elements(
                            By.CSS_SELECTOR, "body > div > div.container.card"
                        )
                        if not card_containers:
                            card_containers = driver.find_elements(
                                By.CSS_SELECTOR, "div.container.card"
                            )

                        text_parts = []
                        seen_text = set()  # Prevent duplicates

                        for container in card_containers:
                            # Extract paragraphs
                            paragraphs = container.find_elements(By.TAG_NAME, "p")
                            for p in paragraphs:
                                p_text = p.text.strip()
                                if (
                                    len(p_text) > 20 and p_text not in seen_text
                                ):  # Only substantial content, no duplicates
                                    text_parts.append(f"<p>{p_text}</p>")
                                    seen_text.add(p_text)

                            # Extract divs with substantial text (but avoid duplicates)
                            text_divs = container.find_elements(By.CSS_SELECTOR, "div")
                            for div in text_divs:
                                # Skip if it contains other elements we've already processed
                                if div.find_elements(
                                    By.CSS_SELECTOR, "p, table, img, canvas"
                                ):
                                    continue
                                div_text = div.text.strip()
                                if (
                                    len(div_text) > 30 and div_text not in seen_text
                                ):  # Only substantial content, no duplicates
                                    text_parts.append(f"<div>{div_text}</div>")
                                    seen_text.add(div_text)

                        if text_parts:
                            background = "<br/>".join(
                                text_parts[:3]
                            )  # Limit to 3 parts to avoid duplicates
                            print(
                                f"  📝 Extracted fallback text content: {len(background)} chars"
                            )
                    except Exception as e:
                        print(f"  ⚠️ Error extracting text content: {e}")
                else:
                    print(
                        f"  ✅ Using background content from extract_comprehensive_background ({len(background)} chars) - SKIPPING fallback"
                    )

                # Add images to background if found
                if page_images:
                    if background:
                        background = page_images + "<br/><br/>" + background
                    else:
                        background = page_images

                # Debug: Print what background content was found
                if background:
                    print(
                        f"  📄 Extracted background content ({len(background)} chars)"
                    )
                    # Show a preview of what was extracted (strip HTML for preview)
                    text_preview = re.sub(r"<[^>]+>", "", background)[:200]
                    preview = (
                        text_preview + "..."
                        if len(text_preview) > 200
                        else text_preview
                    )
                    print(f"  Preview: {preview}")
                else:
                    print(f"  ⚠️  No background content found for card {cid}")

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
                            f'<div class="background" style="background: white; color: black; padding: 10px; margin: 10px 0; border-radius: 5px;">{background}</div>'
                            f'<div class="question" style="background: white; color: black; padding: 10px; margin: 10px 0;"><b>{question}</b></div>'
                            f"{freetext_html}"
                        )
                    else:
                        full_q = (
                            f'<div class="question" style="background: white; color: black; padding: 10px; margin: 10px 0;"><b>{question}</b></div>'
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
                # First try with no answers to see what the correct ones should be
                sol_url = f"{base_host}/solution/{cid}/"

                # Try empty guess first to get the correct answers
                empty_payload = [("timer", "1")]
                resp = sess.post(sol_url, data=empty_payload)
                json_resp = {}
                try:
                    json_resp = resp.json()
                except Exception:
                    # If that fails, try with all options (fallback to original method)
                    payload = [("guess[]", oid) for oid, _ in option_info] + [
                        ("timer", "2")
                    ]
                    resp = sess.post(sol_url, data=payload)
                    try:
                        json_resp = resp.json()
                    except Exception:
                        json_resp = {}

                correct_ids = json_resp.get("answers", [])
                feedback = json_resp.get("feedback", "").strip()
                score_text = json_resp.get("scoreText", "").strip()
                sources = []

                # Compute percentage score - use actual score if available
                raw_score = json_resp.get("score", 0)
                if isinstance(raw_score, (int, float)):
                    percent = f"{raw_score}%"
                else:
                    # Try to extract percentage from scoreText if score field is unreliable
                    score_match = re.search(r"(\d+)%", score_text)
                    if score_match:
                        percent = f"{score_match.group(1)}%"
                    else:
                        percent = "0%"
                # Build options and correct_answers lists by matching IDs
                options = [text for oid, text in option_info]
                correct_answers = [
                    text for oid, text in option_info if oid in correct_ids
                ]
                if not correct_answers and options:
                    correct_answers = [options[0]]
                # Format choices for front
                # Build clickable options HTML with proper styling
                input_type = "checkbox" if multi_flag else "radio"
                options_html = "".join(
                    f'<div class="option" style="margin: 5px 0; padding: 8px; border: 1px solid #ccc; border-radius: 4px; background: white; color: black;">'
                    f'<input type="{input_type}" name="choice" id="choice_{cid}_{i}" value="{opt}" style="margin-right: 8px;">'
                    f'<label for="choice_{cid}_{i}" style="color: black; cursor: pointer;">{opt}</label>'
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
                answer = (
                    " ||| ".join(correct_answers)
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

            # Process images in explanations/feedback for all cards
            print(f"🖼️ Processing images in card explanations...")
            sess = requests.Session()
            for c in driver.get_cookies():
                sess.cookies.set(c["name"], c["value"])

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
                        print(
                            f"  🖼️ Processed {len(extracted_images)} images for card {card['id']}"
                        )
                    except Exception as e:
                        print(
                            f"  ⚠️ Warning: Error processing images for card {card['id']}: {e}"
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

            # Apply card limit for testing if specified
            if card_limit and card_limit < len(card_ids):
                print(
                    f"🔧 Testing mode: Limiting to {card_limit} cards (out of {len(card_ids)} total)"
                )
                card_ids = card_ids[:card_limit]

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

                # Extract comprehensive background content (paragraphs, tables, images, etc.)
                background = extract_comprehensive_background(driver)

                # Prepare session with Selenium cookies for image downloading
                sess = requests.Session()
                for c in driver.get_cookies():
                    sess.cookies.set(c["name"], c["value"])

                # Extract images from the current page (question section, etc.)
                page_images = extract_images_from_page(driver, sess, base_host)

                # Add images to background if found
                if page_images:
                    if background:
                        background = page_images + "<br/><br/>" + background
                    else:
                        background = page_images

                # Debug: Print what background content was found
                if background:
                    print(
                        f"  📄 Extracted background content ({len(background)} chars)"
                    )
                    # Show a preview of what was extracted (strip HTML for preview)
                    text_preview = re.sub(r"<[^>]+>", "", background)[:200]
                    preview = (
                        text_preview + "..."
                        if len(text_preview) > 200
                        else text_preview
                    )
                    print(f"  Preview: {preview}")
                else:
                    print(f"  ⚠️  No background content found for card {cid}")

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
                            f'<div class="background" style="background: white; color: black; padding: 10px; margin: 10px 0; border-radius: 5px;">{background}</div>'
                            f'<div class="question" style="background: white; color: black; padding: 10px; margin: 10px 0;"><b>{question}</b></div>'
                            f"{freetext_html}"
                        )
                    else:
                        full_q = (
                            f'<div class="question" style="background: white; color: black; padding: 10px; margin: 10px 0;"><b>{question}</b></div>'
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

                # Call solution endpoint to get correct answer IDs (improved method)
                sol_url = f"{base_host}/solution/{cid}/"

                # Try empty guess first to get the correct answers
                empty_payload = [("timer", "1")]
                resp = sess.post(sol_url, data=empty_payload)
                json_resp = {}
                try:
                    json_resp = resp.json()
                except Exception:
                    # If that fails, try with all options (fallback to original method)
                    payload = [("guess[]", oid) for oid, _ in option_info] + [
                        ("timer", "2")
                    ]
                    resp = sess.post(sol_url, data=payload)
                    try:
                        json_resp = resp.json()
                    except Exception:
                        json_resp = {}

                correct_ids = json_resp.get("answers", [])
                feedback = json_resp.get("feedback", "").strip()
                score_text = json_resp.get("scoreText", "").strip()
                sources = []

                # Compute percentage score - use actual score if available
                raw_score = json_resp.get("score", 0)
                if isinstance(raw_score, (int, float)):
                    percent = f"{raw_score}%"
                else:
                    # Try to extract percentage from scoreText if score field is unreliable
                    score_match = re.search(r"(\d+)%", score_text)
                    if score_match:
                        percent = f"{score_match.group(1)}%"
                    else:
                        percent = "0%"
                # Build options and correct_answers lists by matching IDs
                options = [text for oid, text in option_info]
                correct_answers = [
                    text for oid, text in option_info if oid in correct_ids
                ]
                if not correct_answers and options:
                    correct_answers = [options[0]]
                # Format choices for front
                # Build clickable options HTML with proper styling
                input_type = "checkbox" if multi_flag else "radio"
                options_html = "".join(
                    f'<div class="option" style="margin: 5px 0; padding: 8px; border: 1px solid #ccc; border-radius: 4px; background: white; color: black;">'
                    f'<input type="{input_type}" name="choice" id="choice_{cid}_{i}" value="{opt}" style="margin-right: 8px;">'
                    f'<label for="choice_{cid}_{i}" style="color: black; cursor: pointer;">{opt}</label>'
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
                answer = (
                    " ||| ".join(correct_answers)
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

            # Process images in explanations/feedback for all cards
            print(f"🖼️ Processing images in card explanations...")
            sess = requests.Session()
            for c in driver.get_cookies():
                sess.cookies.set(c["name"], c["value"])

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
                        print(
                            f"  🖼️ Processed {len(extracted_images)} images for card {card['id']}"
                        )
                    except Exception as e:
                        print(
                            f"  ⚠️ Warning: Error processing images for card {card['id']}: {e}"
                        )

            return cards

    finally:
        driver.quit()


def selenium_scrape_collection(
    collection_id, email, password, base_host, card_limit=None
):
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
                    deck_title = (
                        deck_names_map.get(deck_id)
                        or link.text.strip()
                        or f"Deck {deck_id}"
                    )

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
    pattern = r"^([A-Z]+(?:\s+[A-Z]+)*)\s+(\d+)\.(\d+)\.(\d+)$"
    match = re.match(pattern, collection_name.strip())

    if match:
        base_name = match.group(1)  # e.g., "RIME" or "ASWD"
        block_num = int(match.group(2))
        unit_num = int(match.group(3))
        week_num = int(match.group(4))

        print(
            f"🎓 Detected curriculum pattern: {base_name} Block {block_num}, Unit {unit_num}, Week {week_num}"
        )
        return True, base_name, block_num, unit_num, week_num

    return False, None, None, None, None


def export_hierarchical_apkg(
    data, collection_name, decks_info, path, is_single_deck=False
):
    """
    Export cards with hierarchical deck structure:

    For single deck URLs:
    Deck Name
    ├── Patient 1
    ├── Patient 2
    └── Patient 3

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

/* Support for full card content rendering */
.full-card-content { 
    margin-bottom: 20px; 
    border: 1px solid #ccc; 
    padding: 15px; 
    background: #f9f9f9; 
    border-radius: 5px;
}

.full-card-content .container.card {
    background: white;
    border: none;
    padding: 0;
}

/* Vital signs monitor styling */
.vital-signs-monitor {
    background: #1a1a1a;
    color: #00ff00;
    font-family: 'Courier New', monospace;
    padding: 15px;
    border: 2px solid #333;
    border-radius: 8px;
    margin: 10px 0;
}

.monitor {
    background: #000;
    color: #00ff00;
    font-family: monospace;
    padding: 10px;
    border: 1px solid #333;
}

/* Preserve any dynamic portrait/chart elements */
.group.box {
    border: 1px solid #ddd;
    padding: 10px;
    margin: 5px 0;
    background: #fafafa;
}

/* Support for embedded SVG and canvas elements */
svg, canvas {
    max-width: 100%;
    height: auto;
}

/* Table styling improvements */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
    background: white;
    color: black;
}

table th, table td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
    color: black !important;
    background: white;
}

table th {
    background-color: #f2f2f2 !important;
    font-weight: bold;
    color: black !important;
}

/* Specific styling for tables in explanation/answer sections */
#explanation table, #answer-section table {
    background: white !important;
    color: black !important;
    border: 2px solid #333;
    margin: 15px 0;
}

#explanation table th, #answer-section table th {
    background-color: #e6e6e6 !important;
    color: black !important;
    font-weight: bold;
    border: 1px solid #666;
}

#explanation table td, #answer-section table td {
    background: white !important;
    color: black !important;
    border: 1px solid #666;
}

/* Style medical table headers */
#explanation h4, #answer-section h4 {
    color: #4CAF50;
    font-weight: bold;
    margin-top: 20px;
    margin-bottom: 10px;
}

/* Styling for extracted images */
.extracted-images {
    margin: 15px 0;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    background: #fafafa;
}

.extracted-images img {
    max-width: 100%;
    height: auto;
    margin: 5px;
    border: 1px solid #ccc;
    border-radius: 3px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Responsive image sizing */
.extracted-images img[width] {
    max-width: 100% !important;
    width: auto !important;
    height: auto !important;
}
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
  var answers = "{{CorrectAnswer}}".split(" ||| ").map(function(s){ return s.trim(); });
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
  var answers = "{{CorrectAnswer}}".split(" ||| ").map(function(s){ return s.trim(); });
  var selected = Array.from(document.querySelectorAll('.option input:checked')).map(function(inp){ return inp.value.trim(); });
  var correctLen = answers.length;
  var selectedCorrect = 0;
  
  // More robust text comparison - normalize both sides
  selected.forEach(function(val){
    // Check if this selected value matches any of the correct answers
    var normalizedVal = val.replace(/\s+/g, ' ').trim();
    var isCorrect = answers.some(function(answer){
      var normalizedAnswer = answer.replace(/\s+/g, ' ').trim();
      return normalizedVal === normalizedAnswer;
    });
    if(isCorrect) selectedCorrect++;
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
    is_curriculum, base_name, block_num, unit_num, week_num = detect_curriculum_pattern(
        collection_name, decks_info
    )

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

    if is_single_deck:
        # For single deck URLs, create simple Deck::Patient hierarchy
        # Get the actual deck name from the first card or use collection_name as fallback
        actual_deck_name = collection_name
        if (
            data
            and data[0].get("deck_title")
            and data[0]["deck_title"] != "Unknown Deck"
        ):
            actual_deck_name = data[0]["deck_title"]

        # Group by patient only (no deck grouping needed for single deck)
        patient_structure = {}
        for card in data:
            patient_info = card.get("patient_info", "Unknown Patient")
            if patient_info not in patient_structure:
                patient_structure[patient_info] = []
            patient_structure[patient_info].append(card)

        for patient_info, cards in patient_structure.items():
            # Create simple hierarchy: "DeckName::Patient"
            hierarchical_name = f"{actual_deck_name}::{patient_info}"

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

                # Add simple tags for single deck
                tags = card.get("tags", []) + [
                    f"Deck_{actual_deck_name.replace(' ', '_')}",
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

    elif is_curriculum:
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
    if is_single_deck:
        print("📋 Deck Structure:")
        # For single deck, group by patient only
        patient_structure = {}
        for card in data:
            patient_info = card.get("patient_info", "Unknown Patient")
            if patient_info not in patient_structure:
                patient_structure[patient_info] = []
            patient_structure[patient_info].append(card)

        actual_deck_name = collection_name
        if (
            data
            and data[0].get("deck_title")
            and data[0]["deck_title"] != "Unknown Deck"
        ):
            actual_deck_name = data[0]["deck_title"]

        print(f"  📚 {actual_deck_name}")
        for patient_info, cards in patient_structure.items():
            print(f"    👤 {patient_info} ({len(cards)} cards)")
    elif is_curriculum:
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
  var answers = "{{CorrectAnswer}}".split(" ||| ").map(function(s){ return s.trim(); });
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
  var answers = "{{CorrectAnswer}}".split(" ||| ").map(function(s){ return s.trim(); });
  var selected = Array.from(document.querySelectorAll('.option input:checked')).map(function(inp){ return inp.value.trim(); });
  var correctLen = answers.length;
  var selectedCorrect = 0;
  
  // More robust text comparison - normalize both sides
  selected.forEach(function(val){
    // Check if this selected value matches any of the correct answers
    var normalizedVal = val.replace(/\s+/g, ' ').trim();
    var isCorrect = answers.some(function(answer){
      var normalizedAnswer = answer.replace(/\s+/g, ' ').trim();
      return normalizedVal === normalizedAnswer;
    });
    if(isCorrect) selectedCorrect++;
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

    # Check for command line argument first
    if len(sys.argv) > 1:
        base_url_override = sys.argv[1].strip()
        print(f"Using URL from command line: {base_url_override}")
    else:
        # Prompt URL if no command line argument
        base_url_override = input("Enter UCalgary collection or deck URL: ").strip()

    # Check for card limit as second command line argument
    card_limit = None
    if len(sys.argv) > 2:
        card_limit_arg = sys.argv[2].strip()
        if card_limit_arg.isdigit():
            card_limit = int(card_limit_arg)
            print(f"Using card limit from command line: {card_limit}")
        else:
            print(f"Invalid card limit argument: {card_limit_arg}")

    # Ask for card limit if not provided via command line
    if card_limit is None:
        print("\n🔧 Testing Options:")
        print("   - Press Enter to process ALL cards")
        print("   - Enter a number (e.g., 5) to limit cards for testing")
        card_limit_input = input("Number of cards to process (optional): ").strip()
        if card_limit_input and card_limit_input.isdigit():
            card_limit = int(card_limit_input)
            print(f"   ⚡ Will process only {card_limit} cards for testing")
        else:
            print(f"   📚 Will process ALL cards")
    else:
        print(f"   ⚡ Will process only {card_limit} cards for testing")

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
                card_limit=card_limit,
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
                card_limit=card_limit,
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

    # Export the deck - use hierarchical export for collections OR when we have patient data
    has_patients = any(
        card.get("patient_info") and card.get("patient_info") != "Unknown Patient"
        for card in cards
    )

    if is_collection or has_patients:
        # For collections or when we have patient data, use hierarchical export
        if not is_collection:
            # Single deck with patients - use simple deck::patient hierarchy
            collection_title = deck_name
            decks_info = [{"title": deck_name, "deck_id": deck_id}]
            export_hierarchical_apkg(
                cards, collection_title, decks_info, output_path, is_single_deck=True
            )
        else:
            # Collection - use full collection::deck::patient hierarchy
            export_hierarchical_apkg(
                cards, collection_title, decks_info, output_path, is_single_deck=False
            )
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
