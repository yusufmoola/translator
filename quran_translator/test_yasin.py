#!/usr/bin/env python3
"""
Test Ya-Sin matching specifically
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quran_matcher import QuranMatcher

def test_yasin_matching():
    """Test Ya-Sin verse matching"""
    print("Testing Ya-Sin (Surah 36) matching...")
    
    matcher = QuranMatcher("data/quran_complete.json")
    
    # Test cases for Ya-Sin
    test_cases = [
        "ياسين",      # Full word
        "يس",         # Short form
        "يٰسٓ",        # API form
    ]
    
    print("\nNormalization test:")
    for text in test_cases:
        normalized = matcher.normalize_arabic_text(text)
        print(f"'{text}' → '{normalized}'")
    
    print("\nMatching test:")
    for text in test_cases:
        print(f"\nTesting: '{text}'")
        result = matcher.find_matching_verse(text)
        
        if result:
            print(f"✓ Found: {result.get('surah_name')} Verse {result.get('verse')} (Confidence: {result.get('confidence', 0):.1%})")
            print(f"  Arabic: {result.get('arabic', '')}")
            print(f"  Translation: {result.get('translation', '')}")
        else:
            print("✗ No match found")
    
    # Also test what's actually in Surah 36, Verse 1
    print("\n" + "="*50)
    print("What's actually in the data for Surah 36:")
    for surah in matcher.quran_data.get('surahs', []):
        if surah.get('number') == 36:
            print(f"Surah: {surah.get('name')}")
            for verse in surah.get('verses', [])[:3]:
                original = verse.get('arabic', '')
                normalized = matcher.normalize_arabic_text(original)
                print(f"Verse {verse.get('number')}:")
                print(f"  Original: {original}")
                print(f"  Normalized: {normalized}")
                print(f"  Translation: {verse.get('translation', '')}")
                print()
            break

def main():
    test_yasin_matching()

if __name__ == "__main__":
    main()