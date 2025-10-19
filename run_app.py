#!/usr/bin/env python3
"""
Startup script for Quran Translator
Handles data download and launches the application
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Check if all required dependencies are available"""
    missing = []
    
    try:
        import speech_recognition
    except ImportError:
        missing.append("SpeechRecognition")
    
    try:
        import pyaudio
    except ImportError:
        missing.append("pyaudio")
    
    try:
        import requests
    except ImportError:
        missing.append("requests")
    
    if missing:
        print("Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nPlease install them with:")
        print("pip install " + " ".join(missing))
        return False
    
    return True

def check_quran_data():
    """Check if Quran data is available"""
    complete_data = os.path.exists("data/quran_complete.json")
    sample_data = os.path.exists("data/sample_quran.json")
    
    return complete_data, sample_data

def download_quran_data():
    """Download complete Quran data"""
    try:
        from unified_quran_api import UnifiedQuranAPI
        
        print("Downloading complete Quran data...")
        manager = UnifiedQuranAPI()
        success = manager.download_complete_quran()
        
        if success:
            stats = manager.get_data_stats()
            print(f"✓ Downloaded {stats['chapters']} chapters with {stats['total_verses']} verses")
            print(f"Source: {stats.get('source', 'Unknown')}")
            return True
        else:
            print("✗ Failed to download Quran data")
            return False
            
    except Exception as e:
        print(f"Error downloading data: {e}")
        return False

def main():
    """Main startup function"""
    print("Quran Recitation Translator")
    print("=" * 30)
    
    # Check dependencies
    print("1. Checking dependencies...")
    if not check_dependencies():
        return False
    print("✓ All dependencies available")
    
    # Check Quran data
    print("\n2. Checking Quran data...")
    complete_data, sample_data = check_quran_data()
    
    if complete_data:
        print("✓ Complete Quran data available")
    elif sample_data:
        print("⚠ Only sample data available")
        
        # Ask user if they want to download complete data
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        response = messagebox.askyesno(
            "Download Complete Quran?",
            "Only sample Quran data is available.\n\n"
            "Would you like to download the complete Quran with translations?\n"
            "This will improve recognition accuracy significantly.\n\n"
            "Download size: ~2MB, Time: ~30 seconds"
        )
        
        root.destroy()
        
        if response:
            if download_quran_data():
                print("✓ Complete Quran data downloaded")
            else:
                print("⚠ Using sample data")
        else:
            print("⚠ Using sample data")
    else:
        print("⚠ No Quran data found, downloading...")
        if not download_quran_data():
            print("✗ Failed to download data, application may not work properly")
    
    # Launch application
    print("\n3. Starting Quran Translator...")
    try:
        from app_integrated import QuranTranslatorApp
        
        app = QuranTranslatorApp()
        app.run()
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)