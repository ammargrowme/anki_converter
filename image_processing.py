#!/usr/bin/env python3

import re
import base64
import requests
from selenium.webdriver.common.by import By


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
    
    all_text = f"{src_lower} {alt_lower} {title_lower} {class_lower}"

    # Portrait indicators in file names/paths
    portrait_indicators = [
        "portrait", "headshot", "profile", "photo", "mugshot", "avatar", "face",
        "person", "doctor", "patient_photo", "staff", "physician", "nurse",
        "resident", "attending", "faculty", "bio", "biography", "people",
    ]

    # UI/Logo/Avatar indicators - these should always be filtered
    ui_indicators = [
        "anon.png", "anonymous", "uc-cumming", "UC-cumming-black.png",
        "logo.png", "logo.jpg", "logo.svg", "badge", "icon", "nav",
        "navigation", "header", "footer", "sidebar", "menu", "button",
    ]

    # Medical content indicators that should be kept - comprehensive list
    medical_indicators = [
        "ecg", "ekg", "electrocardiogram", "monitor", "vital_signs", "vitalsigns",
        "cardiac_monitor", "heart_monitor", "rhythm_strip", "waveform", "mri",
        "ct_scan", "ultrasound", "x-ray", "xray", "scan", "blood_pressure",
        "bp_monitor", "oxygen", "saturation", "pulse_ox", "cardiac", "pulmonary",
        "respiratory", "chest_xray", "diagnostic", "test_result", "lab_result",
        "pathology", "radiology", "equipment", "device", "machine", "display",
        "screen", "readout", "medical_chart", "ecg_trace", "rhythm", "heart_rate",
        "anatomy", "antcirc", "circulation", "structure", "identify", "diagram",
        "uploads/card", "medical", "clinical", "patient", "case", "study",
        "education", "learning",
    ]

    # Check for medical indicators FIRST - highest priority for keeping
    medical_matches = [indicator for indicator in medical_indicators if indicator in all_text]
    if medical_matches:
        return False  # Medical content, keep it

    # Check for specific UI/Logo indicators
    for indicator in ui_indicators:
        if indicator in all_text:
            return True

    # Check for strong portrait indicators
    for indicator in portrait_indicators:
        if indicator in all_text:
            return True  # Likely a portrait, filter it out

    # Additional heuristics based on file names
    if any(ext in src_lower for ext in ["jpg", "jpeg", "png"]):
        # If it's in a people/photos/portraits directory
        if any(word in src_lower for word in ["people", "photos", "portraits", "staff", "faculty", "bio", "headshots"]):
            return True

        # If filename suggests it's a person's photo
        if any(word in src_lower for word in ["headshot", "bio", "profile", "_person", "staff_", "faculty_"]):
            return True

    # If no clear indicators, examine the source path more carefully
    portrait_paths = ["/images/people/", "/staff/", "/faculty/", "/photos/", "/portraits/", "/bio/"]
    for path in portrait_paths:
        if path in src_lower:
            return True

    # Default to filtering if uncertain and looks like a person-related image
    if any(word in all_text for word in ["dr.", "dr ", "md", "phd", "professor", "physician"]):
        return True

    # If we can't identify it clearly, but it's in a medical/educational context, keep it
    educational_context = any(
        word in all_text for word in [
            "uploads/card", "question", "case", "study", "patient", "medical",
            "clinical", "anatomy", "identify", "structure", "diagram",
        ]
    )
    
    if educational_context:
        return False

    # Only filter if we're confident it's not medical/educational content
    return True


