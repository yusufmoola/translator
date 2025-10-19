"""
Quran Foundation API Integration
Fetches Quran text and translations from api.quran.foundation
"""

import requests
import json
import os
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin

class QuranFoundationAPI:
    def __init__(self, base_url: str = "https://api.quran.com/api/v4/"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuranTranslator/1.0',
            'Accept': 'application/json'
        })
        self.session.timeout = 10
        
    def get_chapters(self) -> Optional[List[Dict]]:
        """Get list of all chapters (surahs)"""
        try:
            response = self.session.get(urljoin(self.base_url, "chapters"))
            response.raise_for_status()
            data = response.json()
            return data.get('chapters', [])
        except requests.RequestException as e:
            print(f"Error fetching chapters: {e}")
            return None
    
    def get_chapter_info(self, chapter_id: int) -> Optional[Dict]:
        """Get detailed information about a specific chapter"""
        try:
            response = self.session.get(urljoin(self.base_url, f"chapters/{chapter_id}"))
            response.raise_for_status()
            data = response.json()
            return data.get('chapter', {})
        except requests.RequestException as e:
            print(f"Error fetching chapter {chapter_id}: {e}")
            return None
    
    def get_verses(self, chapter_id: int, translation_id: int = 20) -> Optional[List[Dict]]:
        """
        Get verses for a chapter with translation
        translation_id 20 = Saheeh International (widely available)
        """
        try:
            # Try different endpoint patterns
            endpoints_to_try = [
                f"verses/by_chapter/{chapter_id}?translations={translation_id}",
                f"chapters/{chapter_id}/verses?translations={translation_id}",
                f"quran/verses/{chapter_id}?translations={translation_id}"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    url = urljoin(self.base_url, endpoint)
                    response = self.session.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Try different response structures
                    verses = data.get('verses', data.get('data', []))
                    if verses:
                        return verses
                        
                except requests.RequestException:
                    continue
            
            print(f"All endpoints failed for chapter {chapter_id}")
            return None
            
        except Exception as e:
            print(f"Error fetching verses for chapter {chapter_id}: {e}")
            return None
    
    def get_verse_by_key(self, verse_key: str, translation_id: int = 131) -> Optional[Dict]:
        """
        Get a specific verse by key (e.g., "1:1" for Al-Fatihah verse 1)
        """
        try:
            url = urljoin(self.base_url, f"verses/by_key/{verse_key}")
            params = {'translations': translation_id}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('verse', {})
        except requests.RequestException as e:
            print(f"Error fetching verse {verse_key}: {e}")
            return None
    
    def get_available_translations(self) -> Optional[List[Dict]]:
        """Get list of available translations"""
        try:
            response = self.session.get(urljoin(self.base_url, "resources/translations"))
            response.raise_for_status()
            data = response.json()
            return data.get('translations', [])
        except requests.RequestException as e:
            print(f"Error fetching translations: {e}")
            return None

class QuranDataManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.api = QuranFoundationAPI()
        self.quran_file = os.path.join(data_dir, "quran_complete.json")
        self.translations_file = os.path.join(data_dir, "translations.json")
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
    
    def download_complete_quran(self, translation_id: int = 131, force_refresh: bool = False) -> bool:
        """
        Download complete Quran with translation
        translation_id 131 = Dr. Mustafa Khattab, the Clear Quran (English)
        """
        if os.path.exists(self.quran_file) and not force_refresh:
            print(f"Quran data already exists at {self.quran_file}")
            return True
        
        print("Downloading complete Quran from Quran Foundation API...")
        
        try:
            # Get chapters list
            chapters = self.api.get_chapters()
            if not chapters:
                print("Failed to fetch chapters list")
                return False
            
            print(f"Found {len(chapters)} chapters")
            
            # Build complete Quran data structure
            quran_data = {
                "source": "Quran Foundation API",
                "translation_id": translation_id,
                "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "surahs": []
            }
            
            # Download each chapter
            for i, chapter in enumerate(chapters, 1):
                chapter_id = chapter['id']
                chapter_name = chapter['name_simple']
                chapter_arabic = chapter['name_arabic']
                
                print(f"Downloading Chapter {i}/{len(chapters)}: {chapter_name}")
                
                # Get verses for this chapter
                verses = self.api.get_verses(chapter_id, translation_id)
                if not verses:
                    print(f"Failed to fetch verses for chapter {chapter_id}")
                    continue
                
                # Process verses
                processed_verses = []
                for verse in verses:
                    # Extract Arabic text
                    arabic_text = verse.get('text_uthmani', '')
                    
                    # Extract translation
                    translation = ""
                    if 'translations' in verse and verse['translations']:
                        translation = verse['translations'][0].get('text', '')
                    
                    processed_verse = {
                        "number": verse.get('verse_number', 0),
                        "verse_key": verse.get('verse_key', ''),
                        "arabic": arabic_text,
                        "translation": translation,
                        "juz": verse.get('juz_number', 0),
                        "hizb": verse.get('hizb_number', 0),
                        "page": verse.get('page_number', 0)
                    }
                    processed_verses.append(processed_verse)
                
                # Add chapter to quran data
                chapter_data = {
                    "number": chapter_id,
                    "name": chapter_name,
                    "name_arabic": chapter_arabic,
                    "revelation_place": chapter.get('revelation_place', ''),
                    "verses_count": chapter.get('verses_count', 0),
                    "verses": processed_verses
                }
                quran_data["surahs"].append(chapter_data)
                
                # Small delay to be respectful to the API
                time.sleep(0.1)
            
            # Save to file
            with open(self.quran_file, 'w', encoding='utf-8') as f:
                json.dump(quran_data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Complete Quran saved to {self.quran_file}")
            print(f"Total chapters: {len(quran_data['surahs'])}")
            
            return True
            
        except Exception as e:
            print(f"Error downloading Quran: {e}")
            return False
    
    def download_translations_list(self) -> bool:
        """Download list of available translations"""
        try:
            translations = self.api.get_available_translations()
            if not translations:
                return False
            
            # Save translations list
            with open(self.translations_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Translations list saved to {self.translations_file}")
            print(f"Available translations: {len(translations)}")
            
            # Print some popular English translations
            english_translations = [t for t in translations if 'english' in t.get('language_name', '').lower()]
            print("\nPopular English translations:")
            for trans in english_translations[:10]:
                print(f"  ID {trans['id']}: {trans['name']} by {trans.get('author_name', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"Error downloading translations: {e}")
            return False
    
    def load_quran_data(self) -> Optional[Dict]:
        """Load Quran data from local file"""
        try:
            if not os.path.exists(self.quran_file):
                print(f"Quran data file not found: {self.quran_file}")
                return None
            
            with open(self.quran_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✓ Loaded Quran data with {len(data.get('surahs', []))} chapters")
            return data
            
        except Exception as e:
            print(f"Error loading Quran data: {e}")
            return None
    
    def get_data_stats(self) -> Dict:
        """Get statistics about the downloaded data"""
        data = self.load_quran_data()
        if not data:
            return {"error": "No data available"}
        
        total_verses = sum(len(surah.get('verses', [])) for surah in data.get('surahs', []))
        
        return {
            "chapters": len(data.get('surahs', [])),
            "total_verses": total_verses,
            "translation_id": data.get('translation_id'),
            "downloaded_at": data.get('downloaded_at'),
            "source": data.get('source')
        }

def main():
    """Test the API and download data"""
    manager = QuranDataManager()
    
    print("Quran Foundation API Test")
    print("=" * 30)
    
    # Download translations list
    print("1. Downloading translations list...")
    manager.download_translations_list()
    
    # Download complete Quran
    print("\n2. Downloading complete Quran...")
    success = manager.download_complete_quran()
    
    if success:
        print("\n3. Data statistics:")
        stats = manager.get_data_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    print("\nDone!")

if __name__ == "__main__":
    main()