#!/usr/bin/env python3
"""
Batch test script for scraping 15 cities of varying sizes.
Tests the pipeline's generalizability across different city government websites.
"""
import os
import sys
import time
from pathlib import Path

# Ensure we can import pipeline modules
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.run import run

# 15 cities categorized by size, all with significant tourism
CITIES = {
    "large": [
        "New Orleans City Council",           # 390k, major tourism
        "Las Vegas City Council",             # 650k, tourism capital
        "Orlando City Council",               # 310k, theme park hub
        "San Diego City Council",             # 1.4M, coastal tourism
        "Seattle City Council",               # 750k, tech & tourism
    ],
    "medium": [
        "Charleston City Council",            # 150k, historic tourism
        "Savannah City Council",              # 150k, historic tourism
        "Santa Fe City Council",              # 88k, arts & culture tourism
        "Asheville City Council",             # 95k, mountain tourism
        "Key West City Commission",           # 25k, island tourism (medium for tourism impact)
    ],
    "small": [
        "Park City Council",                  # 8k, ski resort tourism
        "Sedona City Council",                # 10k, desert tourism
        "Napa City Council",                  # 80k, wine tourism
        "Aspen City Council",                 # 7k, ski resort tourism
        "Carmel-by-the-Sea City Council",     # 4k, coastal tourism
    ]
}

def main():
    print("=" * 80)
    print("BATCH CITY COUNCIL SCRAPER TEST")
    print("Testing 15 cities: 5 large, 5 medium, 5 small")
    print("All cities selected for significant tourism activity")
    print("=" * 80)
    print()

    results = []
    total_start = time.time()

    for size, cities in CITIES.items():
        print(f"\n{'=' * 80}")
        print(f"Testing {size.upper()} cities ({len(cities)} total)")
        print(f"{'=' * 80}\n")

        for i, city in enumerate(cities, 1):
            print(f"\n[{size.upper()} {i}/{len(cities)}] Processing: {city}")
            print("-" * 80)

            city_start = time.time()

            try:
                # Run the pipeline
                run(city)

                city_duration = time.time() - city_start
                results.append({
                    "city": city,
                    "size": size,
                    "status": "SUCCESS",
                    "duration": city_duration
                })

                print(f"✓ Completed in {city_duration:.1f}s")

            except Exception as e:
                city_duration = time.time() - city_start
                results.append({
                    "city": city,
                    "size": size,
                    "status": "FAILED",
                    "duration": city_duration,
                    "error": str(e)
                })

                print(f"✗ Failed after {city_duration:.1f}s")
                print(f"  Error: {e}")

            print("-" * 80)

    # Summary
    total_duration = time.time() - total_start

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    failed_count = len(results) - success_count

    print(f"\nTotal cities tested: {len(results)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Success rate: {success_count/len(results)*100:.1f}%")
    print(f"Total duration: {total_duration/60:.1f} minutes")
    print(f"Average time per city: {total_duration/len(results):.1f}s")

    # By size category
    print("\nBy size category:")
    for size in ["large", "medium", "small"]:
        size_results = [r for r in results if r["size"] == size]
        size_success = sum(1 for r in size_results if r["status"] == "SUCCESS")
        print(f"  {size.capitalize()}: {size_success}/{len(size_results)} successful")

    # Failed cities
    if failed_count > 0:
        print("\nFailed cities:")
        for r in results:
            if r["status"] == "FAILED":
                print(f"  - {r['city']}")
                print(f"    Error: {r.get('error', 'Unknown')}")

    print("\n" + "=" * 80)
    print("Check data/outputs/ for CSV files and data/reports/ for summary reports")
    print("=" * 80)

if __name__ == "__main__":
    main()
