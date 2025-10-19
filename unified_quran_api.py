"""
Unified Quran API Manager
Handles both official Quran Foundation API and fallback APIs
"""

import requests
import json
import os
import time
from typing import Dict, List, Optional
from config import config

class UnifiedQuranAPI:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuranTranslator/1.0',
            'Accept': 'application/json'
        })
        self.session.timeout = 30
        
        # File paths for different data sources
        self.official_file = os.path.join(data_dir, "quran_official.json")
        self.fallback_file = os.path.join(data_dir, "quran_complete.json")
        
        os.makedirs(data_dir, exist_ok=True)
    
    def download_from_fallback_api(self, force_refresh: bool = False) -> bool:
        """Download from reliable fallback API (Al-Quran Cloud)"""
        if os.path.exists(self.fallback_file) and not force_refresh:
            print(f"Fallback Quran data already exists at {self.fallback_file}")
            return True
        
        print("📖 Downloading from Al-Quran Cloud API (fallback)...")
        
        try:
            quran_data = {
                "source": "Al-Quran Cloud API (Fallback)",
                "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "surahs": []
            }
            
            # Download all surahs (1-114)
            for surah_num in range(1, 115):
                try:
                    # Fetch surah with Arabic and English
                    url = f"https://api.alquran.cloud/v1/surah/{surah_num}/editions/quran-uthmani,en.sahih"
                    response = self.session.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get('code') != 200:
                        continue
                    
                    surah_data = data.get('data', [])
                    if len(surah_data) < 2:
                        continue
                    
                    arabic_surah = surah_data[0]
                    english_surah = surah_data[1]
                    
                    # Process verses
                    verses = []
                    arabic_ayahs = arabic_surah.get('ayahs', [])
                    english_ayahs = english_surah.get('ayahs', [])
                    
                    for i, arabic_ayah in enumerate(arabic_ayahs):
                        english_text = ""
                        if i < len(english_ayahs):
                            english_text = english_ayahs[i].get('text', '')
                        
                        verse = {
                            "number": arabic_ayah.get('numberInSurah', i + 1),
                            "verse_key": f"{surah_num}:{arabic_ayah.get('numberInSurah', i + 1)}",
                            "arabic": arabic_ayah.get('text', ''),
                            "translation": english_text,
                            "juz": arabic_ayah.get('juz', 0),
                            "page": arabic_ayah.get('page', 0)
                        }
                        verses.append(verse)
                    
                    # Add surah info
                    surah_info = {
                        "number": surah_num,
                        "name": arabic_surah.get('englishName', f'Surah {surah_num}'),
                        "name_arabic": arabic_surah.get('name', ''),
                        "revelation_place": arabic_surah.get('revelationType', '').lower(),
                        "verses_count": len(verses),
                        "verses": verses
                    }
                    
                    quran_data["surahs"].append(surah_info)
                    
                    if surah_num % 10 == 0:  # Progress update every 10 surahs
                        print(f"   Downloaded {surah_num}/114 chapters...")
                    
                    # Small delay to be respectful
                    time.sleep(0.05)
                    
                except Exception as e:
                    print(f"Error fetching surah {surah_num}: {e}")
                    continue
            
            # Save to file
            with open(self.fallback_file, 'w', encoding='utf-8') as f:
                json.dump(quran_data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Fallback Quran data saved to {self.fallback_file}")
            print(f"Total chapters: {len(quran_data['surahs'])}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error downloading from fallback API: {e}")
            return False
    
    def download_from_official_api(self, force_refresh: bool = False) -> bool:
        """Download from official Quran Foundation API (when available)"""
        if not config.has_official_api():
            print("Official API credentials not available")
            return False
        
        if os.path.exists(self.official_file) and not force_refresh:
            print(f"Official Quran data already exists at {self.official_file}")
            return True
        
        print("📖 Attempting to download from Official Quran Foundation API...")
        
        try:
            # This would use the QuranFoundationOAuth class
            # For now, return False to use fallback
            print("⚠ Official API endpoints not yet configured, using fallback")
            return False
            
        except Exception as e:
            print(f"✗ Official API failed: {e}")
            return False
    
    def download_complete_quran(self, prefer_official: bool = True, force_refresh: bool = False) -> bool:
        """Download complete Quran, trying official API first if preferred"""
        
        if prefer_official and config.has_official_api():
            print("🔄 Trying official API first...")
            if self.download_from_official_api(force_refresh):
                return True
            print("🔄 Official API failed, falling back to public API...")
        
        # Use fallback API
        return self.download_from_fallback_api(force_refresh)
    
    def get_best_data_file(self) -> Optional[str]:
        """Get the path to the best available data file"""
        if os.path.exists(self.official_file):
            return self.official_file
        elif os.path.exists(self.fallback_file):
            return self.fallback_file
        else:
            return None
    
    def get_data_stats(self) -> Dict:
        """Get statistics about the available data"""
        data_file = self.get_best_data_file()
        
        if not data_file:
            return {"error": "No Quran data available"}
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            total_verses = sum(len(surah.get('verses', [])) for surah in data.get('surahs', []))
            
            return {
                "data_file": os.path.basename(data_file),
                "chapters": len(data.get('surahs', [])),
                "total_verses": total_verses,
                "source": data.get('source', 'Unknown'),
                "downloaded_at": data.get('downloaded_at', 'Unknown'),
                "is_official": "official" in data_file
            }
        except Exception as e:
            return {"error": str(e)}

def main():
    """Test the unified API"""
    print("Unified Quran API Test")
    print("=" * 30)
    
    manager = UnifiedQuranAPI()
    
    # Test download
    success = manager.download_complete_quran()
    
    if success:
        stats = manager.get_data_stats()
        print("\nData Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    print("\nDone!")

if __name__ == "__main__":
    main()