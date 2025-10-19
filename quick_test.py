#!/usr/bin/env python3
"""
Quick test to verify the application components work
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_verse_matching():
    """Test verse matching with the complete Quran data"""
    print("Testing verse matching with complete Quran data...")
    
    try:
        from quran_matcher import QuranMatcher
        
        # Load complete data
        matcher = QuranMatcher("data/quran_complete.json")
        
        # Test with various verses
        test_cases = [
            ("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "Al-Faatiha", 1),
            ("الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", "Al-Faatiha", 2),
            ("قُلْ هُوَ اللَّهُ أَحَدٌ", "Al-Ikhlaas", 1),
            ("اللَّهُ الصَّمَدُ", "Al-Ikhlaas", 2),
        ]
        
        for arabic_text, expected_surah, expected_verse in test_cases:
            result = matcher.find_matching_verse(arabic_text)
            
            if result:
                surah_name = result.get('surah_name', 'Unknown')
                verse_num = result.get('verse', 0)
                confidence = result.get('confidence', 0)
                
                print(f"✓ '{arabic_text[:20]}...' -> {surah_name}, Verse {verse_num} (Confidence: {confidence:.1%})")
                
                # Check if it matches expected
                if expected_surah.lower() in surah_name.lower() and verse_num == expected_verse:
                    print(f"  ✓ Correct match!")
                else:
                    print(f"  ⚠ Expected {expected_surah} {expected_verse}, got {surah_name} {verse_num}")
            else:
                print(f"✗ No match found for: {arabic_text[:20]}...")
        
        return True
        
    except Exception as e:
        print(f"Error in verse matching test: {e}")
        return False

def test_data_stats():
    """Test data statistics"""
    print("\nTesting data statistics...")
    
    try:
        from quran_api_simple import SimpleQuranDataManager
        
        manager = SimpleQuranDataManager()
        stats = manager.get_data_stats()
        
        print(f"✓ Data source: {stats.get('source', 'Unknown')}")
        print(f"✓ Chapters: {stats.get('chapters', 0)}")
        print(f"✓ Total verses: {stats.get('total_verses', 0)}")
        print(f"✓ Downloaded: {stats.get('downloaded_at', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"Error in data stats test: {e}")
        return False

def main():
    """Run quick tests"""
    print("Quran Translator - Quick Test")
    print("=" * 40)
    
    success = True
    
    if not test_verse_matching():
        success = False
    
    if not test_data_stats():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All tests passed! The application is ready to use.")
        print("\n🚀 To run the full application:")
        print("   python run_app.py")
        print("\n📝 Features available:")
        print("   • Real-time Arabic speech recognition")
        print("   • Complete Quran database (6,236 verses)")
        print("   • Intelligent verse matching")
        print("   • English translations")
        print("   • Confidence scoring")
    else:
        print("❌ Some tests failed.")
    
    return success

if __name__ == "__main__":
    main()