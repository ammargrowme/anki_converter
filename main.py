#!/usr/bin/env python3
"""
UCalgary Anki Card Converter - Main Entry Point

This modular script converts UCalgary Cards to Anki format with comprehensive
background extraction, patient organization, and hierarchical deck structure.

Modules:
- utils.py: Configuration and utility functions
- auth.py: Authentication handling
- image_processing.py: Image extraction and portrait filtering
- content_extraction.py: Background content and metadata extraction
- sequential_extraction.py: Sequential card extraction for non-print decks
- deck_scraping.py: Main scraping logic for decks and collections
- anki_export.py: Anki package generation with hierarchical structure
"""

import os
import sys
import json
from urllib.parse import urlparse, parse_qs

from utils import prompt_credentials, prompt_save_location, show_completion_message, CONFIG_PATH, BASE, BAG_ID_DEFAULT
from deck_scraping import selenium_scrape_deck, selenium_scrape_collection
from anki_export import export_hierarchical_apkg, export_apkg


def show_help():
    """Display help information"""
    print("""
📖 USAGE:
  python main.py [URL]
  python main.py [--help|-h|help]

📋 EXAMPLES:
  python main.py https://cards.ucalgary.ca/collection/12345
  python main.py https://cards.ucalgary.ca/details/67890?bag_id=123

🔧 FEATURES:
  • Converts UCalgary Cards to Anki format
  • Extracts comprehensive background content and images
  • Organizes cards by patient with hierarchical deck structure
  • Supports both individual decks and entire collections
  • Automatically handles authentication and image processing

💡 TIP: The script will prompt for credentials and save location if not provided.
    """)


def main():
    print("🎯 UCalgary Anki Card Converter")
    print("=" * 50)

    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_help()
        return

    # Check for command line argument first
    if len(sys.argv) > 1:
        base_url_override = sys.argv[1].strip()
        print(f"Using URL from command line: {base_url_override}")
    else:
        # Prompt URL if no command line argument
        base_url_override = input("Enter UCalgary collection or deck URL: ").strip()

    # No card limit - process all cards
    card_limit = None

    # Parse URL to determine collection vs deck and extract parameters
    host, is_collection, collection_id, details_url, bag_id = parse_input_url(base_url_override)

    # Load or prompt for credentials
    email, password = get_credentials(host)

    # Scrape cards based on URL type
    try:
        if is_collection:
            print(f"\n🔍 Processing collection {collection_id}...")
            cards, decks_info, collection_title = selenium_scrape_collection(
                collection_id=collection_id,
                email=email,
                password=password,
                base_host=host,
                card_limit=card_limit,
            )
            deck_name = collection_title
            deck_id = collection_id
            is_single_deck = False

        else:
            print(f"\n🔍 Processing individual deck...")
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
            decks_info = {}
            is_single_deck = True

    except RuntimeError as e:
        print(f"Login error during scrape: {e}")
        # Re-prompt for credentials and retry
        email, password = prompt_credentials(host)
        save_credentials(email, password)
        
        # Retry scraping with new credentials
        if is_collection:
            cards, decks_info, collection_title = selenium_scrape_collection(
                collection_id=collection_id,
                email=email,
                password=password,
                base_host=host,
                card_limit=card_limit,
            )
            deck_name = collection_title
            deck_id = collection_id
            is_single_deck = False
        else:
            cards = selenium_scrape_deck(
                deck_id=None,
                email=email,
                password=password,
                base_host=host,
                bag_id=bag_id,
                details_url=details_url,
                card_limit=card_limit,
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
            decks_info = {}
            is_single_deck = True

    if not cards:
        print("❌ No cards were extracted. Please check the URL and try again.")
        sys.exit(1)

    print(f"\n✅ Successfully extracted {len(cards)} cards")

    # Prompt for save location
    default_filename = f"{deck_name}.apkg"
    output_path = prompt_save_location(default_filename)

    # Export the deck using hierarchical structure
    print(f"\n📦 Exporting to Anki format...")
    
    # Use hierarchical export for collections OR when we have patient data
    has_patients = any(
        card.get("patient_info") and card.get("patient_info") != "Unknown Patient"
        for card in cards
    )
    
    # Check if we have sequential cards
    has_sequential = any(card.get("is_sequential") for card in cards)

    if is_collection or has_patients or has_sequential:
        # Use hierarchical export for better organization
        export_hierarchical_apkg(
            data=cards,
            collection_name=deck_name,
            decks_info=decks_info,
            path=output_path,
            is_single_deck=is_single_deck
        )
    else:
        # Use simple export for basic single-deck scenarios
        export_apkg(
            data=cards,
            deck_name=deck_name,
            path=output_path
        )

    # Show completion message
    if is_collection:
        deck_count = len(set(card.get("deck_id_source", "unknown") for card in cards))
        print(f"📊 Collection Summary: {deck_count} decks, {len(cards)} total cards")
        show_completion_message(output_path, len(cards))
        print(f"📋 Decks included: {', '.join(set(card.get('deck_title', 'Unknown') for card in cards))}")
    else:
        show_completion_message(output_path, len(cards))
    
    print(f"\n🎉 Process complete! Your Anki deck is ready to import.")


def parse_input_url(base_url_override):
    """Parse the input URL to determine type and extract parameters"""
    host = BASE
    is_collection = False
    collection_id = None
    details_url = None
    bag_id = BAG_ID_DEFAULT

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

    return host, is_collection, collection_id, details_url, bag_id


def get_credentials(host):
    """Load credentials from config or prompt user"""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as cf:
            cfg = json.load(cf)
        email = cfg.get("username")
        password = cfg.get("password")
        
        if email and password:
            print(f"📧 Using saved credentials for {email}")
            return email, password
    
    # Prompt for credentials if not found or incomplete
    print("🔐 Credentials required")
    email, password = prompt_credentials(host)
    save_credentials(email, password)
    return email, password


def save_credentials(email, password):
    """Save credentials to config file"""
    with open(CONFIG_PATH, "w") as cf:
        json.dump({"username": email, "password": password}, cf)
    print(f"💾 Credentials saved")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
