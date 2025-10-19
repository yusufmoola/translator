"""
Simple Quran API Integration
Uses multiple reliable APIs as fallbacks
"""

import requests
import json
import os
import time
from typing import Dict, List, Optional

class SimpleQuranAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuranTranslator/1.0',
            'Accept': 'application/json'
        })
        self.session.timeout = 10
        
        # Multiple API endpoints as fallbacks
        self.apis = [
            {
                'name': 'Al-Quran Cloud',
                'base_url': 'https://api.alquran.cloud/v1/',
                'chapters_endpoint': 'surah',
                'verses_endpoint': 'surah/{}/editions/quran-uthmani,en.sahih'
            },
            {
                'name': 'Quran.com API',
                'base_url': 'https://api.quran.com/api/v4/',
                'chapters_endpoint': 'chapters',
                'verses_endpoint': 'verses/by_chapter/{}?translations=20'
            }
        ]
    
    def get_complete_quran(self) -> Optional[Dict]:
        """Get complete Quran using the first working API"""
        for api_config in self.apis:
            print(f"Trying {api_config['name']}...")
            try:
                quran_data = self._fetch_from_api(api_config)
                if quran_data and quran_data.get('surahs'):
                    print(f"✓ Successfully fetched from {api_config['name']}")
                    return quran_data
            except Exception as e:
                print(f"✗ {api_config['name']} failed: {e}")
                continue
        
        print("All APIs failed, creating enhanced sample data")
        return self._create_enhanced_sample_data()
    
    def _fetch_from_api(self, api_config: Dict) -> Optional[Dict]:
        """Fetch Quran data from a specific API"""
        base_url = api_config['base_url']
        
        if 'alquran.cloud' in base_url:
            return self._fetch_from_alquran_cloud(api_config)
        elif 'quran.com' in base_url:
            return self._fetch_from_quran_com(api_config)
        
        return None
    
    def _fetch_from_alquran_cloud(self, api_config: Dict) -> Optional[Dict]:
        """Fetch from Al-Quran Cloud API"""
        base_url = api_config['base_url']
        
        quran_data = {
            "source": "Al-Quran Cloud API",
            "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "surahs": []
        }
        
        # Get all surahs (1-114)
        for surah_num in range(1, 115):
            try:
                # Fetch surah with Arabic and English
                url = f"{base_url}surah/{surah_num}/editions/quran-uthmani,en.sahih"
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
                print(f"✓ Downloaded Surah {surah_num}: {surah_info['name']} ({len(verses)} verses)")
                
                # Small delay to be respectful
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error fetching surah {surah_num}: {e}")
                continue
        
        return quran_data
    
    def _fetch_from_quran_com(self, api_config: Dict) -> Optional[Dict]:
        """Fetch from Quran.com API (placeholder - needs proper implementation)"""
        # This would need to be implemented based on the actual API structure
        return None
    
    def _create_enhanced_sample_data(self) -> Dict:
        """Create enhanced sample data with more surahs"""
        return {
            "source": "Enhanced Sample Data",
            "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "surahs": [
                {
                    "number": 1,
                    "name": "Al-Fatihah",
                    "name_arabic": "الفاتحة",
                    "revelation_place": "makkah",
                    "verses_count": 7,
                    "verses": [
                        {
                            "number": 1,
                            "verse_key": "1:1",
                            "arabic": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
                            "translation": "In the name of Allah, the Entirely Merciful, the Especially Merciful.",
                            "juz": 1,
                            "page": 1
                        },
                        {
                            "number": 2,
                            "verse_key": "1:2",
                            "arabic": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
                            "translation": "[All] praise is [due] to Allah, Lord of the worlds -",
                            "juz": 1,
                            "page": 1
                        },
                        {
                            "number": 3,
                            "verse_key": "1:3",
                            "arabic": "الرَّحْمَٰنِ الرَّحِيمِ",
                            "translation": "The Entirely Merciful, the Especially Merciful,",
                            "juz": 1,
                            "page": 1
                        },
                        {
                            "number": 4,
                            "verse_key": "1:4",
                            "arabic": "مَالِكِ يَوْمِ الدِّينِ",
                            "translation": "Sovereign of the Day of Recompense.",
                            "juz": 1,
                            "page": 1
                        },
                        {
                            "number": 5,
                            "verse_key": "1:5",
                            "arabic": "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
                            "translation": "It is You we worship and You we ask for help.",
                            "juz": 1,
                            "page": 1
                        },
                        {
                            "number": 6,
                            "verse_key": "1:6",
                            "arabic": "اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ",
                            "translation": "Guide us to the straight path -",
                            "juz": 1,
                            "page": 1
                        },
                        {
                            "number": 7,
                            "verse_key": "1:7",
                            "arabic": "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ",
                            "translation": "The path of those upon whom You have bestowed favor, not of those who have evoked [Your] anger or of those who are astray.",
                            "juz": 1,
                            "page": 1
                        }
                    ]
                },
                {
                    "number": 112,
                    "name": "Al-Ikhlas",
                    "name_arabic": "الإخلاص",
                    "revelation_place": "makkah",
                    "verses_count": 4,
                    "verses": [
                        {
                            "number": 1,
                            "verse_key": "112:1",
                            "arabic": "قُلْ هُوَ اللَّهُ أَحَدٌ",
                            "translation": "Say, \"He is Allah, [who is] One,",
                            "juz": 30,
                            "page": 604
                        },
                        {
                            "number": 2,
                            "verse_key": "112:2",
                            "arabic": "اللَّهُ الصَّمَدُ",
                            "translation": "Allah, the Eternal Refuge.",
                            "juz": 30,
                            "page": 604
                        },
                        {
                            "number": 3,
                            "verse_key": "112:3",
                            "arabic": "لَمْ يَلِدْ وَلَمْ يُولَدْ",
                            "translation": "He neither begets nor is born,",
                            "juz": 30,
                            "page": 604
                        },
                        {
                            "number": 4,
                            "verse_key": "112:4",
                            "arabic": "وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ",
                            "translation": "Nor is there to Him any equivalent.\"",
                            "juz": 30,
                            "page": 604
                        }
                    ]
                }
            ]
        }

class SimpleQuranDataManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.api = SimpleQuranAPI()
        self.quran_file = os.path.join(data_dir, "quran_complete.json")
        
        os.makedirs(data_dir, exist_ok=True)
    
    def download_complete_quran(self, force_refresh: bool = False) -> bool:
        """Download complete Quran using the simple API"""
        if os.path.exists(self.quran_file) and not force_refresh:
            print(f"Quran data already exists at {self.quran_file}")
            return True
        
        print("Downloading complete Quran...")
        
        try:
            quran_data = self.api.get_complete_quran()
            if not quran_data:
                return False
            
            # Save to file
            with open(self.quran_file, 'w', encoding='utf-8') as f:
                json.dump(quran_data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Complete Quran saved to {self.quran_file}")
            print(f"Total chapters: {len(quran_data['surahs'])}")
            
            return True
            
        except Exception as e:
            print(f"Error downloading Quran: {e}")
            return False
    
    def get_data_stats(self) -> Dict:
        """Get statistics about the downloaded data"""
        try:
            if not os.path.exists(self.quran_file):
                return {"error": "No data available"}
            
            with open(self.quran_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            total_verses = sum(len(surah.get('verses', [])) for surah in data.get('surahs', []))
            
            return {
                "chapters": len(data.get('surahs', [])),
                "total_verses": total_verses,
                "source": data.get('source'),
                "downloaded_at": data.get('downloaded_at')
            }
        except Exception as e:
            return {"error": str(e)}

def main():
    """Test the simple API"""
    manager = SimpleQuranDataManager()
    
    print("Simple Quran API Test")
    print("=" * 30)
    
    success = manager.download_complete_quran()
    
    if success:
        stats = manager.get_data_stats()
        print("\nData statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    print("\nDone!")

if __name__ == "__main__":
    main()