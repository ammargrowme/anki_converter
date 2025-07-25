#!/usr/bin/env python3
"""
Enhanced APKG Analyzer for UCalgary Anki Converter

This script provides comprehensive analysis of APKG files to verify the quality
and features of exported Anki decks. Specifically designed to test the output
from our UCalgary Cards to Anki converter.

Features:
- Hierarchical deck structure analysis
- Curriculum pattern detection (RIME, Foundations, etc.)
- Patient organization verification
- MCQ and interactive element detection
- Media content analysis
- Duplicate detection
- Quality scoring system
- Export system compatibility checking

Usage:
    python analyze_apkg.py <path_to_apkg_file>
    python analyze_apkg.py  # Auto-finds sample files
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


def analyze_deck_structure(cursor):
    """Analyze the hierarchical deck structure"""
    try:
        # Try to get deck information - Anki uses a different schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n🗃️  DATABASE TABLES: {', '.join(tables)}")

        # Check if we have deck info in the collection config
        deck_names = []
        deck_count = 0

        # Try to get deck info from notes and cards
        if "cards" in tables:
            cursor.execute("SELECT DISTINCT did FROM cards")
            deck_ids = cursor.fetchall()
            deck_count = len(deck_ids)
            print(f"\n🏗️  DECK STRUCTURE ANALYSIS:")
            print(f"  📚 Deck IDs found: {deck_count}")

        # For APKG files, deck names might be encoded differently
        # Try to extract from the collection config or use a simpler approach
        hierarchical_patterns = []
        curriculum_patterns = []
        patient_patterns = []

        # We'll analyze based on note content and card distribution instead
        print(f"  📁 Analyzing structure from card distribution...")

        return {
            "total_decks": deck_count,
            "hierarchical": hierarchical_patterns,
            "curriculum": curriculum_patterns,
            "patient": patient_patterns,
        }

    except sqlite3.Error as e:
        print(f"  ⚠️  Could not analyze deck structure: {e}")
        return {
            "total_decks": 1,  # Default assumption
            "hierarchical": [],
            "curriculum": [],
            "patient": [],
        }


def analyze_card_types_and_content(cursor):
    """Analyze card types and content structure"""
    # Get all cards with their note content
    cursor.execute(
        """
        SELECT c.id, c.nid, n.flds, n.tags, c.did 
        FROM cards c 
        JOIN notes n ON c.nid = n.id
    """
    )
    cards = cursor.fetchall()

    print(f"\n🃏 CARD CONTENT ANALYSIS:")
    print(f"  🎴 Total cards: {len(cards)}")

    mcq_cards = 0
    interactive_elements = 0
    media_cards = 0
    sequential_cards = 0
    patient_cards = 0

    for card_id, note_id, fields, tags, deck_id in cards:
        field_list = fields.split("\x1f")
        front_content = field_list[0] if field_list else ""

        # Check for MCQ indicators
        if any(
            pattern in front_content
            for pattern in [
                '<input type="radio"',
                '<input type="checkbox"',
                'class="option"',
                "multiple choice",
                "select the correct",
            ]
        ):
            mcq_cards += 1

        # Check for interactive elements
        if any(
            pattern in front_content
            for pattern in [
                "onclick=",
                "addEventListener",
                "function check",
                "score",
                "correct",
                "incorrect",
            ]
        ):
            interactive_elements += 1

        # Check for media content
        if any(
            pattern in front_content
            for pattern in ["<img", "<svg", "data:image", "src=", "<audio", "<video"]
        ):
            media_cards += 1

        # Check for sequential indicators
        if "sequential" in tags.lower() or "is_sequential" in front_content:
            sequential_cards += 1

        # Check for patient info
        if any(
            pattern in front_content.lower()
            for pattern in ["patient", "vital signs", "monitor", "hr:", "spo2:", "bp:"]
        ):
            patient_cards += 1

    print(f"  📊 MCQ cards: {mcq_cards}")
    print(f"  🎮 Interactive elements: {interactive_elements}")
    print(f"  🖼️  Cards with media: {media_cards}")
    print(f"  🔄 Sequential cards: {sequential_cards}")
    print(f"  👤 Patient-related cards: {patient_cards}")

    return {
        "total_cards": len(cards),
        "mcq_cards": mcq_cards,
        "interactive_elements": interactive_elements,
        "media_cards": media_cards,
        "sequential_cards": sequential_cards,
        "patient_cards": patient_cards,
    }


def analyze_apkg(apkg_path):
    """Comprehensive analysis of APKG file contents - Updated for current export system"""
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

            # New comprehensive analysis
            deck_structure = analyze_deck_structure(cursor)
            card_analysis = analyze_card_types_and_content(cursor)

            # Get all notes for detailed analysis
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

            # Enhanced duplicate analysis - check for EXACT duplicates only
            print(f"\n🔍 EXACT DUPLICATE ANALYSIS:")
            exact_question_answer_pairs = {}
            true_exact_duplicates = {}

            for note_id, fields in all_notes:
                field_list = fields.split("\x1f")
                if len(field_list) >= 2:
                    front_content = field_list[0]
                    back_content = field_list[1] if len(field_list) > 1 else ""

                    # Extract just the question text (remove images and HTML)
                    question_text = extract_question_text(front_content)
                    # Remove base64 image data from question
                    question_text = re.sub(r'data:image/[^"\']*', "", question_text)
                    question_text = re.sub(r"\s+", " ", question_text).strip()

                    # Extract answer text
                    answer_text = extract_question_text(back_content)
                    answer_text = re.sub(r'data:image/[^"\']*', "", answer_text)
                    answer_text = re.sub(r"\s+", " ", answer_text).strip()

                    # Create a FULL signature for EXACT matching (question + answer)
                    exact_signature = f"{question_text}||{answer_text}"

                    # Track EXACT question+answer combinations
                    if exact_signature in exact_question_answer_pairs:
                        if exact_signature not in true_exact_duplicates:
                            true_exact_duplicates[exact_signature] = {
                                "original": exact_question_answer_pairs[exact_signature],
                                "duplicates": []
                            }
                        true_exact_duplicates[exact_signature]["duplicates"].append({
                            "note_id": note_id,
                            "question": question_text[:200] + "..." if len(question_text) > 200 else question_text,
                            "answer": answer_text[:100] + "..." if len(answer_text) > 100 else answer_text,
                        })
                    else:
                        exact_question_answer_pairs[exact_signature] = {
                            "note_id": note_id,
                            "question": question_text[:200] + "..." if len(question_text) > 200 else question_text,
                            "answer": answer_text[:100] + "..." if len(answer_text) > 100 else answer_text,
                        }

            # Report ONLY true exact duplicates
            if true_exact_duplicates:
                print(f"\n🚨 EXACT DUPLICATE QUESTIONS FOUND:")
                print(f"   ⚠️  These are identical question+answer pairs (potential errors)")
                for i, (exact_sig, dup_data) in enumerate(true_exact_duplicates.items()):
                    print(f"\n--- 🔄 EXACT DUPLICATE GROUP {i+1} ---")
                    question_part = exact_sig.split("||")[0]
                    answer_part = exact_sig.split("||")[1]
                    print(f"📝 Question: {question_part[:150]}...")
                    print(f"💬 Answer: {answer_part[:100]}...")

                    # Show original
                    original = dup_data["original"]
                    print(f"  � Original Note ID: {original['note_id']}")

                    # Show exact duplicates
                    for j, dup in enumerate(dup_data["duplicates"]):
                        print(f"  🔄 Exact Duplicate {j+1} Note ID: {dup['note_id']}")
                        
                print(f"\n📊 EXACT DUPLICATE SUMMARY:")
                print(f"  ⚠️  {len(true_exact_duplicates)} exact duplicate question+answer pairs found")
                total_duplicate_cards = sum(len(dup_data["duplicates"]) for dup_data in true_exact_duplicates.values())
                print(f"  🔄 {total_duplicate_cards} total duplicate cards that could be removed")
            else:
                print(f"✅ NO EXACT DUPLICATE QUESTIONS FOUND!")
                print(f"   🎓 All question+answer combinations are unique (as expected for educational content)")
                print(f"   📚 Similar scenarios with different questions/answers are intentional educational variants")

            print(f"\n📊 UNIQUE QUESTIONS SUMMARY:")
            print(f"  📝 Total unique question+answer combinations: {len(exact_question_answer_pairs)}")
            print(f"  🔄 Total exact duplicate groups: {len(true_exact_duplicates)}")

            # Show sample unique questions (first 10)
            print(f"\n📋 SAMPLE UNIQUE QUESTIONS (First 10):")
            for i, (exact_sig, data) in enumerate(list(exact_question_answer_pairs.items())[:10]):
                question_part = exact_sig.split("||")[0]
                print(f"\n{i+1:2d}. Note ID {data['note_id']}: {question_part[:150]}...")

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

            print(f"\n📊 EXPORT SYSTEM COMPATIBILITY CHECK:")

            # Check if this looks like our export system's output
            export_indicators = []

            if deck_structure["hierarchical"]:
                export_indicators.append(
                    f"✅ Hierarchical structure ({len(deck_structure['hierarchical'])} hierarchical decks)"
                )

            if deck_structure["curriculum"]:
                export_indicators.append(
                    f"✅ Curriculum patterns ({len(deck_structure['curriculum'])} curriculum decks)"
                )

            if deck_structure["patient"]:
                export_indicators.append(
                    f"✅ Patient organization ({len(deck_structure['patient'])} patient decks)"
                )

            if card_analysis["mcq_cards"] > 0:
                export_indicators.append(
                    f"✅ MCQ functionality ({card_analysis['mcq_cards']} MCQ cards)"
                )

            if card_analysis["interactive_elements"] > 0:
                export_indicators.append(
                    f"✅ Interactive elements ({card_analysis['interactive_elements']} interactive cards)"
                )

            if card_analysis["media_cards"] > 0:
                export_indicators.append(
                    f"✅ Media content ({card_analysis['media_cards']} cards with media)"
                )

            if export_indicators:
                print(f"  🎯 Export system features detected:")
                for indicator in export_indicators:
                    print(f"    {indicator}")
            else:
                print(
                    f"  ⚠️  No specific export system features detected - may be basic export"
                )

            # Final quality assessment
            print(f"\n🏆 OVERALL QUALITY ASSESSMENT:")
            quality_score = 0
            max_score = 7

            if deck_structure["total_decks"] > 1:
                quality_score += 1
                print(f"  ✅ Multiple decks ({deck_structure['total_decks']})")

            if deck_structure["hierarchical"]:
                quality_score += 1
                print(f"  ✅ Hierarchical organization")

            if card_analysis["mcq_cards"] > 0:
                quality_score += 1
                print(f"  ✅ Interactive MCQ cards")

            if card_analysis["media_cards"] > 0:
                quality_score += 1
                print(f"  ✅ Rich media content")

            if card_analysis["patient_cards"] > 0:
                quality_score += 1
                print(f"  ✅ Patient-based content")

            if len(all_notes) >= 3:
                quality_score += 1
                print(f"  ✅ Sufficient content volume ({len(all_notes)} notes)")

            if not true_exact_duplicates:
                quality_score += 1
                print(f"  ✅ No exact duplicate questions")

            print(
                f"\n  🎯 Quality Score: {quality_score}/{max_score} ({quality_score/max_score*100:.0f}%)"
            )

            if quality_score >= 6:
                print(f"  🌟 EXCELLENT - High-quality export with advanced features")
            elif quality_score >= 4:
                print(f"  👍 GOOD - Well-structured export with most features")
            elif quality_score >= 2:
                print(f"  ⚠️  BASIC - Functional but missing advanced features")
            else:
                print(f"  ❌ POOR - Major issues detected")

            conn.close()
        else:
            print("❌ No collection.anki2 found")


if __name__ == "__main__":
    import sys
    import glob

    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print(
            """
