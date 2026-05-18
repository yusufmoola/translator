"""
Quran.Foundation Content API Client
Fetches Quran text, chapters, verses, and translations via the official API.
Feature-flagged: can be toggled off to use offline/fallback data instead.
"""

import json
import os
import time
from typing import Dict, List, Optional
import requests

from oauth2_client import OAuth2Client


class QuranContentAPI:
    """Client for Quran.Foundation Content API v4"""

    def __init__(self, oauth_client: OAuth2Client, data_dir: str = "data"):
        self.oauth = oauth_client
        self.api_base = f"{oauth_client.api_base}/content/api/v4"
        self.data_dir = data_dir
        self.official_file = os.path.join(data_dir, "quran_official.json")

        os.makedirs(data_dir, exist_ok=True)

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated GET request to Content API"""
        headers = self.oauth.get_content_headers()
        if not headers:
            return None

        url = f"{self.api_base}/{endpoint}"
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 401:
                # Token expired, retry once
                self.oauth._content_token = None
                headers = self.oauth.get_content_headers()
                if not headers:
                    return None
                response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Content API error ({endpoint}): {e}")
            return None

    def get_chapters(self) -> Optional[List[Dict]]:
        """Get list of all chapters"""
        data = self._get("chapters")
        if data:
            return data.get("chapters", [])
        return None

    def get_verses_by_chapter(self, chapter_number: int, translation_id: int = 20,
                              page: int = 1, per_page: int = 50) -> Optional[Dict]:
        """Get verses for a chapter with translation"""
        params = {
            "translations": translation_id,
            "language": "en",
            "page": page,
            "per_page": per_page,
            "fields": "text_uthmani",
        }
        return self._get(f"verses/by_chapter/{chapter_number}", params)

    def get_verse_by_key(self, verse_key: str, translation_id: int = 20) -> Optional[Dict]:
        """Get a specific verse by key (e.g. '1:1')"""
        params = {
            "translations": translation_id,
            "language": "en",
            "fields": "text_uthmani",
        }
        return self._get(f"verses/by_key/{verse_key}", params)

    def search(self, query: str, language: str = "en") -> Optional[Dict]:
        """Search Quran text"""
        params = {"q": query, "language": language}
        return self._get("search", params)

    def download_complete_quran(self, translation_id: int = 20,
                                force_refresh: bool = False,
                                progress_callback=None) -> bool:
        """Download the full Quran via Content API and save locally"""
        if os.path.exists(self.official_file) and not force_refresh:
            print(f"Official Quran data already exists at {self.official_file}")
            return True

        print("Downloading Quran from Quran.Foundation Content API...")

        chapters = self.get_chapters()
        if not chapters:
            print("Failed to fetch chapters list")
            return False

        quran_data = {
            "source": "Quran.Foundation Content API v4",
            "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "surahs": []
        }

        for chapter in chapters:
            chapter_num = chapter.get("id", 0)
            chapter_name = chapter.get("name_simple", f"Surah {chapter_num}")
            chapter_name_arabic = chapter.get("name_arabic", "")
            revelation_place = chapter.get("revelation_place", "")
            verses_count = chapter.get("verses_count", 0)

            all_verses = []
            page = 1
            while True:
                data = self.get_verses_by_chapter(chapter_num, translation_id, page=page)
                if not data:
                    break

                verses = data.get("verses", [])
                if not verses:
                    break

                for v in verses:
                    translation_text = ""
                    translations = v.get("translations", [])
                    if translations:
                        translation_text = translations[0].get("text", "")
                        # Strip HTML tags from translation
                        import re
                        translation_text = re.sub(r'<[^>]+>', '', translation_text)

                    verse_entry = {
                        "number": v.get("verse_number", 0),
                        "verse_key": v.get("verse_key", ""),
                        "arabic": v.get("text_uthmani", ""),
                        "translation": translation_text,
                        "juz": v.get("juz_number", 0),
                        "page": v.get("page_number", 0)
                    }
                    all_verses.append(verse_entry)

                pagination = data.get("pagination", {})
                if page >= pagination.get("total_pages", 1):
                    break
                page += 1
                time.sleep(0.05)

            surah_info = {
                "number": chapter_num,
                "name": chapter_name,
                "name_arabic": chapter_name_arabic,
                "revelation_place": revelation_place,
                "verses_count": len(all_verses),
                "verses": all_verses
            }
            quran_data["surahs"].append(surah_info)

            if progress_callback:
                progress_callback(chapter_num, 114)
            elif chapter_num % 10 == 0:
                print(f"   Downloaded {chapter_num}/114 chapters...")

            time.sleep(0.05)

        # Save to file
        with open(self.official_file, 'w', encoding='utf-8') as f:
            json.dump(quran_data, f, ensure_ascii=False, indent=2)

        total_verses = sum(len(s["verses"]) for s in quran_data["surahs"])
        print(f"Official Quran data saved: {len(quran_data['surahs'])} chapters, {total_verses} verses")
        return True

    def get_data_file(self) -> Optional[str]:
        """Get path to downloaded official data file"""
        if os.path.exists(self.official_file):
            return self.official_file
        return None
