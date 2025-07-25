#!/usr/bin/env python3
"""
Performance Benchmark Script

Compare the old Selenium-based approach vs the new fast async approach
"""

import time
import asyncio
import sys
from typing import List, Dict

# Import both approaches
from deck_scraping import selenium_scrape_deck, selenium_scrape_collection
from fast_scraping import (
    fast_scrape_deck,
    fast_scrape_collection,
    run_fast_scraping_sync,
)


def benchmark_deck_scraping(
    deck_id: str,
    email: str,
    password: str,
    base_host: str,
    bag_id: str,
    card_limit: int = 10,
):
    """Benchmark deck scraping performance"""
    print("🏁 DECK SCRAPING BENCHMARK")
    print("=" * 50)

    results = {}

    # Test 1: Original Selenium approach
    print("\n🐌 Testing ORIGINAL Selenium approach...")
    start_time = time.time()
    try:
        cards_selenium = selenium_scrape_deck(
            deck_id=deck_id,
            email=email,
            password=password,
            base_host=base_host,
            bag_id=bag_id,
            card_limit=card_limit,
        )
        selenium_time = time.time() - start_time
        results["selenium"] = {
            "time": selenium_time,
            "cards": len(cards_selenium),
            "cards_per_second": (
                len(cards_selenium) / selenium_time if selenium_time > 0 else 0
            ),
        }
        print(
            f"✅ Selenium: {len(cards_selenium)} cards in {selenium_time:.1f}s ({results['selenium']['cards_per_second']:.2f} cards/sec)"
        )
    except Exception as e:
        print(f"❌ Selenium failed: {e}")
        results["selenium"] = {"time": float("inf"), "cards": 0, "cards_per_second": 0}

    # Test 2: New fast async approach
    print("\n⚡ Testing NEW Fast Async approach...")
    start_time = time.time()
    try:
        cards_fast = run_fast_scraping_sync(
            fast_scrape_deck(deck_id, email, password, base_host, bag_id, card_limit)
        )
        fast_time = time.time() - start_time
        results["fast"] = {
            "time": fast_time,
            "cards": len(cards_fast),
            "cards_per_second": len(cards_fast) / fast_time if fast_time > 0 else 0,
        }
        print(
            f"✅ Fast Async: {len(cards_fast)} cards in {fast_time:.1f}s ({results['fast']['cards_per_second']:.2f} cards/sec)"
        )
    except Exception as e:
        print(f"❌ Fast Async failed: {e}")
        results["fast"] = {"time": float("inf"), "cards": 0, "cards_per_second": 0}

    # Calculate performance improvement
    print("\n📊 PERFORMANCE COMPARISON")
    print("-" * 30)

    if results["selenium"]["time"] > 0 and results["fast"]["time"] > 0:
        speedup = results["selenium"]["time"] / results["fast"]["time"]
        throughput_improvement = (
            results["fast"]["cards_per_second"]
            / results["selenium"]["cards_per_second"]
            if results["selenium"]["cards_per_second"] > 0
            else float("inf")
        )

        print(f"⏱️  Time Comparison:")
        print(f"   • Selenium:  {results['selenium']['time']:.1f} seconds")
        print(f"   • Fast Async: {results['fast']['time']:.1f} seconds")
        print(f"   • Speedup:    {speedup:.1f}x faster")

        print(f"\n🎯 Throughput Comparison:")
        print(
            f"   • Selenium:   {results['selenium']['cards_per_second']:.2f} cards/sec"
        )
        print(f"   • Fast Async: {results['fast']['cards_per_second']:.2f} cards/sec")
        print(f"   • Improvement: {throughput_improvement:.1f}x throughput")

        if speedup >= 5:
            print(f"\n🚀 EXCELLENT! {speedup:.1f}x speedup achieved!")
        elif speedup >= 2:
            print(f"\n✅ GOOD! {speedup:.1f}x speedup achieved!")
        else:
            print(f"\n⚠️  Modest improvement: {speedup:.1f}x speedup")
    else:
        print("❌ Cannot calculate comparison - one method failed")

    return results


