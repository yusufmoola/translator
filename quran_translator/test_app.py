#!/usr/bin/env python3
"""
Test script for the Quran Translator components
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    
    try:
        from quran_matcher import QuranMatcher
        print("✓ QuranMatcher imported successfully")
    except ImportError as e:
        print(f"✗ QuranMatcher import failed: {e}")
        return False
    
    try:
        from quran_api_simple import SimpleQuranDataManager
        print("✓ SimpleQuranDataManager imported successfully")
    except ImportError as e:
        print(f"✗ SimpleQuranDataManager import failed: {e}")
        return False
    
    return True

def test_quran_data():
    """Test Quran data loading and matching"""
    print("\nTesting Quran data...")
    
    try:
        from quran_matcher import QuranMatcher
        
        # Try to load complete data first, fall back to sample
        if os.path.exists("data/quran_complete.json"):
            matcher = QuranMatcher("data/quran_complete.json")
            print("✓ Loaded complete Quran data")
        else:
            matcher = QuranMatcher("data/sample_quran.json")
            print("✓ Loaded sample Quran data")
        
        # Test verse matching
        test_texts = [
            "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
            "قُلْ هُوَ اللَّهُ أَحَدٌ"
        ]
        
        for text in test_texts:
            result = matcher.find_matching_verse(text)
            if result:
                print(f"✓ Found match for: {text[:20]}... -> Surah {result.get('surah')}, Verse {result.get('verse')}")
            else:
                print(f"- No match for: {text[:20]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Quran data test failed: {e}")
        return False

def test_speech_recognition():
    """Test speech recognition import (without actually using microphone)"""
    print("\nTesting speech recognition...")
    
    try:
        import speech_recognition as sr
        print("✓ SpeechRecognition library available")
        
        # Test if we can create a recognizer
        try:
            recognizer = sr.Recognizer()
            print("✓ Speech recognizer created successfully")
        except AttributeError:
            # Try alternative import
            from speech_recognition import Recognizer
            recognizer = Recognizer()
            print("✓ Speech recognizer created successfully (alternative import)")
        
        return True
        
    except ImportError as e:
        print(f"✗ SpeechRecognition import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Speech recognition test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Quran Translator Component Tests")
    print("=" * 40)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test Quran data
    if not test_quran_data():
        all_passed = False
    
    # Test speech recognition
    if not test_speech_recognition():
        all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("✓ All tests passed! The application should work correctly.")
        print("\nTo run the full application:")
        print("python app_integrated.py")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)