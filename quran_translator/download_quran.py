#!/usr/bin/env python3
"""
Standalone script to download Quran data from Quran Foundation API
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quran_api import QuranDataManager

def main():
    print("Quran Data Downloader")
    print("=" * 30)
    print("This will download the complete Quran with English translation")
    print("from the Quran Foundation API (api.quran.foundation)")
    print()
    
    # Ask user for confirmation
    response = input("Do you want to proceed? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Download cancelled.")
        return
    
    # Initialize data manager
    manager = QuranDataManager()
    
    print("\n1. Downloading available translations...")
    translations_success = manager.download_translations_list()
    
    if translations_success:
        print("✓ Translations list downloaded")
    else:
        print("✗ Failed to download translations list")
    
    print("\n2. Downloading complete Quran...")
    print("   Using translation: Dr. Mustafa Khattab, the Clear Quran")
    print("   This may take a few minutes...")
    
    # Download with default translation (ID 131 - Clear Quran)
    success = manager.download_complete_quran(translation_id=131)
    
    if success:
        print("\n✓ Download completed successfully!")
        
        # Show statistics
        stats = manager.get_data_stats()
        print("\nData Statistics:")
        print(f"  Chapters: {stats['chapters']}")
        print(f"  Total Verses: {stats['total_verses']}")
        print(f"  Translation: {stats['translation_id']}")
        print(f"  Downloaded: {stats['downloaded_at']}")
        
        print(f"\nData saved to: {manager.quran_file}")
        print("\nYou can now use the complete Quran data in the translator app!")
        
    else:
        print("\n✗ Download failed!")
        print("Please check your internet connection and try again.")

if __name__ == "__main__":
    main()