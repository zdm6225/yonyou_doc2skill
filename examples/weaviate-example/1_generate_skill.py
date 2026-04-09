#!/usr/bin/env python3
"""
Step 1: Generate Skill for Weaviate

This script:
1. Scrapes React documentation (limited to 20 pages for demo)
2. Packages the skill in Weaviate format
3. Saves to output/react-weaviate.json

Usage:
    python 1_generate_skill.py
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("Step 1: Generating Skill for Weaviate")
    print("=" * 60)

    # Check if yonyou-doc2skill is installed
    try:
        result = subprocess.run(
            ["yonyou-doc2skill", "--version"],
            capture_output=True,
            text=True
        )
        print(f"\n✅ yonyou-doc2skill found: {result.stdout.strip()}")
    except FileNotFoundError:
        print("\n❌ yonyou-doc2skill not found!")
        print("Install it with: pip install yonyou-doc2skill")
        sys.exit(1)

    # Step 1: Scrape React docs (small sample for demo)
    print("\n📥 Step 1/2: Scraping React documentation (20 pages)...")
    print("This may take 1-2 minutes...\n")

    scrape_result = subprocess.run(
        [
            "yonyou-doc2skill", "scrape",
            "--config", "configs/react.json",
            "--max-pages", "20",
        ],
        capture_output=True,
        text=True
    )

    if scrape_result.returncode != 0:
        print(f"❌ Scraping failed:\n{scrape_result.stderr}")
        sys.exit(1)

    print("✅ Scraping completed!")

    # Step 2: Package for Weaviate
    print("\n📦 Step 2/2: Packaging for Weaviate...\n")

    package_result = subprocess.run(
        [
            "yonyou-doc2skill", "package",
            "output/react",
            "--target", "weaviate",
        ],
        capture_output=True,
        text=True
    )

    if package_result.returncode != 0:
        print(f"❌ Packaging failed:\n{package_result.stderr}")
        sys.exit(1)

    # Show the output
    print(package_result.stdout)

    # Check if output file exists
    output_file = Path("output/react-weaviate.json")
    if output_file.exists():
        size_kb = output_file.stat().st_size / 1024
        print(f"📄 File size: {size_kb:.1f} KB")
        print(f"📂 Location: {output_file.absolute()}")
        print("\n✅ Ready for upload! Next step: python 2_upload_to_weaviate.py")
    else:
        print("❌ Output file not found!")
        sys.exit(1)

if __name__ == "__main__":
    main()
