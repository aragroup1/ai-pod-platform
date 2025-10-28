#!/usr/bin/env python3
"""
Import generated keywords to the database via API
Supports batch processing and optional Google Ads validation
"""

import json
import requests
import time
from pathlib import Path
from typing import List, Dict, Optional

# Configuration
API_BASE_URL = "https://backend-production-9f0f.up.railway.app"
KEYWORDS_FILE = "pod_keywords.json"
BATCH_SIZE = 50  # Process 50 keywords at a time

def read_keywords(filepath: str) -> List[Dict]:
    """Read keywords from JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def import_keywords_batch(keywords: List[Dict], validate: bool = False) -> Optional[Dict]:
    """
    Import a batch of keywords via the API
    
    Args:
        keywords: List of keyword dictionaries
        validate: Whether to validate with Google Ads Keyword Planner
    
    Returns:
        Response from API or None if failed
    """
    
    endpoint = f"{API_BASE_URL}/api/v1/trends/import"
    
    payload = {
        "keywords": keywords,
        "validate_with_google": validate
    }
    
    try:
        print(f"   📤 Sending {len(keywords)} keywords to API...")
        
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minute timeout for Google validation
        )
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return None

def main():
    print("=" * 60)
    print("🚀 POD KEYWORDS IMPORTER")
    print("=" * 60)
    
    # Check if keywords file exists
    if not Path(KEYWORDS_FILE).exists():
        print(f"\n❌ Error: {KEYWORDS_FILE} not found!")
        print("   Run generate_keywords.py first!")
        return
    
    # Read keywords
    print(f"\n📖 Reading keywords from {KEYWORDS_FILE}...")
    keywords = read_keywords(KEYWORDS_FILE)
    print(f"✅ Loaded {len(keywords)} keywords")
    
    # Ask about Google validation
    print("\n" + "=" * 60)
    print("⚠️  GOOGLE KEYWORD PLANNER VALIDATION")
    print("=" * 60)
    print("\n📊 Two Options:")
    print("\n   1. WITH Google Validation (RECOMMENDED)")
    print("      • Real search volumes from Google")
    print("      • Competition data")
    print("      • Bid estimates")
    print("      • Takes 2-3 hours for 1000+ keywords")
    print("      • Requires GOOGLE_ADS_REFRESH_TOKEN")
    print("\n   2. WITHOUT Validation (FAST)")
    print("      • Estimated volumes only")
    print("      • No competition data")
    print("      • Completes instantly")
    print("      • Good for testing")
    
    validate_input = input("\n❓ Validate with Google? (y/N): ").strip().lower()
    validate = validate_input == 'y'
    
    if validate:
        print("\n⚠️  IMPORTANT: Make sure you've set GOOGLE_ADS_REFRESH_TOKEN")
        print("   in your Railway environment variables!")
        confirm = input("\n   Press Enter to continue or Ctrl+C to cancel...")
    
    # Import in batches
    print("\n" + "=" * 60)
    print(f"📦 IMPORTING {len(keywords)} KEYWORDS")
    print("=" * 60)
    print(f"\nBatch size: {BATCH_SIZE} keywords per request")
    
    if validate:
        print("⏱️  Estimated time: 2-3 hours (with Google validation)")
    else:
        print("⏱️  Estimated time: 5-10 minutes (no validation)")
    
    print("\n" + "-" * 60)
    
    total_stored = 0
    total_validated = 0
    failed_batches = []
    
    total_batches = (len(keywords) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(0, len(keywords), BATCH_SIZE):
        batch = keywords[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        
        print(f"\n📦 Batch {batch_num}/{total_batches}")
        print(f"   Keywords: {len(batch)}")
        
        start_time = time.time()
        result = import_keywords_batch(batch, validate=validate)
        elapsed = time.time() - start_time
        
        if result and result.get('success'):
            stored = result.get('keywords_stored', 0)
            validated_count = result.get('keywords_validated', 0)
            potential = result.get('potential_listings', 0)
            
            total_stored += stored
            total_validated += validated_count
            
            print(f"   ✅ Success!")
            print(f"   📥 Stored: {stored} keywords")
            if validate:
                print(f"   ✓ Validated: {validated_count} keywords")
            print(f"   🎨 Potential listings: {potential}")
            print(f"   ⏱️  Time: {elapsed:.1f}s")
        else:
            print(f"   ❌ Failed!")
            failed_batches.append(batch_num)
        
        # Progress update
        processed = min(i + BATCH_SIZE, len(keywords))
        progress = (processed / len(keywords)) * 100
        print(f"\n   Progress: {processed}/{len(keywords)} ({progress:.1f}%)")
        
        # Brief pause between batches
        if i + BATCH_SIZE < len(keywords):
            time.sleep(1)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 IMPORT COMPLETE")
    print("=" * 60)
    
    print(f"\nKeywords processed:  {len(keywords)}")
    print(f"Keywords stored:     {total_stored}")
    
    if validate:
        print(f"Keywords validated:  {total_validated}")
    
    print(f"Potential listings:  {total_stored * 8} (×8 styles)")
    
    if failed_batches:
        print(f"\n⚠️  Failed batches:    {len(failed_batches)}")
        print(f"   Batch numbers: {', '.join(map(str, failed_batches))}")
    else:
        print("\n✅ All batches imported successfully!")
    
    # Next steps
    print("\n" + "=" * 60)
    print("🎨 NEXT STEPS")
    print("=" * 60)
    print("\n1. Go to your dashboard:")
    print("   https://frontend-production-23f8.up.railway.app")
    print("\n2. Click 'Generate Products' button")
    print("\n3. Watch your inventory grow!")
    print(f"\n4. You should see ~{total_stored * 8} new product variations")
    
    # High-volume keywords note
    high_vol_keywords = [k for k in keywords if k.get('estimated_volume') == 'high']
    if high_vol_keywords:
        print("\n" + "-" * 60)
        print("💡 TIP: High-Volume Keywords")
        print("-" * 60)
        print(f"\nYou have {len(high_vol_keywords)} high-volume keywords!")
        print("These need 100+ designs each:")
        print("\nTop 10 high-volume keywords:")
        for i, kw in enumerate(high_vol_keywords[:10], 1):
            print(f"   {i:2d}. {kw['keyword']}")
        print("\n➡️  Generate multiple design variations for these!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Import cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
