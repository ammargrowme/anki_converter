#!/usr/bin/env python3
"""
Simple script to show the actual content of cards in an APKG file.
"""
import sqlite3
import sys
import re


def show_card_content(apkg_path):
    """Extract and display the actual content of cards."""
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(apkg_path)
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
                print(front_text[:500] + ("..." if len(front_text) > 500 else ""))

                print(f"\n💡 BACK (Answer):")
                back_text = extract_text(back)
                print(back_text[:200] + ("..." if len(back_text) > 200 else ""))

                # Look specifically for A., B., C., D. patterns
                options_match = re.search(r"(A\..+?D\.[^\n]+)", front_text, re.DOTALL)
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
