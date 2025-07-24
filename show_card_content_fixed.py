#!/usr/bin/env python3
"""
Simple script to show the actual content of cards in an APKG file.
"""
import sqlite3
import sys
import re
import zipfile
import tempfile
import os


def show_card_content(apkg_path):
    """Extract and display the actual content of cards."""
    try:
        # Extract the APKG file (it's a zip file)
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(apkg_path, "r") as zip_file:
                zip_file.extractall(temp_dir)

            # Find the collection.anki2 file
            collection_path = None
            for file in os.listdir(temp_dir):
                if file.endswith(".anki2"):
                    collection_path = os.path.join(temp_dir, file)
                    break

            if not collection_path:
                print("❌ Could not find .anki2 file in APKG")
                return

            # Connect to the SQLite database
            conn = sqlite3.connect(collection_path)
            cursor = conn.cursor()

            # Get notes data
            cursor.execute("SELECT id, flds FROM notes LIMIT 3")
            notes = cursor.fetchall()

            print(f"📋 CARD CONTENT PREVIEW from {apkg_path}")
            print("=" * 80)

            for i, (note_id, fields) in enumerate(notes, 1):
                print(f"\n🗂️  CARD {i} (ID: {note_id})")
                print("-" * 60)

                # Split fields (Anki uses \x1f as field separator)
                field_list = fields.split("\x1f")

                if len(field_list) >= 2:
                    front = field_list[0]
                    back = field_list[1]

                    # Extract text content from HTML (remove tags)
                    def extract_text(html):
                        # Remove HTML tags but keep line breaks
                        text = re.sub(r"<br/?>", "\n", html)
                        text = re.sub(r"<[^>]+>", "", text)
                        return text.strip()

                    print("🔍 FRONT (Question):")
                    front_text = extract_text(front)
                    print(front_text[:800] + ("..." if len(front_text) > 800 else ""))

                    print(f"\n💡 BACK (Answer):")
                    back_text = extract_text(back)
                    print(back_text[:200] + ("..." if len(back_text) > 200 else ""))

                    # Look specifically for A., B., C., D. patterns
                    options_match = re.search(
                        r"(A\..+?D\.[^\n]+)", front_text, re.DOTALL
                    )
                    if options_match:
                        print(f"\n❓ EXTRACTED OPTIONS:")
                        options = options_match.group(1)
                        print(options)
                    else:
                        print(f"\n⚠️  No A,B,C,D options found in this card")

            conn.close()

    except Exception as e:
        print(f"❌ Error reading APKG file: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 show_card_content.py <path_to_apkg_file>")
        sys.exit(1)

    apkg_path = sys.argv[1]
    show_card_content(apkg_path)
