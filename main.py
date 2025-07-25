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

from utils import (
    prompt_credentials,
    prompt_save_location,
    show_completion_message,
    CONFIG_PATH,
    BASE,
    BAG_ID_DEFAULT,
    prompt_url_and_credentials,
    prompt_url_and_credentials_with_url,
    prompt_url_only,
    prompt_url_with_validation,
    load_credentials,
    validate_saved_credentials_for_host,
    show_script_running_dialog,
    close_script_running_dialog,
)
from deck_scraping import selenium_scrape_deck, selenium_scrape_collection
from anki_export import export_hierarchical_apkg, export_apkg


def show_help():
    """Display help information"""
    print(
        """
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
    """
    )


def main():
    print("🎯 UCalgary Anki Card Converter")
    print("=" * 50)

    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        show_help()
        return

    # Check for command line argument first
    if len(sys.argv) > 1:
        base_url_override = sys.argv[1].strip()
        print(f"Using URL from command line: {base_url_override}")
        # Parse URL to determine collection vs deck and extract parameters
        host, is_collection, collection_id, details_url, bag_id = parse_input_url(
            base_url_override
        )
        # Load or prompt for credentials
        email, password = get_credentials(host)
    else:
        # Check if we have saved credentials first
        saved_creds = load_credentials()
        if saved_creds.get("email") and saved_creds.get("password"):
            # We have saved credentials, prompt for URL with validation
            print("Using saved credentials. Please enter URL...")
            full_url = prompt_url_with_validation(
                saved_creds["email"], saved_creds["password"]
            )

            # Parse the URL from the dialog
            host, is_collection, collection_id, details_url, bag_id = parse_input_url(
                full_url
            )

            # Use saved credentials
            email = saved_creds["email"]
            password = saved_creds["password"]
            print(f"📧 Using saved credentials for {email}")
        else:
            # No saved credentials, use unified dialog for both URL and credentials
            print("No saved credentials found. Opening login dialog...")
            email, password, full_url = prompt_url_and_credentials_with_url()

            # Parse the URL from the dialog
            host, is_collection, collection_id, details_url, bag_id = parse_input_url(
                full_url
            )

    # No card limit - process all cards
    card_limit = None

    # Show progress dialog to inform user that script is running
    progress_dialog = show_script_running_dialog()

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
        # Close the progress dialog
        close_script_running_dialog(progress_dialog)

        # Re-prompt for credentials and retry
        email, password = prompt_credentials(host)
        # Note: credentials will be saved only after successful validation in prompt_credentials

        # Show progress dialog again for retry
        progress_dialog = show_script_running_dialog()

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
        # Close progress dialog before exiting
        close_script_running_dialog(progress_dialog)
        sys.exit(1)

    print(f"\n✅ Successfully extracted {len(cards)} cards")

    # Close the progress dialog before showing file save dialog
    close_script_running_dialog(progress_dialog)

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
            is_single_deck=is_single_deck,
        )
    else:
        # Use simple export for basic single-deck scenarios
        export_apkg(data=cards, deck_name=deck_name, path=output_path)

    # Show completion message
    if is_collection:
        deck_count = len(set(card.get("deck_id_source", "unknown") for card in cards))
        print(f"📊 Collection Summary: {deck_count} decks, {len(cards)} total cards")
        show_completion_message(output_path, len(cards))
        print(
            f"📋 Decks included: {', '.join(set(card.get('deck_title', 'Unknown') for card in cards))}"
        )
    else:
        show_completion_message(output_path, len(cards))

    print(f"\n🎉 Process complete! Your Anki deck is ready to import.")


def parse_input_url(base_url_override):
    """Parse the input URL to determine type and extract parameters.

    Returns a 5-tuple of:
        host -- base host portion of the URL
        is_collection -- ``True`` if the URL points to a collection
        collection_id -- collection identifier if applicable
        details_url -- full deck details URL when scraping a single deck
        bag_id -- bag ID query parameter or default value
    """
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
        email = cfg.get("email")  # Fixed: was "username"
        password = cfg.get("password")

        if email and password:
            print(f"📧 Using saved credentials for {email}")
            return email, password

    # Prompt for credentials if not found or incomplete
    print("🔐 Credentials required")
    email, password = prompt_credentials(host)
    return email, password


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