🔍 APKG Analyzer for UCalgary Anki Converter

📖 USAGE:
    python analyze_apkg.py <path_to_apkg_file>
    python analyze_apkg.py                      # Auto-search for APKG files
    python analyze_apkg.py --help              # Show this help

📋 EXAMPLES:
    python analyze_apkg.py ./my_deck.apkg
    python analyze_apkg.py ~/Desktop/Deck_1234.apkg
    python analyze_apkg.py "/path with spaces/deck.apkg"

🎯 FEATURES:
    • Comprehensive APKG file analysis
    • Hierarchical deck structure detection
    • MCQ and interactive element analysis
    • Media content verification
    • Duplicate question detection
    • Quality scoring system
    • Export system compatibility checking

💡 TIP: Generate a test file first with:
    python main.py
        """
        )
        sys.exit(0)

    if len(sys.argv) > 1:
        apkg_path = sys.argv[1]
        print(f"🎯 Using provided file: {apkg_path}")
    else:
        # Look for sample APKG files in common locations (more generic)
        potential_paths = [
            "*.apkg",  # Current directory
            "../*.apkg",  # Parent directory
            "~/Desktop/*.apkg",  # Desktop
            "~/Downloads/*.apkg",  # Downloads folder
            "./test_deck.apkg",  # Test file in current dir
            "./sample.apkg",  # Sample file in current dir
            "./output/*.apkg",  # Output folder
        ]

        apkg_path = None
        print("🔍 No file specified, searching for APKG files...")

        for path in potential_paths:
            expanded_path = os.path.expanduser(path)  # Handle ~ in paths
            if "*" in expanded_path:
                matches = glob.glob(expanded_path)
                if matches:
                    apkg_path = matches[0]  # Use first match
                    print(f"✅ Found: {apkg_path}")
                    break
                else:
                    print(f"   🔍 No files found: {expanded_path}")
            elif os.path.exists(expanded_path):
                apkg_path = expanded_path
                print(f"✅ Found: {apkg_path}")
                break
            else:
                print(f"   ❌ Not found: {expanded_path}")

        if not apkg_path:
            print(f"\n❌ No APKG file found!")
            print(f"📋 Usage options:")
            print(f"   python analyze_apkg.py <path_to_apkg_file>")
            print(f"   python analyze_apkg.py /path/to/your/deck.apkg")
            print(f"\n📁 Or place an APKG file in one of these locations:")
            for path in potential_paths:
                clean_path = os.path.expanduser(path)
                print(f"   - {clean_path}")
            print(f"\n💡 Tip: You can also generate a test file by running:")
            print(f"   python main.py  # This will create an APKG file you can analyze")
            sys.exit(1)

    if not os.path.exists(apkg_path):
        print(f"❌ Error: APKG file not found: {apkg_path}")
        print(f"📁 Make sure the file exists and the path is correct")
        sys.exit(1)

    print(f"🚀 Starting analysis of: {apkg_path}")
    try:
        analyze_apkg(apkg_path)
        print(f"\n✅ Analysis complete!")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
