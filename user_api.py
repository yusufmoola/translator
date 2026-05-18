"""
Quran.Foundation User API Client
Manages bookmarks, collections, and reading sessions for authenticated users.
"""

import json
import os
import time
from typing import Dict, List, Optional

import requests

from oauth2_client import OAuth2Client


class QuranUserAPI:
    """Client for Quran.Foundation User-Related APIs v1"""

    def __init__(self, oauth_client: OAuth2Client, data_dir: str = "data"):
        self.oauth = oauth_client
        self.api_base = f"{oauth_client.api_base}/auth/v1"
        self.data_dir = data_dir
        self._local_file = os.path.join(data_dir, ".user_data.json")
        self._local_data = self._load_local_data()

        os.makedirs(data_dir, exist_ok=True)

    def _load_local_data(self) -> Dict:
        """Load locally cached user data"""
        try:
            if os.path.exists(self._local_file):
                with open(self._local_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {"bookmarks": [], "collections": [], "reading_sessions": []}

    def _save_local_data(self):
        """Save user data locally for offline access"""
        try:
            os.makedirs(os.path.dirname(self._local_file), exist_ok=True)
            with open(self._local_file, 'w') as f:
                json.dump(self._local_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _request(self, method: str, endpoint: str,
                 params: Optional[Dict] = None,
                 json_body: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to User API"""
        headers = self.oauth.get_user_headers()
        if not headers:
            return None

        url = f"{self.api_base}/{endpoint}"
        try:
            response = requests.request(
                method, url, headers=headers, params=params, json=json_body, timeout=15
            )
            if response.status_code == 401:
                # Try refresh
                if self.oauth._refresh_user_token():
                    headers = self.oauth.get_user_headers()
                    if headers:
                        response = requests.request(
                            method, url, headers=headers, params=params,
                            json=json_body, timeout=15
                        )
                    else:
                        return None
                else:
                    return None

            response.raise_for_status()

            if response.status_code == 204:
                return {"success": True}
            return response.json()

        except Exception as e:
            print(f"User API error ({method} {endpoint}): {e}")
            return None

    # --- Bookmarks ---

    def get_bookmarks(self, first: int = 50, after: Optional[str] = None) -> Optional[Dict]:
        """Get user's bookmarks"""
        params = {"first": first}
        if after:
            params["after"] = after

        result = self._request("GET", "bookmarks", params=params)
        if result:
            # Cache locally
            bookmarks = result.get("data", result.get("bookmarks", []))
            if isinstance(bookmarks, list):
                self._local_data["bookmarks"] = bookmarks
                self._save_local_data()
        return result

    def create_bookmark(self, verse_key: str, surah_name: str = "",
                        note: str = "") -> Optional[Dict]:
        """Create a bookmark for a verse"""
        body = {
            "verseKey": verse_key,
        }
        if note:
            body["note"] = note

        result = self._request("POST", "bookmarks", json_body=body)
        if result:
            # Add to local cache
            bookmark_entry = {
                "verse_key": verse_key,
                "surah_name": surah_name,
                "note": note,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            self._local_data["bookmarks"].append(bookmark_entry)
            self._save_local_data()
        return result

    def delete_bookmark(self, bookmark_id: str) -> Optional[Dict]:
        """Delete a bookmark"""
        result = self._request("DELETE", f"bookmarks/{bookmark_id}")
        if result:
            self._local_data["bookmarks"] = [
                b for b in self._local_data["bookmarks"]
                if b.get("id") != bookmark_id
            ]
            self._save_local_data()
        return result

    # --- Collections ---

    def get_collections(self, first: int = 50) -> Optional[Dict]:
        """Get user's collections"""
        params = {"first": first}
        result = self._request("GET", "collections", params=params)
        if result:
            collections = result.get("data", result.get("collections", []))
            if isinstance(collections, list):
                self._local_data["collections"] = collections
                self._save_local_data()
        return result

    def create_collection(self, name: str, description: str = "") -> Optional[Dict]:
        """Create a new collection"""
        body = {"name": name}
        if description:
            body["description"] = description

        result = self._request("POST", "collections", json_body=body)
        if result:
            collection_entry = {
                "name": name,
                "description": description,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "items": []
            }
            self._local_data["collections"].append(collection_entry)
            self._save_local_data()
        return result

    def update_collection(self, collection_id: str, name: Optional[str] = None,
                          description: Optional[str] = None) -> Optional[Dict]:
        """Update a collection"""
        body = {}
        if name:
            body["name"] = name
        if description is not None:
            body["description"] = description
        return self._request("PATCH", f"collections/{collection_id}", json_body=body)

    def delete_collection(self, collection_id: str) -> Optional[Dict]:
        """Delete a collection"""
        result = self._request("DELETE", f"collections/{collection_id}")
        if result:
            self._local_data["collections"] = [
                c for c in self._local_data["collections"]
                if c.get("id") != collection_id
            ]
            self._save_local_data()
        return result

    # --- Reading Sessions ---

    def get_reading_sessions(self, first: int = 20) -> Optional[Dict]:
        """Get user's reading sessions"""
        params = {"first": first}
        result = self._request("GET", "reading-sessions", params=params)
        if result:
            sessions = result.get("data", result.get("reading_sessions", []))
            if isinstance(sessions, list):
                self._local_data["reading_sessions"] = sessions
                self._save_local_data()
        return result

    def create_reading_session(self, chapter_number: int, verse_from: int,
                               verse_to: int) -> Optional[Dict]:
        """Log a reading session"""
        body = {
            "chapterNumber": chapter_number,
            "verseFrom": verse_from,
            "verseTo": verse_to,
        }

        result = self._request("POST", "reading-sessions", json_body=body)

        # Always save locally (even if API fails, track locally)
        session_entry = {
            "chapter_number": chapter_number,
            "verse_from": verse_from,
            "verse_to": verse_to,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "synced": result is not None
        }
        self._local_data["reading_sessions"].append(session_entry)
        self._save_local_data()

        return result

    # --- Local data access (for offline/UI display) ---

    def get_local_bookmarks(self) -> List[Dict]:
        """Get locally cached bookmarks"""
        return self._local_data.get("bookmarks", [])

    def get_local_collections(self) -> List[Dict]:
        """Get locally cached collections"""
        return self._local_data.get("collections", [])

    def get_local_reading_sessions(self) -> List[Dict]:
        """Get locally cached reading sessions"""
        return self._local_data.get("reading_sessions", [])

    def add_local_bookmark(self, verse_key: str, surah_name: str = "",
                           arabic: str = "", translation: str = ""):
        """Add a bookmark to local storage (used when offline or not authenticated)"""
        entry = {
            "verse_key": verse_key,
            "surah_name": surah_name,
            "arabic": arabic,
            "translation": translation,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "synced": False
        }
        # Avoid duplicates
        existing_keys = [b.get("verse_key") for b in self._local_data["bookmarks"]]
        if verse_key not in existing_keys:
            self._local_data["bookmarks"].append(entry)
            self._save_local_data()
            return True
        return False

    def add_local_reading_session(self, chapter_number: int, verse_from: int,
                                  verse_to: int, surah_name: str = ""):
        """Add a reading session to local storage"""
        entry = {
            "chapter_number": chapter_number,
            "verse_from": verse_from,
            "verse_to": verse_to,
            "surah_name": surah_name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "synced": False
        }
        self._local_data["reading_sessions"].append(entry)
        self._save_local_data()

    def sync_local_data(self) -> Dict[str, int]:
        """Sync unsynced local data to the API (when user is authenticated)"""
        if not self.oauth.is_user_authenticated():
            return {"error": "Not authenticated"}

        synced = {"bookmarks": 0, "sessions": 0}

        # Sync bookmarks
        for bookmark in self._local_data.get("bookmarks", []):
            if not bookmark.get("synced", True):
                result = self.create_bookmark(
                    bookmark["verse_key"],
                    bookmark.get("surah_name", "")
                )
                if result:
                    bookmark["synced"] = True
                    synced["bookmarks"] += 1

        # Sync reading sessions
        for session in self._local_data.get("reading_sessions", []):
            if not session.get("synced", True):
                result = self.create_reading_session(
                    session["chapter_number"],
                    session["verse_from"],
                    session["verse_to"]
                )
                if result:
                    session["synced"] = True
                    synced["sessions"] += 1

        self._save_local_data()
        return synced