def benchmark_collection_scraping(
    collection_id: str, email: str, password: str, base_host: str, deck_limit: int = 3
):
    """Benchmark collection scraping performance"""
    print("\n\n🏁 COLLECTION SCRAPING BENCHMARK")
    print("=" * 50)

    results = {}

    # Test 1: Original Selenium approach (limited decks)
    print("\n🐌 Testing ORIGINAL Selenium approach...")
    start_time = time.time()
    try:
        cards_selenium, decks_info_selenium, title_selenium = (
            selenium_scrape_collection(
                collection_id=collection_id,
                email=email,
                password=password,
                base_host=base_host,
                card_limit=deck_limit,  # Use as deck limit for collections
            )
        )
        selenium_time = time.time() - start_time
        results["selenium"] = {
            "time": selenium_time,
            "cards": len(cards_selenium),
            "decks": len(decks_info_selenium),
            "cards_per_second": (
                len(cards_selenium) / selenium_time if selenium_time > 0 else 0
            ),
        }
        print(
            f"✅ Selenium: {len(cards_selenium)} cards from {len(decks_info_selenium)} decks in {selenium_time:.1f}s"
        )
    except Exception as e:
        print(f"❌ Selenium failed: {e}")
        results["selenium"] = {
            "time": float("inf"),
            "cards": 0,
            "decks": 0,
            "cards_per_second": 0,
        }

    # Test 2: New fast async approach
    print("\n⚡ Testing NEW Fast Async approach...")
    start_time = time.time()
    try:
        cards_fast, decks_info_fast, title_fast = run_fast_scraping_sync(
            fast_scrape_collection(
                collection_id, email, password, base_host, deck_limit
            )
        )
        fast_time = time.time() - start_time
        results["fast"] = {
            "time": fast_time,
            "cards": len(cards_fast),
            "decks": len(decks_info_fast),
            "cards_per_second": len(cards_fast) / fast_time if fast_time > 0 else 0,
        }
        print(
            f"✅ Fast Async: {len(cards_fast)} cards from {len(decks_info_fast)} decks in {fast_time:.1f}s"
        )
    except Exception as e:
        print(f"❌ Fast Async failed: {e}")
        results["fast"] = {
            "time": float("inf"),
            "cards": 0,
            "decks": 0,
            "cards_per_second": 0,
        }

    # Calculate performance improvement
    print("\n📊 COLLECTION PERFORMANCE COMPARISON")
    print("-" * 40)

    if results["selenium"]["time"] > 0 and results["fast"]["time"] > 0:
        speedup = results["selenium"]["time"] / results["fast"]["time"]

        print(f"⏱️  Time Comparison:")
        print(f"   • Selenium:   {results['selenium']['time']:.1f} seconds")
        print(f"   • Fast Async: {results['fast']['time']:.1f} seconds")
        print(f"   • Speedup:    {speedup:.1f}x faster")

        print(f"\n📊 Content Comparison:")
        print(
            f"   • Selenium:   {results['selenium']['cards']} cards, {results['selenium']['decks']} decks"
        )
        print(
            f"   • Fast Async: {results['fast']['cards']} cards, {results['fast']['decks']} decks"
        )

        if speedup >= 10:
            print(f"\n🚀 INCREDIBLE! {speedup:.1f}x collection speedup!")
        elif speedup >= 5:
            print(f"\n🎯 EXCELLENT! {speedup:.1f}x collection speedup!")
        else:
            print(f"\n✅ GOOD! {speedup:.1f}x collection speedup!")

    return results


def estimate_real_world_performance(benchmark_results: Dict):
    """Estimate real-world performance for large collections"""
    print("\n\n📈 REAL-WORLD PERFORMANCE ESTIMATES")
    print("=" * 45)

    if "selenium" in benchmark_results and "fast" in benchmark_results:
        selenium_cps = benchmark_results["selenium"]["cards_per_second"]
        fast_cps = benchmark_results["fast"]["cards_per_second"]

        if selenium_cps > 0 and fast_cps > 0:
            scenarios = [
                ("Small deck (50 cards)", 50),
                ("Medium deck (200 cards)", 200),
                ("Large deck (500 cards)", 500),
                ("Small collection (10 decks, ~500 cards)", 500),
                ("Large collection (50 decks, ~2500 cards)", 2500),
            ]

            print("Estimated processing times:")
            print()

            for scenario, card_count in scenarios:
                selenium_time = card_count / selenium_cps
                fast_time = card_count / fast_cps
                speedup = selenium_time / fast_time

                print(f"{scenario}:")
                print(f"  • Original method: {selenium_time/60:.1f} minutes")
                print(f"  • Fast method:     {fast_time/60:.1f} minutes")
                print(
                    f"  • Time saved:      {(selenium_time-fast_time)/60:.1f} minutes"
                )
                print()


def main():
    """Main benchmark function"""
    if len(sys.argv) < 6:
        print(
            "Usage: python benchmark.py <email> <password> <base_host> <deck_id> <bag_id> [collection_id]"
        )
        print(
            "Example: python benchmark.py user@ucalgary.ca password123 https://cards.ucalgary.ca 12345 67890 [collection123]"
        )
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    base_host = sys.argv[3]
    deck_id = sys.argv[4]
    bag_id = sys.argv[5]
    collection_id = sys.argv[6] if len(sys.argv) > 6 else None

    print("🔬 UCalgary Scraping Performance Benchmark")
    print("==========================================")
    print(f"🎯 Target: {base_host}")
    print(f"📧 User: {email}")
    print(f"🔧 Deck ID: {deck_id}, Bag ID: {bag_id}")
    if collection_id:
        print(f"📦 Collection ID: {collection_id}")

    # Benchmark deck scraping
    deck_results = benchmark_deck_scraping(
        deck_id, email, password, base_host, bag_id, card_limit=10
    )

    # Benchmark collection scraping if collection_id provided
    collection_results = None
    if collection_id:
        collection_results = benchmark_collection_scraping(
            collection_id, email, password, base_host, deck_limit=3
        )

    # Show real-world estimates
    estimate_real_world_performance(deck_results)

    print("\n🎉 Benchmark Complete!")
    print("\nNext steps to use fast scraping:")
    print("1. Install new dependencies: pip install aiohttp aiofiles")
    print("2. Import fast_scraping in your code")
    print("3. Use run_fast_scraping_sync() wrapper for sync compatibility")


if __name__ == "__main__":
    main()