def clean_html_portraits(html_content):
    """
    Remove portrait images from HTML content while preserving medical images.
    This includes both <img> tags and portrait SVG elements.
    """
    if not html_content:
        return html_content

    # First, remove portrait DIV containers entirely
    portrait_div_pattern = r'<div[^>]*class=["\'][^"\']*portrait[^"\']*["\'][^>]*>.*?</div>'
    portrait_divs_found = len(re.findall(portrait_div_pattern, html_content, re.DOTALL))
    if portrait_divs_found > 0:
        html_content = re.sub(portrait_div_pattern, "", html_content, flags=re.DOTALL)

    # More aggressive SVG removal - remove ALL SVGs that contain common portrait indicators
    def should_remove_svg(match):
        svg_content = match.group(0)

        # Check if SVG contains portrait/doctor indicators
        portrait_indicators = [
            "doctor_room", "doctor", "portrait", "physician", "staff", "headshot",
            "face", "person", "human", "head", "hair", "eyes", "nose", "mouth",
            "skin", "body", "arm", "hand", "leg", "shirt", "clothing", "uniform",
        ]
        medical_indicators = [
            "ecg", "ekg", "electrocardiogram", "waveform", "heartbeat", "chart",
            "graph", "plot", "data", "line", "axis", "grid",
        ]

        # Count indicators - be much more aggressive about portraits
        portrait_count = sum(1 for indicator in portrait_indicators if indicator.lower() in svg_content.lower())
        medical_count = sum(1 for indicator in medical_indicators if indicator.lower() in svg_content.lower())

        # Remove if ANY portrait indicators found, unless there are significantly more medical indicators
        if portrait_count > 0 and medical_count < (portrait_count * 2):
            return ""

        return svg_content

    # Remove portrait SVG elements
    svg_pattern = r"<svg[^>]*>.*?</svg>"
    html_content = re.sub(svg_pattern, should_remove_svg, html_content, flags=re.DOTALL)

    # Also handle img tags
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
            return ""

        # Otherwise, keep the image
        return img_tag

    # Replace img tags, removing portraits
    html_content = re.sub(r"<img[^>]*>", should_remove_img, html_content)
    return html_content


def extract_images_from_html(html_content, session, base_host):
    """
    Extract images from HTML content and return processed HTML with embedded images.
    """
    if not html_content:
        return html_content, []

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
                html_content = html_content.replace(f'src="{img_src}"', f'src="{data_url}"')
                html_content = html_content.replace(f"src='{img_src}'", f"src='{data_url}'")

                extracted_images.append({"url": img_url, "data": img_data, "type": ext})

        except Exception as e:
            print(f"  ❌ Error processing image {img_src}: {e}")

    return html_content, extracted_images


def extract_images_from_page(driver, session, base_host):
    """
    Extract images directly from the current page using multiple selectors.
    Returns HTML content with embedded images for inclusion in question/background.
    """
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
                        continue

                    # Handle relative URLs
                    if img_src.startswith("/"):
                        img_url = base_host + img_src
                    elif img_src.startswith("http"):
                        img_url = img_src
                    else:
                        img_url = base_host + "/" + img_src

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

                        # Reconstruct the HTML img tag with all attributes
                        img_attrs = [f'src="{data_url}"']
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

                except Exception as e:
                    print(f"  ❌ Error processing image: {e}")

        except Exception as e:
            print(f"  ⚠️ Error with selector {selector}: {e}")

    if all_images_html:
        # Wrap images in a container for better styling
        images_section = '<div class="extracted-images">' + "".join(all_images_html) + "</div>"
        return images_section
    else:
        return ""


def normalize_html_formatting(html_content):
    """
    Normalize HTML formatting to ensure consistent styling in feedback blocks.
    Removes inconsistent inline CSS styling and ensures uniform paragraph structure.
    """
    if not html_content:
        return html_content

    # Remove specific inline styles that cause formatting inconsistencies
    inline_style_pattern = r'style\s*=\s*["\'][^"\']*font-family[^"\']*["\']'
    html_content = re.sub(inline_style_pattern, "", html_content)

    # Convert span elements with remaining inline styles to simple p tags for consistency
    span_to_p_pattern = r"<span[^>]*>(.*?)</span>"

    def replace_span_with_p(match):
        content = match.group(1)
        # Only convert to paragraph if it looks like paragraph content (has substantial text)
        if len(content.strip()) > 20:  # Arbitrary threshold for paragraph-like content
            return f"<p>{content}</p>"
        else:
            return f"<span>{content}</span>"  # Keep as span for short text

    html_content = re.sub(span_to_p_pattern, replace_span_with_p, html_content, flags=re.DOTALL)

    # Clean up any empty or redundant attributes
    html_content = re.sub(r'\s+style\s*=\s*["\']["\']', "", html_content)  # Remove empty style attributes
    html_content = re.sub(r"\s+>", ">", html_content)  # Clean up trailing spaces before closing brackets

    return html_content
