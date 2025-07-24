#!/usr/bin/env python3
"""
Script to analyze the contents of an APKG file to see what images are included
"""
import zipfile
import sqlite3
import json
import tempfile
import os
import re


def extract_question_text(html_content):
    """Extract readable question text from HTML content"""
    import re
    from html import unescape

    # Remove HTML tags
    clean_text = re.sub(r"<[^>]+>", " ", html_content)
    # Decode HTML entities
    clean_text = unescape(clean_text)
    # Normalize whitespace
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    return clean_text


def analyze_apkg(apkg_path):
    """Comprehensive analysis of APKG file contents"""
    print(f"🔍 COMPREHENSIVE APKG ANALYSIS: {apkg_path}")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract the APKG file (it's a ZIP file)
        with zipfile.ZipFile(apkg_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # List contents
        print("\n📁 APKG Contents:")
        for item in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, item)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"  📄 {item} ({size:,} bytes)")
            else:
                print(f"  📁 {item}/")

        # Check media folder if exists
        media_path = os.path.join(temp_dir, "media")
        if os.path.exists(media_path) and os.path.isdir(media_path):
            media_files = os.listdir(media_path)
            print(f"\n🖼️  MEDIA FILES ({len(media_files)} files):")
            for media_file in media_files[:10]:  # Show first 10
                print(f"    📸 {media_file}")
            if len(media_files) > 10:
                print(f"    ... and {len(media_files) - 10} more files")
        elif os.path.exists(media_path):
            # Media is a file, not a directory
            media_size = os.path.getsize(media_path)
            print(f"\n🖼️  MEDIA FILE: {media_size} bytes (not a directory)")
        else:
            print(f"\n🖼️  No media folder found")

        # Read the SQLite database
        db_path = os.path.join(temp_dir, "collection.anki2")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get all notes
            cursor.execute("SELECT id, flds FROM notes")
            all_notes = cursor.fetchall()
            print(f"\n📚 FOUND {len(all_notes)} TOTAL NOTES")

            # Analyze ALL notes for comprehensive overview
            total_images = 0
            total_svgs = 0
            total_portraits = 0
            total_vitals_sections = 0
            content_sizes = []
            duplicate_content = {}
            portrait_indicators_found = set()

            print(f"\n🔬 ANALYZING ALL {len(all_notes)} NOTES...")

            for note_id, fields in all_notes:
                field_list = fields.split("\x1f")
                if field_list:
                    front_content = field_list[0]
                    content_sizes.append(len(front_content))

                    # Track duplicate content
                    content_hash = hash(
                        front_content[:1000]
                    )  # First 1000 chars as signature
                    if content_hash in duplicate_content:
                        duplicate_content[content_hash].append(note_id)
                    else:
                        duplicate_content[content_hash] = [note_id]

                    # Count various elements
                    img_count = len(re.findall(r"<img[^>]*>", front_content))
                    svg_count = len(
                        re.findall(r"<svg[^>]*>.*?</svg>", front_content, re.DOTALL)
                    )
                    vitals_count = front_content.lower().count(
                        "vital"
                    ) + front_content.lower().count("monitor")

                    total_images += img_count
                    total_svgs += svg_count
                    total_vitals_sections += vitals_count

                    # Look for portrait indicators in actual content
                    portrait_words = [
                        "portrait",
                        "headshot",
                        "staff",
                        "physician",
                        "doctor",
                        "faculty",
                        "person",
                        "face",
                    ]
                    for word in portrait_words:
                        if word in front_content.lower():
                            portrait_indicators_found.add(word)
                            total_portraits += front_content.lower().count(word)

            # Summary statistics
            print(f"\n📊 CONTENT STATISTICS:")
            print(f"  📄 Total img tags: {total_images}")
            print(f"  🎨 Total SVG elements: {total_svgs}")
            print(f"  👤 Portrait indicators found: {total_portraits}")
            print(f"  💓 Vital signs mentions: {total_vitals_sections}")
            print(
                f"  📏 Average content size: {sum(content_sizes) / len(content_sizes):,.0f} chars"
            )
            print(f"  📏 Min content size: {min(content_sizes):,} chars")
            print(f"  📏 Max content size: {max(content_sizes):,} chars")

            if portrait_indicators_found:
                print(
                    f"  🚨 Portrait words found: {', '.join(portrait_indicators_found)}"
                )

            # Check for duplicates
            duplicates = {k: v for k, v in duplicate_content.items() if len(v) > 1}
            if duplicates:
                print(f"\n⚠️  DUPLICATE CONTENT DETECTED:")
                for i, (content_hash, note_ids) in enumerate(duplicates.items()):
                    print(
                        f"    🔄 Duplicate group {i+1}: {len(note_ids)} notes with similar content"
                    )
                    print(f"       Note IDs: {note_ids}")

            # Detailed analysis of first few notes
            print(f"\n🔍 DETAILED ANALYSIS (First 3 notes):")
            for i, (note_id, fields) in enumerate(all_notes[:3]):
                field_list = fields.split("\x1f")
                if field_list:
                    front_content = field_list[0]

                    print(f"\n--- 📝 NOTE {i+1} (ID: {note_id}) ---")

                    # Analyze structure
                    print(f"📏 Content length: {len(front_content):,} chars")

                    # Count different types of content
                    div_count = len(re.findall(r"<div[^>]*>", front_content))
                    img_count = len(re.findall(r"<img[^>]*>", front_content))
                    svg_count = len(re.findall(r"<svg[^>]*>", front_content, re.DOTALL))
                    table_count = len(re.findall(r"<table[^>]*>", front_content))

                    print(
                        f"🏗️  Structure: {div_count} divs, {img_count} imgs, {svg_count} svgs, {table_count} tables"
                    )

                    # Extract question text for analysis
                    question_text = extract_question_text(front_content)
                    if len(question_text) > 200:
                        question_preview = question_text[:200] + "..."
                    else:
                        question_preview = question_text

                    print(f"❓ Question preview: {question_preview}")

                    # Look for specific keywords
                    if "cerebrospinal" in question_text.lower():
                        print(f"🧠 CEREBROSPINAL FLUID QUESTION FOUND!")
                        print(f"📝 Full question: {question_text}")

                    # Look for vital signs sections
                    hr_matches = re.findall(
                        r"HR[^0-9]*(\d+)", front_content, re.IGNORECASE
                    )
                    spo2_matches = re.findall(
                        r"SpO2[^0-9]*(\d+)", front_content, re.IGNORECASE
                    )

                    if hr_matches or spo2_matches:
                        print(
                            f"💓 Vital signs found: HR={hr_matches}, SpO2={spo2_matches}"
                        )

                        # Check for duplicate vital signs
                        if len(hr_matches) > 1:
                            print(f"⚠️  DUPLICATE HR values detected: {hr_matches}")
                        if len(spo2_matches) > 1:
                            print(f"⚠️  DUPLICATE SpO2 values detected: {spo2_matches}")

                    # Check for portraits in this specific note
                    portrait_found = False
                    for word in [
                        "portrait",
                        "headshot",
                        "doctor",
                        "physician",
                        "staff",
                        "faculty",
                    ]:
                        if word in front_content.lower():
                            portrait_found = True
                            print(
                                f"👤 PORTRAIT INDICATOR: '{word}' found {front_content.lower().count(word)} times"
                            )

                    # Look for actual image sources that might be portraits
                    img_srcs = re.findall(r'src=["\']([^"\']+)["\']', front_content)
                    for src in img_srcs:
                        if any(
                            word in src.lower()
                            for word in [
                                "portrait",
                                "headshot",
                                "staff",
                                "photo",
                                "person",
                            ]
                        ):
                            print(f"🚨 POTENTIAL PORTRAIT IMAGE: {src}")

                    # Show main content structure
                    print(f"🔍 Content structure preview:")
                    # Remove most content but keep structure
                    structure_preview = re.sub(
                        r">([^<]{50})[^<]*<", r">[CONTENT...]<", front_content[:2000]
                    )
                    print(f"    {structure_preview[:500]}...")

                    # Show vital signs formatting specifically
                    vital_sections = re.findall(
                        r"<div[^>]*(?:monitor|vital)[^>]*>.*?</div>",
                        front_content,
                        re.DOTALL | re.IGNORECASE,
                    )
                    if vital_sections:
                        print(f"💓 Vital Signs formatting:")
                        for j, section in enumerate(vital_sections[:2]):  # Show first 2
                            clean_section = re.sub(r"\s+", " ", section)
                            print(f"    Section {j+1}: {clean_section[:200]}...")

            conn.close()
        else:
            print("❌ No collection.anki2 found")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        apkg_path = sys.argv[1]
    else:
        apkg_path = "/Users/ammarmahdi/Desktop/Deck_1265.apkg"

    if not os.path.exists(apkg_path):
        print(f"❌ Error: APKG file not found: {apkg_path}")
        sys.exit(1)

    analyze_apkg(apkg_path)
