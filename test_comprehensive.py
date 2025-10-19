#!/usr/bin/env python3
"""
Comprehensive test of various Quran verses
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quran_matcher import QuranMatcher

def test_various_verses():
    """Test various verse types"""
    print("Comprehensive Verse Matching Test")
    print("=" * 50)
    
    matcher = QuranMatcher("data/quran_complete.json")
    
    # Test cases from different surahs and types
    test_cases = [
        # Al-Fatihah
        ("الحمد لله رب العالمين", "Al-Fatihah", 2),
        ("الرحمن الرحيم", "Al-Fatihah", 3),
        
        # Mysterious letters
        ("ياسين", "Ya-Sin", 1),
        ("يس", "Ya-Sin", 1),
        
        # Al-Kafirun
        ("قل يا ايها الكافرون", "Al-Kafirun", 1),
        
        # Al-Ikhlas
        ("قل هو الله احد", "Al-Ikhlas", 1),
        ("الله الصمد", "Al-Ikhlas", 2),
        
        # Al-Nas
        ("قل اعوذ برب الناس", "An-Nas", 1),
        
        # Al-Falaq  
        ("قل اعوذ برب الفلق", "Al-Falaq", 1),
    ]
    
    successful = 0
    total = len(test_cases)
    
    for i, (text, expected_surah, expected_verse) in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{text}'")
        result = matcher.find_matching_verse(text)
        
        if result:
            surah_name = result.get('surah_name', 'Unknown')
            verse_num = result.get('verse', 0)
            confidence = result.get('confidence', 0)
            
            print(f"   ✓ Found: {surah_name}, Verse {verse_num} (Confidence: {confidence:.1%})")
            
            # Check if it's the expected match (flexible matching on surah name)
            # Handle common name variations
            name_matches = (
                expected_surah.lower() in surah_name.lower() or
                surah_name.lower() in expected_surah.lower() or
                # Specific mappings for common variations
                (expected_surah == "Al-Fatihah" and "faatiha" in surah_name.lower()) or
                (expected_surah == "Ya-Sin" and "yaseen" in surah_name.lower()) or
                (expected_surah == "Al-Kafirun" and "kaafiroon" in surah_name.lower()) or
                (expected_surah == "Al-Ikhlas" and "ikhlaas" in surah_name.lower()) or
                (expected_surah == "An-Nas" and "naas" in surah_name.lower())
            )
            
            if name_matches and verse_num == expected_verse:
                print(f"   ✅ CORRECT MATCH!")
                successful += 1
            else:
                print(f"   ⚠️  Expected: {expected_surah} {expected_verse}, Got: {surah_name} {verse_num}")
        else:
            print(f"   ✗ No match found")
            print(f"   ❌ Expected: {expected_surah} {expected_verse}")
    
    print(f"\n" + "=" * 50)
    print(f"Results: {successful}/{total} correct matches ({successful/total*100:.1f}%)")
    
    if successful >= total * 0.8:  # 80% success rate
        print("🎉 Excellent! The matching system is working well.")
    elif successful >= total * 0.6:  # 60% success rate
        print("👍 Good! The matching system is working reasonably well.")
    else:
        print("⚠️  The matching system needs more improvement.")

def main():
    test_various_verses()

if __name__ == "__main__":
    main()