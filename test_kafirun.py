#!/usr/bin/env python3
"""
Test Al-Kafirun matching specifically
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quran_matcher import QuranMatcher

def test_kafirun_matching():
    """Test Al-Kafirun verse matching"""
    print("Testing Al-Kafirun (Surah 109) matching...")
    
    matcher = QuranMatcher("data/quran_complete.json")
    
    # Your exact input
    user_input = "قل يا ايها الكافرون"
    
    # What's in the API
    api_text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ قُلْ يَٰٓأَيُّهَا ٱلْكَٰفِرُونَ"
    
    print(f"User input: {user_input}")
    print(f"API text: {api_text}")
    print()
    
    # Test normalization
    user_normalized = matcher.normalize_arabic_text(user_input)
    api_normalized = matcher.normalize_arabic_text(api_text)
    
    print("After normalization:")
    print(f"User: {user_normalized}")
    print(f"API:  {api_normalized}")
    print()
    
    # Test similarity
    similarity = matcher.calculate_similarity(user_normalized, api_normalized)
    print(f"Similarity score: {similarity:.3f}")
    print()
    
    # Test matching
    result = matcher.find_matching_verse(user_input)
    if result:
        print(f"✓ Found: {result.get('surah_name')} Verse {result.get('verse')} (Confidence: {result.get('confidence', 0):.1%})")
        print(f"  Arabic: {result.get('arabic', '')}")
        print(f"  Translation: {result.get('translation', '')}")
    else:
        print("✗ No match found")
    
    # Test just the core part without Bismillah
    core_api = "قُلْ يَٰٓأَيُّهَا ٱلْكَٰفِرُونَ"
    core_normalized = matcher.normalize_arabic_text(core_api)
    print(f"\nCore API text: {core_api}")
    print(f"Core normalized: {core_normalized}")
    
    core_similarity = matcher.calculate_similarity(user_normalized, core_normalized)
    print(f"Core similarity: {core_similarity:.3f}")

def main():
    test_kafirun_matching()

if __name__ == "__main__":
    main()