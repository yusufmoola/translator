#!/usr/bin/env python3
"""
Test the improved verse matching
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quran_matcher import QuranMatcher

def test_normalization():
    """Test the text normalization"""
    print("Testing Arabic text normalization...")
    
    matcher = QuranMatcher("data/quran_complete.json")
    
    # Test cases from your speech recognition
    test_cases = [
        "الحمد لله",  # Your speech recognition
        "لله رب العالمين",  # Your speech recognition  
        "الرحمن الرحيم",  # Your speech recognition
        "مالك يوم الدين",  # Your speech recognition
        "بسم الله الرحمن الرحيم",  # Bismillah
    ]
    
    print("\nNormalization results:")
    for text in test_cases:
        normalized = matcher.normalize_arabic_text(text)
        print(f"Original: {text}")
        print(f"Normalized: {normalized}")
        print()
    
    print("\nFirst few verses from API data (normalized):")
    for surah in matcher.quran_data.get('surahs', [])[:1]:  # Just Al-Fatihah
        for verse in surah.get('verses', [])[:5]:  # First 5 verses
            original = verse.get('arabic', '')
            normalized = matcher.normalize_arabic_text(original)
            print(f"Verse {verse.get('number')}: {original}")
            print(f"Normalized: {normalized}")
            print()

def test_matching():
    """Test verse matching with your exact input"""
    print("Testing verse matching...")
    
    matcher = QuranMatcher("data/quran_complete.json")
    
    # Your exact speech recognition results
    test_inputs = [
        "الحمد لله",
        "لله رب العالمين", 
        "الرحمن الرحيم",
        "مالك يوم الدين",
    ]
    
    for text in test_inputs:
        print(f"\nTesting: '{text}'")
        result = matcher.find_matching_verse(text)
        
        if result:
            print(f"✓ Found: {result.get('surah_name')} Verse {result.get('verse')} (Confidence: {result.get('confidence', 0):.1%})")
            print(f"  Arabic: {result.get('arabic', '')}")
            print(f"  Translation: {result.get('translation', '')}")
        else:
            print("✗ No match found")

def main():
    """Run tests"""
    print("Verse Matching Test")
    print("=" * 40)
    
    test_normalization()
    test_matching()

if __name__ == "__main__":
    main()