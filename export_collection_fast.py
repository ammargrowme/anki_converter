#!/usr/bin/env python3
"""
Export collection 125 using the enhanced fast method for comparison
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".ENV")


def export_collection_with_fast_method():
    """Export collection 125 using enhanced fast method"""

    # Import the enhanced scraping and export functions
    try:
        from enhanced_scraping import enhanced_scrape_collection
        from anki_export import export_hierarchical_apkg

        print("✅ Enhanced modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import enhanced modules: {e}")
        return None

    email = os.getenv("UC_EMAIL")
    password = os.getenv("UC_PASSWORD")
    base_url = os.getenv("UC_BASE_URL", "https://cards.ucalgary.ca")

    # Collection parameters
    collection_id = "125"
    collection_url = f"{base_url}/collection/{collection_id}"

    print("🚀 Fast Method Collection Export Test")
    print("=" * 50)
    print(f"📧 Email: {email}")
    print(f"🌐 Base URL: {base_url}")
    print(f"📦 Collection: {collection_id}")
    print(f"🔗 URL: {collection_url}")

    # Start timing
    total_start_time = time.time()

    print(f"\n⚡ Starting enhanced collection scraping...")
    scraping_start_time = time.time()

    try:
        # Use enhanced scraping for the collection
        cards, decks_info, collection_title = enhanced_scrape_collection(
            collection_id=collection_id,
            email=email,
            password=password,
            base_host=base_url,
            card_limit=None,  # Get all cards
        )

        scraping_duration = time.time() - scraping_start_time

        print(f"✅ Enhanced scraping completed!")
        print(f"   📊 Total cards: {len(cards)}")
        print(f"   📚 Total decks: {len(decks_info)}")
        print(
            f"   ⏱️  Scraping time: {scraping_duration:.1f} seconds ({scraping_duration/60:.1f} minutes)"
        )
        print(f"   📋 Collection title: {collection_title}")

        # Show deck breakdown
        print(f"\n📚 Deck breakdown:")
        for deck_name, deck_data in decks_info.items():
            deck_card_count = len([c for c in cards if c.get("deck_name") == deck_name])
            print(f"   • {deck_name}: {deck_card_count} cards")

        # Export to Anki
        print(f"\n📦 Starting Anki export...")
        export_start_time = time.time()

        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Collection_125_FastMethod_{timestamp}.apkg"

        # Export using hierarchical structure
        export_hierarchical_apkg(
            cards=cards,
            decks_info=decks_info,
            collection_title=collection_title,
            filename=filename,
        )

        export_duration = time.time() - export_start_time
        total_duration = time.time() - total_start_time

        print(f"✅ Export completed!")
        print(f"   📁 File: {filename}")
        print(f"   ⏱️  Export time: {export_duration:.1f} seconds")
        print(
            f"   ⏱️  Total time: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)"
        )

        # Calculate performance metrics
        cards_per_second = (
            len(cards) / scraping_duration if scraping_duration > 0 else 0
        )
        print(f"   🚀 Speed: {cards_per_second:.2f} cards/second")

        return {
            "filename": filename,
            "total_cards": len(cards),
            "total_decks": len(decks_info),
            "scraping_time": scraping_duration,
            "export_time": export_duration,
            "total_time": total_duration,
            "cards_per_second": cards_per_second,
            "collection_title": collection_title,
            "decks_info": decks_info,
        }

    except Exception as e:
        duration = time.time() - total_start_time
        print(f"❌ Export failed: {e}")
        print(f"   ⏱️  Time taken: {duration:.1f} seconds")
        return None


def main():
    """Main export function"""

    # Check credentials
    email = os.getenv("UC_EMAIL")
    password = os.getenv("UC_PASSWORD")

    if not email or not password:
        print("❌ Please set UC_EMAIL and UC_PASSWORD in your .ENV file")
        return

    # Run the export
    result = export_collection_with_fast_method()

    if result:
        print(f"\n🎉 SUCCESS! Collection exported with fast method")
        print(f"📁 File: {result['filename']}")
        print(f"📊 Stats: {result['total_cards']} cards, {result['total_decks']} decks")
        print(f"⚡ Speed: {result['total_time']/60:.1f} minutes total")
        print(
            f"\n💡 Next step: Compare this file with your original export using analyze_apkg.py"
        )
    else:
        print(f"❌ Export failed")


if __name__ == "__main__":
    main()
